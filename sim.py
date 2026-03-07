# sim.py
import pygame
from math import sqrt
from body import Body
from physics import compute_accelerations

class Engine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((900, 700))
        pygame.display.set_caption("Retrograde")
        self.clock = pygame.time.Clock()
        self.bodies = []
        self.running = True

        self.spawning = False
        self.spawn_x = 0
        self.spawn_y = 0
        self.spawn_vel = 0.0
        self.spawn_vx = 0.0
        self.spawn_vy = 0.0

    def spawn_body(self, x, y, vx, vy):
        mass = 80
        b = Body(x, y, mass)
        b.vx = vx
        b.vy = vy
        self.bodies.append(b)

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    self.spawn_x = mx
                    self.spawn_y = my
                    self.spawning = True

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.spawning:
                    dx = event.pos[0] - self.spawn_x
                    dy = event.pos[1] - self.spawn_y
                    dist = sqrt(dx*dx + dy*dy)

                    if dist > 1e-6:
                        dirx = dx / dist
                        diry = dy / dist
                    else:
                        dirx = diry = 0.0

                    vx = dirx * self.spawn_vel
                    vy = diry * self.spawn_vel

                    self.spawn_body(self.spawn_x, self.spawn_y, vx, vy)

                    self.spawn_vx = vx
                    self.spawn_vy = vy
                    self.spawning = False

            if event.type == pygame.MOUSEMOTION:
                if self.spawning:
                    mx, my = event.pos
                    dx = mx - self.spawn_x
                    dy = my - self.spawn_y
                    dist = sqrt(dx*dx + dy*dy)

                    if dist > 1e-6:
                        dirx = dx / dist
                        diry = dy / dist
                        self.spawn_vx = dirx * self.spawn_vel
                        self.spawn_vy = diry * self.spawn_vel
                    else:
                        self.spawn_vx = self.spawn_vy = 0.0

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHTBRACKET]:
            self.spawn_vel = min(200.0, self.spawn_vel + 0.5)
        if keys[pygame.K_LEFTBRACKET]:
            self.spawn_vel = max(0.0, self.spawn_vel - 0.5)

    def update(self, dt):
        ax, ay = compute_accelerations(self.bodies)
        for i, b in enumerate(self.bodies):
            b.vx += ax[i] * dt
            b.vy += ay[i] * dt
            b.update(dt)

    def draw(self):
        self.screen.fill((0, 0, 0))

        for b in self.bodies:
            b.draw(self.screen)

        if self.spawning:
            sx, sy = self.spawn_x, self.spawn_y
            px = sx + self.spawn_vx * 5
            py = sy + self.spawn_vy * 5
            pygame.draw.line(self.screen, (255, 255, 0), (sx, sy), (px, py), 2)

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()

if __name__ == "__main__":
    Engine().run()
