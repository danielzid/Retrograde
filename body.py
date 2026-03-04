# body.py
import pygame
import random

class Body:
    def __init__(self, x, y):
        # position and velocity for each body
        self.x = x
        self.y = y
        # small random initial velocity for zero-g drift
        self.vx = random.uniform(-40, 40)
        self.vy = random.uniform(-40, 40)
        self.radius = 4

    def update(self, dt):
        # integrate velocity into position
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius)
