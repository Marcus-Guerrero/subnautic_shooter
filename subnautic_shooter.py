import pygame
from sys import exit
from random import randint

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, group):
        super().__init__(group)
        self.image = pygame.image.load('graphics/player.png').convert_alpha()
        self.rect = self.image.get_rect(center = pos)
        self.direction = pygame.math.Vector2()
        self.speed = 5
    
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

    def update (self):
        self.player_movement()
        self.rect.center += (self.direction * self.speed)

class Obstacle (pygame.sprite.Sprite):
    def __init__(self, pos, group):
        super().__init__(group)
        self.image = pygame.image.load("graphics/tree.png").convert_alpha()
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

pygame.init() 
screen = pygame.display.set_mode((1500, 1000))
pygame.display.set_caption("Subnautic Shooter")
fps = pygame.time.Clock()

#General Setup
camera_group = Camera()
player = Player((500, 300), camera_group)

#Surface
surface = pygame.image.load("graphics/ground.png").convert_alpha()
surface_rect = surface.get_rect(center = (0, 0))

for obs in range(20):
    random_x = randint(0, 1500)
    random_y = randint(0, 1000)
    Obstacle((random_x, random_y), camera_group)

while True: 
    for event in pygame.event.get(): 
        if event.type == pygame.QUIT: 
            pygame.quit() 
            exit()
    
    screen.fill((0, 0, 0))
    camera_group.update()
    camera_group.custom(player)

    pygame.display.update() 
    fps.tick(60)