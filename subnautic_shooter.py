import pygame
from sys import exit
from random import randint

#Game status
PLAYING = "playing"
PAUSED = "paused"
SCOREBOARD = "scoreboard"
MENU = "menu"

#World Boundaries
WORLD_LEFT = -1824
WORLD_RIGHT = 1824
WORLD_TOP = -1600
WORLD_BOTTOM = 1600

#Detection Range of enemies
DETECTION_RANGE = 350
LOSE_INTEREST_RANGE = 450

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group, bullet_group):
        super().__init__(group)

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
        self.xp_to_next = [0, 50, 100, 150, 200, float("inf")]

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
    
    def add_xp (self, amount):
        if self.level >= self.max_level:
            return
        
        self.xp += amount

        if self.xp >= self.xp_to_next[self.level] and self.level < self.max_level:
            self.xp -= self.xp_to_next[self.level]
            self.level_up()
    
    def level_up(self):
        self.level += 1
        self.damage += 1

        print(f"LEVEL UP! Level {self.level}, Damage {self.damage}")

        if self.level == self.max_level:
            print("MAX LEVEL! One-hit kills unlocked.")

    def update (self):
        self.player_movement()
        self.rect.center += (self.direction * self.speed)
        self.regenerate_power()

class Obstacle (pygame.sprite.Sprite):
    def __init__(self, pos, group, player):
        super().__init__(group)
        self.image = pygame.image.load("graphics/Fly1.png").convert_alpha()
        self.rect = self.image.get_rect(center= pos)
        self.player = player

        #Health System
        self.max_health = 2 + player.level
        self.health = self.max_health

        #Basic Random Movement
        self.speed = randint (1, 3)
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

    def update(self):
        #Move toward player
        player_pos = pygame.math.Vector2(self.player.rect.center)
        enemy_pos = pygame.math.Vector2(self.rect.center)
        distance = player_pos.distance_to(enemy_pos)

        #State transition
        if self.state == "wander" and distance <= DETECTION_RANGE:
            self.state = "chase"
        elif self.state == "chase" and distance >= LOSE_INTEREST_RANGE:
            self.state = "wander"
        
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

        for sprite in sorted(self.sprites(), key = lambda sprite: sprite.rect.centery):
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

        #General Setup
        self.camera_group = Camera()
        self.bullet_group = pygame.sprite.Group()
        self.player = Player((500, 300), self.camera_group, self.bullet_group)
        self.obstacle_group =pygame.sprite.Group()

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

        #Number of rounds
        self.current_round = 1
        self.max_rounds = 5
        self.round_over = False
        self.final_round = False

        #XP system
        self.xp_per_enemy = 20
        self.kills = 0

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

    def reset_game(self):
        self.score = 0
        self.player.health = 5
        self.kills = 0
        self.round_over = False

        #Clearing all entities
        self.bullet_group.empty()
        self.obstacle_group.empty()
        self.camera_group.empty()

        #Recreating the character
        self.player = Player((500, 300), self.camera_group, self.bullet_group)

        #Spawn enemies again
        self.spawn_enemies(25)

        #Starting timer
        self.round_start_time = pygame.time.get_ticks()
    
    def end_round(self):
        if self.round_over:
            return
        
        self.round_over = True

        self.scores.append({
            "kills": self.kills,
            "level": self.player.level
        })
        self.scores.sort(
            key =lambda s: (s["kills"], s["level"]),
            reverse = True
        )
        self.scores = self.scores[:self.max_scores]

        if self.current_round >= self.max_rounds:
            self.final_round = True
            self.state = SCOREBOARD
            self.scoreboard_time = pygame.time.get_ticks()
        else:
            self.final_round = False
            self.current_round += 1
            self.state = SCOREBOARD

    def spawn_enemies(self, amount = 25):
        for obs in range(amount):
            random_x = randint(-1824, 1824)
            random_y = randint(-1600, 1600)
            Obstacle(
                (random_x, random_y), 
                [self.camera_group, self.obstacle_group],
                self.player
            )

    def collision_handling(self):
        #Player collision
        if pygame.sprite.spritecollide(self.player, self.obstacle_group, False):
            self.player.take_damage()

        #Bullet collision
        for bullet in self.bullet_group:
            hit_enemies = pygame.sprite.spritecollide(bullet,self.obstacle_group, False)

            if hit_enemies:
                bullet.kill()

                for enemy in hit_enemies:
                    died = enemy.take_damage(self.player.damage)

                    if died:
                        self.kills += 1
                        self.score = self.kills
                        self.player.add_xp(self.xp_per_enemy)
        
        if self.player.health <= 0:
            self.end_round()
            # self.scores.sort(reverse = True)
            # self.scores = self.scores[:self.max_scores]

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
                        self.reset_game()
                        self.state = PLAYING
                    elif self.multi_button.is_clicked(event):
                        print("Multiplayer coming soon")
                    elif self.quit_button.is_clicked(event):
                        self.running = False
                
                elif self.state == PAUSED:
                    if self.resume_button.is_clicked(event):
                        self.state = PLAYING
                    elif self.pause_quit_button.is_clicked(event):
                        self.state = MENU

            if event.type == pygame.KEYDOWN:

                #Toggling Pause
                if event.key == pygame.K_ESCAPE:
                    if self.state == PLAYING:
                        self.state = PAUSED
                    elif self.state == PAUSED:
                        self.state = PLAYING

                if self.state == PAUSED:
                    if self.resume_button.is_clicked(event):
                        self.state = PLAYING
                        self.state = PLAYING
                    elif self.pause_quit_button.is_clicked(event):
                        self.running = MENU

                if event.key == pygame.K_RETURN and self.state == SCOREBOARD:
                    self.reset_game()
                    self.state = MENU
                
                if self.state == PLAYING and event.key == pygame.K_SPACE:
                        self.player.player_shooting(self.camera_group.offset)
            

    def update(self):
        if self.state == PLAYING:
            self.camera_group.update()
            self.bullet_group.update()
            self.collision_handling()

            #Updating timer once
            self.remaining_time = self.update_timer()
    
    def update_timer(self):
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
        
    def draw_scoreboard(self):
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title= self.font_b.render("FINAL RESULTS", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center= (750, 200)))

        for i, entry in enumerate(self.scores):
            text = self.font_s.render(
                f"{i + 1}. Kills: {entry['kills']} | Level: {entry['level']}", 
                True, 
                (255, 255, 255)
            )
            self.screen.blit(text, (550, 300 + i * 50))

        if self.final_round:
            hint = self.font_s.render("Game complete! Returning to menu...", 
                                      True, 
                                      (200, 200, 200))
            self.screen.blit(hint, hint.get_rect(center= (750, 560)))
            
            if pygame.time.get_ticks() - self.scoreboard_time > 2500:
                self.current_round = 1
                self.final_round = False
                self.stete = MENU
                return

        self.replay_button.draw(self.screen)
        self.end_button.draw(self.screen)
    
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
        
        #For Health bar
        self.draw_health_bar(20, 20, 200, 18)

        #For power bar
        self.draw_power_core(20, 55, 200, 14)

        if self.player.level < self.player.max_level:
            xp_ratio = self.player.xp / self.player.xp_to_next[self.player.level]
        else:
            xp_ratio = 1

        pygame.draw.rect(self.screen, (80, 80, 80), (20, 70, 200, 10))
        pygame.draw.rect(self.screen, (120, 200, 120), (20, 70, 200 * xp_ratio, 10))

        level_surf = self.font_s.render(f"Level: {self.player.level}", True, (0, 0, 0))
        self.screen.blit(level_surf, (20, 85))
        
        score_surf = self.font_s.render(f"Score: {self.score}", True, (0, 0, 0))
        self.screen.blit(score_surf, (20, 110))

        if self.state == PLAYING:
            timer_surf = self.font_s.render(
                f"TIme: {self.remaining_time // 60:02}:{self.remaining_time % 60:02}",
                True,
                (0, 0, 0)
            )
            self.screen.blit(timer_surf, (20, 135))
        
        round_surf = self.font_s.render(
            f"Round: {self.current_round}/{self.max_rounds}",
            True,
            (0, 0, 0)
        )
        self.screen.blit(round_surf, (20, 160))
        
        if self.state == SCOREBOARD:
            self.draw_scoreboard()
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