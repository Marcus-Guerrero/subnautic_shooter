import pygame
from sys import exit
from random import randint
from collections import deque

#Game status
PLAYING = "playing"
PAUSED = "paused"
SCOREBOARD = "scoreboard"
MENU = "menu"

#Game mode
SINGLEPLAYER = "singleplayer"
MULTIPLAYER = "multiplayer"

#Game Configurations
SINGLEPLAYER_CONFIG = {
    "timer": False,
    "rounds": False,
    "spawn_interval": 5000,
}
MULTIPLAYER_CONFIG = {
    "timer": True,
    "rounds": True,
    "round_time": 180,
}

#Scoreboard overlay
SCOREBOARD_POPUP = "scoreboard_popup"

#World Boundaries
WORLD_LEFT = -1824
WORLD_RIGHT = 1824
WORLD_TOP = -1600
WORLD_BOTTOM = 1600

#Detection Range of enemies
DETECTION_RANGE = 350
LOSE_INTEREST_RANGE = 450

#RESPAWN RADIUS
RESPAWN_SAFE_RADIUS = 350

#Enemy Types
ENEMY_TYPES = {
    "fly": {
        "hp": 2,
        "xp": 20,
        "speed": (1, 3),
        "image": "graphics/Fly1.png"
    },
    "brute": {
        "hp": 6,
        "xp": 60,
        "speed": (1, 2),
        "image": "graphics/Fly1.png"
    },
    "scout": {
        "hp": 1,
        "xp": 15,
        "speed": (3, 5),
        "image": "graphics/Fly1.png"
    },
    "tank": {
        "hp": 10,
        "xp": 120,
        "speed": (1, 1),
        "image": "graphics/Fly1.png"
    },
    "elite": {
        "hp": 4,
        "xp": 45,
        "speed": (2, 4),
        "image": "graphics/Fly1.png"
    }
    
}

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group, bullet_group):
        super().__init__(group)

        self.game = None

        #Character rendering
        self.image = pygame.image.load('graphics/player.png').convert_alpha()
        self.rect = self.image.get_rect(center = pos)
        self.direction = pygame.math.Vector2()
        self.speed = 5

        #Health System
        self.max_health = 5
        self.health = self.max_health
        self.last_hit_time = 0
        self.hit_cooldown = 1000

        #Shooting System
        self.bullet_group = bullet_group
        self.shoot_cooldown = 300
        self.last_shot = 0

        #Power Core
        self.max_power = 100
        self.power = self.max_power
        self.power_regen = 15
        self.boost_drain = 30
        self.shoot_cost = 20

        #Speed value
        self.normal_speed = 5
        self.boost_speed = 9

        #Level Up System
        self.level = 1
        self.max_level = 5
        self.xp = 0
        

        #Damage Scaling
        self.base_damage = 1
        self.damage = self.base_damage

    def player_movement(self):
        keys = pygame.key.get_pressed()

        #Direction
        self.direction.x = keys[pygame.K_d] - keys[pygame.K_a]
        self.direction.y = keys[pygame.K_s] - keys[pygame.K_w]

        #Diagonal movement
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

        #Boosting
        if keys[pygame.K_LSHIFT] and self.power > 0:
            self.speed = self.boost_speed
            self.power -= self.boost_drain * (1/60)
        else:
            self.speed = self.normal_speed

    def regenerate_power (self):
        self.power += self.power_regen * (1/60)
        self.power = min(self.power, self.max_power)
    
    def take_damage(self):
        current = pygame.time.get_ticks()
        if current - self.last_hit_time > self.hit_cooldown:
            self.health -= 1
            self.last_hit_time = current
            print (f"Player health: {self.health}")

    def player_shooting (self, camere_offset):
        current_time = pygame.time.get_ticks()

        if current_time - self.last_shot >= self.shoot_cooldown:
            if self.power < self.shoot_cost:
                return
            
            #World position of mouse
            mouse_screen = pygame.mouse.get_pos()
            mouse_world = pygame.math.Vector2(mouse_screen) + camere_offset
            player_pos = pygame.math.Vector2(self.rect.center)
            direction = mouse_world - player_pos

            if direction.length() != 0:
                Bullet(self.rect.center, direction, self.bullet_group)
                self.last_shot = current_time
                self.power -= self.shoot_cost
    
    def xp_needed (self):
        base = 50
        growth = 1.5
        return int(base * (self.level ** growth))
    
    def add_xp (self, amount):
        if self.level >= self.max_level:
            return
        
        self.xp += amount

        if self.xp >= self.xp_needed() and self.level < self.max_level:
            self.xp -= self.xp_needed()
            self.level_up()
    
    def level_up(self):
        self.level += 1
        self.damage = self.base_damage + self.level

        print(f"LEVEL UP! Level {self.level}, Damage {self.damage}")

        if self.level == self.max_level:
            print("MAX LEVEL! One-hit kills unlocked.")

    def update (self):
        self.player_movement()
        self.rect.center += (self.direction * self.speed)
        self.regenerate_power()

