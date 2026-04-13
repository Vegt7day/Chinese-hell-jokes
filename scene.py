"""
场景物体类
"""

import pygame
from __init__ import (
    GRID_SIZE,
    BROWN, DARK_GREEN, RED, GRAY, DARK_YELLOW,
    GREEN, BLUE, YELLOW, PURPLE, CYAN, DARK_GRAY,WHITE
)

class SceneObject:
    """场景物体基类"""
    def __init__(self, x, y, char, color, player_collidable=True, bullet_collidable=True):
        self.x = x
        self.y = y
        self.char = char
        self.color = color

        # 新碰撞属性
        self.player_collidable = player_collidable
        self.bullet_collidable = bullet_collidable

        # 兼容旧代码
        self.collidable = player_collidable

        self.rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)

    def update_rect(self):
        self.rect = pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)

    def draw(self, screen, font):
        text_surface = font.render(self.char, True, self.color)
        text_rect = text_surface.get_rect(
            center=(self.x * GRID_SIZE + GRID_SIZE // 2,
                    self.y * GRID_SIZE + GRID_SIZE // 2)
        )
        screen.blit(text_surface, text_rect)

    def collides_with(self, other):
        return self.rect.colliderect(other.rect)


class Ground(SceneObject):
    """地面"""
    def __init__(self, x, y):
        super().__init__(x, y, "地", BROWN, True, True)


class Wall(SceneObject):
    """墙壁"""
    def __init__(self, x, y):
        super().__init__(x, y, "墙", DARK_GREEN, True, True)


class Platform(SceneObject):
    """平台"""
    def __init__(self, x, y):
        super().__init__(x, y, "台", DARK_YELLOW, True, True)


class EndPoint(SceneObject):
    """终点 - 到达后进入下一关"""
    def __init__(self, x, y):
        super().__init__(x, y, "终", GREEN, False, False)

    def collides_with(self, other):
        """终点不阻挡，但可以触发"""
        return self.rect.colliderect(other.rect)


class Door(SceneObject):
    """门 - 会同步开关的状态"""
    def __init__(self, x, y, color_code=0, initial_state="on"):
        color_map = {
            0: RED,
            1: GREEN,
            2: BLUE,
            3: YELLOW,
            4: PURPLE,
            5: CYAN
        }

        self.color_code = color_code
        self.active = initial_state == "on"
        self.state = initial_state

        if self.active:
            color = color_map.get(color_code, RED)
            char = "门"
        else:
            color = GRAY
            char = "门"

        super().__init__(x, y, char, color, self.active, self.active)

    def set_state(self, state, game_world=None):
        """设置门的状态"""
        if self.state == state:
            return False

        self.state = state
        self.active = (state == "on")

        self.player_collidable = self.active
        self.bullet_collidable = self.active
        self.collidable = self.active  # 兼容旧代码

        color_map = {
            0: RED,
            1: GREEN,
            2: BLUE,
            3: YELLOW,
            4: PURPLE,
            5: CYAN
        }

        if self.active:
            self.color = color_map.get(self.color_code, RED)
        else:
            self.color = GRAY

        self.char = "门"
        return True

    def toggle(self, game_world=None):
        """切换门的状态"""
        new_state = "off" if self.state == "on" else "on"
        return self.set_state(new_state, game_world)


class Switch(SceneObject):
    """开关 - 常态是'开'，被攻击后变成'关'"""
    def __init__(self, x, y, color_code=0, initial_state="on"):
        color_map = {
            0: RED,
            1: GREEN,
            2: BLUE,
            3: YELLOW,
            4: PURPLE,
            5: CYAN
        }

        self.color_code = color_code
        self.state = initial_state
        self.switch_cooldown = 0

        if self.state == "on":
            char = "开"
            color = color_map.get(color_code, RED)
        else:
            char = "关"
            color = GRAY

        # 开关不阻挡玩家，也不阻挡子弹
        super().__init__(x, y, char, color, False, False)

    def toggle(self, game_world=None):
        """切换开关状态"""
        if self.state == "on":
            new_state = "off"
            new_char = "关"
            new_color = GRAY
        else:
            new_state = "on"
            new_char = "开"
            color_map = {
                0: RED,
                1: GREEN,
                2: BLUE,
                3: YELLOW,
                4: PURPLE,
                5: CYAN
            }
            new_color = color_map.get(self.color_code, RED)

        self.state = new_state
        self.char = new_char
        self.color = new_color
        self.switch_cooldown = 10

        if game_world:
            self.update_doors(game_world, new_state)

        return True

    def update_doors(self, game_world, new_state):
        """更新所有相同颜色的门的状态"""
        for obj in game_world.get_scene_objects():
            if isinstance(obj, Door) and obj.color_code == self.color_code:
                obj.set_state(new_state, game_world)

    def update(self):
        """更新开关状态"""
        if self.switch_cooldown > 0:
            self.switch_cooldown -= 1


class Trap(SceneObject):
    """陷阱"""
    def __init__(self, x, y):
        super().__init__(x, y, "火", RED, False, False)
        self.damage = 1
class Hole(SceneObject):
    """洞 - 挡玩家，不挡子弹"""
    def __init__(self, x, y):
        super().__init__(x, y, "洞",WHITE , True, False)