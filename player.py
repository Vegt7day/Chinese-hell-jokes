"""
玩家类 - 商鞅
"""

import pygame
import random
from __init__ import GRID_SIZE, YELLOW, GREEN, BLUE, RED, CYAN,WHITE
from bullet import Bullet
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
        return self.x == other.x and self.y == other.y


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
        self.move_speed = 1  # 玩家移动速度是敌人的2倍
        self.direction = "right"  # 初始面朝右
        
        # 攻击系统
        self.unlocked_attacks = ["hand"]  # 初始只能发射手
        self.active_bullets = {
            "hand_left": False,  # 左手是否已发射
            "hand_right": False, # 右手是否已发射
            "leg_left": False,   # 左腿是否已发射
            "leg_right": False,  # 右腿是否已发射
            "head": False        # 头是否已发射
        }
        self.attack_cooldown = 0
    
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
    
    def move(self, dx, dy, game_world):
        """移动玩家"""
        new_x = self.x + dx
        new_y = self.y + dy
        
        # 边界检查 - 确保所有身体部位都在屏幕内
        min_x = 1
        max_x = (game_world.width - 2)  # 确保右侧手不超出
        min_y = 2  # 确保头不超出
        max_y = (game_world.height - 2)  # 确保腿不超出
        
        if min_x <= new_x <= max_x and min_y <= new_y <= max_y:
            self.update_position(new_x, new_y)
            return True
        return False
    
    def update_direction(self, dx, dy):
        """更新玩家方向"""
        if dx > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "left"
    
    def update(self):
        """更新玩家状态"""
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
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
        
        # 无论玩家朝哪个方向，固定发射方向：
        # 左手和左腿向左，右手和右腿向右，头向上
        
        if "hand" in self.unlocked_attacks:
            # 发射左手 - 向左
            if self.can_attack("hand", "left"):
                bullets.append(Bullet(self.x-2, self.y-1, "hand", "left", self.level, self, "left"))
                self.set_bullet_active("hand", "left", True)
                self.body_parts["left_hand"].visible = False
                attack_made = True
            # 发射右手 - 向右
            if self.can_attack("hand", "right"):
                bullets.append(Bullet(self.x+2, self.y-1, "hand", "right", self.level, self, "right"))
                self.set_bullet_active("hand", "right", True)
                self.body_parts["right_hand"].visible = False
                attack_made = True
        
        if "leg" in self.unlocked_attacks:
            # 发射左腿 - 向左
            if self.can_attack("leg", "left"):
                bullets.append(Bullet(self.x-2, self.y+1, "leg", "left", self.level, self, "left"))
                self.set_bullet_active("leg", "left", True)
                self.body_parts["left_leg"].visible = False
                attack_made = True
            # 发射右腿 - 向右
            if self.can_attack("leg", "right"):
                bullets.append(Bullet(self.x+2, self.y+1, "leg", "right", self.level, self, "right"))
                self.set_bullet_active("leg", "right", True)
                self.body_parts["right_leg"].visible = False
                attack_made = True
        
        if "head" in self.unlocked_attacks and self.can_attack("head"):
            # 发射头 - 向上
            bullets.append(Bullet(self.x, self.y-3, "head", "up", self.level, self, None))
            self.set_bullet_active("head", None, True)
            self.body_parts["head"].visible = False
            attack_made = True
        
        if attack_made:
            self.attack_cooldown = 10  # 攻击冷却时间
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
        
        # 根据等级解锁新攻击方式
        if self.level == 2 and "leg" not in self.unlocked_attacks:
            self.unlocked_attacks.append("leg")
        elif self.level >= 3 and "head" not in self.unlocked_attacks:
            self.unlocked_attacks.append("head")
    
    def draw(self, screen, font):
        """绘制玩家"""
        # 绘制所有身体部位
        for part in self.body_parts.values():
            part.draw(screen, font)
        
        # 在玩家上方显示等级
        level_font = pygame.font.SysFont(None, 20)
        level_text = level_font.render(f"Lv.{self.level}", True, CYAN)
        screen.blit(level_text, (self.x * GRID_SIZE, (self.y-2) * GRID_SIZE - 20))