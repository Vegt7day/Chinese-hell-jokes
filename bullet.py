"""
子弹类
"""

import pygame
from __init__ import GRID_SIZE, GREEN, BLUE, RED,WHITE

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


class Bullet(GameObject):
    """子弹类"""
    def __init__(self, x, y, bullet_type, direction, level, player, side):
        char_dict = {"hand": "手", "leg": "腿", "head": "头"}
        color_dict = {"hand": WHITE, "leg": WHITE, "head": WHITE}
        
        super().__init__(x, y, char_dict[bullet_type], color_dict[bullet_type])
        self.bullet_type = bullet_type
        self.direction = direction
        self.level = level
        self.speed = 5  # 子弹速度是敌人的5倍
        self.damage = 1 + level  # 伤害随等级增加
        self.player = player
        self.side = side  # 哪个部位发射的（left, right, None）
    
    def update(self, game_world):
        """更新子弹位置"""
        # 根据方向移动
        if self.direction == "left":
            self.x -= self.speed / GRID_SIZE
        elif self.direction == "right":
            self.x += self.speed / GRID_SIZE
        elif self.direction == "up":
            self.y -= self.speed / GRID_SIZE
        
        self.update_rect()
        
        # 检查是否出界
        if (self.x < 0 or self.x >= game_world.width or 
            self.y < 0 or self.y >= game_world.height):
            # 子弹消失，回收对应部位
            self.player.recover_part(self.bullet_type, self.side)
            return False
        
        return True