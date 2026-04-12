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
        
        # 绘制玩家状态
        status_y = 50
        level_text = self.font.render(f"等级: {game_state['player_level']}", True, GREEN)
        self.screen.blit(level_text, (20, status_y))
        
        exp_text = self.font.render(f"经验: {game_state['player_exp']}/{game_state['player_exp_to_next']}", True, GREEN)
        self.screen.blit(exp_text, (20, status_y + 30))
        
        health_text = self.font.render(f"生命: {game_state['player_health']}/{game_state['player_max_health']}", True, RED)
        self.screen.blit(health_text, (20, status_y + 60))
        
        score_text = self.font.render(f"分数: {game_state['score']}", True, YELLOW)
        self.screen.blit(score_text, (20, status_y + 90))
        
        killed_text = self.font.render(f"击败: {game_state['enemies_killed']}/{20 + game_state['level'] * 5}", True, YELLOW)
        self.screen.blit(killed_text, (20, status_y + 120))
        
        # 绘制当前关卡
        level_display = self.font.render(f"关卡: {game_state['level']}", True, PURPLE)
        self.screen.blit(level_display, (20, status_y + 150))
        
        # 绘制已解锁的攻击方式
        attacks_y = status_y + 180
        attacks_title = self.font.render("已解锁攻击部位:", True, BLUE)
        self.screen.blit(attacks_title, (20, attacks_y))
        
        # 这里需要从游戏状态中获取已解锁的攻击方式
        # 由于UI不知道玩家的具体状态，我们只显示通用的攻击方式
        attack_y_offset = 30
        attack_types = [
            ("手", "左右同时发射", GREEN),
            ("腿", "左右同时发射", BLUE),
            ("头", "向上发射", RED)
        ]
        
        for i, (name, desc, color) in enumerate(attack_types):
            if game_state['player_level'] > i:  # 简单判断是否解锁
                attack_text = self.small_font.render(f"  - {name} ({desc})", True, color)
                self.screen.blit(attack_text, (20, attacks_y + attack_y_offset))
                attack_y_offset += 25
        
        # 绘制当前可用部位
        available_y = attacks_y + attack_y_offset + 20
        available_title = self.font.render("当前可用部位:", True, PURPLE)
        self.screen.blit(available_title, (20, available_y))
        
        available_y_offset = 30
        available_parts = game_state.get("player_available_parts", [])
        
        if available_parts:
            for part in available_parts:
                part_text = self.small_font.render(f"  - {part}", True, GREEN)
                self.screen.blit(part_text, (20, available_y + available_y_offset))
                available_y_offset += 25
        else:
            no_parts_text = self.small_font.render("  无可用部位", True, RED)
            self.screen.blit(no_parts_text, (20, available_y + available_y_offset))
        
        # 绘制控制说明
        controls_y = SCREEN_HEIGHT - 180
        controls_title = self.font.render("控制说明:", True, PURPLE)
        self.screen.blit(controls_title, (SCREEN_WIDTH - 200, controls_y))
        
        controls = [
            "WASD - 移动",
            "空格 - 发射子弹",
            "ESC - 退出游戏",
            "R - 重新开始"
        ]
        
        for i, control in enumerate(controls):
            control_text = self.small_font.render(control, True, WHITE)
            self.screen.blit(control_text, (SCREEN_WIDTH - 200, controls_y + 30 + i * 25))
        
        # 绘制游戏目标
        target_y = SCREEN_HEIGHT - 250
        target_title = self.font.render("游戏目标:", True, PURPLE)
        self.screen.blit(target_title, (SCREEN_WIDTH - 200, target_y))
        
        target_text = self.small_font.render(f"过关", True, WHITE)
        self.screen.blit(target_text, (SCREEN_WIDTH - 200, target_y + 30))
        

        # 绘制生命条
        bar_width = 200
        bar_height = 20
        bar_x = SCREEN_WIDTH - bar_width - 20
        bar_y = 50
        
        # 绘制背景条
        pygame.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        
        # 绘制生命条
        health_ratio = game_state['player_health'] / game_state['player_max_health']
        health_width = int(bar_width * health_ratio)
        health_color = (
            int(255 * (1 - health_ratio)),
            int(255 * health_ratio),
            0
        )
        pygame.draw.rect(self.screen, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # 绘制生命条边框
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # 绘制生命条文本
        health_bar_text = self.small_font.render(f"生命值: {game_state['player_health']}/{game_state['player_max_health']}", True, WHITE)
        health_bar_rect = health_bar_text.get_rect(center=(bar_x + bar_width//2, bar_y + bar_height//2))
        self.screen.blit(health_bar_text, health_bar_rect)
    
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
        
        # 绘制状态说明
        status_y = start_y + row_height * 5 + 10
        status_font = pygame.font.SysFont("simhei", 16)
        
        # 玩家当前选中的部位
        selected_part = game_state.get("player_selected_part", "手")
        selected_text = status_font.render(f"当前部位: {selected_part}", True, GREEN)
        self.screen.blit(selected_text, (start_x, status_y))
        
        # 分离的部位
        separated_parts = game_state.get("player_separated_parts", [])
        if separated_parts:
            separated_text = status_font.render(f"分离: {', '.join(separated_parts)}", True, YELLOW)
            self.screen.blit(separated_text, (start_x + 120, status_y))
        else:
            separated_text = status_font.render("分离: 无", True, GRAY)
            self.screen.blit(separated_text, (start_x + 120, status_y))

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
        
        subtitle = self.title_font.render("商鞅 vs 马", True, YELLOW)
        self.screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 200))
        
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