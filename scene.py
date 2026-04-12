"""
场景物体类
"""

import pygame
from __init__ import GRID_SIZE, BROWN, DARK_GREEN, RED, GRAY, DARK_YELLOW, GREEN, BLUE, YELLOW, PURPLE, CYAN, WHITE, DARK_RED, DARK_BLUE, DARK_GRAY

class SceneObject:
    """场景物体基类"""
    def __init__(self, x, y, char, color, collidable=True):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.collidable = collidable
        self.rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
    
    def update_rect(self):
        self.rect = pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
    
    def draw(self, screen, font):
        text_surface = font.render(self.char, True, self.color)
        text_rect = text_surface.get_rect(center=(self.x * GRID_SIZE + GRID_SIZE//2, 
                                                  self.y * GRID_SIZE + GRID_SIZE//2))
        screen.blit(text_surface, text_rect)
    
    def collides_with(self, other):
        return self.rect.colliderect(other.rect)


class Ground(SceneObject):
    """地面"""
    def __init__(self, x, y):
        super().__init__(x, y, "地", BROWN, True)


class Wall(SceneObject):
    """墙壁"""
    def __init__(self, x, y):
        super().__init__(x, y, "墙", DARK_GREEN, True)


class Platform(SceneObject):
    """平台"""
    def __init__(self, x, y):
        super().__init__(x, y, "台", DARK_YELLOW, False)  # 可以从下方通过

class EndPoint(SceneObject):
    """终点 - 到达后进入下一关"""
    def __init__(self, x, y):
        super().__init__(x, y, "终", GREEN, False)  # 不可碰撞，可以直接穿过
        self.color = GREEN
    
    def collides_with(self, other):
        """重写碰撞检测，返回True表示触发事件"""
        return self.rect.colliderect(other.rect)


class Door(SceneObject):
    """门 - 会同步开关的状态"""
    def __init__(self, x, y, color_code=0, initial_state="on"):
        # 颜色代码: 0=红色(默认), 1=绿色, 2=蓝色, 3=黄色, 4=紫色, 5=青色
        color_map = {
            0: RED,
            1: GREEN,
            2: BLUE,
            3: YELLOW,
            4: PURPLE,
            5: CYAN
        }
        self.color_code = color_code
        self.active = initial_state == "on"  # 门是否激活
        self.state = initial_state  # 状态："on"或"off"
        
        # 根据状态设置颜色和字符
        if self.active:
            color = color_map.get(color_code, RED)
            char = "门"
        else:
            # 关闭状态使用灰色
            color = GRAY
            char = "门"  # 仍然是"门"字符，但颜色变灰
        
        super().__init__(x, y, char, color, self.active)
    
    def set_state(self, state, game_world=None):
        """设置门的状态"""
        if self.state == state:
            return False
        
        self.state = state
        self.active = (state == "on")
        self.collidable = self.active
        
        # 颜色代码: 0=红色(默认), 1=绿色, 2=蓝色, 3=黄色, 4=紫色, 5=青色
        color_map = {
            0: RED,
            1: GREEN,
            2: BLUE,
            3: YELLOW,
            4: PURPLE,
            5: CYAN
        }
        
        if self.active:
            # 激活状态 - 对应颜色
            self.color = color_map.get(self.color_code, RED)
        else:
            # 关闭状态 - 灰色
            self.color = GRAY
        
        self.char = "门"  # 保持"门"字符不变
        
        return True
    
    def toggle(self, game_world=None):
        """切换门的状态"""
        new_state = "off" if self.state == "on" else "on"
        return self.set_state(new_state, game_world)


class Switch(SceneObject):
    """开关 - 常态是"开"，被攻击后变成"关"，可以互相转化"""
    def __init__(self, x, y, color_code=0, initial_state="on"):
        # 颜色代码: 0=红色(默认), 1=绿色, 2=蓝色, 3=黄色, 4=紫色, 5=青色
        color_map = {
            0: RED,
            1: GREEN,
            2: BLUE,
            3: YELLOW,
            4: PURPLE,
            5: CYAN
        }
        self.color_code = color_code
        self.state = initial_state  # 状态："on"或"off"
        self.switch_cooldown = 0
        
        # 根据初始状态设置
        if self.state == "on":
            char = "开"
            color = color_map.get(color_code, RED)
        else:
            char = "关"
            # 关闭状态使用灰色
            color = GRAY
        
        super().__init__(x, y, char, color, False)  # 开关本身不可碰撞
    
    def toggle(self, game_world=None):
        """切换开关状态"""
        # if self.switch_cooldown > 0:
        #     return False
        
        # 切换状态
        if self.state == "on":
            new_state = "off"
            new_char = "关"
            new_color = GRAY
        else:
            new_state = "on"
            new_char = "开"
            # 恢复对应颜色
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
        
        # 如果提供了游戏世界，更新所有相同颜色的门
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
        super().__init__(x, y, "陷", RED, True)
        self.damage = 1