class Obstacle (pygame.sprite.Sprite):
    def __init__(self, pos, group, player, enemy_type = "fly"):
        super().__init__(group)

        #Dictionary of different enemy types
        data = ENEMY_TYPES[enemy_type]

        #Loading enemy image
        self.image = pygame.image.load(data["image"]).convert_alpha()
        self.base_image = self.image.copy()
        self.rect = self.image.get_rect(center= pos)
        self.alpha = 255
        
        self.player = player
        self.enemy_type = enemy_type
        self.xp_reward = data["xp"]

        #Health System
        self.max_health = max(1, data["hp"] + player.level // 2)
        self.health = self.max_health

        #Basic Random Movement
        self.speed = randint (*data["speed"])
        self.direction = pygame.math.Vector2(
            randint(-100, 100),
            randint (-100, 100)
        )

        if self.direction.length() != 0:
            self.direction = self.direction.normalize()

        #Current AI state
        self.state = "wander"
        self.change_dir_time = pygame.time.get_ticks()
    
    def wander(self):
        #Random movement
        if pygame.time.get_ticks() - self.change_dir_time > 2000:
            self.direction = pygame.math.Vector2(
                randint(-100, 100),
                randint(-100, 100)
            )
            if self.direction.length() != 0:
                self.direction = self.direction.normalize()
            self.change_dir_time = pygame.time.get_ticks()
        
        self.rect.center += self.direction * self.speed
    
    def chase(self):
        player_pos = pygame.math.Vector2(self.player.rect.center)
        enemy_pos = pygame.math.Vector2(self.rect.center)

        direction = player_pos - enemy_pos
        if direction.length() != 0:
            direction = direction.normalize()
        
        self.rect.center += direction * (self.speed + 1)

    def take_damage (self, amount = 1):
        self.health -= amount
        if self.health <= 0:
            self.kill()
            return True
        return False

    def draw_health_bar (self, surface, offset):
        if self.alpha <=40:
            return
        
        bar_width = 30
        bar_height = 5
        ratio = self.health / self.max_health

        #Position above enemy
        bar_x = self.rect.centerx - bar_width // 2 - offset.x
        bar_y = self.rect.top - 10 - offset.y

        #Background
        pygame.draw.rect(
            surface,
            (80, 80, 80),
            (bar_x, bar_y, bar_width, bar_height)
        )

        #Health
        pygame.draw.rect(
            surface,
            (200, 50, 50),
            (bar_x, bar_y, bar_width * ratio, bar_height)
        )
    
    def update_visibility (self, player, fog_radius, visible_radius, sonar_active = False):
        distance = pygame.math.Vector2(self.rect.center).distance_to(player.rect.center)
        
        #Override sonar
        if sonar_active:
            self.alpha = 255
            self.image = self.base_image.copy()
            self.image.set_alpha (self.alpha)
            return

        if distance <= visible_radius:
            self.alpha = 255
        elif distance >= fog_radius:
            self.alpha = 0
        else:
            ratio = 1 - (distance - visible_radius) / (fog_radius - visible_radius)
            self.alpha = int(255 * ratio)
        
        self.image = self.base_image.copy()
        self.image.set_alpha(self.alpha)

    def update(self):
        self.player = self.player.game.player
        
        #Kill broken enemies
        if self.health <= 0:
            self.kill()
            return
        
        #Move toward player
        player_pos = pygame.math.Vector2(self.player.rect.center)
        enemy_pos = pygame.math.Vector2(self.rect.center)
        distance = player_pos.distance_to(enemy_pos)

        #State transition
        if self.state == "wander" and distance <= DETECTION_RANGE:
            self.state = "chase"
        elif self.state == "chase" and distance >= LOSE_INTEREST_RANGE:
            self.state = "wander"
        
        #Grace period
        if not self.player.game:
            self.wander()
            return
        
        if pygame.time.get_ticks() - self.player.game.last_respawn_time < self.player.game.spawn_protection_time:
            self.wander()
            return
        
        #Executing behavior
        if self.state == "wander":
            self.wander()
        elif self.state == "chase":
            self.chase()

        #keeping enemies inside the world
        self.rect.centerx = max(WORLD_LEFT, min(self.rect.centerx, WORLD_RIGHT))
        self.rect.centery = max(WORLD_TOP, min(self.rect.centery, WORLD_BOTTOM))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction, group):
        super().__init__(group)
        self.image = pygame.image.load("graphics/bullet.png").convert_alpha()
        self.rect = self.image.get_rect(center = pos)
        self.direction = direction.normalize() #if direction.length() != 0 else direction
        self.speed = 12
    
    def update(self):
        self.rect.center += self.direction * self.speed

        #Removing bullets
        if abs(self.rect.x) > 4000 or abs(self.rect.y) >4000:
            self.kill()

