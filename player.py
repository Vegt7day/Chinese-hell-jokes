"""
玩家类 - 商鞅
"""

import pygame
import random
from __init__ import GRID_SIZE, YELLOW, GREEN, BLUE, RED, CYAN, WHITE
from bullet import Bullet
from scene import Ground, Wall, Platform, Door, Trap  # 导入场景物体

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
        """检查玩家下方是否为空（没有障碍物）"""
        # 计算玩家核心的下方位置
        below_y = int(self.y) + 1  # 向下取整后+1
        
        # 检查以玩家为中心的一个范围
        check_range_x = 1  # 横向检查范围
        check_range_y = 1  # 纵向检查范围
        
        # 获取玩家整数坐标
        player_center_x = int(self.x)
        player_center_y = int(self.y)
        
        # 创建一个检测范围的矩形
        # 检查从玩家中心向左右各check_range_x格，向下check_range_y格的范围
        check_rect = pygame.Rect(
            (player_center_x - check_range_x) * GRID_SIZE,
            (player_center_y + 1) * GRID_SIZE,  # 从玩家下方开始
            (check_range_x * 2 + 1) * GRID_SIZE,
            check_range_y * GRID_SIZE
        )
        
        # 遍历所有场景物体
        for scene_obj in game_world.get_scene_objects():
            if not scene_obj.collidable:
                continue
                
            # 检查场景物体是否在检测范围内
            if check_rect.colliderect(scene_obj.rect):
                # 计算物体相对于玩家的精确位置
                obj_below_player = scene_obj.y > self.y
                obj_vertically_aligned = abs(scene_obj.x - self.x) <= 1.5
                
                if obj_below_player and obj_vertically_aligned:
                    # 在玩家正下方有障碍物
                    return False
        
        # 再检查所有可见的身体部位下方
        for name, part in self.body_parts.items():
            if not part.visible or self.parts_separated.get(name, False):
                continue
                
            # 计算部位下方的位置（取整）
            part_below_x = int(part.x)
            part_below_y = int(part.y) + 1
            
            # 检查这个整数坐标位置是否有障碍
            for scene_obj in game_world.get_scene_objects():
                if not scene_obj.collidable:
                    continue
                    
                # 检查障碍物是否在部位下方
                obj_at_part_below = (int(scene_obj.x) == part_below_x and 
                                    int(scene_obj.y) == part_below_y)
                
                # 或者障碍物在部位下方很近的位置
                obj_near_part_below = (abs(scene_obj.x - part.x) < 1.0 and
                                    scene_obj.y > part.y and
                                    abs(scene_obj.y - (part.y + 1)) < 1.0)
                
                if obj_at_part_below or obj_near_part_below:
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
        collision_result = self.check_vertical_collision(self.y - 1, game_world, True)
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
        if self.big_jump_timer!=0:
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
        """移动玩家 - 改进版，遇到障碍停在障碍旁边"""
        # 检查是否可以移动

        if self.check_leg_auto_recover(game_world):
        # 自动回收腿，只回收腿部
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
        
        # 处理水平移动
        if dx != 0:
            # 查找最近的无碰撞位置
            safe_x = self.find_horizontal_collision_distance(new_x, game_world, dx)
            new_x = safe_x
            
            # 应用边界限制
            new_x = max(min_x, min(new_x, max_x))
        
        # 处理垂直移动
        if dy != 0:
            # 查找最近的无碰撞位置
            safe_y = self.find_vertical_collision_distance(new_y, game_world, dy)
            new_y = safe_y
            
            # 应用边界限制
            new_y = max(min_y, min(new_y, max_y))
            
            # 检查是否落地
            if dy > 0:  # 向下移动
                collision = self.check_vertical_collision(new_y, game_world, False)
                if collision == "down":
                    self.on_ground = True
                    self.vertical_velocity = 0
                    # 落地后停止空中移动
                    if self.has_legs_separated():
                        self.airborne_movement_allowed = False
                        # 检查是否应该自动回收腿
            
            elif dy < 0:  # 向上移动
                collision = self.check_vertical_collision(new_y, game_world, True)
                if collision == "up":
                    self.vertical_velocity = 0

        # 更新位置
        if new_x != self.x or new_y != self.y:
            self.update_position(new_x, new_y)
            return True
            
        return False
    
    def jump(self, game_world):
        """普通跳跃"""
        if not self.can_move() or not self.is_jumping and self.on_ground and self.jump_cooldown <= 0:
            # 检查头顶是否有障碍
            collision_result = self.check_vertical_collision(self.y - 1, game_world, True)
            if collision_result == "up":
                return False
                
            self.is_jumping = True
            self.on_ground = False
            self.vertical_velocity = -self.jump_power
            self.jump_cooldown = 10
            return True
        return False
    
    def apply_gravity(self, game_world):
        """应用重力 - 改进版，下落时正好停在障碍上方"""
        # 更新坠落检查计时器
        if self.fall_check_timer > 0:
            self.fall_check_timer -= 1
        
        # 如果玩家在地面上，检查是否需要开始下坠
        if self.on_ground and self.fall_check_timer <= 0:
            if self.check_below_empty(game_world):
                # 下方为空，开始下坠
                self.on_ground = False
                self.is_jumping = False
                self.vertical_velocity = 0  # 初始速度为0
            else :
                self.on_ground=True
            self.fall_check_timer = self.fall_check_interval
        
        if not self.on_ground:
            # 应用重力
            self.vertical_velocity += self.gravity
            target_y = self.y + self.vertical_velocity
            
            # 边界检查
            min_y = 2
            max_y = (game_world.height - 2)
            target_y = max(min_y, min(target_y, max_y))
            
            # 处理下落（垂直速度为正）
            if self.vertical_velocity > 0:
                # 查找最近的不会碰撞的位置
                safe_y = self.find_vertical_collision_distance(target_y, game_world, 1)
                
                # 检查是否落地
                if safe_y < target_y:
                    # 碰到下方障碍
                    self.on_ground = True
                    self.is_jumping = False
                    self.vertical_velocity = 0
                    new_y = safe_y
                    
                    # # 检查是否应该自动回收腿
                    # if self.has_legs_separated():
                    #     if self.check_leg_auto_recover(game_world):
                    #         # 自动回收腿，只回收腿部
                    #         self.recover_legs_only(game_world)
                    #     else:
                    #         # 落地后停止空中移动
                    #         self.airborne_movement_allowed = False
                else:
                    new_y = target_y
                    
            # 处理上升（垂直速度为负）
            elif self.vertical_velocity < 0:
                # 查找最近的不会碰撞的位置
                safe_y = self.find_vertical_collision_distance(target_y, game_world, -1)
                
                # 检查是否碰到头顶障碍
                if safe_y > target_y:
                    # 碰到上方障碍
                    self.airborne_movement_allowed = False
                    self.vertical_velocity = 0
                    self.is_jumping = False
                    new_y = safe_y
                else:
                    new_y = target_y
                    
            else:
                new_y = target_y
            
            # 更新位置
            if new_y != self.y:
                self.update_position(self.x, new_y)
        
        # 更新跳跃冷却
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1
    def update_direction(self, dx, dy):
        """更新玩家方向"""
        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"
    
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
        