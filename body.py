# body.py
import pygame
from math import sqrt
from collections import deque

TRAIL_LENGTH = 40

class Body:
    def __init__(self, x, y, mass):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.mass = mass
        self.radius = max(3, int(sqrt(mass)))
        self.trail = deque(maxlen=TRAIL_LENGTH)

    def update(self, dt):
        self.trail.append((self.x, self.y))
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surf):
        pts = list(self.trail)
        for i in range(1, len(pts)):
            pygame.draw.line(
                surf,
                (180, 180, 180),
                (int(pts[i-1][0]), int(pts[i-1][1])),
                (int(pts[i][0]),   int(pts[i][1])),
                1
            )

        pygame.draw.circle(
            surf,
            self.body_color(),
            (int(self.x), int(self.y)),
            self.radius
        )

    def body_color(self):
        m = self.mass
        if m < 20:  return (225, 65, 55)
        if m < 60:  return (255, 160, 95)
        if m < 150: return (255, 225, 138)
        if m < 400: return (245, 248, 248)
        if m < 900: return (200, 218, 255)
        return (138, 172, 255)
