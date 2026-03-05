# body.py
import pygame
from math import sqrt

class Body:
    def __init__(self, x, y, mass):
        # position
        self.x = x
        self.y = y

        # velocity
        self.vx = 0
        self.vy = 0

        # mass and size
        self.mass = mass
        self.radius = max(3, int(sqrt(mass)))

    def update(self, dt):
        # integrate velocity
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surf):
        # color by mass
        color = self.body_color()
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), self.radius)

    def body_color(self):
        # mass - color mapping
        m = self.mass
        if m < 20:
            return (225, 65, 55)
        if m < 60:
            return (255, 160, 95)
        if m < 150:
            return (255, 225, 138)
        if m < 400:
            return (245, 248, 248)
        if m < 900:
            return (200, 218, 255)
        return (138, 172, 255)
