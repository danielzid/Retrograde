import pygame
from math import sqrt

TRAIL_THRESHOLD = 5
TRAIL_LENGTH = 60
BH_BIRTH_FRAMES = 60

class Body:
    def __init__(self, x, y, mass):
        self.x = x
        self.y = y
        self.mass = mass
        self.radius = max(2, int(sqrt(mass)))
        self.vx = 0.0
        self.vy = 0.0
        self.spin = 0.0
        self.is_singularity = False
        self.bh_birth_timer = 0
        self.bh_born = True
        self.trail = []

    def update(self, dt):
        if self.mass >= TRAIL_THRESHOLD:
            self.trail.append((self.x, self.y))
            if len(self.trail) > TRAIL_LENGTH:
                self.trail.pop(0)
        if self.is_singularity and not self.bh_born:
            self.bh_birth_timer += 1
            if self.bh_birth_timer >= BH_BIRTH_FRAMES:
                self.bh_born = True

    def draw(self, screen, sx, sy, world_to_screen):
        if len(self.trail) > 1:
            for i in range(1, len(self.trail)):
                x1, y1 = self.trail[i - 1]
                x2, y2 = self.trail[i]
                s1 = world_to_screen(x1, y1)
                s2 = world_to_screen(x2, y2)
                pygame.draw.line(screen, (200, 200, 255), s1, s2, 2)
        pygame.draw.circle(screen, (255, 255, 255), (sx, sy), self.radius)
