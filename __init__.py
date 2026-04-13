"""
坦克大战游戏 - 常量定义和初始化
"""

import pygame
import sys

# 初始化Pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 1000
GRID_SIZE = 20
FPS = 60
MAX_LEVEL=5
# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
YELLOW = (255, 255, 50)
PURPLE = (200, 50, 200)
CYAN = (0, 200, 200)
GRAY = (150, 150, 150)
DARK_GREEN = (0, 150, 0)
BROWN = (150, 100, 50)
DARK_YELLOW = (150, 150, 0)  # 隐藏部位的颜色
WHITE = (255, 255, 255) 
# 新增颜色
DARK_RED = (150, 0, 0)
DARK_BLUE = (0, 0, 150)
DARK_GRAY = (100, 100, 100)

# 马的5种颜色
HORSE_COLORS = [
    (255, 100, 100),    # 红色
    (100, 255, 100),    # 绿色
    (100, 150, 255),    # 蓝色
    (255, 255, 100),    # 黄色
    (200, 100, 255),    # 紫色
]

# 游戏状态
GAME_STATE_MENU = 0
GAME_STATE_PLAYING = 1
GAME_STATE_PAUSED = 2
GAME_STATE_GAME_OVER = 3
GAME_STATE_VICTORY = 4