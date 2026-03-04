# sim.py
import pygame
from body import Body
from physics import apply_gravity

class Engine:
    def __init__(self):
        # initialize pygame and core engine state
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.bodies = []
        self.running = True

    def handle_events(self):
        # process window and input events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                self.bodies.append(Body(x, y))

    def update(self, dt):
        # update physics and body state
        for body in self.bodies:
            apply_gravity(body, dt)
            body.update(dt)

    def draw(self):
        # render all bodies to the screen
        self.screen.fill((0, 0, 0))
        for body in self.bodies:
            body.draw(self.screen)
        pygame.display.flip()

    def run(self):
        # main loop controlling events, updates, and rendering
        while self.running:
            dt = self.clock.tick(60) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()

if __name__ == "__main__":
    Engine().run()
