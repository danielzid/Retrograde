# body.py
import pygame
from math import sqrt
from collections import deque

TRAIL_LENGTH = 40

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

        # trail history
        self.trail = deque(maxlen=TRAIL_LENGTH)

    def update(self, dt):
        # store previous position
        self.trail.append((self.x, self.y))

        # integrate velocity
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surf):
        # draw trail
        pts = list(self.trail)
        for i in range(1, len(pts)):
            pygame.draw.line(
                surf,
                (180, 180, 180),
                (int(pts[i-1][0]), int(pts[i-1][1])),
                (int(pts[i][0]),   int(pts[i][1])),
                1
            )

        # draw body
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
