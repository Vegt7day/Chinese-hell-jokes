"""
地图加载器
"""

import os
import random
from __init__ import SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE
from scene import Ground, Wall, Platform, Door, Trap, Switch, EndPoint, Hole
from player import ShangYang
from enemy import Horse


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

            if len(clean_lines) < 2:
                raise ValueError("关卡文件格式错误：至少需要地图尺寸和玩家信息两行")

            # 解析地图尺寸
            width, height = map(int, clean_lines[0].split())

            # 解析玩家信息
            # 格式示例：商鞅 10 20
            player_info = clean_lines[1].split()
            if len(player_info) < 3:
                raise ValueError("玩家信息格式错误，应为：名字 x y")

            player_x, player_y = map(int, player_info[1:3])

            # 创建游戏世界
            from system import GameWorld
            world = GameWorld(width, height)

            # 创建玩家
            player = ShangYang(player_x, player_y)

            # 创建敌人列表
            enemies = []

            # 解析场景物体
            for line in clean_lines[2:]:
                parts = line.split()
                if len(parts) < 3:
                    continue

                obj_type = parts[0]

                # -------------------------
                # 普通单格对象：类型 x y
                # -------------------------
                if obj_type in ["地", "墙", "台", "火", "门", "开", "马", "终", "洞"]:
                    x, y = map(int, parts[1:3])

                    if obj_type == "地":
                        world.add_scene_object(Ground(x, y))

                    elif obj_type == "墙":
                        world.add_scene_object(Wall(x, y))

                    elif obj_type == "台":
                        world.add_scene_object(Platform(x, y))

                    elif obj_type == "火":
                        world.add_scene_object(Trap(x, y))

                    elif obj_type == "洞":
                        world.add_scene_object(Hole(x, y))

                    elif obj_type == "门":
                        color_code = int(parts[3]) if len(parts) > 3 else 0
                        initial_state = parts[4] if len(parts) > 4 else "on"
                        world.add_scene_object(Door(x, y, color_code, initial_state))

                    elif obj_type == "开":
                        color_code = int(parts[3]) if len(parts) > 3 else 0
                        initial_state = parts[4] if len(parts) > 4 else "on"
                        world.add_scene_object(Switch(x, y, color_code, initial_state))

                    elif obj_type == "马":
                        enemies.append(Horse(x, y))

                    elif obj_type == "终":
                        world.add_scene_object(EndPoint(x, y))

                # -------------------------
                # 横向连续地面：ground_line x1 x2 y
                # 示例：ground_line 5 20 30
                # 表示 y=30, x从5到20
                # -------------------------
                elif obj_type == "ground_line":
                    if len(parts) < 4:
                        continue
                    x1 = int(parts[1])
                    x2 = int(parts[2])
                    y = int(parts[3])

                    for ground_x in range(min(x1, x2), max(x1, x2) + 1):
                        world.add_scene_object(Ground(ground_x, y))

                # -------------------------
                # 横向连续墙：wall_line x1 x2 y
                # -------------------------
                elif obj_type == "wall_line":
                    if len(parts) < 4:
                        continue
                    x1 = int(parts[1])
                    x2 = int(parts[2])
                    y = int(parts[3])

                    for wall_x in range(min(x1, x2), max(x1, x2) + 1):
                        world.add_scene_object(Wall(wall_x, y))

                # -------------------------
                # 横向连续平台：platform_line x1 x2 y
                # -------------------------
                elif obj_type == "platform_line":
                    if len(parts) < 4:
                        continue
                    x1 = int(parts[1])
                    x2 = int(parts[2])
                    y = int(parts[3])

                    for platform_x in range(min(x1, x2), max(x1, x2) + 1):
                        world.add_scene_object(Platform(platform_x, y))

            # 保险：全部加载完后重建一次碰撞图
            world.update_collision_grid()

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
        start_y = height - 5
        player = ShangYang(start_x, start_y)

        # 造一层地面
        for x in range(width):
            world.add_scene_object(Ground(x, height - 2))

        # 默认终点
        world.add_scene_object(EndPoint(width - 3, height - 3))

        # 默认几个敌人
        enemies = []
        enemy_count = 5 + level_number * 2
        for _ in range(enemy_count):
            x = random.randint(5, width - 5)
            y = random.randint(5, height - 6)
            enemies.append(Horse(x, y))

        world.update_collision_grid()
        return world, player, enemies