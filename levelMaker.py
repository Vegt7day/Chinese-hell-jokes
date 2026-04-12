"""
地图生成器
"""

import pygame
import sys
import json
import os
from pygame.locals import *

# 初始化pygame
pygame.init()

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
DARK_GREEN = (0, 100, 0)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)
GRID_COLOR = (50, 50, 50)
BUTTON_HOVER_COLOR = (220, 220, 220)
BUTTON_SELECTED_COLOR = (100, 200, 100)

# 游戏配置
GRID_SIZE = 20
MIN_GRID_SIZE = 10
MAX_GRID_SIZE = 100
ITEM_PANEL_HEIGHT = 100
COLOR_PANEL_HEIGHT = 50
INFO_BAR_HEIGHT = 30
ITEM_BUTTON_WIDTH = 100
COLOR_BUTTON_WIDTH = 60

class MapGenerator:
    """地图生成器类"""
    
    def __init__(self):
        # 屏幕设置
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("地图生成器 - 商鞅 vs 马")
        
        # 网格设置
        self.grid_cols = 50
        self.grid_rows = 30
        self.map_width = self.grid_cols
        self.map_height = self.grid_rows
        
        # 创建地图数据
        self.map_data = [[None for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
        
        # 可用项目
        self.items = [
            {"name": "player", "label": "玩家", "color": BLUE, "fixed_color": True},
            {"name": "ground", "label": "地面", "color": (139, 69, 19), "fixed_color": True},  # 棕色
            {"name": "wall", "label": "墙壁", "color": DARK_GREEN, "fixed_color": True},
            {"name": "platform", "label": "平台", "color": ORANGE, "fixed_color": True},
            {"name": "trap", "label": "陷阱", "color": RED, "fixed_color": True},
            {"name": "door", "label": "门", "color": RED, "fixed_color": False},
            {"name": "switch", "label": "开关", "color": RED, "fixed_color": False},
            {"name": "horse", "label": "马(敌人)", "color": MAGENTA, "fixed_color": True},
        ]
        
        # 门和开关的颜色选项
        self.door_colors = [
            {"name": "red", "label": "红", "color": RED},
            {"name": "green", "label": "绿", "color": GREEN},
            {"name": "blue", "label": "蓝", "color": BLUE},
            {"name": "yellow", "label": "黄", "color": YELLOW},
            {"name": "purple", "label": "紫", "color": PURPLE},
            {"name": "cyan", "label": "青", "color": CYAN},
        ]
        
        # 当前设置
        self.selected_item_index = 0
        self.selected_color_index = 0
        self.dragging = False
        self.drag_start = None
        self.drag_end = None
        self.is_erasing = False
        
        # 玩家位置标记
        self.player_position = None
        
        # 字体 - 使用中文字体
        self.font_paths = [
            "C:/Windows/Fonts/simhei.ttf",  # Windows
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux
            "C:/Windows/Fonts/msyh.ttc",  # Windows 雅黑
            "C:/Windows/Fonts/simhei.ttf",  # Windows 黑体
        ]
        
        # 尝试加载中文字体
        self.font = None
        self.title_font = None
        self.button_font = None
        self.cell_font_cache = {}  # 缓存不同大小的字体
        
        for font_path in self.font_paths:
            if os.path.exists(font_path):
                try:
                    self.font = pygame.font.Font(font_path, 16)
                    self.title_font = pygame.font.Font(font_path, 20)
                    self.button_font = pygame.font.Font(font_path, 14)
                    print(f"使用字体: {font_path}")
                    break
                except:
                    continue
        
        # 如果找不到中文字体，使用默认字体
        if self.font is None:
            self.font = pygame.font.SysFont(None, 16)
            self.title_font = pygame.font.SysFont(None, 20)
            self.button_font = pygame.font.SysFont(None, 14)
            print("警告: 使用默认字体，可能无法显示中文")
        
        # 保存的文件名
        self.save_path = "./level"
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        
        # 缩放和滚动
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = ITEM_PANEL_HEIGHT + COLOR_PANEL_HEIGHT
        self.panning = False
        self.last_mouse_pos = None
        
        # 按钮状态
        self.item_button_rects = []
        self.color_button_rects = []
        self.hovered_item_index = -1
        self.hovered_color_index = -1
        
    def get_cell_font(self, size):
        """获取指定大小的字体，使用缓存"""
        if size not in self.cell_font_cache:
            # 尝试使用中文字体
            for font_path in self.font_paths:
                if os.path.exists(font_path):
                    try:
                        font = pygame.font.Font(font_path, size)
                        self.cell_font_cache[size] = font
                        break
                    except:
                        continue
            else:
                # 如果找不到中文字体，使用默认字体
                self.cell_font_cache[size] = pygame.font.SysFont(None, size)
        
        return self.cell_font_cache[size]
    
    def get_selected_item(self):
        """获取当前选中的项目"""
        return self.items[self.selected_item_index]
    
    def get_selected_color(self):
        """获取当前选中的颜色"""
        return self.door_colors[self.selected_color_index]
    
    def get_grid_pos(self, screen_x, screen_y):
        """将屏幕坐标转换为网格坐标"""
        grid_x = int((screen_x - self.offset_x) / (GRID_SIZE * self.zoom))
        grid_y = int((screen_y - self.offset_y) / (GRID_SIZE * self.zoom))
        return grid_x, grid_y
    
    def is_valid_grid_pos(self, grid_x, grid_y):
        """检查网格坐标是否有效"""
        return 0 <= grid_x < self.grid_cols and 0 <= grid_y < self.grid_rows
    
    def set_cell(self, grid_x, grid_y, item=None):
        """设置单元格内容"""
        if not self.is_valid_grid_pos(grid_x, grid_y):
            return False
        
        item_name = self.get_selected_item()["name"]
        
        # 如果是玩家，确保只有一个
        if item_name == "player":
            # 清除旧的玩家位置
            if self.player_position:
                old_x, old_y = self.player_position
                if self.is_valid_grid_pos(old_x, old_y):
                    self.map_data[old_y][old_x] = None
            
            # 设置新的玩家位置
            self.player_position = (grid_x, grid_y)
            self.map_data[grid_y][grid_x] = {"type": "player", "color_index": 0}
            return True
        
        # 如果是门或开关，需要记录颜色
        elif item_name in ["door", "switch"]:
            color_info = self.get_selected_color()
            self.map_data[grid_y][grid_x] = {
                "type": item_name,
                "color": color_info["name"],
                "color_index": self.selected_color_index
            }
            return True
        
        # 其他项目
        else:
            self.map_data[grid_y][grid_x] = {
                "type": item_name,
                "color_index": 0
            }
            return True
    
    def clear_cell(self, grid_x, grid_y):
        """清除单元格内容"""
        if not self.is_valid_grid_pos(grid_x, grid_y):
            return False
        
        # 如果是玩家位置，清除玩家标记
        if self.player_position == (grid_x, grid_y):
            self.player_position = None
        
        self.map_data[grid_y][grid_x] = None
        return True
    
    def fill_rect(self, start_x, start_y, end_x, end_y, fill_func):
        """填充矩形区域"""
        x1, x2 = sorted([start_x, end_x])
        y1, y2 = sorted([start_y, end_y])
        
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                if self.is_valid_grid_pos(x, y):
                    fill_func(x, y)
    
    def handle_events(self):
        """处理事件"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # 更新悬停状态
        self.hovered_item_index = -1
        self.hovered_color_index = -1
        
        # 检查项目按钮悬停
        for i, rect in enumerate(self.item_button_rects):
            if rect.collidepoint(mouse_x, mouse_y):
                self.hovered_item_index = i
                break
        
        # 检查颜色按钮悬停
        for i, rect in enumerate(self.color_button_rects):
            if rect.collidepoint(mouse_x, mouse_y):
                self.hovered_color_index = i
                break
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    mouse_x, mouse_y = event.pos
                    
                    # 检查是否在项目按钮区域
                    for i, rect in enumerate(self.item_button_rects):
                        if rect.collidepoint(mouse_x, mouse_y) and i < len(self.items):
                            self.selected_item_index = i
                            break
                    
                    # 检查是否在颜色按钮区域
                    for i, rect in enumerate(self.color_button_rects):
                        if rect.collidepoint(mouse_x, mouse_y) and i < len(self.door_colors):
                            self.selected_color_index = i
                            break
                    
                    # 检查是否在网格区域
                    if mouse_y >= self.offset_y:
                        grid_x, grid_y = self.get_grid_pos(mouse_x, mouse_y)
                        if self.is_valid_grid_pos(grid_x, grid_y):
                            self.dragging = True
                            self.drag_start = (grid_x, grid_y)
                            self.drag_end = (grid_x, grid_y)
                            self.is_erasing = False
                            self.set_cell(grid_x, grid_y)
                
                elif event.button == 3:  # 右键
                    mouse_x, mouse_y = event.pos
                    if mouse_y >= self.offset_y:
                        grid_x, grid_y = self.get_grid_pos(mouse_x, mouse_y)
                        if self.is_valid_grid_pos(grid_x, grid_y):
                            self.dragging = True
                            self.drag_start = (grid_x, grid_y)
                            self.drag_end = (grid_x, grid_y)
                            self.is_erasing = True
                            self.clear_cell(grid_x, grid_y)
                
                elif event.button == 4:  # 滚轮向上
                    # 滚轮在任何地方都可以切换项目
                    self.selected_item_index = (self.selected_item_index - 1) % len(self.items)
                
                elif event.button == 5:  # 滚轮向下
                    # 滚轮在任何地方都可以切换项目
                    self.selected_item_index = (self.selected_item_index + 1) % len(self.items)
                
                elif event.button == 2:  # 中键开始拖拽视图
                    self.panning = True
                    self.last_mouse_pos = event.pos
            
            elif event.type == MOUSEBUTTONUP:
                if event.button in [1, 3]:  # 左键或右键释放
                    if self.dragging and self.drag_start and self.drag_end:
                        start_x, start_y = self.drag_start
                        end_x, end_y = self.drag_end
                        
                        if start_x != end_x or start_y != end_y:
                            if self.is_erasing:
                                self.fill_rect(start_x, start_y, end_x, end_y, self.clear_cell)
                            else:
                                self.fill_rect(start_x, start_y, end_x, end_y, self.set_cell)
                        
                        self.dragging = False
                        self.drag_start = None
                        self.drag_end = None
                
                elif event.button == 2:  # 中键停止拖拽
                    self.panning = False
                    self.last_mouse_pos = None
            
            elif event.type == MOUSEMOTION:
                if self.dragging and self.drag_start:
                    mouse_x, mouse_y = event.pos
                    grid_x, grid_y = self.get_grid_pos(mouse_x, mouse_y)
                    if self.is_valid_grid_pos(grid_x, grid_y):
                        self.drag_end = (grid_x, grid_y)
                
                elif self.panning and self.last_mouse_pos:
                    dx = event.pos[0] - self.last_mouse_pos[0]
                    dy = event.pos[1] - self.last_mouse_pos[1]
                    self.offset_x += dx
                    self.offset_y += dy
                    self.last_mouse_pos = event.pos
            
            elif event.type == KEYDOWN:
                # 数字键选择颜色
                if event.key in [K_1, K_2, K_3, K_4, K_5, K_6]:
                    index = event.key - K_1
                    if index < len(self.door_colors):
                        self.selected_color_index = index
                
                # 加减号调整地图大小
                elif event.key == K_EQUALS or event.key == K_PLUS:  # +
                    self.resize_map(self.grid_cols + 5, self.grid_rows + 3)
                elif event.key == K_MINUS:  # -
                    new_cols = max(MIN_GRID_SIZE, self.grid_cols - 5)
                    new_rows = max(MIN_GRID_SIZE, self.grid_rows - 3)
                    self.resize_map(new_cols, new_rows)
                
                # 保存地图
                elif event.key == K_s and pygame.key.get_mods() & KMOD_CTRL:
                    self.save_map()
                
                # 加载地图
                elif event.key == K_l and pygame.key.get_mods() & KMOD_CTRL:
                    self.load_map()
                
                # 清空地图
                elif event.key == K_c and pygame.key.get_mods() & KMOD_CTRL:
                    self.clear_map()
                
                # 退出
                elif event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
    def resize_map(self, new_cols, new_rows):
        """调整地图大小"""
        new_cols = min(max(new_cols, MIN_GRID_SIZE), MAX_GRID_SIZE)
        new_rows = min(max(new_rows, MIN_GRID_SIZE), MAX_GRID_SIZE)
        
        new_map_data = [[None for _ in range(new_cols)] for _ in range(new_rows)]
        
        # 复制旧数据
        for y in range(min(self.grid_rows, new_rows)):
            for x in range(min(self.grid_cols, new_cols)):
                new_map_data[y][x] = self.map_data[y][x]
        
        # 更新玩家位置
        if self.player_position:
            px, py = self.player_position
            if px >= new_cols or py >= new_rows:
                self.player_position = None
        
        self.map_data = new_map_data
        self.grid_cols = new_cols
        self.grid_rows = new_rows
        self.map_width = new_cols
        self.map_height = new_rows
    
    def save_map(self):
        """保存地图到文件"""
        try:
            # 查找可用的关卡编号
            level_num = 1
            while os.path.exists(os.path.join(self.save_path, f"level_{level_num}.txt")):
                level_num += 1
            
            filename = os.path.join(self.save_path, f"level_{level_num}.txt")
            
            with open(filename, 'w', encoding='utf-8') as f:
                # 写入地图尺寸
                f.write(f"{self.grid_cols} {self.grid_rows}\n")
                
                # 写入玩家位置
                if self.player_position:
                    px, py = self.player_position
                    f.write(f"player {px} {py}\n")
                else:
                    f.write(f"player {self.grid_cols//2} {self.grid_rows-5}\n")
                
                # 写入所有物体
                for y in range(self.grid_rows):
                    for x in range(self.grid_cols):
                        cell = self.map_data[y][x]
                        if cell:
                            item_type = cell["type"]
                            
                            if item_type == "ground":
                                f.write(f"ground {x} {y}\n")
                            elif item_type == "wall":
                                f.write(f"wall {x} {y}\n")
                            elif item_type == "platform":
                                f.write(f"platform {x} {y}\n")
                            elif item_type == "trap":
                                f.write(f"trap {x} {y}\n")
                            elif item_type == "door":
                                color_name = cell.get("color", "red")
                                color_map = {"red": 0, "green": 1, "blue": 2, "yellow": 3, "purple": 4, "cyan": 5}
                                color_code = color_map.get(color_name, 0)
                                f.write(f"door {x} {y} {color_code}\n")
                            elif item_type == "switch":
                                color_name = cell.get("color", "red")
                                color_map = {"red": 0, "green": 1, "blue": 2, "yellow": 3, "purple": 4, "cyan": 5}
                                color_code = color_map.get(color_name, 0)
                                f.write(f"switch {x} {y} {color_code}\n")
                            elif item_type == "horse":
                                f.write(f"horse {x} {y}\n")
                
                print(f"地图已保存到: {filename}")
                return True
                
        except Exception as e:
            print(f"保存地图时出错: {e}")
            return False
    
    def load_map(self):
        """从文件加载地图"""
        try:
            # 查找最新的关卡文件
            level_num = 1
            latest_file = None
            
            while os.path.exists(os.path.join(self.save_path, f"level_{level_num}.txt")):
                latest_file = os.path.join(self.save_path, f"level_{level_num}.txt")
                level_num += 1
            
            if not latest_file:
                print("没有找到地图文件")
                return False
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # 读取地图尺寸
                width, height = map(int, lines[0].strip().split())
                self.resize_map(width, height)
                
                # 读取玩家位置
                player_parts = lines[1].strip().split()
                if player_parts[0] == "player":
                    px, py = map(int, player_parts[1:])
                    self.player_position = (px, py)
                
                # 清空地图
                self.map_data = [[None for _ in range(width)] for _ in range(height)]
                
                # 读取物体
                for line in lines[2:]:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    
                    item_type = parts[0]
                    x, y = map(int, parts[1:3])
                    
                    if not self.is_valid_grid_pos(x, y):
                        continue
                    
                    if item_type == "ground":
                        self.map_data[y][x] = {"type": "ground", "color_index": 0}
                    elif item_type == "wall":
                        self.map_data[y][x] = {"type": "wall", "color_index": 0}
                    elif item_type == "platform":
                        self.map_data[y][x] = {"type": "platform", "color_index": 0}
                    elif item_type == "trap":
                        self.map_data[y][x] = {"type": "trap", "color_index": 0}
                    elif item_type == "door":
                        color_code = int(parts[3]) if len(parts) > 3 else 0
                        color_names = ["red", "green", "blue", "yellow", "purple", "cyan"]
                        color_name = color_names[color_code] if color_code < len(color_names) else "red"
                        self.map_data[y][x] = {"type": "door", "color": color_name, "color_index": color_code}
                    elif item_type == "switch":
                        color_code = int(parts[3]) if len(parts) > 3 else 0
                        color_names = ["red", "green", "blue", "yellow", "purple", "cyan"]
                        color_name = color_names[color_code] if color_code < len(color_names) else "red"
                        self.map_data[y][x] = {"type": "switch", "color": color_name, "color_index": color_code}
                    elif item_type == "horse":
                        self.map_data[y][x] = {"type": "horse", "color_index": 0}
                
                print(f"地图已从 {latest_file} 加载")
                return True
                
        except Exception as e:
            print(f"加载地图时出错: {e}")
            return False
    
    def clear_map(self):
        """清空地图"""
        self.map_data = [[None for _ in range(self.grid_cols)] for _ in range(self.grid_rows)]
        self.player_position = None
    
    def draw_grid(self):
        """绘制网格"""
        for x in range(self.grid_cols + 1):
            screen_x = self.offset_x + x * GRID_SIZE * self.zoom
            pygame.draw.line(
                self.screen, GRID_COLOR,
                (screen_x, self.offset_y),
                (screen_x, self.offset_y + self.grid_rows * GRID_SIZE * self.zoom),
                1
            )
        
        for y in range(self.grid_rows + 1):
            screen_y = self.offset_y + y * GRID_SIZE * self.zoom
            pygame.draw.line(
                self.screen, GRID_COLOR,
                (self.offset_x, screen_y),
                (self.offset_x + self.grid_cols * GRID_SIZE * self.zoom, screen_y),
                1
            )
    
    def draw_cells(self):
        """绘制所有单元格"""
        for y in range(self.grid_rows):
            for x in range(self.grid_cols):
                cell = self.map_data[y][x]
                if cell:
                    screen_x = self.offset_x + x * GRID_SIZE * self.zoom
                    screen_y = self.offset_y + y * GRID_SIZE * self.zoom
                    cell_width = GRID_SIZE * self.zoom
                    cell_height = GRID_SIZE * self.zoom
                    
                    item_type = cell["type"]
                    
                    # 根据项目类型选择颜色
                    if item_type == "player":
                        color = BLUE
                        label = "商"
                    elif item_type == "ground":
                        color = (139, 69, 19)  # 棕色
                        label = "地"
                    elif item_type == "wall":
                        color = DARK_GREEN
                        label = "墙"
                    elif item_type == "platform":
                        color = ORANGE
                        label = "台"
                    elif item_type == "trap":
                        color = RED
                        label = "陷"
                    elif item_type == "door":
                        color_name = cell.get("color", "red")
                        color_map = {
                            "red": RED, "green": GREEN, "blue": BLUE,
                            "yellow": YELLOW, "purple": PURPLE, "cyan": CYAN
                        }
                        color = color_map.get(color_name, RED)
                        label = "门"
                    elif item_type == "switch":
                        color_name = cell.get("color", "red")
                        color_map = {
                            "red": RED, "green": GREEN, "blue": BLUE,
                            "yellow": YELLOW, "purple": PURPLE, "cyan": CYAN
                        }
                        color = color_map.get(color_name, RED)
                        label = "开"  # 默认显示"开"
                    elif item_type == "horse":
                        color = MAGENTA
                        label = "马"
                    else:
                        continue
                    
                    # 绘制单元格背景
                    pygame.draw.rect(
                        self.screen, color,
                        (screen_x, screen_y, cell_width, cell_height)
                    )
                    
                    # 绘制边框
                    pygame.draw.rect(
                        self.screen, BLACK,
                        (screen_x, screen_y, cell_width, cell_height),
                        1
                    )
                    
                    # 绘制文字
                    if cell_width > 10:  # 只在足够大时绘制文字
                        font_size = max(10, int(GRID_SIZE * self.zoom * 0.6))
                        cell_font = self.get_cell_font(font_size)
                        try:
                            text = cell_font.render(label, True, WHITE)
                            text_rect = text.get_rect(center=(screen_x + cell_width//2, screen_y + cell_height//2))
                            self.screen.blit(text, text_rect)
                        except:
                            # 如果渲染失败，绘制一个简单的方块
                            pass
    
    def draw_dragging_rect(self):
        """绘制拖拽矩形"""
        if self.dragging and self.drag_start and self.drag_end:
            start_x, start_y = self.drag_start
            end_x, end_y = self.drag_end
            
            x1, x2 = sorted([start_x, end_x])
            y1, y2 = sorted([start_y, end_y])
            
            for y in range(y1, y2 + 1):
                for x in range(x1, x2 + 1):
                    if self.is_valid_grid_pos(x, y):
                        screen_x = self.offset_x + x * GRID_SIZE * self.zoom
                        screen_y = self.offset_y + y * GRID_SIZE * self.zoom
                        cell_width = GRID_SIZE * self.zoom
                        cell_height = GRID_SIZE * self.zoom
                        
                        # 绘制半透明的预览
                        if self.is_erasing:
                            color = (255, 0, 0, 128)  # 红色半透明
                        else:
                            selected_item = self.get_selected_item()
                            color = (*selected_item["color"], 128)  # 当前颜色半透明
                        
                        # 创建一个临时surface来绘制半透明矩形
                        temp_surface = pygame.Surface((cell_width, cell_height), pygame.SRCALPHA)
                        pygame.draw.rect(temp_surface, color, (0, 0, cell_width, cell_height))
                        self.screen.blit(temp_surface, (screen_x, screen_y))
                        
                        # 绘制边框
                        border_color = RED if self.is_erasing else GREEN
                        pygame.draw.rect(
                            self.screen, border_color,
                            (screen_x, screen_y, cell_width, cell_height),
                            2
                        )
    
    def draw_item_panel(self):
        """绘制项目选择面板"""
        # 清空按钮矩形列表
        self.item_button_rects = []
        
        # 绘制项目按钮
        x = 10
        y = 10
        button_width = ITEM_BUTTON_WIDTH
        button_height = 30
        button_spacing = 10
        
        for i, item in enumerate(self.items):
            # 计算按钮位置
            button_rect = pygame.Rect(x, y, button_width, button_height)
            self.item_button_rects.append(button_rect)
            
            # 确定按钮颜色
            if i == self.selected_item_index:
                bg_color = BUTTON_SELECTED_COLOR
            elif i == self.hovered_item_index:
                bg_color = BUTTON_HOVER_COLOR
            else:
                bg_color = LIGHT_GRAY
            
            # 绘制按钮背景
            pygame.draw.rect(self.screen, bg_color, button_rect, border_radius=5)
            pygame.draw.rect(self.screen, BLACK, button_rect, 2, border_radius=5)
            
            # 绘制项目颜色预览
            color_preview_rect = pygame.Rect(x + 5, y + 5, 20, 20)
            pygame.draw.rect(self.screen, item["color"], color_preview_rect)
            pygame.draw.rect(self.screen, BLACK, color_preview_rect, 1)
            
            # 绘制项目标签
            try:
                label_text = self.button_font.render(item["label"], True, BLACK)
            except:
                # 如果字体不支持中文，使用英文标签
                labels = {
                    "玩家": "Player", "地面": "Ground", "墙壁": "Wall",
                    "平台": "Platform", "陷阱": "Trap", "门": "Door",
                    "开关": "Switch", "马(敌人)": "Horse"
                }
                english_label = labels.get(item["label"], item["label"])
                label_text = self.button_font.render(english_label, True, BLACK)
            
            text_rect = label_text.get_rect(midleft=(x + 30, y + button_height//2))
            self.screen.blit(label_text, text_rect)
            
            # 更新下一个按钮的位置
            x += button_width + button_spacing
            
            # 如果一行放不下，换行
            if x + button_width > self.screen_width - 10:
                x = 10
                y += button_height + 5
    
    def draw_color_panel(self):
        """绘制颜色选择面板"""
        # 清空颜色按钮矩形列表
        self.color_button_rects = []
        
        # 只有当前选中的项目可以选颜色时才显示颜色面板
        selected_item = self.get_selected_item()
        if selected_item["fixed_color"]:
            return
        
        # 绘制颜色选择面板背景
        color_panel_y = ITEM_PANEL_HEIGHT
        pygame.draw.rect(self.screen, DARK_GRAY, (0, color_panel_y, self.screen_width, COLOR_PANEL_HEIGHT))
        
        # 绘制标题
        try:
            title_text = self.font.render("颜色:", True, WHITE)
        except:
            title_text = self.font.render("Color:", True, WHITE)
        self.screen.blit(title_text, (10, color_panel_y + 10))
        
        # 绘制颜色按钮
        x = 80
        y = color_panel_y + 5
        button_width = COLOR_BUTTON_WIDTH
        button_height = 30
        button_spacing = 5
        
        for i, color_info in enumerate(self.door_colors):
            # 计算按钮位置
            button_rect = pygame.Rect(x, y, button_width, button_height)
            self.color_button_rects.append(button_rect)
            
            # 确定按钮颜色
            if i == self.selected_color_index:
                bg_color = BUTTON_SELECTED_COLOR
            elif i == self.hovered_color_index:
                bg_color = BUTTON_HOVER_COLOR
            else:
                bg_color = LIGHT_GRAY
            
            # 绘制按钮背景
            pygame.draw.rect(self.screen, bg_color, button_rect, border_radius=5)
            pygame.draw.rect(self.screen, BLACK, button_rect, 2, border_radius=5)
            
            # 绘制颜色预览
            color_preview_rect = pygame.Rect(x + 5, y + 5, 20, 20)
            pygame.draw.rect(self.screen, color_info["color"], color_preview_rect)
            pygame.draw.rect(self.screen, BLACK, color_preview_rect, 1)
            
            # 绘制颜色标签
            try:
                label_text = self.button_font.render(color_info["label"], True, BLACK)
            except:
                # 如果字体不支持中文，使用英文颜色名
                labels = {"红": "Red", "绿": "Green", "蓝": "Blue", 
                         "黄": "Yellow", "紫": "Purple", "青": "Cyan"}
                english_label = labels.get(color_info["label"], color_info["label"])
                label_text = self.button_font.render(english_label, True, BLACK)
            
            text_rect = label_text.get_rect(center=button_rect.center)
            self.screen.blit(label_text, text_rect)
            
            # 更新下一个按钮的位置
            x += button_width + button_spacing
    
    def draw_info_panel(self):
        """绘制信息面板"""
        info_panel_y = self.screen_height - INFO_BAR_HEIGHT
        
        # 绘制信息面板背景
        pygame.draw.rect(self.screen, DARK_GRAY, (0, info_panel_y, self.screen_width, INFO_BAR_HEIGHT))
        
        info_x = 10
        info_y = info_panel_y + 5
        
        selected_item = self.get_selected_item()
        selected_color = self.get_selected_color()
        
        # 当前选中的项目
        try:
            item_text = self.font.render(f"当前: {selected_item['label']}", True, WHITE)
        except:
            item_text = self.font.render(f"Current: {selected_item['label']}", True, WHITE)
        self.screen.blit(item_text, (info_x, info_y))
        
        # 当前选中的颜色
        if not selected_item["fixed_color"]:
            try:
                color_text = self.font.render(f"颜色: {selected_color['label']}", True, selected_color["color"])
            except:
                color_text = self.font.render(f"Color: {selected_color['label']}", True, selected_color["color"])
            self.screen.blit(color_text, (info_x + 150, info_y))
        
        # 地图信息
        try:
            map_info = self.font.render(f"地图尺寸: {self.grid_cols} × {self.grid_rows}", True, WHITE)
        except:
            map_info = self.font.render(f"Map Size: {self.grid_cols} × {self.grid_rows}", True, WHITE)
        self.screen.blit(map_info, (info_x + 300, info_y))
        
        # 玩家位置
        if self.player_position:
            px, py = self.player_position
            try:
                player_info = self.font.render(f"玩家位置: ({px}, {py})", True, BLUE)
            except:
                player_info = self.font.render(f"Player: ({px}, {py})", True, BLUE)
            self.screen.blit(player_info, (info_x + 500, info_y))
        
        # 绘制控制提示
        controls = [
            "Ctrl+S: 保存地图",
            "Ctrl+L: 加载地图",
            "Ctrl+C: 清空地图",
            "+/-: 调整尺寸",
        ]
        
        control_x = self.screen_width - 400
        for i, text in enumerate(controls):
            try:
                control_text = self.font.render(text, True, WHITE)
            except:
                # 如果字体不支持中文，使用英文提示
                english_controls = [
                    "Ctrl+S: Save map",
                    "Ctrl+L: Load map",
                    "Ctrl+C: Clear map",
                    "+/-: Resize",
                ]
                if i < len(english_controls):
                    control_text = self.font.render(english_controls[i], True, WHITE)
                else:
                    control_text = self.font.render(text, True, WHITE)
            
            self.screen.blit(control_text, (control_x + i * 100, info_y))
    
    def draw_toolbar(self):
        """绘制工具栏"""
        # 绘制项目面板背景
        pygame.draw.rect(self.screen, DARK_GRAY, (0, 0, self.screen_width, ITEM_PANEL_HEIGHT))
        
        # 绘制项目面板
        self.draw_item_panel()
        
        # 绘制颜色面板
        self.draw_color_panel()
    
    def draw(self):
        """绘制整个界面"""
        # 清屏
        self.screen.fill(BLACK)
        
        # 绘制网格
        self.draw_grid()
        
        # 绘制单元格
        self.draw_cells()
        
        # 绘制拖拽矩形
        self.draw_dragging_rect()
        
        # 绘制工具栏和信息面板
        self.draw_toolbar()
        self.draw_info_panel()
        
        # 更新显示
        pygame.display.flip()
    
    def run(self):
        """运行地图生成器"""
        clock = pygame.time.Clock()
        
        print("地图生成器启动!")
        print("使用Ctrl+S保存地图，Ctrl+L加载最近的地图")
        
        while True:
            self.handle_events()
            self.draw()
            clock.tick(60)

if __name__ == "__main__":
    generator = MapGenerator()
    generator.run()