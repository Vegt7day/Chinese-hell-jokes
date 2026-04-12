"""
场景物体类
"""

import pygame
from __init__ import GRID_SIZE, BROWN, DARK_GREEN, RED, GRAY, DARK_YELLOW

class SceneObject:
    """场景物体基类"""
    def __init__(self, x, y, char, color, collidable=True):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.collidable = collidable
        self.rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
    
    def update_rect(self):
        self.rect = pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
    
    def draw(self, screen, font):
        text_surface = font.render(self.char, True, self.color)
        text_rect = text_surface.get_rect(center=(self.x * GRID_SIZE + GRID_SIZE//2, 
                                                  self.y * GRID_SIZE + GRID_SIZE//2))
        screen.blit(text_surface, text_rect)
    
    def collides_with(self, other):
        return self.rect.colliderect(other.rect)


class Ground(SceneObject):
    """地面"""
    def __init__(self, x, y):
        super().__init__(x, y, "地", BROWN, True)


class Wall(SceneObject):
    """墙壁"""
    def __init__(self, x, y):
        super().__init__(x, y, "墙", DARK_GREEN, True)


class Platform(SceneObject):
    """平台"""
    def __init__(self, x, y):
        super().__init__(x, y, "台", DARK_YELLOW, False)  # 可以从下方通过


class Door(SceneObject):
    """门"""
    def __init__(self, x, y):
        super().__init__(x, y, "门", RED, True)


class Trap(SceneObject):
    """陷阱"""
    def __init__(self, x, y):
        super().__init__(x, y, "陷", RED, True)
        self.damage = 1