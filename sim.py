import pygame
from math import sqrt
from body import Body
from physics import calc_accel, handle_collisions

class Engine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((900, 700))
        pygame.display.set_caption("Retrograde")
        self.clock = pygame.time.Clock()
        self.running = True
        self.bodies = []

        # camera state
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.zoom = 1.0
        self.panning = False
        self.pan_last = (0, 0)

        # spawn state
        self.spawning = False
        self.spawn_x = 0
        self.spawn_y = 0
        self.spawn_vel = 40.0
        self.spawn_vx = 0.0
        self.spawn_vy = 0.0

    # convert world → screen
    def world_to_screen(self, x, y):
        sx = (x - self.cam_x) * self.zoom + 450
        sy = (y - self.cam_y) * self.zoom + 350
        return int(sx), int(sy)

    # convert screen → world
    def screen_to_world(self, sx, sy):
        wx = (sx - 450) / self.zoom + self.cam_x
        wy = (sy - 350) / self.zoom + self.cam_y
        return wx, wy

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            # start spawn
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    wx, wy = self.screen_to_world(mx, my)
                    self.spawn_x = wx
                    self.spawn_y = wy
                    self.spawning = True

                # start camera pan
                if event.button == 3:
                    self.panning = True
                    self.pan_last = event.pos

            # release spawn or stop pan
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.spawning:
                    mx, my = event.pos
                    wx, wy = self.screen_to_world(mx, my)
                    dx = wx - self.spawn_x
                    dy = wy - self.spawn_y
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

                if event.button == 3:
                    self.panning = False

            # mouse move
            if event.type == pygame.MOUSEMOTION:
                # pan camera
                if self.panning:
                    dx = event.pos[0] - self.pan_last[0]
                    dy = event.pos[1] - self.pan_last[1]
                    self.cam_x -= dx / self.zoom
                    self.cam_y -= dy / self.zoom
                    self.pan_last = event.pos

                # update spawn direction
                if self.spawning:
                    mx, my = event.pos
                    wx, wy = self.screen_to_world(mx, my)
                    dx = wx - self.spawn_x
                    dy = wy - self.spawn_y
                    dist = sqrt(dx*dx + dy*dy)

                    if dist > 1e-6:
                        dirx = dx / dist
                        diry = dy / dist
                        self.spawn_vx = dirx * self.spawn_vel
                        self.spawn_vy = diry * self.spawn_vel
                    else:
                        self.spawn_vx = self.spawn_vy = 0.0

            # zoom
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.zoom = min(4.0, self.zoom * 1.1)
                else:
                    self.zoom = max(0.2, self.zoom / 1.1)

        # adjust spawn speed
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHTBRACKET]:
            self.spawn_vel = min(300.0, self.spawn_vel + 1.0)
        if keys[pygame.K_LEFTBRACKET]:
            self.spawn_vel = max(0.0, self.spawn_vel - 1.0)

    def spawn_body(self, x, y, vx, vy):
        b = Body(x, y, 80)
        b.vx = vx
        b.vy = vy
        self.bodies.append(b)

    def update(self, dt):
        ax, ay = calc_accel(self.bodies)

        for i, b in enumerate(self.bodies):
            b.vx += ax[i] * dt
            b.vy += ay[i] * dt
            b.update(dt)

        handle_collisions(self.bodies)

    def draw(self):
        self.screen.fill((0, 0, 0))

        # draw bodies
        for b in self.bodies:
            sx, sy = self.world_to_screen(b.x, b.y)
            b.draw(self.screen, sx, sy, self.world_to_screen)

        # preview vector
        if self.spawning:
            sx, sy = self.world_to_screen(self.spawn_x, self.spawn_y)
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
