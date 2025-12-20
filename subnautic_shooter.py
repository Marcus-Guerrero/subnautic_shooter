import pygame
from sys import exit
from random import randint

#Game status
PLAYING = "playing"
PAUSED = "paused"
SCOREBOARD = "scoreboard"

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group, bullet_group):
        super().__init__(group)

        #Character rendering
        self.image = pygame.image.load('graphics/player.png').convert_alpha()
        self.rect = self.image.get_rect(center = pos)
        self.direction = pygame.math.Vector2()
        self.speed = 5

        #Health System
        self.health = 5
        self.last_hit_time = 0
        self.hit_cooldown = 1000

        #Shooting System
        self.bullet_group = bullet_group
        self.shoot_cooldown = 300
        self.last_shot = 0

    def player_movement(self):
        keys = pygame.key.get_pressed()

        #Vertical Movement
        if keys[pygame.K_w]:
            self.direction.y = -1
        elif keys[pygame.K_s]:
            self.direction.y = 1
        else:
            self.direction.y = 0

        #Horizontal Movement
        if keys[pygame.K_d]:
            self.direction.x = 1
        elif keys[pygame.K_a]:
            self.direction.x = -1
        else:
            self.direction.x = 0
    
    def take_damage(self):
        current = pygame.time.get_ticks()
        if current - self.last_hit_time > self.hit_cooldown:
            self.health -= 1
            self.last_hit_time = current
            print (f"Player health: {self.health}")

    def player_shooting (self, camere_offset):
        current_time = pygame.time.get_ticks()

        if current_time - self.last_shot >= self.shoot_cooldown:
            mouse_screen = pygame.mouse.get_pos()

            #World position of mouse
            mouse_world = pygame.math.Vector2(mouse_screen) + camere_offset
            player_pos = pygame.math.Vector2(self.rect.center)
            direction = mouse_world - player_pos

            if direction.length() != 0:
                Bullet(self.rect.center, direction, self.bullet_group)

    def update (self):
        self.player_movement()
        self.rect.center += (self.direction * self.speed)

class Obstacle (pygame.sprite.Sprite):
    def __init__(self, pos, group):
        super().__init__(group)
        self.image = pygame.image.load("graphics/Fly1.png").convert_alpha()
        self.rect = self.image.get_rect(center= pos)

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
        self.obstacle_implementation()
        self.running = True

        #Score board
        self.score = 0
        self.scores = []
        self.max_scores =5
        self.show_scoreboard = False
        self.font_b = pygame.font.Font(None, 70)
        self.font_s = pygame.font.Font (None, 36)

        #Current state of game status
        self.state = PLAYING

    def obstacle_implementation(self):
        for obs in range(25):
            random_x = randint(-1824, 1824)
            random_y = randint(-1600, 1600)
            Obstacle((random_x, random_y), [self.camera_group, self.obstacle_group])

    def collision_handling(self):
        #Player collision
        if pygame.sprite.spritecollide(self.player, self.obstacle_group, False):
            self.player.take_damage()

        #Bullet collision
        for bullet in self.bullet_group:
            hit_obstacles = pygame.sprite.spritecollide(bullet,self.obstacle_group, True)
            if hit_obstacles:
                bullet.kill()
                self.score += len(hit_obstacles)
        
        if self.player.health <= 0:
            self.scores.append(self.score)
            self.scores.sort(reverse = True)
            self.scores = self.scores[:self.max_scores]
            self.state = SCOREBOARD

    def handling_events(self):
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                self.running = False
            
            if event.type == pygame.KEYDOWN:

                #Toggling Pause
                if event.key == pygame.K_ESCAPE:
                    if self.state == PLAYING:
                        self.state = PAUSED
                    elif self.state == PAUSED:
                        self.state = PLAYING

                if self.state == PAUSED:
                    if event.key == pygame.K_r:
                        self.state = PLAYING
                    elif event.key == pygame.K_q:
                        self.running = False

                if event.key == pygame.K_RETURN and self.state == SCOREBOARD:
                    self.state = PLAYING
                    self.score = 0
                    self.player.health = 5
                
                if self.state == PLAYING:
                    if event.key == pygame.K_SPACE:
                        self.player.player_shooting(self.camera_group.offset)

    def update(self):
        if self.state == PLAYING:
            self.camera_group.update()
            self.bullet_group.update()
            self.collision_handling()
    
    def draw_scoreboard(self):
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title= self.font_b.render("HIGHSCORE", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center= (750, 200)))

        for i, score in enumerate(self.scores):
            text = self.font_s.render(f"{i + 1}. {score}", True, (255, 255, 255))
            self.screen.blit(text, (650, 300 + i * 50))

        hint = self.font_s.render("Please ENTER to close", True, (180, 180, 180))
        self.screen.blit(hint, hint.get_rect(center= (750, 550)))
    
    def draw_paused_menu (self):
        overlay = pygame.Surface(self.screen.get_size())
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.font_b.render("PAUSED", True, (255, 255, 255))
        resume = self.font_s.render("R - Resume Game", True, (255, 255, 255))
        quit_game = self.font_s.render("Q - Exit Game", True, (255, 255, 255))

        self.screen.blit(title, title.get_rect(center=(750, 350)))
        self.screen.blit(resume, resume.get_rect(center=(750, 450)))
        self.screen.blit(quit_game, quit_game.get_rect(center=(750, 500)))

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.camera_group.custom(self.player)

        for bullet in self.bullet_group:
            offset_pos = bullet.rect.topleft - self.camera_group.offset
            self.screen.blit(bullet.image, offset_pos)
        
        score_surf = self.font_s.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_surf, (20, 20))

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