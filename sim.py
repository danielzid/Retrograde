import pygame
from math import sqrt, sin, cos, pi
from body import Body
from physics import calc_accel, handle_collisions
import random

class Engine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((900, 700))
        pygame.display.set_caption("Retrograde")
        self.clock = pygame.time.Clock()
        self.running = True
        self.bodies = []

        self.cam_x = 0.0
        self.cam_y = 0.0
        self.zoom = 1.0
        self.panning = False
        self.pan_last = (0, 0)

        self.spawning = False
        self.spawn_x = 0
        self.spawn_y = 0
        self.spawn_vel = 40.0
        self.spawn_vx = 0.0
        self.spawn_vy = 0.0

        self.spawn_mode = "single"

    def world_to_screen(self, x, y):
        sx = (x - self.cam_x) * self.zoom + 450
        sy = (y - self.cam_y) * self.zoom + 350
        return int(sx), int(sy)

    def screen_to_world(self, sx, sy):
        wx = (sx - 450) / self.zoom + self.cam_x
        wy = (sy - 350) / self.zoom + self.cam_y
        return wx, wy

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    wx, wy = self.screen_to_world(mx, my)
                    self.spawn_x = wx
                    self.spawn_y = wy
                    self.spawning = True

                if event.button == 3:
                    self.panning = True
                    self.pan_last = event.pos

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

                    self.apply_spawn_mode(self.spawn_x, self.spawn_y, vx, vy)
                    self.spawning = False

                if event.button == 3:
                    self.panning = False

            if event.type == pygame.MOUSEMOTION:
                if self.panning:
                    dx = event.pos[0] - self.pan_last[0]
                    dy = event.pos[1] - self.pan_last[1]
                    self.cam_x -= dx / self.zoom
                    self.cam_y -= dy / self.zoom
                    self.pan_last = event.pos

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

            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0:
                    self.zoom = min(4.0, self.zoom * 1.1)
                else:
                    self.zoom = max(0.2, self.zoom / 1.1)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHTBRACKET]:
            self.spawn_vel = min(300.0, self.spawn_vel + 1.0)
        if keys[pygame.K_LEFTBRACKET]:
            self.spawn_vel = max(0.0, self.spawn_vel - 1.0)

        if keys[pygame.K_q]: self.spawn_mode = "single"
        if keys[pygame.K_b]: self.spawn_mode = "binary"
        if keys[pygame.K_u]: self.spawn_mode = "uneven"
        if keys[pygame.K_c]: self.spawn_mode = "cluster"
        if keys[pygame.K_s]: self.spawn_mode = "system"
        if keys[pygame.K_3]: self.spawn_mode = "ring"
        if keys[pygame.K_5]: self.spawn_mode = "scatter"

    def spawn_body(self, x, y, vx, vy, mass=80):
        b = Body(x, y, mass)
        b.vx = vx
        b.vy = vy
        self.bodies.append(b)

    def apply_spawn_mode(self, x, y, vx, vy):
        mode = self.spawn_mode

        match mode:

            case "single":
                self.spawn_body(x, y, vx, vy)

            case "binary":
                self.spawn_body(x, y,  vx,  vy)
                self.spawn_body(x, y, -vx, -vy)

            case "uneven":
                self.spawn_body(x, y, vx, vy, mass=120)
                self.spawn_body(x, y, -vx * 0.4, -vy * 0.4, mass=40)

            case "cluster":
                for _ in range(6):
                    ox = x + (random.random() - 0.5) * 20
                    oy = y + (random.random() - 0.5) * 20
                    self.spawn_body(ox, oy, vx, vy)

            case "system":
                self.spawn_body(x, y, 0, 0, mass=500)
                for _ in range(5):
                    ang = random.random() * 2 * pi
                    dist = 80 + random.random() * 120
                    px = x + cos(ang) * dist
                    py = y + sin(ang) * dist
                    speed = sqrt(500 / dist)
                    vx2 = -sin(ang) * speed
                    vy2 =  cos(ang) * speed
                    self.spawn_body(px, py, vx2, vy2, mass=40)

            case "ring":
                for i in range(12):
                    ang = (i / 12) * 2 * pi
                    ox = x + cos(ang) * 40
                    oy = y + sin(ang) * 40
                    self.spawn_body(ox, oy, vx, vy)

            case "scatter":
                for _ in range(10):
                    ang = random.random() * 2 * pi
                    spd = self.spawn_vel * (0.5 + random.random())
                    self.spawn_body(x, y, cos(ang)*spd, sin(ang)*spd)


    def update(self, dt):
        ax, ay = calc_accel(self.bodies)

        for i, b in enumerate(self.bodies):
            b.vx += ax[i] * dt
            b.vy += ay[i] * dt
            b.update(dt)

        handle_collisions(self.bodies)

    def draw(self):
        self.screen.fill((0, 0, 0))

        for b in self.bodies:
            sx, sy = self.world_to_screen(b.x, b.y)
            b.draw(self.screen, sx, sy, self.world_to_screen)

        if self.spawning:
            sx, sy = self.world_to_screen(self.spawn_x, self.spawn_y)
            px = sx + self.spawn_vx * 5
            py = sy + self.spawn_vy * 5
            pygame.draw.line(self.screen, (255, 255, 0), (sx, sy), (px, py), 2)

        font = pygame.font.SysFont("consolas", 18)
        text = [
            f"Mode: {self.spawn_mode}",
            f"Spawn Vel: {int(self.spawn_vel)}",
            f"Bodies: {len(self.bodies)}"
        ]
        for i, t in enumerate(text):
            surf = font.render(t, True, (255, 255, 255))
            self.screen.blit(surf, (10, 10 + i*20))

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()

if __name__ == "__main__":
    Engine().run()