class PortalNode:
    def __init__ (self, position):
        self.position = pygame.math.Vector2(position)
        self.next = None
        self.prev = None

class Portal (pygame.sprite.Sprite):
    def __init__ (self, node, group):
        super().__init__(group)

        #Graphics and rectangles
        self.image = pygame.image.load("graphics/Portal.png").convert_alpha()
        self.rect = self.image.get_rect(center = node.position)
        self.node = node
        self.draw_offset_y = 40

        #Cooldown system
        self.cooldown = 2000
        self.last_used = -9999
    
    def try_teleport (self, player, direction):
        current_time = pygame.time.get_ticks()

        if current_time - self.last_used < self.cooldown:
            return
        
        if direction == "next" and self.node.next:
            target = self.node.next.position
        elif direction == "prev" and self.node.prev:
            target = self.node.prev.position
        else:
            return
        
        #Teleport Player
        player.rect.center = target

        #Prevent instant trigger
        player.last_hit_time = current_time

        #Last use time
        self.last_used = current_time

class Camera (pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.surface = pygame.display.get_surface()

        #Character centered camera initialization
        self.offset = pygame.math.Vector2()
        self.cam_w = self.surface.get_size()[0] // 2
        self.cam_h = self.surface.get_size()[1] // 2

        #Ground initialization
        self.ground_surf = pygame.image.load('graphics/ground.png').convert()
        self.ground_rect = self.ground_surf.get_rect(center =(0, 0))
    
    def centered_player_cam (self, target):
        self.offset.x = target.rect.centerx - self.cam_w
        self.offset.y = target.rect.centery - self.cam_h

    def custom (self, player):

        self.centered_player_cam(player)

        offset = self.ground_rect.topleft - self.offset
        self.surface.blit(self.ground_surf, offset)

        for sprite in sorted(
            self.sprites(), 
            key = lambda sprite: sprite.rect.centery + getattr(sprite, "draw_offset_y", 0)
        ):
            offset_pos = sprite.rect.topleft - self.offset
            self.surface.blit(sprite.image, offset_pos)

class Button:
    def __init__(self, text, pos, size, font, bg_color, text_color):
        self.text = text
        self.rect = pygame.Rect(pos, size)
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color

    def draw (self, surface):
        mouse_pos = pygame.mouse.get_pos()
        color = self.bg_color

        if self.rect.collidepoint(mouse_pos):
            color = (min(color[0] + 40, 255), min(color[1] + 40, 255), min(color[2] + 40, 255))
        
        pygame.draw.rect(surface, color, self.rect, border_radius=8)

        text_surf = self.font.render(self.text, True, self.text_color)
        surface.blit(text_surf, text_surf.get_rect(center = self.rect.center))

    def is_clicked (self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button ==1
                and self.rect.collidepoint(event.pos)
        )

class Game:
    def __init__(self):
        #Initialization
        pygame.init() 
        self.screen = pygame.display.set_mode((1500, 1000))
        pygame.display.set_caption("Subnautic Shooter")
        self.fps = pygame.time.Clock()

        #Mode Tracker
        self.game_mode = None

        #General Setup
        self.camera_group = Camera()
        self.bullet_group = pygame.sprite.Group()
        self.player = Player((500, 300), self.camera_group, self.bullet_group)
        self.player.game = self
        self.obstacle_group =pygame.sprite.Group()

        #Respawn points
        self.respawn_points = deque([
            pygame.math.Vector2(0, 0),
            pygame.math.Vector2(800, -400),
            pygame.math.Vector2(-1200, 600),
            pygame.math.Vector2(1400, 1000),
            pygame.math.Vector2(-900, -1200)
        ])

        #Single Player survival tracker
        self.survival_start_time = 0
        self.survival_end_time = 0
        self.last_spawn_tick = 0

        #Respawn Delay
        self.respawn_delay = 2000
        self.death_time = None

        #Respawn protection
        self.spawn_protection_time = 1500
        self.last_respawn_time = 0

        #Creating obstacles
        self.spawn_enemies(25)
        self.running = True

        #Score board
        self.score = 0
        self.scores = []
        self.scoreboard_time = 0
        self.max_scores =5
        self.show_scoreboard = False
        self.font_b = pygame.font.Font(None, 70)
        self.font_s = pygame.font.Font (None, 36)

        #Round Timer
        self.round_time = 120
        self.round_start_time = 0
        self.remaining_time = 0

        #Number of rounds
        self.current_round = 1
        self.max_rounds = 5
        self.round_over = False
        self.final_round = False

        #XP system
        self.kills = 0

        #Fog of war
        self.fog_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        self.visibility_radius = 220
        self.fog_radius = 380

        #Sonar System
        self.sonar_active = False
        self.sonar_duration = 3.5
        self.sonar_start_time = 0
        self.sonar_cost = 40
        #Sonar cooldown
        self.sonar_cooldown = 6.0
        self.last_sonar_time = -9999

        #Current state of game status
        self.state = MENU

        #Start menu buttons
        self.play_button = Button(
            "Solo",
            (600, 420),
            (300, 60),
            self.font_s,
            (50, 150, 255),
            (255, 255, 255)
        )

        self.multi_button = Button(
            "Multiplayer",
            (600, 500),
            (300, 60),
            self.font_s,
            (120, 120, 120),
            (255, 255, 255)
        )
    
        self.quit_button = Button(
            "Quit",
            (600, 580),
            (300, 60),
            self.font_s,
            (200, 60, 60),
            (255, 255, 255)
        )

        #Pause menu buttons
        self.resume_button = Button(
            "Resume",
            (600, 450),
            (300, 60),
            self.font_s,
            (50, 180, 120),
            (255, 255, 255)
        )

        self.pause_quit_button = Button(
            "Quit to Menu",
            (600, 530),
            (300, 60),
            self.font_s,
            (200, 60, 60),
            (255, 255, 255)
        )

        #Replaying and ending round
        self.replay_button = Button(
            "Play Again",
            (600, 620),
            (300, 60),
            self.font_s,
            (50, 150, 255),
            (255, 255, 255)
        )

        self.end_button = Button(
            "End Game",
            (600, 700),
            (300, 60),
            self.font_s,
            (200, 60, 60),
            (255, 255, 255)
        )
    
    def respawn_player_next_round(self):
        #Get next respawn point
        spawn_pos = self.get_safe_respawn_point()

        #Move player
        self.player.rect.center = spawn_pos
        
        #Reset player stats
        self.player.health = self.player.max_health
        self.player.power = self.player.max_power

        #Brief invulnerability
        self.player.last_hit_time = pygame.time.get_ticks()

        #Clear old entities
        self.bullet_group.empty()
        self.obstacle_group.empty()

        #Spawn stronger enemies
        enemy_count = 25 + (self.current_round - 1)* 5
        self.spawn_enemies(enemy_count)

        #Restart timer
        self.round_start_time = pygame.time.get_ticks()

        #Respawn time
        self.last_respawn_time = pygame.time.get_ticks()

        #Reset camera instantly
        self.camera_group.centered_player_cam(self.player)

    def get_safe_respawn_point (self):
        for g in range(len(self.respawn_points)):
            point = self.respawn_points.popleft()

            safe = True
            for enemy in self.obstacle_group:
                if point.distance_to(enemy.rect.center) < RESPAWN_SAFE_RADIUS:
                    safe = False
                    break
            
            #Rotate queue
            self.respawn_points.append(point)

            if safe:
                return point
        
        return self.respawn_points[0]

    def reset_game(self):
        self.score = 0
        self.kills = 0
        self.round_over = False
        self.current_round = 1
        self.final_round = False

        if self.game_mode == SINGLEPLAYER:
            self.survival_start_time = pygame.time.get_ticks()
            self.last_spawn_tick = pygame.time.get_ticks()

        #Clearing all entities
        self.bullet_group.empty()
        self.obstacle_group.empty()
        self.camera_group.empty()

        #Recreating the character
        self.player = Player((500, 300), self.camera_group, self.bullet_group)
        self.player.game = self

        #Creating a portal
        self.create_portal()

        #Spawn enemies again
        self.spawn_enemies(25)

        #Starting timer
        self.round_start_time = pygame.time.get_ticks()
    
    def end_round(self):
        # Prevent multiple calls in the same frame
        if self.round_over:
            return
        
        # Mark round as over immediately
        self.round_over = True

        if self.game_mode == MULTIPLAYER:
            self.state = SCOREBOARD
            self.scoreboard_time = pygame.time.get_ticks()

        #Kill all enemies immediately 
        for enemy in self.obstacle_group:
            enemy.kill()
        self.obstacle_group.empty()

        # Save score for this round
        if self.game_mode == SINGLEPLAYER:
            self.scores.append({
                "kills": self.kills,
                "time": (self.survival_end_time - self.survival_start_time) // 1000
            })
        else:
            self.scores.append({
                "kills": self.kills,
                "level": self.player.level,
                "time": self.round_time - self.remaining_time
            })

        # Sort scores and keep only top max_scores
        self.scores.sort(
            key=lambda s: (s["kills"], s["level"]),
            reverse=True
        )
        self.scores = self.scores[:self.max_scores]

        # Check if this was the last round
        if self.current_round >= self.max_rounds:
            self.final_round = True
            self.state = SCOREBOARD
            self.scoreboard_time = pygame.time.get_ticks()
            return 
        else:
            # Prepare next round
            self.current_round += 1
            self.kills = 0
            self.score = 0

            # Respawn player at safe location
            self.respawn_player_next_round()

            # Reset the round_over flag so next round can end properly
            self.round_over = False

            # Set game state to PLAYING
            self.state = PLAYING

    def spawn_enemies(self, amount = 25):
        types = list(ENEMY_TYPES.keys())

        for e in range (amount):
            for attempt in range (10):
                pos = pygame.math.Vector2(
                    randint(WORLD_LEFT, WORLD_RIGHT), 
                    randint(WORLD_TOP, WORLD_BOTTOM)
                )

                #Safe distance from players
                if pos.distance_to(self.player.rect.center) < RESPAWN_SAFE_RADIUS * 1.5:
                    continue

                Obstacle(
                    pos,
                    [self.camera_group, self.obstacle_group],
                    self.player,
                    types[randint(0, len(types)- 1)]
                )
                break
    
    def portal_collision(self):
            portals = pygame.sprite.spritecollide(
                self.player, self.portal_group, False
            )

            if not portals:
                return
            
            keys = pygame.key.get_pressed()

            for portal in portals:
                if keys[pygame.K_e]:
                    portal.try_teleport(self.player, "next")
                elif keys[pygame.K_q]:
                    portal.try_teleport(self.player, "prev")

    def collision_handling(self):
        #Player collision
        if pygame.sprite.spritecollide(self.player, self.obstacle_group, False):
            self.player.take_damage()

        #Bullet collision
        for bullet in self.bullet_group:
            hit_enemies = pygame.sprite.spritecollide(bullet,self.obstacle_group, False)

            if hit_enemies:
                for enemy in hit_enemies:
                    died = enemy.take_damage(self.player.damage)

                    if died:
                        self.kills += 1
                        self.score = self.kills
                        self.player.add_xp(enemy.xp_reward)

                bullet.kill()

        #Calling portal collision 
        self.portal_collision()
        
        if self.player.health <= 0:
            if self.game_mode == SINGLEPLAYER:
                self.survival_end_time = pygame.time.get_ticks()
                self.scores.append({
                    "kills": self.kills,
                    "time": (self.survival_end_time - self.survival_start_time) // 1000
                })
                self.state = SCOREBOARD
            else:
                self.end_round()

    def handling_events(self):
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                self.running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:

                if self.state == SCOREBOARD:
                    if self.replay_button.is_clicked(event):
                        self.reset_game()
                        self.state = PLAYING
                    elif self.end_button.is_clicked(event):
                        self.running = False

                elif self.state == MENU:
                    if self.play_button.is_clicked(event):
                        self.game_mode = SINGLEPLAYER
                        self.reset_game()
                        self.survival_start_time = pygame.time.get_ticks()
                        self.state = PLAYING
                    elif self.multi_button.is_clicked(event):
                        self.game_mode = MULTIPLAYER
                        self.round_time = MULTIPLAYER_CONFIG["round_time"]
                        self.reset_game()
                        self.state = PLAYING
                    elif self.quit_button.is_clicked(event):
                        self.running = False
                
                elif self.state == PAUSED:
                    if self.resume_button.is_clicked(event):
                        self.state = PLAYING
                    elif self.pause_quit_button.is_clicked(event):
                        self.state = MENU

            if event.type == pygame.KEYDOWN:
                #Toggling Scoreboard
                if event.key == pygame.K_BACKSPACE:
                    if self.state == PLAYING:
                        self.state = SCOREBOARD_POPUP
                    elif self.state == SCOREBOARD_POPUP:
                        self.state = PLAYING

                #Toggling Pause
                if event.key == pygame.K_ESCAPE:
                    if self.state == PLAYING:
                        self.state = PAUSED
                    elif self.state == PAUSED:
                        self.state = PLAYING

                if event.key == pygame.K_RETURN and self.state == SCOREBOARD:
                    self.reset_game()
                    self.state = MENU
                
                if self.state == PLAYING and event.key == pygame.K_SPACE:
                        self.player.player_shooting(self.camera_group.offset)
                
                if self.state == PLAYING and event.key == pygame.K_f:
                    current = pygame.time.get_ticks()

                    cooldown_ready = (
                        (current - self.last_sonar_time) / 1000
                        >= self.sonar_cooldown
                    )

                    if (
                        self.player.level >=3 and
                        cooldown_ready and
                        not self.sonar_active and
                        self.player.power >= self.sonar_cost
                    ):
                        self.player.power -= self.sonar_cost
                        self.sonar_active = True
                        self.sonar_start_time = current
                        self.last_sonar_time = current

    def update(self):
        if self.state != PLAYING:
            return
        
        if self.state == PLAYING:
            if self.game_mode == SINGLEPLAYER:
                now = pygame.time.get_ticks()
                if now - self.last_spawn_tick >= SINGLEPLAYER_CONFIG["spawn_interval"]:
                    self.spawn_enemies(5 + self.current_round)
                    self.last_spawn_tick = now

            self.camera_group.update()
            self.bullet_group.update()
            self.collision_handling()

            for enemy in self.obstacle_group:
                enemy.update_visibility(
                    self.player,
                    self.fog_radius,
                    self.visibility_radius,
                    self.sonar_active
                )

            #Updating timer once
            self.remaining_time = self.update_timer()
        
        if self.sonar_active:
            elapsed = (pygame.time.get_ticks() - self.sonar_start_time) / 1000
            if elapsed >= self.sonar_duration:
                self.sonar_active = False
    
    def update_timer(self):
        if self.game_mode == SINGLEPLAYER:
            return None
        
        elapsed = (pygame.time.get_ticks() - self.round_start_time) // 1000
        remaining = max(0, self.round_time - elapsed) 

        if remaining <= 0:
            self.end_round()
        
        return remaining
    
    def draw_health_bar(self, x, y, width, height):
        ratio = self.player.health / self.player.max_health
        pygame.draw.rect(self.screen, (100, 100, 100), (x, y, width, height))
        pygame.draw.rect(
            self.screen,
            (200, 50, 50),
            (x, y, width * ratio, height)
        )

    def draw_power_core(self, x, y, width, height):
        ratio = self.player.power / self.player.max_power

        pygame.draw.rect(self.screen, (60, 60, 60), (x, y, width, height))
        pygame.draw.rect(
            self.screen,
            (50, 180, 255),
            (x, y, width * ratio, height)
        )

        label = self.font_s.render(None, True, (255, 255, 255))
        self.screen.blit(label, (x, y - 22))
    
    def draw_fog (self):
        self.fog_surface.fill((0, 0, 0, 180))

        #Player screen position
        player_screen_pos = self.player.rect.center - self.camera_group.offset

        #Create gradient visibility
        for radius in range (self.fog_radius, self.visibility_radius, -6):
            alpha = int(180 * (radius - self.visibility_radius) / (self.fog_radius - self.visibility_radius))
            alpha = max(0, min(180, alpha))

            pygame.draw.circle(
                self.fog_surface,
                (0, 0, 0, alpha),
                player_screen_pos,
                radius
            )

        #Fully clear center
        pygame.draw.circle(
            self.fog_surface,
            (0, 0, 0, 0),
            player_screen_pos,
            self.visibility_radius
        )

        self.screen.blit(self.fog_surface, (0, 0))
        
    def draw_scoreboard(self):
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title= self.font_b.render("FINAL RESULTS", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center= (750, 200)))

        y = 300
        for i, score in enumerate(self.scores):
            if self.game_mode == SINGLEPLAYER:
                text = f"{i + 1}. Kills: {score['kills']} | Time: {score['time']}s"
            else:
                text = f"{i + 1}. Kills: {score['kills']} | Level: {score['level']} | Time: {score['time']}s"
            
            line = self.font_s.render(text, True, (255, 255, 255))
            self.screen.blit(line, (500, y))
            y += 40

        self.replay_button.draw(self.screen)
        self.end_button.draw(self.screen)
    
    def draw_scoreboard_popup(self):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.font_b.render("SCOREBOARD", True, (255, 255, 255))
        self.screen.blit (title, title.get_rect(center = (750, 200)))

        if self.game_mode == SINGLEPLAYER:
            time_alive = (pygame.time.get_ticks() - self.survival_start_time) // 1000
            text = self.font_s.render(
                f"Kills: {self.kills} | Time Survived: {time_alive}s",
                True,
                (255, 255, 255)
            )
            self.screen.blit(text, text.get_rect(center = (750, 350)))
        
        elif self.game_mode == MULTIPLAYER:
            text = self.font_s.render(
                f"Round {self.current_round} | Kills: {self.kills}",
                True,
                (255, 255, 255)
            )
            self.screen.blit(text,text.get_rect(center = (750, 350)))

    def draw_paused_menu (self):
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.font_b.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(750, 350)))

        self.resume_button.draw(self.screen)
        self.pause_quit_button.draw(self.screen)
    
    def draw_start_menu(self):
        self.screen.fill((10, 10, 20))

        title = self.font_b.render("SUBNAUTIC SHOOTER", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(750, 300)))

        self.play_button.draw(self.screen)
        self.multi_button.draw(self.screen)
        self.quit_button.draw(self.screen)
    
    def create_portal (self):
        self.portal_group = pygame.sprite.Group()

        #Create nodes
        nodes = [
            PortalNode((0, 0)),
            PortalNode ((900, - 600)),
            PortalNode((-1200, 900)),
            PortalNode((1400, 1200))
        ]

        #Linked List
        for i in range(len(nodes)):
            if i > 0:
                nodes[i].prev = nodes[i - 1]
            if i < len(nodes) - 1:
                nodes[i].next = nodes[i + 1]
        
        for node in nodes:
            Portal(node, [self.camera_group, self.portal_group])
        
    def draw(self):
        if self.state == MENU:
            self.draw_start_menu()
            pygame.display.update()
            return
        
        self.screen.fill((0, 0, 0))
        self.camera_group.custom(self.player)

        for enemy in self.obstacle_group:
            enemy.draw_health_bar(self.screen, self.camera_group.offset)

        for bullet in self.bullet_group:
            offset_pos = bullet.rect.topleft - self.camera_group.offset
            self.screen.blit(bullet.image, offset_pos)
        
        if self.state == PLAYING and not self.sonar_active:
            self.draw_fog()

        #UI positioning
        ui_x = 20
        ui_y = 20
        gap = 6
        
        #For Health bar
        self.draw_health_bar(ui_x, ui_y, 200, 18)
        ui_y += 18 + gap

        #For power bar
        self.draw_power_core(ui_x, ui_y, 200, 14)
        ui_y += 14 + gap

        # XP bar
        if self.player.level < self.player.max_level:
            xp_ratio = self.player.xp / self.player.xp_needed()
        else:
            xp_ratio = 1

        pygame.draw.rect(self.screen, (80, 80, 80), (ui_x, ui_y, 200, 10))
        pygame.draw.rect(self.screen, (120, 200, 120), (ui_x, ui_y, 200 * xp_ratio, 10))
        ui_y += 10 + gap

        # Level
        level_surf = self.font_s.render(f"Level: {self.player.level}", True, (255, 255, 255))
        self.screen.blit(level_surf, (ui_x, ui_y))
        ui_y += level_surf.get_height() + gap

        # Sonar 
        current = pygame.time.get_ticks()
        time_since = (current - self.last_sonar_time) / 1000
        remaining = max(0, self.sonar_cooldown - time_since)

        if self.player.level < 3:
            sonar_text = "SONAR LOCKED (LVL 3)"
            color = (120, 120, 120)
        elif self.sonar_active:
            sonar_text = "SONAR ACTIVE"
            color = (50, 200, 255)
        elif remaining <= 0:
            sonar_text = "SONAR READY"
            color = (120, 220, 120)
        else:
            sonar_text = f"SONAR COOLDOWN: {remaining:.1f}s"
            color = (200, 200, 200)

        sonar_surf = self.font_s.render(sonar_text, True, color)
        self.screen.blit(sonar_surf, (ui_x, ui_y))
        ui_y += sonar_surf.get_height() + gap

        # Score
        score_surf = self.font_s.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_surf, (ui_x, ui_y))
        ui_y += score_surf.get_height() + gap

        # Timer
        if self.state == PLAYING and self.game_mode == MULTIPLAYER:
            timer_surf = self.font_s.render(
                f"Time: {self.remaining_time // 60:02}:{self.remaining_time % 60:02}",
                True,
                (255, 255, 255)
            )
            self.screen.blit(timer_surf, (ui_x, ui_y))
            ui_y += timer_surf.get_height() + gap

        # Round
        if self.game_mode == MULTIPLAYER:
            round_surf = self.font_s.render(
                f"Round: {self.current_round}/{self.max_rounds}",
                True,
                (255, 255, 255)
            )
            self.screen.blit(round_surf, (ui_x, ui_y))
            ui_y += round_surf.get_height() + gap
        
        if self.state == SCOREBOARD:
            self.draw_scoreboard()
        elif self.state == SCOREBOARD_POPUP:
            self.draw_scoreboard_popup()
        elif self.state == PAUSED:
            self.draw_paused_menu()

        pygame.display.update() 
    
    def run(self):
        while self.running:
            self.handling_events()
            self.update()
            self.draw()
            self.fps.tick(60)

        pygame.quit()
        exit()

if __name__ == "__main__":
    game = Game()
    game.run()