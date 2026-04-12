"""
玩家类 - 商鞅
"""

import pygame
import random
from __init__ import GRID_SIZE, YELLOW, GREEN, BLUE, RED, CYAN, WHITE
from bullet import Bullet
from scene import Ground, Wall, Platform, Door, Trap,EndPoint  # 导入场景物体

class GameObject:
    """基础游戏对象类"""
    def __init__(self, x, y, char, color, visible=True):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.visible = visible
        self.rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
    
    def update_rect(self):
        self.rect = pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
    
    def draw(self, screen, font):
        if self.visible:
            text_surface = font.render(self.char, True, self.color)
            text_rect = text_surface.get_rect(center=(self.x * GRID_SIZE + GRID_SIZE//2, 
                                                      self.y * GRID_SIZE + GRID_SIZE//2))
            screen.blit(text_surface, text_rect)
    
    def collides_with(self, other):
        return self.rect.colliderect(other.rect)


class ShangYang:
    """玩家角色 - 商鞅"""
    def __init__(self, x, y):
        # 玩家主体 - 竖排排列
        self.body_parts = {
            "head": GameObject(x, y-2, "头", WHITE, True),
            "shang": GameObject(x, y-1, "商", YELLOW, True),
            "left_hand": GameObject(x-1, y-1, "手", WHITE, True),
            "right_hand": GameObject(x+1, y-1, "手", WHITE, True),
            "yang": GameObject(x, y, "鞅", YELLOW, True),
            "left_leg": GameObject(x-1, y+1, "腿", WHITE, True),
            "right_leg": GameObject(x+1, y+1, "腿", WHITE, True)
        }
        
        # 主位置（以"商"为中心）
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.fall_check_timer = 0
        self.fall_check_interval = 5  # 每5帧检查一次
        self.big_jump_timer=0
        # 游戏属性
        self.level = 1
        self.exp = 0
        self.exp_to_next_level = 5
        self.max_health = 10
        self.health = 10
        self.move_speed = 0.3
        self.direction = "right"
        
        # 攻击系统
        self.unlocked_attacks = ["hand"]
        self.active_bullets = {
            "hand_left": False,
            "hand_right": False,
            "leg_left": False,
            "leg_right": False,
            "head": False
        }
        self.attack_cooldown = 0
        
        # 重力系统
        self.gravity = 0.15
        self.vertical_velocity = 0
        self.is_jumping = False
        self.jump_power = 1.44
        self.super_jump_power = 2.5  # 强力跳跃力度
        self.on_ground = False
        self.ground_level = 0
        
        # 跳跃冷却
        self.jump_cooldown = 0
        
        # 新控制系统
        self.selected_part = "hand"  # 默认选择手
        self.available_parts = ["hand", "head", "leg"]  # 可选择的部位
        self.selected_index = 0  # 当前选择部位的索引
        
        # 身体部位留在原地状态
        self.left_hand_original_pos = None
        self.right_hand_original_pos = None
        self.head_original_pos = None
        self.left_leg_original_pos = None
        self.right_leg_original_pos = None
        
        # 部位是否分离状态
        self.parts_separated = {
            "left_hand": False,
            "right_hand": False,
            "head": False,
            "left_leg": False,
            "right_leg": False
        }
        
        # 攻击模式
        self.attack_mode = "horizontal"  # horizontal, vertical, super_jump
        
        # 冷却时间
        self.q_cooldown = 0
        self.j_cooldown = 0
        self.r_cooldown = 0
        
        # 攻击状态
        self.just_fired_bullet = False
        self.last_fired_bullet = None
        
        # 移动状态
        self.is_airborne_without_legs = False
        self.airborne_movement_allowed = True
    def check_below_empty(self, game_world):
        """检查玩家下方是否为空（使用碰撞网格）"""
        # 检查玩家核心的下方位置
        player_center_x = int(self.x)
        player_center_y = int(self.y)
        
        # 检查玩家正下方的几个格子
        for offset_x in [-1, 0, 1]:  # 检查左右相邻位置
            check_x = player_center_x + offset_x
            check_y = player_center_y + 1
            
            if 0 <= check_x < game_world.width and 0 <= check_y < game_world.height:
                if game_world.collision_grid[check_x][check_y] == 1:
                    return False
        
        # 检查所有可见的身体部位下方
        for name, part in self.body_parts.items():
            if not part.visible or self.parts_separated.get(name, False):
                continue
            
            # 计算部位下方的位置
            part_x = int(part.x)
            part_y = int(part.y) + 1
            
            if 0 <= part_x < game_world.width and 0 <= part_y < game_world.height:
                if game_world.collision_grid[part_x][part_y] == 1:
                    return False
        
        return True
    def update_position(self, x, y):
        """更新玩家位置"""
        self.x = x
        self.y = y
        
        # 只更新没有分离的身体部位
        if not self.parts_separated["head"]:
            self.body_parts["head"].x = x
            self.body_parts["head"].y = y-2
            
        if not self.parts_separated["left_hand"]:
            self.body_parts["left_hand"].x = x-1
            self.body_parts["left_hand"].y = y-1
            
        if not self.parts_separated["right_hand"]:
            self.body_parts["right_hand"].x = x+1
            self.body_parts["right_hand"].y = y-1
            
        # 核心部分始终跟随
        self.body_parts["shang"].x = x
        self.body_parts["shang"].y = y-1
        
        self.body_parts["yang"].x = x
        self.body_parts["yang"].y = y
        
        if not self.parts_separated["left_leg"]:
            self.body_parts["left_leg"].x = x-1
            self.body_parts["left_leg"].y = y+1
            
        if not self.parts_separated["right_leg"]:
            self.body_parts["right_leg"].x = x+1
            self.body_parts["right_leg"].y = y+1
        
        # 更新所有部位的矩形
        for part in self.body_parts.values():
            part.update_rect()
    
    def set_ground_level(self, ground_level):
        """设置地面高度"""
        self.ground_level = ground_level
    
    def get_collision_rects(self):
        """获取玩家所有碰撞矩形"""
        rects = []
        for part in self.body_parts.values():
            if part.visible:
                rects.append(part.rect)
        return rects
    
    def find_horizontal_collision_distance(self, target_x, game_world, direction):
        """查找水平方向最近的碰撞距离"""
        if direction == 0:
            return target_x
            
        # 计算从当前位置到目标位置的步进
        current_x = self.x
        step = 1 if target_x > current_x else -1
        
        # 逐步检查每个位置
        for test_x in range(int(current_x + step), int(target_x + step), int(step)):
            if self.check_horizontal_collision(test_x, game_world):
                # 找到碰撞，返回碰撞前的位置
                return test_x - step
                
        return target_x
    
    def find_vertical_collision_distance(self, target_y, game_world, direction):
        """查找垂直方向最近的碰撞距离"""
        if direction == 0:
            return target_y
            
        # 计算从当前位置到目标位置的步进
        current_y = self.y
        step = 1 if target_y > current_y else -1
        
        # 逐步检查每个位置
        for test_y in range(int(current_y + step),int( target_y + step),int( step)):
            if self.check_vertical_collision(test_y, game_world, direction < 0):
                # 找到碰撞，返回碰撞前的位置
                return test_y - step
                
        return target_y
    
    def check_horizontal_collision(self, test_x, game_world):
        """检查特定水平位置是否有碰撞"""
        # 临时计算新位置
        temp_parts = {}
        for name, part in self.body_parts.items():
            if part.visible and not self.parts_separated.get(name, False):
                offset_x = part.x - self.x
                offset_y = part.y - self.y
                new_part_x = test_x + offset_x
                new_part_y = self.y + offset_y
                temp_rect = pygame.Rect(new_part_x * GRID_SIZE, new_part_y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                temp_parts[name] = temp_rect
        
        # 检查与所有场景物体的碰撞
        for scene_obj in game_world.get_scene_objects():
            if not scene_obj.collidable:
                continue
                
            for part_name, part_rect in temp_parts.items():
                if part_rect.colliderect(scene_obj.rect):
                    return True
                    
        return False
    
    def check_vertical_collision(self, test_y, game_world, check_up=False):
        """检查特定垂直位置是否有碰撞"""
        # 临时计算新位置
        temp_parts = {}
        for name, part in self.body_parts.items():
            if part.visible and not self.parts_separated.get(name, False):
                offset_x = part.x - self.x
                offset_y = part.y - self.y
                new_part_x = self.x + offset_x
                new_part_y = test_y + offset_y
                temp_rect = pygame.Rect(new_part_x * GRID_SIZE, new_part_y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                temp_parts[name] = temp_rect
        
        # 检查与所有场景物体的碰撞
        for scene_obj in game_world.get_scene_objects():
            if not scene_obj.collidable:
                continue
                
            for part_name, part_rect in temp_parts.items():
                if part_rect.colliderect(scene_obj.rect):
                    return "up" if check_up else "down"
                        
        return None
    
    def select_next_part(self):
        """选择下一个部位"""
        if self.q_cooldown > 0:
            return
            
        self.selected_index = (self.selected_index + 1) % len(self.available_parts)
        self.selected_part = self.available_parts[self.selected_index]
        
        # 根据选择的部位设置攻击模式
        if self.selected_part == "hand":
            self.attack_mode = "horizontal"
        elif self.selected_part == "head":
            self.attack_mode = "vertical"
        elif self.selected_part == "leg":
            self.attack_mode = "super_jump"
        
        # 重置身体部位颜色
        self.reset_body_part_colors()
        
        # 将选中的部位变绿
        if self.selected_part == "hand":
            if not self.parts_separated["left_hand"]:
                self.body_parts["left_hand"].color = GREEN
            if not self.parts_separated["right_hand"]:
                self.body_parts["right_hand"].color = GREEN
        elif self.selected_part == "head":
            if not self.parts_separated["head"]:
                self.body_parts["head"].color = GREEN
        elif self.selected_part == "leg":
            if not self.parts_separated["left_leg"]:
                self.body_parts["left_leg"].color = GREEN
            if not self.parts_separated["right_leg"]:
                self.body_parts["right_leg"].color = GREEN
        
        self.q_cooldown = 10  # 选择冷却时间
    
    def reset_body_part_colors(self):
        """重置所有身体部位的颜色"""
        if not self.parts_separated["head"]:
            self.body_parts["head"].color = WHITE
        if not self.parts_separated["left_hand"]:
            self.body_parts["left_hand"].color = WHITE
        if not self.parts_separated["right_hand"]:
            self.body_parts["right_hand"].color = WHITE
        if not self.parts_separated["left_leg"]:
            self.body_parts["left_leg"].color = WHITE
        if not self.parts_separated["right_leg"]:
            self.body_parts["right_leg"].color = WHITE
    
    def perform_action(self, game_world):
        """执行当前选中的动作"""
        if self.j_cooldown > 0:
            return False
            
        action_performed = False
        
        if self.attack_mode == "horizontal":
            # 水平发射子弹
            action_performed = self.horizontal_attack(game_world)
            self.just_fired_bullet = True
        elif self.attack_mode == "vertical":
            # 垂直发射子弹
            action_performed = self.vertical_attack(game_world)
            self.just_fired_bullet = True
        elif self.attack_mode == "super_jump":
            # 强力跳跃
            action_performed = self.super_jump(game_world)
            self.big_jump_timer=20
        if action_performed:
            self.j_cooldown = 15  # 动作冷却时间

            
        return action_performed
    
    def horizontal_attack(self, game_world):
        """水平发射子弹"""
        if not self.can_attack("hand", "left") or not self.can_attack("hand", "right"):
            return False
            
        # 发射左手 - 向左
        bullet_left = Bullet(self.x-2, self.y-1, "hand", "left", self.level, self, "left")
        
        # 发射右手 - 向右
        bullet_right = Bullet(self.x+2, self.y-1, "hand", "right", self.level, self, "right")
        
        # 设置最后发射的子弹
        self.last_fired_bullet = [bullet_left, bullet_right]
        
        # 设置子弹激活状态
        self.set_bullet_active("hand", "left", True)
        self.set_bullet_active("hand", "right", True)
        
        # 标记手部分离
        self.parts_separated["left_hand"] = True
        self.parts_separated["right_hand"] = True
        
        # 保存手的原始位置
        self.left_hand_original_pos = (self.body_parts["left_hand"].x, self.body_parts["left_hand"].y)
        self.right_hand_original_pos = (self.body_parts["right_hand"].x, self.body_parts["right_hand"].y)
        
        # 隐藏手部
        self.body_parts["left_hand"].visible = False
        self.body_parts["right_hand"].visible = False
        
        return True
    
    def vertical_attack(self, game_world):
        """垂直发射子弹"""
        if not self.can_attack("head"):
            return False
            
        # 发射头 - 向上
        bullet = Bullet(self.x, self.y-3, "head", "up", self.level, self, None)
        
        # 设置最后发射的子弹
        self.last_fired_bullet = bullet
        
        # 设置子弹激活状态
        self.set_bullet_active("head", None, True)
        
        # 标记头部分离
        self.parts_separated["head"] = True
        
        # 保存头的原始位置
        self.head_original_pos = (self.body_parts["head"].x, self.body_parts["head"].y)
        
        # 隐藏头部
        self.body_parts["head"].visible = False
        
        return True
    
    def get_fired_bullets(self):
        """获取刚刚发射的子弹"""
        if not self.just_fired_bullet or not self.last_fired_bullet:
            return []
            
        bullets = []
        if isinstance(self.last_fired_bullet, list):
            bullets.extend(self.last_fired_bullet)
        else:
            bullets.append(self.last_fired_bullet)
            
        self.just_fired_bullet = False
        return bullets
    def super_jump(self, game_world):
        """强力跳跃 - 腿留在原地"""
        if not self.on_ground or self.jump_cooldown > 0 or self.has_legs_separated():
            return False
            
        # 检查头顶是否有障碍
        collision_result = self.check_vertical_collision_grid(self.y - 1, game_world, True)
        if collision_result == "up":
            return False
        
        # 标记腿部分离
        self.parts_separated["left_leg"] = True
        self.parts_separated["right_leg"] = True
        
        # 保存腿的原始位置
        self.left_leg_original_pos = (self.body_parts["left_leg"].x, self.body_parts["left_leg"].y)
        self.right_leg_original_pos = (self.body_parts["right_leg"].x, self.body_parts["right_leg"].y)
        
        # 隐藏腿
        self.body_parts["left_leg"].visible = False
        self.body_parts["right_leg"].visible = False
        
        # 执行强力跳跃
        self.is_jumping = True
        self.is_airborne_without_legs = True
        self.airborne_movement_allowed = True
        self.on_ground = False
        self.vertical_velocity = -self.super_jump_power
        self.jump_cooldown = 20
        
        return True
    
    def has_legs_separated(self):
        """检查腿是否已经分离"""
        return self.parts_separated["left_leg"] and self.parts_separated["right_leg"]
    
    def check_leg_auto_recover(self, game_world):
        """检查是否应该自动回收腿"""
        if not self.has_legs_separated():
            return False
        if self.big_jump_timer > 0:
            return False

        # 计算腿的原始位置
        left_leg_x, left_leg_y = self.left_leg_original_pos
        right_leg_x, right_leg_y = self.right_leg_original_pos
        
        # 计算玩家的当前位置
        player_x = self.x
        player_y = self.y
        
        # 检查是否落在左腿位置
        if (abs(player_x - left_leg_x) <= 2 and 
            abs(player_y - left_leg_y) <= 2):
            return True
        
        # 检查是否落在右腿位置
        if (abs(player_x - right_leg_x) <= 2 and 
            abs(player_y - right_leg_y) <= 2):
            return True
        
        # 检查是否落在两腿中间位置
        if (abs(player_x - (left_leg_x + right_leg_x) / 2) <= 2 and
            abs(player_y - (left_leg_y + right_leg_y) / 2) <= 2):
            return True
        
        return False
    
    def check_foot_collision_after_recovery(self, new_y, game_world):
        """检查回收腿后是否会与脚下障碍碰撞"""
        # 模拟回收腿后的位置
        temp_y = new_y
        
        # 创建临时腿部对象
        left_leg_temp = GameObject(self.x-1, temp_y+1, "腿", WHITE, True)
        right_leg_temp = GameObject(self.x+1, temp_y+1, "腿", WHITE, True)
        
        # 检查腿部是否与场景物体碰撞
        for scene_obj in game_world.get_scene_objects():
            if not scene_obj.collidable:
                continue
                
            if left_leg_temp.rect.colliderect(scene_obj.rect) or right_leg_temp.rect.colliderect(scene_obj.rect):
                return True
                
        return False
    
    def recover_legs_only(self, game_world):
        """只回收腿部，并进行碰撞检测，回收时执行小跳跃"""
        if self.r_cooldown > 0:
            return False
            
        recovered = False
        
        # 回收左腿
        if self.parts_separated["left_leg"]:
            self.parts_separated["left_leg"] = False
            self.set_bullet_active("leg", "left", False)
            self.body_parts["left_leg"].visible = True
            if self.selected_part == "leg":
                self.body_parts["left_leg"].color = GREEN
            else:
                self.body_parts["left_leg"].color = WHITE
            recovered = True
            
        # 回收右腿
        if self.parts_separated["right_leg"]:
            self.parts_separated["right_leg"] = False
            self.set_bullet_active("leg", "right", False)
            self.body_parts["right_leg"].visible = True
            if self.selected_part == "leg":
                self.body_parts["right_leg"].color = GREEN
            else:
                self.body_parts["right_leg"].color = WHITE
            recovered = True
        
        if recovered:
            # 先更新一次位置，让腿回到角色身上
            self.update_position(self.x, self.y)
            

            # 检查回收后腿和地面/平台是否重叠
            if self.check_foot_collision_after_recovery(self.y, game_world):
                # 如果重叠，尝试调整位置
                self.adjust_position_after_leg_recovery(game_world)
            
            self.r_cooldown = 20
            self.is_airborne_without_legs = False
            self.airborne_movement_allowed = False
            # 执行小跳跃 - 比正常跳跃高度低
            self.perform_leg_recovery_jump(game_world)
                        
        return recovered
    
    def perform_leg_recovery_jump(self, game_world):
        """执行腿部回收时的小跳跃"""
        # 小跳跃高度是正常跳跃的一半
        small_jump_power = self.jump_power * 0.5
        
        # 检查头顶是否有障碍
        collision_result = self.check_vertical_collision(self.y - 1, game_world, True)
        if collision_result == "up":
            # 头顶有障碍，不跳跃
            return False
        
        # 执行小跳跃
        self.is_jumping = True
        self.on_ground = False
        self.vertical_velocity = -small_jump_power
        self.jump_cooldown = 5  # 短冷却时间
        
        return True
    
    def adjust_position_after_leg_recovery(self, game_world):
        """腿部回收后调整位置避免碰撞"""
        # 如果回收后腿和地面重叠，向上调整位置
        adjustment_made = False
        
        # 最多尝试向上调整5格
        for adjust in range(1, 6):
            test_y = self.y - adjust
            
            # 检查这个位置是否安全
            if not self.check_foot_collision_after_recovery(test_y, game_world):
                # 找到安全位置
                self.y = test_y
                self.update_position(self.x, self.y)
                adjustment_made = True
                break
        
        if not adjustment_made:
            # 如果找不到安全位置，尝试向上小跳
            self.perform_leg_recovery_jump(game_world)
    
    def check_foot_collision_after_recovery(self, new_y, game_world):
        """检查回收腿后是否会与脚下障碍碰撞"""
        # 模拟回收腿后的位置
        temp_y = new_y
        
        # 创建临时腿部对象
        left_leg_temp = GameObject(self.x-1, temp_y+1, "腿", WHITE, True)
        right_leg_temp = GameObject(self.x+1, temp_y+1, "腿", WHITE, True)
        
        # 检查腿部是否与场景物体碰撞
        for scene_obj in game_world.get_scene_objects():
            if not scene_obj.collidable:
                continue
                
            if left_leg_temp.rect.colliderect(scene_obj.rect) or right_leg_temp.rect.colliderect(scene_obj.rect):
                return True
                
        return False
    def recover_all_parts(self,game_world):
        """回收所有身体部位"""
        if self.r_cooldown > 0:
            return False
            
        recovered = False
        
        # 回收左手
        if self.parts_separated["left_hand"]:
            self.parts_separated["left_hand"] = False
            self.set_bullet_active("hand", "left", False)
            self.body_parts["left_hand"].visible = True
            self.body_parts["left_hand"].color=WHITE
            if self.selected_part == "hand":
                self.body_parts["left_hand"].color = GREEN
            recovered = True
            
        # 回收右手
        if self.parts_separated["right_hand"]:
            self.parts_separated["right_hand"] = False
            self.set_bullet_active("hand", "right", False)
            self.body_parts["right_hand"].visible = True
            self.body_parts["right_hand"].color = WHITE
            if self.selected_part == "hand":
                self.body_parts["right_hand"].color = GREEN
            recovered = True
            
        # 回收头部
        if self.parts_separated["head"]:
            self.parts_separated["head"] = False
            self.set_bullet_active("head", None, False)

            self.body_parts["head"].visible = True
            self.body_parts["head"].color = WHITE
            if self.selected_part == "head":
                self.body_parts["head"].color = GREEN
            recovered = True
        self.perform_leg_recovery_jump(game_world)
                
        # 回收左腿
        if self.parts_separated["left_leg"]:
            self.parts_separated["left_leg"] = False
            self.set_bullet_active("leg", "left", False)
            self.body_parts["left_leg"].visible = True
            self.body_parts["left_leg"].color = WHITE
            if self.selected_part == "leg":
                self.body_parts["left_leg"].color = GREEN
            recovered = True
            
        # 回收右腿
        if self.parts_separated["right_leg"]:
            self.parts_separated["right_leg"] = False
            self.set_bullet_active("leg", "right", False)
            self.body_parts["right_leg"].visible = True
            self.body_parts["right_leg"].color = WHITE
            if self.selected_part == "leg":
                self.body_parts["right_leg"].color = GREEN
            recovered = True
        
        if recovered:
            self.r_cooldown = 20  # 回收冷却时间
            self.is_airborne_without_legs = False
            self.airborne_movement_allowed = False
            
        return recovered
    
    def can_move(self):
        """检查是否可以移动"""
        # 如果两条腿都分离，但在空中时可以移动
 
        if self.has_legs_separated():
            if not self.on_ground and self.airborne_movement_allowed:
                return True
            return False
        return True
    
    def move(self, dx, dy, game_world):
        """移动玩家 - 只计算目标位置，不实际移动"""
        if self.check_leg_auto_recover(game_world):
            self.recover_legs_only(game_world)

        if not self.can_move():
            return False
        
        new_x = self.x + dx
        new_y = self.y + dy
        
        # 边界检查
        min_x = 1
        max_x = (game_world.width - 2)
        min_y = 2
        max_y = (game_world.height - 2)
        
        # 应用边界限制
        new_x = max(min_x, min(new_x, max_x))
        new_y = max(min_y, min(new_y, max_y))
        
        # 存储目标位置
        self.target_x = new_x
        self.target_y = new_y
        return True
    def jump(self, game_world):
        """普通跳跃"""
        if not self.can_move() or not self.is_jumping and self.on_ground and self.jump_cooldown <= 0:
            # 检查头顶是否有障碍
            collision_result = self.check_vertical_collision_grid(self.y - 1, game_world, True)
            if collision_result == "up":
                return False
                
            self.is_jumping = True
            self.on_ground = False
            self.vertical_velocity = -self.jump_power
            self.jump_cooldown = 10
            return True
        return False
    
    def find_horizontal_collision_distance_grid(self, target_x, game_world, direction):
        """使用碰撞网格查找水平方向最近的碰撞距离"""
        if direction == 0:
            return target_x
        
        # 计算从当前位置到目标位置的步进
        current_x = self.x
        step = 1 if target_x > current_x else -1
        
        # 逐步检查每个位置，步长为0.1以确保精度
        test_x = current_x
        while (direction > 0 and test_x < target_x) or (direction < 0 and test_x > target_x):
            # 检查当前位置是否有碰撞
            if self.check_horizontal_collision_grid(test_x, game_world):
                # 找到碰撞，返回碰撞前的位置
                # 向左或向右微调一点，确保不进入障碍物
                if direction > 0:  # 向右移动
                    return test_x - 0.1
                else:  # 向左移动
                    return test_x + 0.1
            
            test_x += step * 0.1
        
        return target_x
    def check_horizontal_collision_grid(self, test_x, game_world):
        """使用碰撞网格检查特定水平位置是否有碰撞"""
        for name, part in self.body_parts.items():
            if part.visible and not self.parts_separated.get(name, False):
                # 计算部位在测试位置的坐标
                offset_x = part.x - self.x
                offset_y = part.y - self.y
                test_part_x = test_x + offset_x
                test_part_y = self.y + offset_y
                
                # 计算整数坐标
                part_x_int = int(test_part_x)
                part_y_int = int(test_part_y)
                
                # 检查这个坐标是否有障碍物
                if 0 <= part_x_int < game_world.width and 0 <= part_y_int < game_world.height:
                    if game_world.collision_grid[part_x_int][part_y_int] == 1:
                        return True
                
                # 同时检查相邻位置，防止在格子边界处穿模
                # 检查当前位置
                for check_x in [part_x_int, part_x_int - 1, part_x_int + 1]:
                    for check_y in [part_y_int, part_y_int - 1, part_y_int + 1]:
                        if 0 <= check_x < game_world.width and 0 <= check_y < game_world.height:
                            if game_world.collision_grid[check_x][check_y] == 1:
                                return True
        
        return False
    def find_vertical_collision_distance_grid(self, target_y, game_world, direction):
        """使用碰撞网格查找垂直方向最近的碰撞距离"""
        if direction == 0:
            return target_y
        
        # 计算从当前位置到目标位置的步进
        current_y = self.y
        step = 1 if target_y > current_y else -1
        
        # 逐步检查每个位置，步长为0.1以确保精度
        test_y = current_y
        while (direction > 0 and test_y < target_y) or (direction < 0 and test_y > target_y):
            # 检查当前位置是否有碰撞
            collision = self.check_vertical_collision_grid(test_y, game_world, direction < 0)
            if collision:
                # 找到碰撞，返回碰撞前的位置
                # 向上或向下微调一点，确保不进入障碍物
                if direction > 0:  # 向下移动
                    return test_y - 0.1
                else:  # 向上移动
                    return test_y + 0.1
            
            test_y += step * 0.1
        
        return target_y
    def check_vertical_collision_grid(self, test_y, game_world, check_up=False):
        """使用碰撞网格检查特定垂直位置是否有碰撞"""
        # 获取玩家所有身体部位在测试位置的碰撞点
        collision_points = []
        
        for name, part in self.body_parts.items():
            if part.visible and not self.parts_separated.get(name, False):
                # 计算部位在测试位置的坐标
                offset_y = part.y - self.y
                test_part_y = test_y + offset_y
                
                # 计算整数坐标
                part_x_int = int(part.x)
                part_y_int = int(test_part_y)
                
                # 检查这个坐标是否有障碍物
                if 0 <= part_x_int < game_world.width and 0 <= part_y_int < game_world.height:
                    if game_world.collision_grid[part_x_int][part_y_int] == 1:
                        return "up" if check_up else "down"
                
                # 同时检查相邻位置，防止在格子边界处穿模
                # 检查上方（如果检查上升）或下方（如果检查下落）
                if check_up:
                    # 检查头顶上方一格
                    check_y = int(test_part_y) - 1
                    if 0 <= part_x_int < game_world.width and 0 <= check_y < game_world.height:
                        if game_world.collision_grid[part_x_int][check_y] == 1:
                            return "up"
                else:
                    # 检查脚下一格
                    check_y = int(test_part_y) + 1
                    if 0 <= part_x_int < game_world.width and 0 <= check_y < game_world.height:
                        if game_world.collision_grid[part_x_int][check_y] == 1:
                            return "down"
        
        return None
    def apply_gravity(self, game_world):
        """应用重力 - 只计算目标位置，不实际移动"""
        # 更新坠落检查计时器
        if self.fall_check_timer > 0:
            self.fall_check_timer -= 1
        
        # 检查腿是否分离
        legs_separated = self.has_legs_separated()
        
        # 如果玩家在地面上，检查是否需要开始下坠
        if self.on_ground and self.fall_check_timer <= 0 and not legs_separated:
            if self.check_below_empty(game_world):
                self.on_ground = False
                self.is_jumping = False
                self.vertical_velocity = 0
            self.fall_check_timer = self.fall_check_interval
        
        if not self.on_ground:
                # 应用重力
            self.vertical_velocity += self.gravity
            target_y = self.y + self.vertical_velocity
            
            # 边界检查
            min_y = 2
            max_y = (game_world.height - 2)
            target_y = max(min_y, min(target_y, max_y))
            
            # 存储目标位置
            if target_y != self.y:
                self.target_y = target_y
        
        # 更新跳跃冷却
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1
    def check_endpoint_collision(self, game_world):
        """检查是否到达终点"""
        for obj in game_world.get_scene_objects():
            if hasattr(obj, 'char') and obj.char == "终" and isinstance(obj, EndPoint):
                # 检查玩家任意部位是否与终点碰撞
                for part_name, part in self.body_parts.items():
                    if part.visible and part.collides_with(obj):
                        return True
        return False
    def update_move(self, game_world=None):
        """执行实际的移动操作 - 使用射线投射进行碰撞检测"""
        if game_world is None:
            return False
        
        moved = False
        moved_x = False
        moved_y = False
        
        # 初始化目标位置
        target_x = self.target_x
        target_y = self.target_y
        
        # 如果没有目标位置，使用当前位置
        if target_x is None:
            target_x = self.x
        if target_y is None:
            target_y = self.y
        
        # 计算移动向量
        dx = target_x - self.x
        dy = target_y - self.y
        
        # 如果两个方向都没有移动，直接返回
        if dx == 0 and dy == 0:
            return False
        
        # 处理水平移动
        if dx != 0:
            moved_x = self.move_horizontal(dx, game_world)
        
        # 处理垂直移动
        if dy != 0:
            moved_y = self.move_vertical(dy, game_world)
        
        moved = moved_x or moved_y
        
        # 重置目标位置
        self.target_x = None
        self.target_y = None
        
        return moved
    def move_horizontal(self, dx, game_world):
        """处理水平移动"""
        if dx == 0:
            return False
        
        # 计算移动方向
        direction = 1 if dx > 0 else -1
        
        # 从当前位置到目标位置，逐步检查
        current_x = self.x
        target_x = self.x + dx
        
        # 获取所有需要检查的碰撞点
        collision_points = self.get_horizontal_collision_points(current_x, target_x, self.y, game_world)
        
        # 如果没有碰撞点，直接移动到目标位置
        if not collision_points:
            self.x = target_x
            self.update_position(self.x, self.y)
            return True
        
        # 找出最近的碰撞点
        nearest_collision = None
        min_distance = float('inf')
        
        for point in collision_points:
            # 修正：point[0] 是碰撞x坐标，point[1] 是碰撞表面
            collision_x, collision_surface = point
            
            # 计算到当前位置的距离
            distance = abs(collision_x - current_x)
            
            # 确保碰撞点在移动方向上
            if (direction > 0 and collision_x > current_x) or (direction < 0 and collision_x < current_x):
                if distance < min_distance:
                    min_distance = distance
                    nearest_collision = point
        
        # 如果没有在移动方向上的碰撞点，直接移动到目标位置
        if nearest_collision is None:
            self.x = target_x
            self.update_position(self.x, self.y)
            return True
        
        # 根据碰撞表面的方向调整位置
        collision_x, collision_surface = nearest_collision
        
        if collision_surface == "left":
            # 从左侧碰撞，停在碰撞点左侧
            # 向左移动一小段距离，确保不穿入障碍物
            self.x = collision_x - 0.1
        elif collision_surface == "right":
            # 从右侧碰撞，停在碰撞点右侧
            # 向右移动一小段距离，确保不穿入障碍物
            self.x = collision_x + 0.1
        
        self.update_position(self.x, self.y)
        return True

    def move_vertical(self, dy, game_world):
        """处理垂直移动"""
        if dy == 0:
            return False
        
        # 计算移动方向
        direction = 1 if dy > 0 else -1
        
        # 从当前位置到目标位置，逐步检查
        current_y = self.y
        target_y = self.y + dy
        
        # 获取所有需要检查的碰撞点
        collision_points = self.get_vertical_collision_points(current_y, target_y, self.x, game_world)
        
        # 如果没有碰撞点，直接移动到目标位置
        if not collision_points:
            self.y = target_y
            self.update_position(self.x, self.y)
            
            # 检查是否落地
            if dy > 0:  # 向下移动
                self.on_ground = True
                self.vertical_velocity = 0
            return True
        
        # 找出最近的碰撞点
        nearest_collision = None
        min_distance = float('inf')
        
        for point in collision_points:
            # 修正：point[0] 是碰撞y坐标，point[1] 是碰撞表面
            collision_y, collision_surface = point
            
            # 计算到当前位置的距离
            distance = abs(collision_y - current_y)
            
            # 确保碰撞点在移动方向上
            if (direction > 0 and collision_y > current_y) or (direction < 0 and collision_y < current_y):
                if distance < min_distance:
                    min_distance = distance
                    nearest_collision = point
        
        # 如果没有在移动方向上的碰撞点，直接移动到目标位置
        if nearest_collision is None:
            self.y = target_y
            self.update_position(self.x, self.y)
            
            # 检查是否落地
            if dy > 0:  # 向下移动
                self.on_ground = True
                self.vertical_velocity = 0
            return True
        
        # 根据碰撞表面的方向调整位置
        collision_y, collision_surface = nearest_collision
        
        if collision_surface == "top":
            # 从上侧碰撞，停在碰撞点上侧
            # 向上移动一小段距离，确保不穿入障碍物
            self.y = collision_y - 0.1-1
            self.on_ground = True
    def get_horizontal_collision_points(self, start_x, end_x, y, game_world):
        """获取水平方向上的所有碰撞点"""
        collision_points = []
        
        # 计算步进方向
        direction = 1 if end_x > start_x else -1
        
        # 检查每个身体部位的水平移动路径
        for name, part in self.body_parts.items():
            if not part.visible or self.parts_separated.get(name, False):
                continue
            
            # 计算部位相对于玩家的偏移
            offset_x = part.x - self.x
            offset_y = part.y - self.y
            
            # 计算部位的起始和结束位置
            part_start_x = start_x + offset_x
            part_end_x = end_x + offset_x
            part_y = y + offset_y
            
            # 检查从起始到结束的每个整数x坐标
            start_grid_x = int(min(part_start_x, part_end_x))
            end_grid_x = int(max(part_start_x, part_end_x)) + 1
            
            for grid_x in range(start_grid_x, end_grid_x + 1):
                # 检查当前位置是否有碰撞
                if 0 <= grid_x < game_world.width and 0 <= int(part_y) < game_world.height:
                    if game_world.collision_grid[grid_x][int(part_y)] == 1:
                        # 确定碰撞表面
                        if direction > 0:  # 向右移动
                            collision_surface = "left"
                            # 碰撞面是障碍物的左侧边缘
                            collision_x = grid_x
                        else:  # 向左移动
                            collision_surface = "right"
                            # 碰撞面是障碍物的右侧边缘
                            collision_x = grid_x + 1
                        
                        collision_points.append((collision_x, collision_surface))
        
        return collision_points

    def get_vertical_collision_points(self, start_y, end_y, x, game_world):
        """获取垂直方向上的所有碰撞点"""
        collision_points = []
        
        # 计算步进方向
        direction = 1 if end_y > start_y else -1
        
        # 检查每个身体部位的垂直移动路径
        for name, part in self.body_parts.items():
            if not part.visible or self.parts_separated.get(name, False):
                continue
            
            # 计算部位相对于玩家的偏移
            offset_x = part.x - self.x
            offset_y = part.y - self.y
            
            # 计算部位的起始和结束位置
            part_x = x + offset_x
            part_start_y = start_y + offset_y
            part_end_y = end_y + offset_y
            
            # 检查从起始到结束的每个整数y坐标
            start_grid_y = int(min(part_start_y, part_end_y))
            end_grid_y = int(max(part_start_y, part_end_y)) + 1
            
            for grid_y in range(start_grid_y, end_grid_y + 1):
                # 检查当前位置是否有碰撞
                if 0 <= int(part_x) < game_world.width and 0 <= grid_y < game_world.height:
                    if game_world.collision_grid[int(part_x)][grid_y] == 1:
                        # 确定碰撞表面
                        if direction > 0:  # 向下移动
                            collision_surface = "top"
                            # 碰撞面是障碍物的上侧边缘
                            collision_y = grid_y
                        else:  # 向上移动
                            collision_surface = "bottom"
                            # 碰撞面是障碍物的下侧边缘
                            collision_y = grid_y + 1
                        
                        collision_points.append((collision_y, collision_surface))
        
        return collision_points
    def check_below_empty(self, game_world):
        """检查玩家下方是否为空（使用新的碰撞检测）"""
        # 检查每个身体部位下方
        for name, part in self.body_parts.items():
            if not part.visible or self.parts_separated.get(name, False):
                continue
            
            # 计算部位下方的位置
            part_x = int(part.x)
            part_y = int(part.y) + 1
            
            if 0 <= part_x < game_world.width and 0 <= part_y < game_world.height:
                if game_world.collision_grid[part_x][part_y] == 1:
                    return False
        
        return True
    def update(self, game_world=None):
        """更新玩家状态"""
        # 更新冷却时间
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.q_cooldown > 0:
            self.q_cooldown -= 1
        if self.j_cooldown > 0:
            self.j_cooldown -= 1
        if self.r_cooldown > 0:
            self.r_cooldown -= 1
        if self.big_jump_timer>0:
            self.big_jump_timer -=1
        # 应用重力
        if game_world:
            self.apply_gravity(game_world)
        self.update_move(game_world)
        

            # 检查是否到达终点
        if game_world:
            self.check_endpoint_collision(game_world)
        # 更新身体部位可见性
        for part_name, is_active in self.active_bullets.items():
            if part_name == "hand_left":
                self.body_parts["left_hand"].visible = not is_active
            elif part_name == "hand_right":
                self.body_parts["right_hand"].visible = not is_active
            elif part_name == "leg_left":
                self.body_parts["left_leg"].visible = not is_active
            elif part_name == "leg_right":
                self.body_parts["right_leg"].visible = not is_active
            elif part_name == "head":
                self.body_parts["head"].visible = not is_active
    
    def can_attack(self, bullet_type, side=None):
        """检查是否可以发射指定部位的子弹"""
        if bullet_type == "hand":
            if side == "left":
                return not self.active_bullets["hand_left"] and not self.parts_separated["left_hand"]
            elif side == "right":
                return not self.active_bullets["hand_right"] and not self.parts_separated["right_hand"]
        elif bullet_type == "leg":
            if side == "left":
                return not self.active_bullets["leg_left"] and not self.parts_separated["left_leg"]
            elif side == "right":
                return not self.active_bullets["leg_right"] and not self.parts_separated["right_leg"]
        elif bullet_type == "head":
            return not self.active_bullets["head"] and not self.parts_separated["head"]
        return False
    
    def set_bullet_active(self, bullet_type, side, active):
        """设置子弹激活状态"""
        if bullet_type == "hand":
            if side == "left":
                self.active_bullets["hand_left"] = active
            elif side == "right":
                self.active_bullets["hand_right"] = active
        elif bullet_type == "leg":
            if side == "left":
                self.active_bullets["leg_left"] = active
            elif side == "right":
                self.active_bullets["leg_right"] = active
        elif bullet_type == "head":
            self.active_bullets["head"] = active

    def attack(self, bullets, game_world):
        """兼容旧的攻击方法"""
        return False  # 现在通过perform_action方法攻击
    
    def recover_part(self, bullet_type, side=None):
        """回收身体部位 - 子弹击中目标时调用"""
        if bullet_type == "hand":
            if side == "left":
                self.parts_separated["left_hand"] = False
                self.set_bullet_active("hand", "left", False)
                self.body_parts["left_hand"].visible = True
                # 恢复颜色
                if self.selected_part == "hand":
                    self.body_parts["left_hand"].color = GREEN
                else:
                    self.body_parts["left_hand"].color = WHITE
            elif side == "right":
                self.parts_separated["right_hand"] = False
                self.set_bullet_active("hand", "right", False)
                self.body_parts["right_hand"].visible = True
                # 恢复颜色
                if self.selected_part == "hand":
                    self.body_parts["right_hand"].color = GREEN
                else:
                    self.body_parts["right_hand"].color = WHITE
        elif bullet_type == "leg":
            if side == "left":
                self.parts_separated["left_leg"] = False
                self.set_bullet_active("leg", "left", False)
                self.body_parts["left_leg"].visible = True
                # 恢复颜色
                if self.selected_part == "leg":
                    self.body_parts["left_leg"].color = GREEN
                else:
                    self.body_parts["left_leg"].color = WHITE
            elif side == "right":
                self.parts_separated["right_leg"] = False
                self.set_bullet_active("leg", "right", False)
                self.body_parts["right_leg"].visible = True
                # 恢复颜色
                if self.selected_part == "leg":
                    self.body_parts["right_leg"].color = GREEN
                else:
                    self.body_parts["right_leg"].color = WHITE
        elif bullet_type == "head":
            self.parts_separated["head"] = False
            self.set_bullet_active("head", None, False)
            self.body_parts["head"].visible = True
            # 恢复颜色
            if self.selected_part == "head":
                self.body_parts["head"].color = GREEN
            else:
                self.body_parts["head"].color = WHITE
    
    def gain_exp(self, amount):
        """获得经验值"""
        self.exp += amount
        if self.exp >= self.exp_to_next_level:
            self.level_up()
    
    def level_up(self):
        """升级"""
        self.level += 1
        self.exp = 0
        self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
        self.max_health += 2
        self.health = self.max_health
        
        if self.level == 2 and "leg" not in self.unlocked_attacks:
            self.unlocked_attacks.append("leg")
        elif self.level >= 3 and "head" not in self.unlocked_attacks:
            self.unlocked_attacks.append("head")
        # 解锁新的可用部位
        if self.level == 2 and "leg" not in self.available_parts:
            self.available_parts.append("leg")
        elif self.level >= 3 and "head" not in self.available_parts:
            self.available_parts.append("head")
    
    def get_selected_part_info(self):
        """获取当前选中部位的信息"""
        if self.selected_part == "hand":
            return "手（水平发射）"
        elif self.selected_part == "head":
            return "头（垂直发射）"
        elif self.selected_part == "leg":
            return "腿（强力跳跃）"
        return "未知"
    
    def get_separated_parts_info(self):
        """获取分离部位的信息"""
        separated = []
        if self.parts_separated["left_hand"]:
            separated.append("左手")
        if self.parts_separated["right_hand"]:
            separated.append("右手")
        if self.parts_separated["head"]:
            separated.append("头")
        if self.parts_separated["left_leg"]:
            separated.append("左腿")
        if self.parts_separated["right_leg"]:
            separated.append("右腿")
        return separated
    
    def draw(self, screen, font):
        """绘制玩家"""
        # 绘制留在原地的身体部位

            
        if self.parts_separated["left_leg"] and self.left_leg_original_pos:
            left_leg = GameObject(self.left_leg_original_pos[0], self.left_leg_original_pos[1], "腿", WHITE)
            left_leg.draw(screen, font)
            
        if self.parts_separated["right_leg"] and self.right_leg_original_pos:
            right_leg = GameObject(self.right_leg_original_pos[0], self.right_leg_original_pos[1], "腿",WHITE)
            right_leg.draw(screen, font)
        
        # 绘制所有身体部位
        for part in self.body_parts.values():
            part.draw(screen, font)
        
        # 绘制状态信息
        level_font = pygame.font.SysFont(None, 20)
        
        # 等级
        level_text = level_font.render(f"Lv.{self.level}", True, CYAN)
        screen.blit(level_text, (self.x * GRID_SIZE, (self.y-2) * GRID_SIZE - 20))
        