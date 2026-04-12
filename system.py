"""
游戏逻辑类
"""

import pygame
import random
from __init__ import FPS,GAME_STATE_MENU,SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, BLACK, GAME_STATE_PLAYING, GAME_STATE_GAME_OVER, GAME_STATE_VICTORY
from player import ShangYang
from enemy import Horse
from bullet import Bullet
from scene import Ground, Wall, Platform, Door, Trap,Switch  # 导入新的场景物体
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
            
    # 在GameSystem类的handle_keydown方法中修改
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
            elif event.key == pygame.K_q:
                # 切换选择部位
                if self.game_instance:
                    self.game_instance.player.select_next_part()
            elif event.key == pygame.K_j:
                # 执行当前选中动作
                if self.game_instance:
                    result = self.game_instance.player.perform_action(self.game_instance.world)
                    if result:
                        # 获取发射的子弹并添加到子弹列表
                        bullets = self.game_instance.player.get_fired_bullets()
                        for bullet in bullets:
                            self.game_instance.bullets.append(bullet)
            elif event.key == pygame.K_r:
                # 回收所有身体部位并清除所有子弹
                if self.game_instance:
                    # 回收身体部位
                    self.game_instance.player.recover_all_parts(self.game_instance.world)
                    # 清除所有子弹
                    bullets_to_clear = []
                    for bullet in self.game_instance.bullets:
                        if bullet.is_stopped:
                            bullets_to_clear.append(bullet)
                            bullet.clear()
                    
                    # 移除被清除的子弹
                    for bullet in bullets_to_clear:
                        if bullet in self.game_instance.bullets:
                            self.game_instance.bullets.remove(bullet)
            elif event.key == pygame.K_w:
                # 普通跳跃
                if self.game_instance:
                    self.game_instance.player.jump(self.game_instance.world)
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
"""
游戏逻辑类
"""

import pygame
import random
from __init__ import SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, BLACK, GAME_STATE_PLAYING, GAME_STATE_GAME_OVER, GAME_STATE_VICTORY
from player import ShangYang
from enemy import Horse
from bullet import Bullet

