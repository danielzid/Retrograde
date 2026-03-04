# body.py
import pygame

class Body:
    def __init__(self, x, y):
        # position and velocity for each body
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = 4

    def update(self, dt):
        # integrate velocity into position
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface):
        # draw the body as a small circle
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius)
