"""
UI界面类
"""

import pygame
from __init__ import (
    SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, RED, GREEN, BLUE, 
    YELLOW, PURPLE, CYAN, GRAY, DARK_GREEN, BROWN, DARK_YELLOW,
    GAME_STATE_MENU, GAME_STATE_PLAYING, GAME_STATE_PAUSED,
    GAME_STATE_GAME_OVER, GAME_STATE_VICTORY
)

class UI:
    """UI界面类"""
    def __init__(self):
        self.screen = None
        self.font = pygame.font.SysFont("simhei", 24)
        self.small_font = pygame.font.SysFont("simhei", 20)
        self.title_font = pygame.font.SysFont("simhei", 36, bold=True)
        self.big_font = pygame.font.SysFont("simhei", 72, bold=True)
    
    def set_screen(self, screen):
        """设置屏幕"""
        self.screen = screen
    
    def draw_background(self):
        """绘制背景"""
        self.screen.fill(BLACK)
    
    def draw_game(self, game_objects, game_state):
        """绘制游戏界面"""
        # 绘制游戏世界
        game_objects["world"].draw(self.screen)
        
        # 绘制玩家
        game_objects["player"].draw(self.screen, self.font)
        
        # 绘制敌人
        for enemy in game_objects["enemies"]:
            enemy.draw(self.screen, self.font)
        
        # 绘制子弹
        for bullet in game_objects["bullets"]:
            bullet.draw(self.screen, self.font)
        
        # 绘制UI
        self.draw_game_ui(game_state)
        self.draw_keyboard_status(game_state)
        # 绘制消息
        if game_state["message"]:
            self.draw_message(game_state["message"])
    
    def draw_game_ui(self, game_state):
        """绘制游戏UI"""
        # 绘制标题
        title = self.title_font.render("文字地狱游戏 - 商鞅 ", True, CYAN)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 10))
        
        level_display = self.font.render(f"关卡: {game_state['level']}", True, PURPLE)
        self.screen.blit(level_display,  (SCREEN_WIDTH//2 - level_display.get_width()//2, 50))
        

    def draw_message(self, message):
        """绘制消息"""
        message_surface = pygame.font.SysFont("simhei", 28).render(
            message, True, YELLOW)
        message_rect = message_surface.get_rect(center=(SCREEN_WIDTH//2, 50))
        self.screen.blit(message_surface, message_rect)
    
    def draw_keyboard_status(self, game_state):
        """绘制键盘触发状态（类似游戏主播的键盘映射）"""
        # 获取按键状态
        keys = pygame.key.get_pressed()
        
        # 键盘布局配置
        key_size = 40
        key_spacing = 5
        start_x = 20
        start_y = SCREEN_HEIGHT - 300
        
        # 定义键盘布局
        keyboard_layout = {
            # 第一行：数字键
            "1": {"label": "1", "key": pygame.K_1, "desc": "关卡1", "color": PURPLE},
            "2": {"label": "2", "key": pygame.K_2, "desc": "关卡2", "color": PURPLE},
            "3": {"label": "3", "key": pygame.K_3, "desc": "关卡3", "color": PURPLE},
            "4": {"label": "4", "key": pygame.K_4, "desc": "关卡4", "color": PURPLE},
            "5": {"label": "5", "key": pygame.K_5, "desc": "关卡5", "color": PURPLE},
            
            # 第二行：QWER
            "Q": {"label": "Q", "key": pygame.K_q, "desc": "切换部位", "color": GREEN},
            "W": {"label": "W", "key": pygame.K_w, "desc": "跳跃", "color": BLUE},
            "E": {"label": "E", "key": pygame.K_e, "desc": "(备用)", "color": GRAY},
            "R": {"label": "R", "key": pygame.K_r, "desc": "回收部位", "color": RED},
            
            # 第三行：ASDF
            "A": {"label": "A", "key": pygame.K_a, "desc": "左移", "color": CYAN},
            "S": {"label": "S", "key": pygame.K_s, "desc": "下蹲", "color": CYAN},
            "D": {"label": "D", "key": pygame.K_d, "desc": "右移", "color": CYAN},
            "F": {"label": "F", "key": pygame.K_f, "desc": "(备用)", "color": GRAY},
            
            # 第四行：ZXCV
            "Z": {"label": "Z", "key": pygame.K_z, "desc": "(备用)", "color": GRAY},
            "X": {"label": "X", "key": pygame.K_x, "desc": "(备用)", "color": GRAY},
            "C": {"label": "C", "key": pygame.K_c, "desc": "(备用)", "color": GRAY},
            "V": {"label": "V", "key": pygame.K_v, "desc": "(备用)", "color": GRAY},
            
            # 第五行：空格和特殊键
            "J": {"label": "J", "key": pygame.K_j, "desc": "发射/动作", "color": YELLOW, "x_offset": 2},
            "空格": {"label": "空格", "key": pygame.K_SPACE, "desc": "普通攻击", "color": YELLOW, "width": 120, "x_offset": 1},
            "ESC": {"label": "ESC", "key": pygame.K_ESCAPE, "desc": "菜单", "color": RED, "x_offset": 3}
        }
        
        # 绘制标题
        keyboard_title = self.small_font.render("键盘状态:", True, PURPLE)
        self.screen.blit(keyboard_title, (start_x, start_y - 30))
        
        # 绘制键盘按键
        row_height = key_size + 20
        col_width = key_size + key_spacing
        
        # 第一行：数字键
        for i, key in enumerate(["1", "2", "3", "4", "5"]):
            key_info = keyboard_layout[key]
            is_pressed = keys[key_info["key"]]
            self._draw_key_button(
                start_x + i * col_width, 
                start_y, 
                key_info, 
                is_pressed
            )
        
        # 第二行：QWER
        for i, key in enumerate(["Q", "W", "E", "R"]):
            key_info = keyboard_layout[key]
            is_pressed = keys[key_info["key"]]
            self._draw_key_button(
                start_x + i * col_width, 
                start_y + row_height, 
                key_info, 
                is_pressed
            )
        
        # 第三行：ASDF
        for i, key in enumerate(["A", "S", "D", "F"]):
            key_info = keyboard_layout[key]
            is_pressed = keys[key_info["key"]]
            self._draw_key_button(
                start_x + i * col_width, 
                start_y + row_height * 2, 
                key_info, 
                is_pressed
            )
        
        # 第四行：ZXCV
        for i, key in enumerate(["Z", "X", "C", "V"]):
            key_info = keyboard_layout[key]
            is_pressed = keys[key_info["key"]]
            self._draw_key_button(
                start_x + i * col_width, 
                start_y + row_height * 3, 
                key_info, 
                is_pressed
            )
        
        # 第五行：特殊键
        # J键
        j_info = keyboard_layout["J"]
        is_j_pressed = keys[j_info["key"]]
        self._draw_key_button(
            start_x, 
            start_y + row_height * 4, 
            j_info, 
            is_j_pressed
        )
        
        # 空格键
        space_info = keyboard_layout["空格"]
        is_space_pressed = keys[space_info["key"]]
        self._draw_key_button(
            start_x + col_width, 
            start_y + row_height * 4, 
            space_info, 
            is_space_pressed
        )
        
        # ESC键
        esc_info = keyboard_layout["ESC"]
        is_esc_pressed = keys[esc_info["key"]]
        self._draw_key_button(
            start_x + col_width + space_info.get("width", key_size) + key_spacing, 
            start_y + row_height * 4, 
            esc_info, 
            is_esc_pressed
        )
        

    def _draw_key_button(self, x, y, key_info, is_pressed):
        """绘制单个按键按钮"""
        # 按键大小
        width = key_info.get("width", 40)
        height = 40
        
        # 按键颜色
        normal_color = (50, 50, 50)  # 灰色
        pressed_color = key_info["color"]  # 按键对应的颜色
        
        # 绘制按键背景
        color = pressed_color if is_pressed else normal_color
        pygame.draw.rect(self.screen, color, (x, y, width, height), border_radius=5)
        
        # 绘制按键边框
        border_color = WHITE if is_pressed else (100, 100, 100)
        pygame.draw.rect(self.screen, border_color, (x, y, width, height), 2, border_radius=5)
        
        # 绘制按键标签
        key_font = pygame.font.SysFont("simhei", 16, bold=True)
        key_text = key_font.render(key_info["label"], True, WHITE)
        key_rect = key_text.get_rect(center=(x + width//2, y + height//2 - 8))
        self.screen.blit(key_text, key_rect)
        
        # 绘制按键功能描述
        desc_font = pygame.font.SysFont("simhei", 10)
        desc_text = desc_font.render(key_info["desc"], True, WHITE)
        desc_rect = desc_text.get_rect(center=(x + width//2, y + height//2 + 8))
        self.screen.blit(desc_text, desc_rect)

    def draw_menu(self, current_level, max_level):
        """绘制主菜单"""
        # 绘制背景
        self.screen.fill(BLACK)
        
        # 绘制标题
        title = self.big_font.render("文字地狱大战", True, CYAN)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        # 绘制关卡选择
        level_text = self.title_font.render(f"当前关卡: {current_level}", True, GREEN)
        self.screen.blit(level_text, (SCREEN_WIDTH//2 - level_text.get_width()//2, 300))
        
        # 绘制控制说明
        controls_y = 400
        controls = [
            "1-5: 选择关卡",
            "空格: 开始游戏",
            "ESC: 退出游戏"
        ]
        
        for i, control in enumerate(controls):
            control_text = self.font.render(control, True, WHITE)
            self.screen.blit(control_text, (SCREEN_WIDTH//2 - control_text.get_width()//2, controls_y + i * 40))
        
        # 绘制关卡信息
        info_y = 550
        info_text = self.small_font.render(f"共有{max_level}个关卡，每关敌人数量和难度递增", True, GRAY)
        self.screen.blit(info_text, (SCREEN_WIDTH//2 - info_text.get_width()//2, info_y))
    
    def draw_game_over(self, score, level, is_victory=False):
        """绘制游戏结束画面"""
        # 创建半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # 选择标题
        if is_victory:
            title = "恭喜通关！"
            title_color = GREEN
        else:
            title = "游戏结束"
            title_color = RED
        
        # 绘制标题
        title_font = pygame.font.SysFont("simhei", 48)
        title_surface = title_font.render(title, True, title_color)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
        self.screen.blit(title_surface, title_rect)
        
        # 绘制分数
        score_font = pygame.font.SysFont("simhei", 36)
        score_surface = score_font.render(f"分数: {score}", True, YELLOW)
        score_rect = score_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
        self.screen.blit(score_surface, score_rect)
        
        # 绘制关卡
        level_surface = score_font.render(f"关卡: {level}", True, YELLOW)
        level_rect = level_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10))
        self.screen.blit(level_surface, level_rect)
        
        # 绘制操作提示
        hint_font = pygame.font.SysFont("simhei", 24)
        
        if is_victory and level < 5:  # 不是最后一关
            hint1 = hint_font.render("按 R 重新开始当前关卡", True, WHITE)
            hint2 = hint_font.render("按 N 进入下一关", True, WHITE)
        else:
            hint1 = hint_font.render("按 R 重新开始游戏", True, WHITE)
            hint2 = hint_font.render("按 ESC 返回主菜单", True, WHITE)
        
        hint1_rect = hint1.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
        hint2_rect = hint2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 90))
        
        self.screen.blit(hint1, hint1_rect)
        self.screen.blit(hint2, hint2_rect)