import pygame
from sys import exit
from random import randint

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group):
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

    def player_movement(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.direction.y = -1
        elif keys[pygame.K_s]:
            self.direction.y = 1
        else:
            self.direction.y = 0

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

    def update (self):
        self.player_movement()
        self.rect.center += (self.direction * self.speed)

class Obstacle (pygame.sprite.Sprite):
    def __init__(self, pos, group):
        super().__init__(group)
        self.image = pygame.image.load("graphics/Fly1.png").convert_alpha()
        self.rect = self.image.get_rect(center= pos)

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
        pygame.init() 
        self.screen = pygame.display.set_mode((1500, 1000))
        pygame.display.set_caption("Subnautic Shooter")
        self.fps = pygame.time.Clock()

        #General Setup
        self.camera_group = Camera()
        self.player = Player((500, 300), self.camera_group)
        self.obstacle_group =pygame.sprite.Group()

        #Creating obstacles
        self.obstacle_implementation()
        self.running = True
        
    def obstacle_implementation(self):
        for obs in range(25):
            random_x = randint(-1824, 1824)
            random_y = randint(-1600, 1600)
            Obstacle((random_x, random_y), [self.camera_group, self.obstacle_group])

    def collision_handling(self):
        if pygame.sprite.spritecollide(self.player, self.obstacle_group, False):
            self.player.take_damage()
        
        if self.player.health <= 0:
            self.running = False

    def handling_events(self):
        for event in pygame.event.get(): 
            if event.type == pygame.QUIT: 
                self.running = False

    def update(self):
        self.camera_group.update()
        self.collision_handling()

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.camera_group.custom(self.player)
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