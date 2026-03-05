# sim.py
import pygame
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

    def spawn_body(self, x, y):
        # fixed mass for now
        mass = 80
        b = Body(x, y, mass)
        self.bodies.append(b)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                self.spawn_body(x, y)

    def update(self, dt):
        # gravity
        ax, ay = compute_accelerations(self.bodies)

        # integrate
        for i, b in enumerate(self.bodies):
            b.vx += ax[i] * dt
            b.vy += ay[i] * dt
            b.update(dt)

    def draw(self):
        self.screen.fill((0, 0, 0))
        for b in self.bodies:
            b.draw(self.screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()

if __name__ == "__main__":
    Engine().run()
