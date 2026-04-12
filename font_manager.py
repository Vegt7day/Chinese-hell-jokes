"""
字体管理类
"""

import pygame
import os

class FontManager:
    """字体管理器"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'fonts'):
            self.fonts = {}
            self.load_fonts()
    
    def load_fonts(self):
        """加载字体"""
        # 尝试加载多种中文字体
        font_paths = [
            "fonts/simsum.ttf",           # 黑体
            "simhei.ttf",                 # 当前目录
            "C:/Windows/Fonts/simsun.ttc",  # Windows宋体
            "/System/Library/Fonts/PingFang.ttc",  # Mac字体
        ]
        
        loaded_font = None
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    loaded_font = font_path
                    print(f"找到字体文件: {font_path}")
                    
                    # 加载不同大小的字体
                    self.fonts[20] = pygame.font.Font(font_path, 20)
                    self.fonts[24] = pygame.font.Font(font_path, 24)
                    self.fonts[30] = pygame.font.Font(font_path, 30)
                    self.fonts[40] = pygame.font.Font(font_path, 40)
                    self.fonts[50] = pygame.font.Font(font_path, 50)
                    self.fonts[80] = pygame.font.Font(font_path, 80)
                    
                    print("字体加载成功！")
                    return
            except Exception as e:
                print(f"无法加载字体 {font_path}: {e}")
                continue
        
        # 如果都没有找到，使用默认字体
        print("警告：未找到中文字体文件，使用系统默认字体")
        print("请下载中文字体文件 simhei.ttf 到项目目录")
        
        # 使用pygame默认字体
        self.fonts[20] = pygame.font.SysFont(None, 20)
        self.fonts[24] = pygame.font.SysFont(None, 24)
        self.fonts[30] = pygame.font.SysFont(None, 30)
        self.fonts[40] = pygame.font.SysFont(None, 40)
        self.fonts[50] = pygame.font.SysFont(None, 50)
        self.fonts[80] = pygame.font.SysFont(None, 80)
    
    def get_font(self, size):
        """获取指定大小的字体"""
        if size in self.fonts:
            return self.fonts[size]
        else:
            # 如果请求的大小不存在，创建新的
            if hasattr(self, 'default_font_path') and os.path.exists(self.default_font_path):
                self.fonts[size] = pygame.font.Font(self.default_font_path, size)
            else:
                self.fonts[size] = pygame.font.SysFont(None, size)
            return self.fonts[size]