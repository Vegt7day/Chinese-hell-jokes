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
        self.on_ground = False
        self.ground_level = 0
        
        # 跳跃冷却
        self.jump_cooldown = 0
        
        # 碰撞检测缓存
        self.collision_rects = {}
    
    def update_position(self, x, y):
        """更新玩家位置"""
        self.x = x
        self.y = y
        
        # 更新所有身体部位位置
        self.body_parts["head"].x = x
        self.body_parts["head"].y = y-2
        
        self.body_parts["shang"].x = x
        self.body_parts["shang"].y = y-1
        
        self.body_parts["left_hand"].x = x-1
        self.body_parts["left_hand"].y = y-1
        
        self.body_parts["right_hand"].x = x+1
        self.body_parts["right_hand"].y = y-1
        
        self.body_parts["yang"].x = x
        self.body_parts["yang"].y = y
        
        self.body_parts["left_leg"].x = x-1
        self.body_parts["left_leg"].y = y+1
        
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
            if part.visible:
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
            if part.visible:
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
    
    def move(self, dx, dy, game_world):
        """移动玩家 - 改进版，遇到障碍停在障碍旁边"""
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
        """跳跃"""
        if not self.is_jumping and self.on_ground and self.jump_cooldown <= 0:
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
                else:
                    new_y = target_y
                    
            # 处理上升（垂直速度为负）
            elif self.vertical_velocity < 0:
                # 查找最近的不会碰撞的位置
                safe_y = self.find_vertical_collision_distance(target_y, game_world, -1)
                
                # 检查是否碰到头顶障碍
                if safe_y > target_y:
                    # 碰到上方障碍
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
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
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
                return not self.active_bullets["hand_left"]
            elif side == "right":
                return not self.active_bullets["hand_right"]
        elif bullet_type == "leg":
            if side == "left":
                return not self.active_bullets["leg_left"]
            elif side == "right":
                return not self.active_bullets["leg_right"]
        elif bullet_type == "head":
            return not self.active_bullets["head"]
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
        """发射子弹"""
        if self.attack_cooldown > 0:
            return False
        
        attack_made = False
        
        if "hand" in self.unlocked_attacks:
            if self.can_attack("hand", "left"):
                bullets.append(Bullet(self.x-2, self.y-1, "hand", "left", self.level, self, "left"))
                self.set_bullet_active("hand", "left", True)
                self.body_parts["left_hand"].visible = False
                attack_made = True
            if self.can_attack("hand", "right"):
                bullets.append(Bullet(self.x+2, self.y-1, "hand", "right", self.level, self, "right"))
                self.set_bullet_active("hand", "right", True)
                self.body_parts["right_hand"].visible = False
                attack_made = True
        
        if "leg" in self.unlocked_attacks:
            if self.can_attack("leg", "left"):
                bullets.append(Bullet(self.x-2, self.y+1, "leg", "left", self.level, self, "left"))
                self.set_bullet_active("leg", "left", True)
                self.body_parts["left_leg"].visible = False
                attack_made = True
            if self.can_attack("leg", "right"):
                bullets.append(Bullet(self.x+2, self.y+1, "leg", "right", self.level, self, "right"))
                self.set_bullet_active("leg", "right", True)
                self.body_parts["right_leg"].visible = False
                attack_made = True
        
        if "head" in self.unlocked_attacks and self.can_attack("head"):
            bullets.append(Bullet(self.x, self.y-3, "head", "up", self.level, self, None))
            self.set_bullet_active("head", None, True)
            self.body_parts["head"].visible = False
            attack_made = True
        
        if attack_made:
            self.attack_cooldown = 10
            return True
        return False
    
    def recover_part(self, bullet_type, side=None):
        """回收身体部位"""
        if bullet_type == "hand":
            if side == "left":
                self.set_bullet_active("hand", "left", False)
                self.body_parts["left_hand"].visible = True
            elif side == "right":
                self.set_bullet_active("hand", "right", False)
                self.body_parts["right_hand"].visible = True
        elif bullet_type == "leg":
            if side == "left":
                self.set_bullet_active("leg", "left", False)
                self.body_parts["left_leg"].visible = True
            elif side == "right":
                self.set_bullet_active("leg", "right", False)
                self.body_parts["right_leg"].visible = True
        elif bullet_type == "head":
            self.set_bullet_active("head", None, False)
            self.body_parts["head"].visible = True
    
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
    
    def draw(self, screen, font):
        """绘制玩家"""
        for part in self.body_parts.values():
            part.draw(screen, font)
        
        level_font = pygame.font.SysFont(None, 20)
        level_text = level_font.render(f"Lv.{self.level}", True, CYAN)
        screen.blit(level_text, (self.x * GRID_SIZE, (self.y-2) * GRID_SIZE - 20))