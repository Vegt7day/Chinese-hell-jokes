"""
玩家类 - 商鞅
"""

import pygame
import random
from __init__ import GRID_SIZE, YELLOW, GREEN, BLUE, RED, CYAN, WHITE
from bullet import Bullet
from scene import Ground, Wall, Platform, Door, Trap, EndPoint  # 导入场景物体


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
        self.rect.x = self.x * GRID_SIZE
        self.rect.y = self.y * GRID_SIZE

    def draw(self, screen, font):
        if self.visible:
            text_surface = font.render(self.char, True, self.color)
            text_rect = text_surface.get_rect(center=(self.x * GRID_SIZE + GRID_SIZE // 2,
                                                      self.y * GRID_SIZE + GRID_SIZE // 2))
            screen.blit(text_surface, text_rect)

    def collides_with(self, other):
        return self.rect.colliderect(other.rect)


class ShangYang:
    """玩家角色 - 商鞅"""
    def __init__(self, x, y):
        # 玩家主体 - 竖排排列
        self.body_parts = {
            "head": GameObject(x, y - 2, "头", WHITE, True),
            "shang": GameObject(x, y - 1, "商", YELLOW, True),
            "left_hand": GameObject(x - 1, y - 1, "手", WHITE, True),
            "right_hand": GameObject(x + 1, y - 1, "手", WHITE, True),
            "yang": GameObject(x, y, "鞅", YELLOW, True),
            "left_leg": GameObject(x - 1, y + 1, "腿", WHITE, True),
            "right_leg": GameObject(x + 1, y + 1, "腿", WHITE, True)
        }

        # 主位置（以"商"为中心）
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.fall_check_timer = 0
        self.fall_check_interval = 5  # 每5帧检查一次
        self.big_jump_timer = 0

        # 游戏属性
        self.level = 1
        self.exp = 0
        self.exp_to_next_level = 5
        self.max_health = 10
        self.health = 10
        self.move_speed = 0.3
        self.direction = "right"
        self.waiting_leg_recovery = False

        # 攻击系统
        self.unlocked_attacks = ["hand"]
        self.active_bullets = {
            "hand_left": False,
            "hand_right": False,
            "leg_left": False,
            "leg_right": False,
            "head": False
        }
        self.attack_cooldown = 0

        # 重力系统
        self.gravity = 0.15
        self.vertical_velocity = 0
        self.is_jumping = False
        self.jump_power = 1.44
        self.super_jump_power = 2.5  # 强力跳跃力度
        self.on_ground = False
        self.ground_level = 0

        # 跳跃冷却
        self.jump_cooldown = 0

        # 新控制系统
        self.selected_part = "hand"  # 默认选择手
        self.available_parts = ["hand", "head", "leg"]  # 可选择的部位
        self.selected_index = 0  # 当前选择部位的索引

        # 身体部位留在原地状态
        self.left_hand_original_pos = None
        self.right_hand_original_pos = None
        self.head_original_pos = None
        self.left_leg_original_pos = None
        self.right_leg_original_pos = None

        # 部位是否分离状态
        self.parts_separated = {
            "left_hand": False,
            "right_hand": False,
            "head": False,
            "left_leg": False,
            "right_leg": False
        }

        # 攻击模式
        self.attack_mode = "horizontal"  # horizontal, vertical, super_jump

        # 冷却时间
        self.q_cooldown = 0
        self.j_cooldown = 0
        self.r_cooldown = 0

        # 攻击状态
        self.just_fired_bullet = False
        self.last_fired_bullet = None

        # 移动状态
        self.is_airborne_without_legs = False
        self.airborne_movement_allowed = True

        # 调试开关
        self.debug_recovery = False

    def debug_print(self, *args):
        if self.debug_recovery:
            print("[RECOVERY DEBUG]", *args)

    def check_trap_collision(self, game_world):
        """检查玩家任意身体部位是否碰到陷阱(火)"""
        for obj in game_world.get_scene_objects():
            if not isinstance(obj, Trap):
                continue

            for part_name, part in self.body_parts.items():
                if part.visible:
                    if part.collides_with(obj):
                        return True
                    if int(part.x) == int(obj.x) and int(part.y) == int(obj.y):
                        return True

            if self.parts_separated["left_leg"] and self.left_leg_original_pos:
                leg_x, leg_y = self.left_leg_original_pos
                if int(leg_x) == int(obj.x) and int(leg_y) == int(obj.y):
                    return True

            if self.parts_separated["right_leg"] and self.right_leg_original_pos:
                leg_x, leg_y = self.right_leg_original_pos
                if int(leg_x) == int(obj.x) and int(leg_y) == int(obj.y):
                    return True

        return False

    def check_below_empty(self, game_world):
        """检查当前支撑部位下方是否为空"""
        support_parts = self.get_support_parts()

        for name in support_parts:
            part = self.body_parts[name]

            if not part.visible or self.parts_separated.get(name, False):
                continue

            part_x = int(part.x)
            part_y = int(part.y) + 1

            if 0 <= part_x < game_world.width and 0 <= part_y < game_world.height:
                if game_world.collision_grid[part_x][part_y] == 1:
                    return False

        return True

    def is_part_colliding_at_position(self, part_name, player_x, player_y, game_world):
        """检测指定部位在玩家位于(player_x, player_y)时是否与障碍重叠"""
        if part_name not in self.body_parts:
            self.debug_print(f"is_part_colliding_at_position: 未知部位 {part_name}")
            return False

        offsets = {
            "head": (0, -2),
            "shang": (0, -1),
            "left_hand": (-1, -1),
            "right_hand": (1, -1),
            "yang": (0, 0),
            "left_leg": (-1, 1),
            "right_leg": (1, 1)
        }

        if part_name not in offsets:
            self.debug_print(f"is_part_colliding_at_position: offsets里没有 {part_name}")
            return False

        offset_x, offset_y = offsets[part_name]
        test_x = player_x + offset_x
        test_y = player_y + offset_y

        x_int = int(test_x)+1
        y_int = int(test_y)+1

        if 0 <= x_int < game_world.width and 0 <= y_int < game_world.height:
            result = game_world.collision_grid[x_int][y_int] == 1
            self.debug_print(
                f"检测部位 {part_name}: 玩家中心=({player_x:.2f},{player_y:.2f}) "
                f"部位坐标=({test_x:.2f},{test_y:.2f}) -> 格子=({x_int},{y_int}) 碰撞={result}"
            )
            return result

        self.debug_print(
            f"检测部位 {part_name}: 玩家中心=({player_x:.2f},{player_y:.2f}) "
            f"部位坐标=({test_x:.2f},{test_y:.2f}) 越界，视为碰撞"
        )
        return True

    def get_colliding_recovered_parts(self, game_world):
        """获取当前回收后卡在障碍中的部位列表"""
        colliding_parts = []

        self.debug_print(f"开始检测回收后卡住部位，当前玩家中心=({self.x:.2f}, {self.y:.2f})")

        for part_name, part in self.body_parts.items():
            if not part.visible:
                self.debug_print(f"跳过 {part_name}: 不可见")
                continue
            if self.parts_separated.get(part_name, False):
                self.debug_print(f"跳过 {part_name}: 仍处于分离状态")
                continue

            if self.is_part_colliding_at_position(part_name, self.x, self.y, game_world):
                colliding_parts.append(part_name)

        self.debug_print(f"当前卡住部位列表: {colliding_parts}")
        return colliding_parts

    def force_shift_after_recovery(self, dx, dy, game_world):
        """回收后用于脱困的强制整体位移，不走普通移动判定"""
        old_x, old_y = self.x, self.y
        new_x = self.x + dx
        new_y = self.y + dy

        min_x = 1
        max_x = game_world.width - 2
        min_y = 2
        max_y = game_world.height - 2

        new_x = max(min_x, min(new_x, max_x))
        new_y = max(min_y, min(new_y, max_y))

        self.debug_print(
            f"强制位移: 原位置=({old_x:.2f},{old_y:.2f}) 位移=({dx},{dy}) "
            f"目标=({new_x:.2f},{new_y:.2f})"
        )

        self.x = new_x
        self.y = new_y
        self.update_position(self.x, self.y)

        self.debug_print(f"强制位移后位置=({self.x:.2f},{self.y:.2f})")
        return True

    def can_shift_to(self, new_x, new_y, game_world):
        """检测整体移动到(new_x, new_y)后所有可见且未分离部位是否安全"""
        for part_name, part in self.body_parts.items():
            if not part.visible:
                continue
            if self.parts_separated.get(part_name, False):
                continue

            if self.is_part_colliding_at_position(part_name, new_x, new_y, game_world):
                return False

        return True

    def resolve_recovery_stuck_by_symmetry(self, game_world):
        """回收部位后若卡入障碍，按对称部位规则强制修正"""
        self.debug_print("=== 进入 resolve_recovery_stuck_by_symmetry ===")

        colliding_parts = self.get_colliding_recovered_parts(game_world)

        if not colliding_parts:
            self.debug_print("没有卡住部位，不需要修正")
            return False

        self.debug_print(f"检测到卡住部位: {colliding_parts}")

        # 左腿卡，右腿不卡 -> 整体向右强制平移一格
        if "left_leg" in colliding_parts:
            right_leg_colliding = self.is_part_colliding_at_position("right_leg", self.x, self.y, game_world)
            self.debug_print(f"分支判断: 左腿卡住，右腿是否卡住? {right_leg_colliding}")
            if not right_leg_colliding:
                self.debug_print("执行规则: 左腿卡 / 右腿不卡 -> 向右强制位移1格")
                self.force_shift_after_recovery(1, 0, game_world)
                return True

        # 右腿卡，左腿不卡 -> 整体向左强制平移一格
        if "right_leg" in colliding_parts:
            left_leg_colliding = self.is_part_colliding_at_position("left_leg", self.x, self.y, game_world)
            self.debug_print(f"分支判断: 右腿卡住，左腿是否卡住? {left_leg_colliding}")
            if not left_leg_colliding:
                self.debug_print("执行规则: 右腿卡 / 左腿不卡 -> 向左强制位移1格")
                self.force_shift_after_recovery(-1, 0, game_world)
                return True

        # 左手卡，右手不卡 -> 整体向右强制平移一格
        if "left_hand" in colliding_parts:
            right_hand_colliding = self.is_part_colliding_at_position("right_hand", self.x, self.y, game_world)
            self.debug_print(f"分支判断: 左手卡住，右手是否卡住? {right_hand_colliding}")
            if not right_hand_colliding:
                self.debug_print("执行规则: 左手卡 / 右手不卡 -> 向右强制位移1格")
                self.force_shift_after_recovery(1, 0, game_world)
                return True

        # 右手卡，左手不卡 -> 整体向左强制平移一格
        if "right_hand" in colliding_parts:
            left_hand_colliding = self.is_part_colliding_at_position("left_hand", self.x, self.y, game_world)
            self.debug_print(f"分支判断: 右手卡住，左手是否卡住? {left_hand_colliding}")
            if not left_hand_colliding:
                self.debug_print("执行规则: 右手卡 / 左手不卡 -> 向左强制位移1格")
                self.force_shift_after_recovery(-1, 0, game_world)
                return True

        # 两腿都卡住，则看头是否安全，若头安全则向上强制位移一格
        if "left_leg" in colliding_parts and "right_leg" in colliding_parts:
            head_colliding = self.is_part_colliding_at_position("head", self.x, self.y, game_world)
            self.debug_print(f"分支判断: 两腿都卡住，头是否卡住? {head_colliding}")
            if not head_colliding:
                self.debug_print("执行规则: 两腿都卡 / 头不卡 -> 向上强制位移1格")
                self.force_shift_after_recovery(0, -1, game_world)
                return True

        self.debug_print("没有命中任何可执行修正规则")
        return False

    def resolve_recovery_stuck_loop(self, game_world, max_attempts=3):
        """回收后重复尝试对称纠偏，避免一次位移不够"""
        self.debug_print(f"=== 进入 resolve_recovery_stuck_loop，最多尝试 {max_attempts} 次 ===")

        for i in range(max_attempts):
            colliding_parts = self.get_colliding_recovered_parts(game_world)
            self.debug_print(f"第 {i + 1} 次纠偏前，卡住部位: {colliding_parts}")

            if not colliding_parts:
                self.debug_print("已经没有卡住部位，纠偏成功")
                return True

            moved = self.resolve_recovery_stuck_by_symmetry(game_world)
            self.debug_print(f"第 {i + 1} 次纠偏是否发生移动: {moved}")

            if not moved:
                self.debug_print("本次未能执行纠偏，提前结束")
                return False

        final_colliding = self.get_colliding_recovered_parts(game_world)
        self.debug_print(f"纠偏结束后最终卡住部位: {final_colliding}")
        return len(final_colliding) == 0

    def update_position(self, x, y):
        """更新玩家位置"""
        self.x = x
        self.y = y

        # 只更新没有分离的身体部位
        if not self.parts_separated["head"]:
            self.body_parts["head"].x = x
            self.body_parts["head"].y = y - 2

        if not self.parts_separated["left_hand"]:
            self.body_parts["left_hand"].x = x - 1
            self.body_parts["left_hand"].y = y - 1

        if not self.parts_separated["right_hand"]:
            self.body_parts["right_hand"].x = x + 1
            self.body_parts["right_hand"].y = y - 1

        # 核心部分始终跟随
        self.body_parts["shang"].x = x
        self.body_parts["shang"].y = y - 1

        self.body_parts["yang"].x = x
        self.body_parts["yang"].y = y

        if not self.parts_separated["left_leg"]:
            self.body_parts["left_leg"].x = x - 1
            self.body_parts["left_leg"].y = y + 1

        if not self.parts_separated["right_leg"]:
            self.body_parts["right_leg"].x = x + 1
            self.body_parts["right_leg"].y = y + 1

        # 更新所有部位的矩形
        for part in self.body_parts.values():
            part.update_rect()

    def set_ground_level(self, ground_level):
        """设置地面高度"""
        self.ground_level = ground_level

    def get_collision_rects(self):
        """获取玩家所有碰撞矩形"""
        rects = []
        for part in self.body_parts.values():
            if part.visible:
                rects.append(part.rect)
        return rects

    def find_horizontal_collision_distance(self, target_x, game_world, direction):
        """查找水平方向最近的碰撞距离"""
        if direction == 0:
            return target_x

        current_x = self.x
        step = 1 if target_x > current_x else -1

        for test_x in range(int(current_x + step), int(target_x + step), int(step)):
            if self.check_horizontal_collision(test_x, game_world):
                return test_x - step

        return target_x

    def find_vertical_collision_distance(self, target_y, game_world, direction):
        """查找垂直方向最近的碰撞距离"""
        if direction == 0:
            return target_y

        current_y = self.y
        step = 1 if target_y > current_y else -1

        for test_y in range(int(current_y + step), int(target_y + step), int(step)):
            if self.check_vertical_collision(test_y, game_world, direction < 0):
                return test_y - step

        return target_y

    def check_horizontal_collision(self, test_x, game_world):
        """检查特定水平位置是否有碰撞"""
        temp_parts = {}
        for name, part in self.body_parts.items():
            if part.visible and not self.parts_separated.get(name, False):
                offset_x = part.x - self.x
                offset_y = part.y - self.y
                new_part_x = test_x + offset_x
                new_part_y = self.y + offset_y
                temp_rect = pygame.Rect(new_part_x * GRID_SIZE, new_part_y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                temp_parts[name] = temp_rect

        for scene_obj in game_world.get_scene_objects():
            if not scene_obj.collidable:
                continue

            for part_name, part_rect in temp_parts.items():
                if part_rect.colliderect(scene_obj.rect):
                    return True

        return False

    def check_vertical_collision(self, test_y, game_world, check_up=False):
        """检查特定垂直位置是否有碰撞"""
        temp_parts = {}
        for name, part in self.body_parts.items():
            if part.visible and not self.parts_separated.get(name, False):
                offset_x = part.x - self.x
                offset_y = part.y - self.y
                new_part_x = self.x + offset_x
                new_part_y = test_y + offset_y+1
                temp_rect = pygame.Rect(new_part_x * GRID_SIZE, new_part_y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                temp_parts[name] = temp_rect

        for scene_obj in game_world.get_scene_objects():
            if not scene_obj.collidable:
                continue

            for part_name, part_rect in temp_parts.items():
                if part_rect.colliderect(scene_obj.rect):
                    return "up" if check_up else "down"

        return None

    def select_next_part(self):
        """选择下一个部位"""
        if self.q_cooldown > 0:
            return

        self.selected_index = (self.selected_index + 1) % len(self.available_parts)
        self.selected_part = self.available_parts[self.selected_index]

        if self.selected_part == "hand":
            self.attack_mode = "horizontal"
        elif self.selected_part == "head":
            self.attack_mode = "vertical"
        elif self.selected_part == "leg":
            self.attack_mode = "super_jump"

        self.reset_body_part_colors()

        if self.selected_part == "hand":
            if not self.parts_separated["left_hand"]:
                self.body_parts["left_hand"].color = GREEN
            if not self.parts_separated["right_hand"]:
                self.body_parts["right_hand"].color = GREEN
        elif self.selected_part == "head":
            if not self.parts_separated["head"]:
                self.body_parts["head"].color = GREEN
        elif self.selected_part == "leg":
            if not self.parts_separated["left_leg"]:
                self.body_parts["left_leg"].color = GREEN
            if not self.parts_separated["right_leg"]:
                self.body_parts["right_leg"].color = GREEN

        self.q_cooldown = 3

    def reset_body_part_colors(self):
        """重置所有身体部位的颜色"""
        if not self.parts_separated["head"]:
            self.body_parts["head"].color = WHITE
        if not self.parts_separated["left_hand"]:
            self.body_parts["left_hand"].color = WHITE
        if not self.parts_separated["right_hand"]:
            self.body_parts["right_hand"].color = WHITE
        if not self.parts_separated["left_leg"]:
            self.body_parts["left_leg"].color = WHITE
        if not self.parts_separated["right_leg"]:
            self.body_parts["right_leg"].color = WHITE

    def perform_action(self, game_world):
        """执行当前选中的动作"""
        if self.j_cooldown > 0:
            return False

        action_performed = False

        if self.attack_mode == "horizontal":
            action_performed = self.horizontal_attack(game_world)
            self.just_fired_bullet = True
        elif self.attack_mode == "vertical":
            action_performed = self.vertical_attack(game_world)
            self.just_fired_bullet = True
        elif self.attack_mode == "super_jump":
            action_performed = self.super_jump(game_world)
            self.big_jump_timer = 20

        if action_performed:
            self.j_cooldown = 15

        return action_performed

    def horizontal_attack(self, game_world):
        """水平发射子弹"""
        if not self.can_attack("hand", "left") or not self.can_attack("hand", "right"):
            return False

        bullet_left = Bullet(self.x - 2, self.y - 1, "hand", "left", self.level, self, "left")
        bullet_right = Bullet(self.x + 2, self.y - 1, "hand", "right", self.level, self, "right")

        self.last_fired_bullet = [bullet_left, bullet_right]

        self.set_bullet_active("hand", "left", True)
        self.set_bullet_active("hand", "right", True)

        self.parts_separated["left_hand"] = True
        self.parts_separated["right_hand"] = True

        self.left_hand_original_pos = (self.body_parts["left_hand"].x, self.body_parts["left_hand"].y)
        self.right_hand_original_pos = (self.body_parts["right_hand"].x, self.body_parts["right_hand"].y)

        self.body_parts["left_hand"].visible = False
        self.body_parts["right_hand"].visible = False

        return True

    def vertical_attack(self, game_world):
        """垂直发射子弹"""
        if not self.can_attack("head"):
            return False

        bullet = Bullet(self.x, self.y - 3, "head", "up", self.level, self, None)

        self.last_fired_bullet = bullet

        self.set_bullet_active("head", None, True)

        self.parts_separated["head"] = True

        self.head_original_pos = (self.body_parts["head"].x, self.body_parts["head"].y)

        self.body_parts["head"].visible = False

        return True

    def get_fired_bullets(self):
        """获取刚刚发射的子弹"""
        if not self.just_fired_bullet or not self.last_fired_bullet:
            return []

        bullets = []
        if isinstance(self.last_fired_bullet, list):
            bullets.extend(self.last_fired_bullet)
        else:
            bullets.append(self.last_fired_bullet)

        self.just_fired_bullet = False
        return bullets

    def super_jump(self, game_world):
        """强力跳跃 - 腿留在原地"""
        if not self.on_ground or self.jump_cooldown > 0 or self.has_legs_separated():
            return False

        self.parts_separated["left_leg"] = True
        self.parts_separated["right_leg"] = True

        self.left_leg_original_pos = (self.body_parts["left_leg"].x, self.body_parts["left_leg"].y)
        self.right_leg_original_pos = (self.body_parts["right_leg"].x, self.body_parts["right_leg"].y)

        self.body_parts["left_leg"].visible = False
        self.body_parts["right_leg"].visible = False

        self.is_jumping = True
        self.is_airborne_without_legs = True
        self.airborne_movement_allowed = True
        self.on_ground = False
        self.vertical_velocity = -self.super_jump_power
        self.jump_cooldown = 20

        return True

    def has_legs_separated(self):
        """检查腿是否已经分离"""
        return self.parts_separated["left_leg"] and self.parts_separated["right_leg"]

    def check_leg_auto_recover(self, game_world):
        """检查是否应该自动回收腿"""
        if not self.has_legs_separated():
            return False
        if self.big_jump_timer > 0:
            return False

        left_leg_x, left_leg_y = self.left_leg_original_pos
        right_leg_x, right_leg_y = self.right_leg_original_pos

        player_x = self.x
        player_y = self.y

        if abs(player_x - left_leg_x) <= 2 and abs(player_y - left_leg_y) <= 2:
            return True

        if abs(player_x - right_leg_x) <= 2 and abs(player_y - right_leg_y) <= 2:
            return True

        if abs(player_x - (left_leg_x + right_leg_x) / 2) <= 2 and abs(player_y - (left_leg_y + right_leg_y) / 2) <= 2:
            return True

        return False

    def check_foot_collision_after_recovery(self, new_y, game_world):
        """检查回收腿后是否会与脚下障碍碰撞"""
        temp_y = new_y

        left_leg_temp = GameObject(self.x - 1, temp_y + 1, "腿", WHITE, True)
        right_leg_temp = GameObject(self.x + 1, temp_y + 1, "腿", WHITE, True)

        for scene_obj in game_world.get_scene_objects():
            if not scene_obj.collidable:
                continue

            if left_leg_temp.rect.colliderect(scene_obj.rect) or right_leg_temp.rect.colliderect(scene_obj.rect):
                return True

        return False

    def start_leg_recovery_jump(self, game_world):
        """开始腿部回收流程：先执行小跳，等到最高点再真正回收腿"""
        self.debug_print("=== 调用 start_leg_recovery_jump ===")

        if self.r_cooldown > 0:
            self.debug_print(f"start_leg_recovery_jump: r_cooldown={self.r_cooldown}，不能开始")
            return False

        if not self.parts_separated["left_leg"] and not self.parts_separated["right_leg"]:
            self.debug_print("start_leg_recovery_jump: 没有分离的腿")
            return False

        if self.waiting_leg_recovery:
            self.debug_print("start_leg_recovery_jump: 已在等待腿回收")
            return False

        # collision_result = self.check_vertical_collision(self.y - 1, game_world, True)
        # self.debug_print(f"start_leg_recovery_jump: 头顶检测结果={collision_result}")
        # if collision_result == "up":
        #     self.debug_print("start_leg_recovery_jump: 头顶有障碍，不能起跳")
        #     return False

        self.waiting_leg_recovery = True
        self.r_cooldown = 20
        self.is_airborne_without_legs = False
        self.airborne_movement_allowed = False

        small_jump_power = self.jump_power * 0.5
        self.is_jumping = True
        self.on_ground = False
        self.vertical_velocity = -small_jump_power
        self.jump_cooldown = 5

        self.debug_print(f"start_leg_recovery_jump: 启动成功，vertical_velocity={self.vertical_velocity}")
        return True

    def finish_leg_recovery(self, game_world):
        """在小跳最高点真正回收腿"""
        self.debug_print("=== 调用 finish_leg_recovery ===")

        if not self.waiting_leg_recovery:
            self.debug_print("finish_leg_recovery: waiting_leg_recovery=False，直接返回")
            return False

        recovered = False

        if self.parts_separated["left_leg"]:
            self.debug_print("回收左腿")
            self.parts_separated["left_leg"] = False
            self.set_bullet_active("leg", "left", False)
            self.body_parts["left_leg"].visible = True
            self.body_parts["left_leg"].color = GREEN if self.selected_part == "leg" else WHITE
            recovered = True

        if self.parts_separated["right_leg"]:
            self.debug_print("回收右腿")
            self.parts_separated["right_leg"] = False
            self.set_bullet_active("leg", "right", False)
            self.body_parts["right_leg"].visible = True
            self.body_parts["right_leg"].color = GREEN if self.selected_part == "leg" else WHITE
            recovered = True

        if recovered:
            self.debug_print("finish_leg_recovery: 腿已回收，开始更新位置并纠偏")
            self.update_position(self.x, self.y)

            self.debug_print(f"回收腿后当前位置=({self.x:.2f}, {self.y:.2f})")
            self.debug_print(f"回收腿后卡住检测={self.get_colliding_recovered_parts(game_world)}")

            fixed = self.resolve_recovery_stuck_loop(game_world, max_attempts=3)

            self.debug_print(f"腿回收后的对称纠偏结果 fixed={fixed}")
            self.debug_print(f"纠偏后位置=({self.x:.2f}, {self.y:.2f})")
            self.debug_print(f"纠偏后卡住检测={self.get_colliding_recovered_parts(game_world)}")

            if not fixed and self.check_foot_collision_after_recovery(self.y, game_world):
                self.debug_print("对称纠偏失败，进入 adjust_position_after_leg_recovery")
                self.adjust_position_after_leg_recovery(game_world)

        self.waiting_leg_recovery = False
        return recovered

    def perform_leg_recovery_jump(self, game_world):
        """执行腿部回收时的小跳跃"""
        small_jump_power = self.jump_power * 0.5

        collision_result = self.check_vertical_collision(self.y - 1, game_world, True)
        if collision_result == "up":
            return False

        self.is_jumping = True
        self.on_ground = False
        self.vertical_velocity = -small_jump_power
        self.jump_cooldown = 5

        return True

    def adjust_position_after_leg_recovery(self, game_world):
        """腿部回收后调整位置避免碰撞"""
        self.debug_print("=== 进入 adjust_position_after_leg_recovery ===")
        adjustment_made = False

        for adjust in range(1, 6):
            test_y = self.y - adjust
            result = self.check_foot_collision_after_recovery(test_y, game_world)
            self.debug_print(f"尝试向上调整 {adjust} 格 -> test_y={test_y:.2f}, 是否碰脚={result}")

            if not result:
                self.y = test_y
                self.update_position(self.x, self.y)
                adjustment_made = True
                self.debug_print(f"找到安全位置，调整后=({self.x:.2f},{self.y:.2f})")
                break

        if not adjustment_made:
            self.debug_print("没找到安全位置，尝试执行小跳")
            self.perform_leg_recovery_jump(game_world)

    def recover_all_parts(self, game_world):
        """回收所有身体部位：手和头立即回收，腿先小跳到最高点再回收"""
        self.debug_print("=== 调用 recover_all_parts ===")
        self.debug_print(f"回收前位置=({self.x:.2f}, {self.y:.2f})")
        self.debug_print(f"当前分离状态={self.parts_separated}")

        if self.r_cooldown > 0:
            self.debug_print(f"recover_all_parts: r_cooldown={self.r_cooldown}，不能回收")
            return False

        recovered = False

        if self.parts_separated["left_hand"]:
            self.debug_print("回收左手")
            self.parts_separated["left_hand"] = False
            self.set_bullet_active("hand", "left", False)
            self.body_parts["left_hand"].visible = True
            self.body_parts["left_hand"].color = GREEN if self.selected_part == "hand" else WHITE
            recovered = True

        if self.parts_separated["right_hand"]:
            self.debug_print("回收右手")
            self.parts_separated["right_hand"] = False
            self.set_bullet_active("hand", "right", False)
            self.body_parts["right_hand"].visible = True
            self.body_parts["right_hand"].color = GREEN if self.selected_part == "hand" else WHITE
            recovered = True

        if self.parts_separated["head"]:
            self.debug_print("回收头")
            self.parts_separated["head"] = False
            self.set_bullet_active("head", None, False)
            self.body_parts["head"].visible = True
            self.body_parts["head"].color = GREEN if self.selected_part == "head" else WHITE
            recovered = True

        leg_recovery_started = False
        if self.parts_separated["left_leg"] or self.parts_separated["right_leg"]:
            self.debug_print("尝试启动腿部延迟回收")
            leg_recovery_started = self.start_leg_recovery_jump(game_world)
            self.debug_print(f"腿部延迟回收是否启动成功: {leg_recovery_started}")
            if leg_recovery_started:
                recovered = True

        if recovered and not leg_recovery_started:
            self.debug_print("只回收了手/头，设置回收冷却")
            self.r_cooldown = 20
            self.is_airborne_without_legs = False
            self.airborne_movement_allowed = False

        if recovered:
            self.update_position(self.x, self.y)
            self.debug_print(f"recover_all_parts: 更新位置后=({self.x:.2f}, {self.y:.2f})")
            self.debug_print(f"recover_all_parts: 当前卡住部位={self.get_colliding_recovered_parts(game_world)}")

            fixed = self.resolve_recovery_stuck_loop(game_world, max_attempts=3)

            self.debug_print(f"recover_all_parts: 对称纠偏结果 fixed={fixed}")
            self.debug_print(f"recover_all_parts: 纠偏后位置=({self.x:.2f}, {self.y:.2f})")
            self.debug_print(f"recover_all_parts: 纠偏后卡住部位={self.get_colliding_recovered_parts(game_world)}")

            if not fixed:
                colliding_parts = self.get_colliding_recovered_parts(game_world)
                if "left_leg" in colliding_parts or "right_leg" in colliding_parts:
                    self.debug_print("recover_all_parts: 腿仍卡住，进入 adjust_position_after_leg_recovery")
                    self.adjust_position_after_leg_recovery(game_world)

        return recovered

    def can_move(self):
        """检查是否可以移动"""
        if self.has_legs_separated():
            if not self.on_ground and self.airborne_movement_allowed:
                return True
            return False
        return True

    def move(self, dx, dy, game_world):
        """移动玩家 - 只计算目标位置，不实际移动"""
        if self.check_leg_auto_recover(game_world):
            self.start_leg_recovery_jump(game_world)

        if not self.can_move():
            return False

        new_x = self.x + dx
        new_y = self.y + dy

        min_x = 1
        max_x = (game_world.width - 2)
        min_y = 2
        max_y = (game_world.height - 2)

        new_x = max(min_x, min(new_x, max_x))
        new_y = max(min_y, min(new_y, max_y))

        self.target_x = new_x
        self.target_y = new_y
        return True

    def jump(self, game_world):
        """普通跳跃"""
        if not self.can_move() or not self.is_jumping and self.on_ground and self.jump_cooldown <= 0:
            self.is_jumping = True
            self.on_ground = False
            self.vertical_velocity = -self.jump_power
            self.jump_cooldown = 10
            return True
        return False

    def apply_gravity(self, game_world):
        """应用重力 - 只计算目标位置，不实际移动"""
        if self.fall_check_timer > 0:
            self.fall_check_timer -= 1

        legs_separated = self.has_legs_separated()

        if self.on_ground and self.fall_check_timer <= 0 and not legs_separated:
            if self.check_below_empty(game_world):
                self.on_ground = False
                self.is_jumping = False
                self.vertical_velocity = 0
            self.fall_check_timer = self.fall_check_interval

        if not self.on_ground:
            self.vertical_velocity += self.gravity
            target_y = self.y + self.vertical_velocity

            min_y = 2
            max_y = (game_world.height - 2)
            target_y = max(min_y, min(target_y, max_y))

            if target_y != self.y:
                self.target_y = target_y

        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1

    def check_endpoint_collision(self, game_world):
        """检查是否到达终点"""
        for obj in game_world.get_scene_objects():
            if hasattr(obj, 'char') and obj.char == "终" and isinstance(obj, EndPoint):
                for part_name, part in self.body_parts.items():
                    if part.visible and part.collides_with(obj):
                        return True
        return False

    def update_move(self, game_world=None):
        if game_world is None:
            return False

        target_x = self.target_x if self.target_x is not None else self.x
        target_y = self.target_y if self.target_y is not None else self.y

        dx = target_x - self.x
        dy = target_y - self.y

        if dx == 0 and dy == 0:
            return False

        max_dist = max(abs(dx), abs(dy))
        step_size = 0.1
        steps = max(1, int(max_dist / step_size))

        step_dx = dx / steps
        step_dy = dy / steps

        moved = False
        current_x = self.x
        current_y = self.y

        for _ in range(steps):
            next_x = current_x + step_dx
            next_y = current_y + step_dy

            if self.check_step_collision(next_x, current_y, 1 if step_dx > 0 else -1 if step_dx < 0 else 0, 0, game_world) is None:
                current_x = next_x

            collision_result = self.check_step_collision(current_x, next_y, 0, 1 if step_dy > 0 else -1 if step_dy < 0 else 0, game_world)
            if collision_result is None:
                current_y = next_y
            else:
                if step_dy > 0 and collision_result == "top":
                    self.on_ground = True
                    self.vertical_velocity = 0
                    self.is_jumping = False
                elif step_dy < 0 and collision_result == "bottom":
                    self.vertical_velocity = 0
                    self.airborne_movement_allowed = False
                    self.is_jumping = False

            moved = True

        if moved:
            self.x = current_x
            self.y = current_y
            self.update_position(self.x, self.y)

        self.target_x = None
        self.target_y = None
        return moved

    def move_horizontal_stepwise(self, dx, game_world):
        """连续水平移动，但沿路径做小步长碰撞检测"""
        if dx == 0:
            return False

        moved = False
        direction = 1 if dx > 0 else -1

        step_size = 0.1
        step = step_size * direction

        current_x = self.x
        target_x = self.x + dx

        while abs(target_x - current_x) > step_size:
            next_x = current_x + step
            collision_result = self.check_step_collision(next_x, self.y, direction, 0, game_world)

            if collision_result is not None:
                break

            current_x = next_x
            moved = True

        if abs(target_x - current_x) > 1e-6:
            collision_result = self.check_step_collision(target_x, self.y, direction, 0, game_world)

            if collision_result is None:
                current_x = target_x
                moved = True

        if moved:
            self.x = current_x
            self.update_position(self.x, self.y)

        return moved

    def move_vertical_stepwise(self, dy, game_world):
        """连续垂直移动，但沿路径做小步长碰撞检测"""
        if dy == 0:
            return False

        moved = False
        direction = 1 if dy > 0 else -1

        step_size = 0.1
        step = step_size * direction

        current_y = self.y
        target_y = self.y + dy

        while abs(target_y - current_y) > step_size:
            next_y = current_y + step
            collision_result = self.check_step_collision(self.x, next_y, 0, direction, game_world)

            if collision_result is not None:
                if collision_result == "top":
                    self.on_ground = True
                    self.vertical_velocity = 0
                    self.is_jumping = False
                elif collision_result == "bottom":
                    self.vertical_velocity = 0
                    self.airborne_movement_allowed = False
                    self.is_jumping = False
                break

            current_y = next_y
            moved = True

        if abs(target_y - current_y) > 1e-6:
            collision_result = self.check_step_collision(self.x, target_y, 0, direction, game_world)

            if collision_result is None:
                current_y = target_y
                moved = True
            else:
                if collision_result == "top":
                    self.on_ground = True
                    self.vertical_velocity = 0
                    self.is_jumping = False
                elif collision_result == "bottom":
                    self.vertical_velocity = 0
                    self.airborne_movement_allowed = False
                    self.is_jumping = False

        if moved:
            self.y = current_y
            self.update_position(self.x, self.y)

        return moved

    def get_collision_parts_for_horizontal(self):
        parts = []
        for name, part in self.body_parts.items():
            if part.visible and not self.parts_separated.get(name, False):
                parts.append(name)
        return parts

    def get_collision_parts_for_upward(self):
        parts = []
        for name in ["head", "shang", "left_hand", "right_hand", "yang"]:
            if name in self.body_parts:
                part = self.body_parts[name]
                if part.visible and not self.parts_separated.get(name, False):
                    parts.append(name)
        return parts

    def get_support_parts(self):
        """返回当前负责落地的部位：有腿时腿着地，无腿时鞅着地"""
        parts = []

        if not self.parts_separated["left_leg"] and self.body_parts["left_leg"].visible:
            parts.append("left_leg")
        if not self.parts_separated["right_leg"] and self.body_parts["right_leg"].visible:
            parts.append("right_leg")

        if parts:
            return parts

        if not self.parts_separated.get("yang", False) and self.body_parts["yang"].visible:
            return ["yang"]

        return []

    def get_horizontal_collision_parts(self):
        """水平方向碰撞：所有当前存在的部位都参与"""
        parts = []
        for name, part in self.body_parts.items():
            if part.visible and not self.parts_separated.get(name, False):
                parts.append(name)
        return parts

    def get_upward_collision_parts(self):
        """向上碰撞：所有当前存在的部位都可参与"""
        parts = []
        for name, part in self.body_parts.items():
            if part.visible and not self.parts_separated.get(name, False):
                parts.append(name)
        return parts
    def get_part_test_position(self, name, test_x, test_y):
        """获取某个部位在玩家中心位于(test_x, test_y)时的位置"""
        part = self.body_parts[name]
        offset_x = part.x - self.x
        offset_y = part.y - self.y

        test_part_x = test_x + offset_x
        test_part_y = test_y + offset_y

        return test_part_x, test_part_y, offset_x, offset_y

    def check_horizontal_step_collision(self, test_x, test_y, dx, game_world):
        """检测左右方向碰撞：先左右，保留原有 +1 逻辑"""
        if dx == 0:
            return None

        check_parts = self.get_horizontal_collision_parts()

        self.debug_print(
            f"check_horizontal_step_collision: test=({test_x:.2f},{test_y:.2f}) dx={dx} 检测部位={check_parts}"
        )

        for name in check_parts:
            part = self.body_parts[name]

            if not part.visible or self.parts_separated.get(name, False):
                self.debug_print(f"check_horizontal_step_collision: 跳过 {name}")
                continue

            test_part_x, test_part_y, offset_x, offset_y = self.get_part_test_position(name, test_x, test_y)

            raw_x_int = int(test_part_x)
            raw_y_int = int(test_part_y)

            # 保留你原先左右检测的逻辑
            if dx > 0:
                x_bias = 1
                collision_side = "left"
            else:
                x_bias = 0
                collision_side = "right"

            y_bias = 1

            part_x_int = int(test_part_x) + x_bias
            part_y_int = int(test_part_y) + y_bias

            self.debug_print(
                f"check_horizontal_step_collision: 部位={name} "
                f"部位测试坐标=({test_part_x:.2f},{test_part_y:.2f}) "
                f"raw格=({raw_x_int},{raw_y_int}) "
                f"offset_x={offset_x:.2f} offset_y={offset_y:.2f} "
                f"bias=({x_bias},{y_bias}) "
                f"检测格=({part_x_int},{part_y_int})"
            )

            if 0 <= part_x_int < game_world.width and 0 <= part_y_int < game_world.height:
                if game_world.collision_grid[part_x_int][part_y_int] == 1:
                    self.debug_print(
                        f"check_horizontal_step_collision: 部位 {name} 撞上格子 ({part_x_int},{part_y_int})"
                    )
                    return collision_side
            else:
                self.debug_print(
                    f"check_horizontal_step_collision: 部位 {name} 检测越界 ({part_x_int},{part_y_int})"
                )

        return None

    def check_vertical_step_collision(self, test_x, test_y, dy, game_world):
        """检测上下方向碰撞：先左右后上下中的‘上下’，保留原有 +1 逻辑"""
        if dy == 0:
            return None

        if dy > 0:
            check_parts = self.get_support_parts()
        else:
            check_parts = self.get_upward_collision_parts()

        self.debug_print(
            f"check_vertical_step_collision: test=({test_x:.2f},{test_y:.2f}) dy={dy} 检测部位={check_parts}"
        )

        for name in check_parts:
            part = self.body_parts[name]

            if not part.visible or self.parts_separated.get(name, False):
                self.debug_print(f"check_vertical_step_collision: 跳过 {name}")
                continue

            test_part_x, test_part_y, offset_x, offset_y = self.get_part_test_position(name, test_x, test_y)

            raw_x_int = int(test_part_x)
            raw_y_int = int(test_part_y)

            # 保留你原来的垂直检测逻辑
            if dy > 0:
                y_bias = 1
                collision_side = "top"
            else:
                y_bias = 0
                collision_side = "bottom"

            if offset_x < 0:
                x_bias = 0
            elif offset_x > 0:
                x_bias = 1
            else:
                x_bias = 0

            part_x_int = int(test_part_x) + x_bias
            part_y_int = int(test_part_y) + y_bias

            self.debug_print(
                f"check_vertical_step_collision: 部位={name} "
                f"部位测试坐标=({test_part_x:.2f},{test_part_y:.2f}) "
                f"raw格=({raw_x_int},{raw_y_int}) "
                f"offset_x={offset_x:.2f} offset_y={offset_y:.2f} "
                f"bias=({x_bias},{y_bias}) "
                f"检测格=({part_x_int},{part_y_int})"
            )

            if 0 <= part_x_int < game_world.width and 0 <= part_y_int < game_world.height:
                if game_world.collision_grid[part_x_int][part_y_int] == 1:
                    self.debug_print(
                        f"check_vertical_step_collision: 部位 {name} 撞上格子 ({part_x_int},{part_y_int})"
                    )
                    return collision_side
            else:
                self.debug_print(
                    f"check_vertical_step_collision: 部位 {name} 检测越界 ({part_x_int},{part_y_int})"
                )

        return None

    def check_step_collision(self, test_x, test_y, dx, dy, game_world):
        """检查从当前位置到测试位置这一步是否会碰撞
        先检测左右碰撞，再检测上下碰撞
        """
        self.debug_print(
            f"check_step_collision: test=({test_x:.2f},{test_y:.2f}) dx={dx} dy={dy} -> 先水平后垂直"
        )

        horizontal_result = self.check_horizontal_step_collision(test_x, test_y, dx, game_world)
        if horizontal_result is not None:
            return horizontal_result

        vertical_result = self.check_vertical_step_collision(test_x, test_y, dy, game_world)
        if vertical_result is not None:
            return vertical_result

        return None

    def update(self, game_world=None):
        """更新玩家状态"""
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.q_cooldown > 0:
            self.q_cooldown -= 1
        if self.j_cooldown > 0:
            self.j_cooldown -= 1
        if self.r_cooldown > 0:
            self.r_cooldown -= 1
        if self.big_jump_timer > 0:
            self.big_jump_timer -= 1

        if game_world:
            self.apply_gravity(game_world)
        self.update_move(game_world)

        if game_world and self.waiting_leg_recovery:
            if self.vertical_velocity >= 0:
                self.finish_leg_recovery(game_world)

        for part_name, is_active in self.active_bullets.items():
            if part_name == "hand_left":
                self.body_parts["left_hand"].visible = not is_active
            elif part_name == "hand_right":
                self.body_parts["right_hand"].visible = not is_active
            elif part_name == "leg_left":
                self.body_parts["left_leg"].visible = not is_active
            elif part_name == "leg_right":
                self.body_parts["right_leg"].visible = not is_active
            elif part_name == "head":
                self.body_parts["head"].visible = not is_active

    def can_attack(self, bullet_type, side=None):
        """检查是否可以发射指定部位的子弹"""
        if bullet_type == "hand":
            if side == "left":
                return not self.active_bullets["hand_left"] and not self.parts_separated["left_hand"]
            elif side == "right":
                return not self.active_bullets["hand_right"] and not self.parts_separated["right_hand"]
        elif bullet_type == "leg":
            if side == "left":
                return not self.active_bullets["leg_left"] and not self.parts_separated["left_leg"]
            elif side == "right":
                return not self.active_bullets["leg_right"] and not self.parts_separated["right_leg"]
        elif bullet_type == "head":
            return not self.active_bullets["head"] and not self.parts_separated["head"]
        return False

    def set_bullet_active(self, bullet_type, side, active):
        """设置子弹激活状态"""
        if bullet_type == "hand":
            if side == "left":
                self.active_bullets["hand_left"] = active
            elif side == "right":
                self.active_bullets["hand_right"] = active
        elif bullet_type == "leg":
            if side == "left":
                self.active_bullets["leg_left"] = active
            elif side == "right":
                self.active_bullets["leg_right"] = active
        elif bullet_type == "head":
            self.active_bullets["head"] = active

    def attack(self, bullets, game_world):
        """兼容旧的攻击方法"""
        return False

    def recover_part(self, bullet_type, side=None):
        """回收身体部位 - 子弹击中目标时调用"""
        if bullet_type == "hand":
            if side == "left":
                self.parts_separated["left_hand"] = False
                self.set_bullet_active("hand", "left", False)
                self.body_parts["left_hand"].visible = True
                if self.selected_part == "hand":
                    self.body_parts["left_hand"].color = GREEN
                else:
                    self.body_parts["left_hand"].color = WHITE
            elif side == "right":
                self.parts_separated["right_hand"] = False
                self.set_bullet_active("hand", "right", False)
                self.body_parts["right_hand"].visible = True
                if self.selected_part == "hand":
                    self.body_parts["right_hand"].color = GREEN
                else:
                    self.body_parts["right_hand"].color = WHITE
        elif bullet_type == "leg":
            if side == "left":
                self.parts_separated["left_leg"] = False
                self.set_bullet_active("leg", "left", False)
                self.body_parts["left_leg"].visible = True
                if self.selected_part == "leg":
                    self.body_parts["left_leg"].color = GREEN
                else:
                    self.body_parts["left_leg"].color = WHITE
            elif side == "right":
                self.parts_separated["right_leg"] = False
                self.set_bullet_active("leg", "right", False)
                self.body_parts["right_leg"].visible = True
                if self.selected_part == "leg":
                    self.body_parts["right_leg"].color = GREEN
                else:
                    self.body_parts["right_leg"].color = WHITE
        elif bullet_type == "head":
            self.parts_separated["head"] = False
            self.set_bullet_active("head", None, False)
            self.body_parts["head"].visible = True
            if self.selected_part == "head":
                self.body_parts["head"].color = GREEN
            else:
                self.body_parts["head"].color = WHITE

    def gain_exp(self, amount):
        """获得经验值"""
        self.exp += amount
        if self.exp >= self.exp_to_next_level:
            self.level_up()

    def level_up(self):
        """升级"""
        self.level += 1
        self.exp = 0
        self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
        self.max_health += 2
        self.health = self.max_health

        if self.level == 2 and "leg" not in self.unlocked_attacks:
            self.unlocked_attacks.append("leg")
        elif self.level >= 3 and "head" not in self.unlocked_attacks:
            self.unlocked_attacks.append("head")

        if self.level == 2 and "leg" not in self.available_parts:
            self.available_parts.append("leg")
        elif self.level >= 3 and "head" not in self.available_parts:
            self.available_parts.append("head")

    def get_selected_part_info(self):
        """获取当前选中部位的信息"""
        if self.selected_part == "hand":
            return "手（水平发射）"
        elif self.selected_part == "head":
            return "头（垂直发射）"
        elif self.selected_part == "leg":
            return "腿（强力跳跃）"
        return "未知"

    def get_separated_parts_info(self):
        """获取分离部位的信息"""
        separated = []
        if self.parts_separated["left_hand"]:
            separated.append("左手")
        if self.parts_separated["right_hand"]:
            separated.append("右手")
        if self.parts_separated["head"]:
            separated.append("头")
        if self.parts_separated["left_leg"]:
            separated.append("左腿")
        if self.parts_separated["right_leg"]:
            separated.append("右腿")
        return separated

    def draw(self, screen, font):
        """绘制玩家"""
        if self.parts_separated["left_leg"] and self.left_leg_original_pos:
            left_leg = GameObject(self.left_leg_original_pos[0], self.left_leg_original_pos[1], "腿", WHITE)
            left_leg.draw(screen, font)

        if self.parts_separated["right_leg"] and self.right_leg_original_pos:
            right_leg = GameObject(self.right_leg_original_pos[0], self.right_leg_original_pos[1], "腿", WHITE)
            right_leg.draw(screen, font)

        for part in self.body_parts.values():
            part.draw(screen, font)

        level_font = pygame.font.SysFont(None, 20)
        level_text = level_font.render(f"Lv.{self.level}", True, CYAN)
        screen.blit(level_text, (self.x * GRID_SIZE, (self.y - 2) * GRID_SIZE - 20))