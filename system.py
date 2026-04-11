"""
游戏系统类
"""

import pygame
import sys
from __init__ import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    GAME_STATE_MENU, GAME_STATE_PLAYING, GAME_STATE_GAME_OVER, GAME_STATE_VICTORY
)
from game import TankGame
from ui import UI

class GameSystem:
    """游戏系统类"""
    def __init__(self):
        # 初始化屏幕
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("文字版坦克大战 - 商鞅 vs 马")
        
        # 初始化UI
        self.ui = UI()
        self.ui.set_screen(self.screen)
        
        # 游戏状态
        self.state = GAME_STATE_MENU
        self.clock = pygame.time.Clock()
        
        # 关卡系统
        self.current_level = 1
        self.max_level = 5
        self.game_instance = None
    
    def run(self):
        """运行游戏主循环"""
        while True:
            # 处理事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    self.handle_keydown(event)
            
            # 更新游戏状态
            self.update()
            
            # 绘制
            self.draw()
            
            # 控制帧率
            self.clock.tick(FPS)
    
    def handle_keydown(self, event):
        """处理键盘按下事件"""
        if self.state == GAME_STATE_MENU:
            # 主菜单状态
            if event.key == pygame.K_1 and self.max_level >= 1:
                self.current_level = 1
            elif event.key == pygame.K_2 and self.max_level >= 2:
                self.current_level = 2
            elif event.key == pygame.K_3 and self.max_level >= 3:
                self.current_level = 3
            elif event.key == pygame.K_4 and self.max_level >= 4:
                self.current_level = 4
            elif event.key == pygame.K_5 and self.max_level >= 5:
                self.current_level = 5
            elif event.key == pygame.K_SPACE:
                # 开始游戏
                self.start_game()
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
        
        elif self.state in [GAME_STATE_GAME_OVER, GAME_STATE_VICTORY]:
            # 游戏结束或胜利状态
            if event.key == pygame.K_r:
                # 重新开始当前关卡
                self.start_game()
            elif event.key == pygame.K_ESCAPE:
                # 返回主菜单
                self.state = GAME_STATE_MENU
                self.game_instance = None
            elif event.key == pygame.K_n and self.state == GAME_STATE_VICTORY and self.current_level < self.max_level:
                # 进入下一关
                self.current_level += 1
                self.start_game()
        
        elif self.state == GAME_STATE_PLAYING:
            # 游戏进行中状态
            if event.key == pygame.K_ESCAPE:
                # 返回主菜单
                self.state = GAME_STATE_MENU
                self.game_instance = None
            elif event.key == pygame.K_SPACE:
                # 发射子弹
                if self.game_instance:
                    self.game_instance.player.attack(self.game_instance.bullets, self.game_instance.world)
    
    def start_game(self):
        """开始游戏"""
        self.game_instance = TankGame(self.current_level)
        self.state = GAME_STATE_PLAYING
    
    def update(self):
        """更新游戏"""
        if self.state == GAME_STATE_PLAYING and self.game_instance:
            # 获取按键状态
            keys = pygame.key.get_pressed()
            
            # 处理输入
            self.game_instance.handle_input(keys)
            
            # 更新游戏
            self.game_instance.update()
            
            # 检查游戏状态
            if self.game_instance.state == GAME_STATE_GAME_OVER:
                self.state = GAME_STATE_GAME_OVER
            elif self.game_instance.state == GAME_STATE_VICTORY:
                self.state = GAME_STATE_VICTORY
    
    def draw(self):
        """绘制游戏"""
        if self.state == GAME_STATE_MENU:
            # 绘制主菜单
            self.ui.draw_menu(self.current_level, self.max_level)
        
        elif self.state == GAME_STATE_PLAYING and self.game_instance:
            # 绘制游戏界面
            self.ui.draw_background()
            self.ui.draw_game(
                self.game_instance.get_game_objects(),
                self.game_instance.get_game_state()
            )
        
        elif self.state in [GAME_STATE_GAME_OVER, GAME_STATE_VICTORY] and self.game_instance:
            # 绘制游戏界面
            self.ui.draw_background()
            self.ui.draw_game(
                self.game_instance.get_game_objects(),
                self.game_instance.get_game_state()
            )
            
            # 绘制游戏结束画面
            self.ui.draw_game_over(
                self.game_instance.score,
                self.game_instance.level,
                self.state == GAME_STATE_VICTORY
            )
        
        # 更新显示
        pygame.display.flip()