class GameWorld:
    """游戏世界类"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.ground_level = self.height - 2
        self.scene_objects = []
        
        # 创建底部地面
        self.create_level_1()
        self.create_ground()
    # 在GameWorld类中创建关卡时
    def create_level_1(self):
        """创建第1关"""
        # 创建红色开关
        red_switch = Switch(5, 8, 0)  # 红色开关
        self.add_scene_object(red_switch)
        
        # 创建红色门
        red_door = Door(3, 46, 0)  # 红色门
        self.add_scene_object(red_door)
        
        # 创建绿色开关
        green_switch = Switch(15, 8, 1)  # 绿色开关
        self.add_scene_object(green_switch)
        
        # 创建绿色门
        green_door = Door(3, 47, 1)  # 绿色门
        self.add_scene_object(green_door)
    def create_ground(self):
        """创建底部地面"""
        for x in range(self.width):
            ground = Ground(x, self.ground_level)
            self.scene_objects.append(ground)
    
    def add_scene_object(self, scene_object):
        """添加场景物体"""
        self.scene_objects.append(scene_object)
    
    def remove_scene_object(self, scene_object):
        """移除场景物体"""
        if scene_object in self.scene_objects:
            self.scene_objects.remove(scene_object)
    
    def get_scene_objects(self):
        """获取所有场景物体"""
        return self.scene_objects
    
    def get_ground_level(self):
        """获取地面高度"""
        return self.ground_level
    
    def draw(self, screen):
        """绘制游戏世界"""
        # 绘制场景物体
        for obj in self.scene_objects:
            obj.draw(screen, pygame.font.SysFont("simhei", 20))
        
        # 绘制背景网格线
        for x in range(0, self.width * GRID_SIZE, GRID_SIZE):
            pygame.draw.line(screen, (30, 30, 30), (x, 0), (x, self.height * GRID_SIZE), 1)
        for y in range(0, self.height * GRID_SIZE, GRID_SIZE):
            pygame.draw.line(screen, (30, 30, 30), (0, y), (self.width * GRID_SIZE, y), 1)

class TankGame:
    """游戏主类"""
    def __init__(self, level=1):
        self.level = level
        self.reset_game()
    
    def reset_game(self):
        """重置游戏"""
        # 创建游戏世界
        self.world = GameWorld(SCREEN_WIDTH // GRID_SIZE, SCREEN_HEIGHT // GRID_SIZE)
        
        # 创建玩家
        start_x = SCREEN_WIDTH // (2 * GRID_SIZE)
        start_y = self.world.ground_level - 5  # 从地面上方5格开始
        self.player = ShangYang(start_x, start_y)
        
        # 设置地面高度
        self.player.set_ground_level(self.world.get_ground_level())
        
        # 创建敌人列表
        self.enemies = []
        self.spawn_enemies(5 + self.level * 2)  # 每关增加2个敌人
        
        # 子弹列表
        self.bullets = []
        
        # 游戏状态
        self.score = 0
        self.state = GAME_STATE_PLAYING
        self.enemies_killed = 0
        
        # 游戏消息
        self.message = ""
        self.message_timer = 0
        
    # ... 其他方法保持不变 ...
    
    def spawn_enemies(self, count):
        """生成敌人"""
        for _ in range(count):
            # 在远离玩家的位置生成敌人
            while True:
                x = random.randint(5, self.world.width - 5)
                y = random.randint(5, self.world.height - 5)
                
                # 确保不生成在玩家附近
                if abs(x - self.player.x) > 10 and abs(y - self.player.y) > 10:
                    self.enemies.append(Horse(x, y))
                    break
    
    def show_message(self, message, duration=60):
        """显示消息"""
        self.message = message
        self.message_timer = duration
    
    def handle_input(self, keys):
        """处理输入"""
        if self.state not in [GAME_STATE_PLAYING]:
            return
        
        # 玩家移动
        dx, dy = 0, 0
        if keys[pygame.K_a]:  # 左
            dx -= self.player.move_speed
        if keys[pygame.K_d]:  # 右
            dx += self.player.move_speed
        # if keys[pygame.K_w]:  # 上
        #     dy -= 1
        # if keys[pygame.K_s]:  # 下
        #     dy += 1
        
        if dx != 0 or dy != 0:
            if self.player.move(dx, dy, self.world):
                self.player.update_direction(dx, dy)
        
        # 按住空格键连续发射
        if keys[pygame.K_SPACE]:
            self.player.attack(self.bullets, self.world)
        # 在TankGame的update方法中，修改子弹碰撞检测部分
    # 在TankGame的update方法中，修改子弹碰撞检测部分
    # 在TankGame的update方法中，修改子弹与开关的碰撞检测
    def update(self):
        """更新游戏状态"""
        if self.state not in [GAME_STATE_PLAYING]:
            return
        
        # 更新玩家
        self.player.update(self.world)
        
        # 更新敌人
        for enemy in self.enemies:
            enemy.update(self.world)
            
            # 检查敌人是否与场景物体碰撞
            for obj in self.world.get_scene_objects():
                if isinstance(obj, Ground) and enemy.collides_with(obj):
                    enemy.y = obj.y - 1
                    enemy.on_ground = True
                    enemy.update_rect()
                    break
                
                # 检查敌人是否与玩家身体部位碰撞
                player_hit = False
                for part_name, part in self.player.body_parts.items():
                    if part.visible and enemy.collides_with(part):
                        player_hit = True
                        break
                
                if player_hit:
                    self.player.health -= 1
                    if self.player.health <= 0:
                        self.state = GAME_STATE_GAME_OVER
                        self.show_message("游戏结束！", 300)
                    else:
                        enemy.x += random.choice([-2, 2])
                        enemy.y += random.choice([-2, 2])
                        enemy.update_rect()
                        self.show_message("被马撞到了！", 30)
        
        # 更新子弹
        bullets_to_remove = []
        for bullet in self.bullets:
            # 更新子弹
            bullet_active = bullet.update(self.world)
            
            if not bullet_active:
                bullets_to_remove.append(bullet)
                continue
            
            # 只检查没有停止的子弹
            if not bullet.is_stopped:
                # 检查子弹是否击中开关
                switch_hit = None
                for obj in self.world.get_scene_objects():
                    if isinstance(obj, Switch) and bullet.rect.colliderect(obj.rect):
                        switch_hit = obj
                        break
                
                if switch_hit:
                    # 切换开关状态
                    switch_hit.toggle(self.world)
                    state_text = "开" if switch_hit.state == "on" else "关"
                    self.show_message(f"开关变为{state_text}!", 30)
                    # 击中开关后清除子弹
                    bullets_to_remove.append(bullet)
                    bullet.clear()
                    continue
                
                # 检查子弹是否击中敌人
                enemy_hit = None
                for enemy in self.enemies:
                    if bullet.rect.colliderect(enemy.rect):
                        enemy_hit = enemy
                        break
                
                if enemy_hit:
                    if enemy_hit.take_damage(bullet.damage):
                        self.enemies.remove(enemy_hit)
                        self.player.gain_exp(enemy_hit.exp_value)
                        self.score += 10
                        self.enemies_killed += 1
                        
                        self.show_message(f"获得{enemy_hit.exp_value}经验值！", 30)
                        
                        if self.enemies_killed % 3 == 0:
                            self.spawn_enemies(3)
                    
                    # 击中敌人后清除子弹
                    bullets_to_remove.append(bullet)
                    bullet.clear()
        
        for bullet in bullets_to_remove:
            if bullet in self.bullets:
                self.bullets.remove(bullet)
        
        if self.message_timer > 0:
            self.message_timer -= 1
        else:
            self.message = ""
    def get_game_objects(self):
        """获取所有游戏对象"""
        return {
            "world": self.world,
            "player": self.player,
            "enemies": self.enemies,
            "bullets": self.bullets
        }
    
    def get_game_state(self):
        """获取游戏状态"""
        return {
            "state": self.state,
            "score": self.score,
            "level": self.level,
            "player_level": self.player.level,
            "player_exp": self.player.exp,
            "player_exp_to_next": self.player.exp_to_next_level,
            "player_health": self.player.health,
            "player_max_health": self.player.max_health,
            "enemies_killed": self.enemies_killed,
            "message": self.message,
            "player_available_parts": self.get_available_parts()
        }
    
    def get_available_parts(self):
        """获取可用部位"""
        available_parts = []
        
        # 检查哪些部位可用
        if not self.player.active_bullets["hand_left"] and "hand" in self.player.unlocked_attacks:
            available_parts.append("左手")
        if not self.player.active_bullets["hand_right"] and "hand" in self.player.unlocked_attacks:
            available_parts.append("右手")
        if not self.player.active_bullets["leg_left"] and "leg" in self.player.unlocked_attacks:
            available_parts.append("左腿")
        if not self.player.active_bullets["leg_right"] and "leg" in self.player.unlocked_attacks:
            available_parts.append("右腿")
        if not self.player.active_bullets["head"] and "head" in self.player.unlocked_attacks:
            available_parts.append("头")
        
        return available_parts