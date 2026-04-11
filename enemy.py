"""
敌人类 - 马
"""

import pygame
import random
from __init__ import GRID_SIZE, HORSE_COLORS

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


class Horse(GameObject):
    """马类（敌人）"""
    def __init__(self, x, y):
        color = random.choice(HORSE_COLORS)
        super().__init__(x, y, "马", color)
        self.move_speed = 1  # 敌人移动速度
        self.direction = random.choice(["left", "right", "up", "down"])
        self.move_timer = 0
        self.move_delay = 30  # 移动延迟
        self.health = 2
        self.exp_value = 1
    
    def update(self, game_world):
        """更新敌人状态"""
        self.move_timer += 1
        if self.move_timer >= self.move_delay:
            self.move_timer = 0
            
            # 简单的移动逻辑：随机移动，碰到边界则改变方向
            if random.random() < 0.3:  # 30%几率改变方向
                self.direction = random.choice(["left", "right", "up", "down"])
            
            new_x, new_y = self.x, self.y
            
            if self.direction == "left":
                new_x -= 1
            elif self.direction == "right":
                new_x += 1
            elif self.direction == "up":
                new_y -= 1
            elif self.direction == "down":
                new_y += 1
            
            # 检查新位置是否在屏幕内
            if (0 <= new_x < game_world.width and 0 <= new_y < game_world.height):
                self.x = new_x
                self.y = new_y
                self.update_rect()
            else:
                # 如果新位置无效，改变方向
                directions = ["left", "right", "up", "down"]
                if self.direction in directions:
                    directions.remove(self.direction)
                if directions:  # 确保列表不为空
                    self.direction = random.choice(directions)
    
    def take_damage(self, damage):
        """受到伤害"""
        self.health -= damage
        return self.health <= 0