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
    
    def draw(self, screen):
        """绘制游戏世界"""
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
        self.player = ShangYang(SCREEN_WIDTH // (2 * GRID_SIZE), SCREEN_HEIGHT // (2 * GRID_SIZE))
        
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
            dx -= 1
        if keys[pygame.K_d]:  # 右
            dx += 1
        if keys[pygame.K_w]:  # 上
            dy -= 1
        if keys[pygame.K_s]:  # 下
            dy += 1
        
        if dx != 0 or dy != 0:
            if self.player.move(dx, dy, self.world):
                self.player.update_direction(dx, dy)
        
        # 按住空格键连续发射
        if keys[pygame.K_SPACE]:
            self.player.attack(self.bullets, self.world)
    
    def update(self):
        """更新游戏状态"""
        if self.state not in [GAME_STATE_PLAYING]:
            return
        
        # 更新玩家
        self.player.update()
        
        # 更新敌人
        for enemy in self.enemies:
            enemy.update(self.world)
            
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
                    # 将敌人弹开
                    enemy.x += random.choice([-2, 2])
                    enemy.y += random.choice([-2, 2])
                    enemy.update_rect()
                    self.show_message("被马撞到了！", 30)
        
        # 更新子弹
        bullets_to_remove = []
        for bullet in self.bullets:
            if not bullet.update(self.world):
                bullets_to_remove.append(bullet)
                continue
            
            # 检查子弹是否击中敌人
            enemy_hit = None
            for enemy in self.enemies:
                if bullet.rect.colliderect(enemy.rect):
                    enemy_hit = enemy
                    break
            
            if enemy_hit:
                if enemy_hit.take_damage(bullet.damage):
                    # 敌人死亡
                    self.enemies.remove(enemy_hit)
                    self.player.gain_exp(enemy_hit.exp_value)
                    self.score += 10
                    self.enemies_killed += 1
                    
                    # 显示获得经验消息
                    self.show_message(f"获得{enemy_hit.exp_value}经验值！", 30)
                    
                    # 每击败3个敌人生成一个新敌人
                    if self.enemies_killed % 3 == 0:
                        self.spawn_enemies(3)


                    # 检查是否胜利
                    if self.enemies_killed >= 20 + self.level * 5:  # 每关增加5个胜利条件
                        self.state = GAME_STATE_VICTORY
                        self.show_message("恭喜获胜！你击败了所有马！", 300)
                
                # 击中敌人后回收子弹对应的身体部位
                bullet.player.recover_part(bullet.bullet_type, bullet.side)
                bullets_to_remove.append(bullet)
        
        # 移除已消失的子弹
        for bullet in bullets_to_remove:
            if bullet in self.bullets:
                self.bullets.remove(bullet)
        
        # 更新消息显示
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