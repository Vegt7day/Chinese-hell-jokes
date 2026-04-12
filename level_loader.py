"""
地图加载器
"""

import os
from __init__ import SCREEN_WIDTH,SCREEN_HEIGHT,GRID_SIZE
from scene import Ground, Wall, Platform, Door, Trap, Switch
from player import ShangYang
from enemy import Horse
import random

class LevelLoader:
    """地图加载器类"""
    
    @staticmethod
    def load_level(level_number):
        """加载指定关卡"""
        level_file = f"./level/level_{level_number}.txt"
        
        if not os.path.exists(level_file):
            # 如果没有找到关卡文件，使用默认关卡
            return LevelLoader.load_default_level(level_number)
        
        try:
            with open(level_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                        # 过滤掉注释和空行
            clean_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    clean_lines.append(stripped)
            # 解析地图信息
            width, height = map(int, lines[0].strip().split())
            
            # 解析玩家信息
            player_info = lines[1].strip().split()
            player_name = player_info[0]
            player_x, player_y = map(int, player_info[1:])
            
            # 创建游戏世界
            from system import GameWorld
            world = GameWorld(width, height)
            
            # 创建玩家
            player = ShangYang(player_x, player_y)
            
            # 创建敌人列表
            enemies = []
            
            # 解析场景物体
            for line in lines[2:]:
                line = line.strip()
                if not line or line.startswith('#'):  # 跳过空行和注释
                    continue
                
                parts = line.split()
                if len(parts) < 3:
                    continue
                
                obj_type = parts[0]
                x, y = map(int, parts[1:3])
                
                if obj_type == "ground":
                    world.add_scene_object(Ground(x, y))
                
                elif obj_type == "wall":
                    world.add_scene_object(Wall(x, y))
                
                elif obj_type == "platform":
                    world.add_scene_object(Platform(x, y))
                
                elif obj_type == "trap":
                    world.add_scene_object(Trap(x, y))
                
                elif obj_type == "door":
                    color_code = int(parts[3]) if len(parts) > 3 else 0
                    initial_state = parts[4] if len(parts) > 4 else "on"
                    world.add_scene_object(Door(x, y, color_code, initial_state))
                
                elif obj_type == "switch":
                    color_code = int(parts[3]) if len(parts) > 3 else 0
                    initial_state = parts[4] if len(parts) > 4 else "on"
                    world.add_scene_object(Switch(x, y, color_code, initial_state))
                
                elif obj_type == "horse":
                    # 敌人
                    enemies.append(Horse(x, y))
                
                elif obj_type == "ground_line":
                    # 地面线：从x1到x2的地面
                    x2 = int(parts[2])
                    for ground_x in range(x, x2 + 1):
                        world.add_scene_object(Ground(ground_x, y))
                
                elif obj_type == "wall_line":
                    # 墙壁线：从x1到x2的墙壁
                    x2 = int(parts[2])
                    for wall_x in range(x, x2 + 1):
                        world.add_scene_object(Wall(wall_x, y))
                
                elif obj_type == "platform_line":
                    # 平台线：从x1到x2的平台
                    x2 = int(parts[2])
                    for platform_x in range(x, x2 + 1):
                        world.add_scene_object(Platform(platform_x, y))
            
            return world, player, enemies
            
        except Exception as e:
            print(f"加载关卡{level_number}时出错: {e}")
            return LevelLoader.load_default_level(level_number)
    
    @staticmethod
    def load_default_level(level_number):
        """加载默认关卡（当没有找到关卡文件时使用）"""
        width = SCREEN_WIDTH // GRID_SIZE
        height = SCREEN_HEIGHT // GRID_SIZE
        
        from system import GameWorld
        world = GameWorld(width, height)
        
        # 创建玩家
        start_x = SCREEN_WIDTH // (2 * GRID_SIZE)
        start_y = world.ground_level - 5
        player = ShangYang(start_x, start_y)
        
        # 创建敌人
        enemies = []
        enemy_count = 5 + level_number * 2
        for _ in range(enemy_count):
            x = random.randint(5, width - 5)
            y = random.randint(5, height - 5)
            enemies.append(Horse(x, y))
        
        return world, player, enemies