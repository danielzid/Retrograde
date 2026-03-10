import pygame
from collections import deque
from math import sqrt

TRAIL_THRESHOLD = 5
TRAIL_LENGTH    = 100
BH_BIRTH_FRAMES = 60


def get_body_color(body):
    if body.is_singularity:
        return (20, 0, 60)
    if body.is_anomaly:
        return (210, 255, 180)

    color_stops = [
        (0.000,  220,  60,  50),
        (0.003,  240,  95,  70),
        (0.006,  255, 160,  95),
        (0.010,  255, 195, 115),
        (0.015,  255, 222, 138),
        (0.020,  255, 236, 158),
        (0.025,  255, 244, 182),
        (0.033,  255, 248, 202),
        (0.050,  255, 250, 222),
        (0.080,  252, 250, 236),
        (0.120,  245, 248, 248),
        (0.180,  215, 228, 255),
        (0.250,  200, 218, 255),
        (0.350,  182, 206, 255),
        (0.450,  168, 196, 255),
        (0.550,  152, 184, 255),
        (0.650,  138, 172, 255),
        (0.750,  122, 158, 245),
        (0.880,  108, 146, 235),
        (1.000,   95, 135, 225),
    ]

    from physics import SINGULARITY_THRESHOLD
    fraction = min(body.mass / SINGULARITY_THRESHOLD, 1.0)

    for index in range(len(color_stops) - 1):
        f0, r0, g0, b0 = color_stops[index]
        f1, r1, g1, b1 = color_stops[index + 1]
        if fraction <= f1:
            t = (fraction - f0) / (f1 - f0) if f1 > f0 else 0
            return (
                int(r0 + (r1 - r0) * t),
                int(g0 + (g1 - g0) * t),
                int(b0 + (b1 - b0) * t),
            )
    return (95, 135, 225)


glow_cache  = {}
hatch_cache = {}


def get_glow_surface(radius, color, max_alpha):
    key = (radius, color, max_alpha)
    if key in glow_cache:
        return glow_cache[key]
    size = max(4, radius + 10)
    surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    for layer in range(3, 0, -1):
        alpha    = int(max_alpha * (layer / 3) ** 3)
        ring_rad = int(radius * layer / 3)
        pygame.draw.circle(surf, (*color[:3], alpha), (size, size), ring_rad)
    if len(glow_cache) > 512:
        glow_cache.pop(next(iter(glow_cache)))
    glow_cache[key] = surf
    return surf


def get_hatch_surface(screen_radius):
    if screen_radius in hatch_cache:
        return hatch_cache[screen_radius]
    size       = screen_radius * 2 + 2
    hatch_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    spacing    = max(4, screen_radius // 4)
    for offset in range(-screen_radius * 2, screen_radius * 2, spacing):
        pygame.draw.line(hatch_surf, (220, 220, 220, 220),
                         (offset, 0), (offset + screen_radius * 2, screen_radius * 2), 1)
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (screen_radius + 1, screen_radius + 1), screen_radius)
    hatch_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    if len(hatch_cache) > 64:
        hatch_cache.pop(next(iter(hatch_cache)))
    hatch_cache[screen_radius] = hatch_surf
    return hatch_surf


class Body:
    def __init__(self, world_x, world_y, vel_x, vel_y, mass, radius):
        self.x      = world_x
        self.y      = world_y
        self.vx     = vel_x
        self.vy     = vel_y
        self.mass   = mass
        self.radius = radius
        self.spin   = 0.0

        self.is_singularity = False
        self.is_anomaly     = False
        self.is_pinned      = False
        self.is_ghost       = False

        self.bh_birth_timer = 0
        self.bh_born        = False

        self.trail = deque(maxlen=TRAIL_LENGTH) if mass >= TRAIL_THRESHOLD else None

    def get_birth_progress(self):
        if self.bh_born:
            return 1.0
        return min(1.0, self.bh_birth_timer / BH_BIRTH_FRAMES)

    def become_singularity(self):
        if not self.bh_born:
            self.is_singularity = True
            self.bh_birth_timer = 0
            self.bh_born        = False

    def draw(self, surface, zoom, world_to_screen_fn, nearest_body, follow_body):
        from physics import G, SINGULARITY_THRESHOLD
        base_color = get_body_color(self)

        birth_progress = self.get_birth_progress()
        if self.is_singularity and not self.bh_born:
            p = birth_progress
            scale = 1.0 - (p / 0.35) * 0.85 if p < 0.35 else 0.15 + ((p - 0.35) / 0.65) * 0.85
            draw_radius = max(1, self.radius * scale)
        else:
            draw_radius = self.radius

        screen_radius = max(2, int(draw_radius * zoom))

        if self.trail:
            trail_points = list(self.trail)
            for k in range(1, len(trail_points)):
                p1 = world_to_screen_fn(*trail_points[k - 1])
                p2 = world_to_screen_fn(*trail_points[k])
                width = max(1, int(zoom * self.radius * 0.3 * k / len(trail_points)))
                pygame.draw.line(surface, base_color, p1, p2, width)

        screen_x, screen_y = world_to_screen_fn(self.x, self.y)

        grav_strength = G * self.mass
        glow_radius   = int(screen_radius + sqrt(grav_strength) * zoom * 0.35)
        glow_alpha    = max(2, min(10, int(grav_strength * 0.003)))
        glow_surf     = get_glow_surface(glow_radius, base_color, glow_alpha)
        glow_half     = glow_surf.get_width() // 2
        surface.blit(glow_surf, (screen_x - glow_half, screen_y - glow_half),
                     special_flags=pygame.BLEND_RGBA_ADD)

        pygame.draw.circle(surface, base_color, (screen_x, screen_y), screen_radius)

        if screen_radius >= 4:
            dot_radius  = max(1, screen_radius // 3)
            br, bg, bb  = base_color
            highlight   = (min(255, br + 60), min(255, bg + 60), min(255, bb + 60))
            pygame.draw.circle(surface, highlight, (screen_x, screen_y), dot_radius)

        if self.is_singularity:
            pygame.draw.circle(surface, (110, 5, 188), (screen_x, screen_y), screen_radius + 3, 2)
            pygame.draw.circle(surface, (25, 5, 80),   (screen_x, screen_y), screen_radius + 6, 1)
            if not self.bh_born:
                ring_alpha  = int(80 + 175 * (1.0 - birth_progress))
                flash_size  = screen_radius * 6 + 20
                flash_surf  = pygame.Surface((flash_size, flash_size), pygame.SRCALPHA)
                flash_center = screen_radius * 3 + 10
                pygame.draw.circle(flash_surf, (120, 40, 255, ring_alpha),
                                   (flash_center, flash_center), screen_radius + 10, 3)
                surface.blit(flash_surf, (screen_x - flash_center, screen_y - flash_center),
                             special_flags=pygame.BLEND_RGBA_ADD)

        if self.is_anomaly:
            pygame.draw.circle(surface, (140, 255, 100), (screen_x, screen_y), screen_radius + 3, 2)
            pygame.draw.circle(surface, (200, 255, 160), (screen_x, screen_y), screen_radius + 6, 1)

        if self is nearest_body:
            highlight_radius = glow_radius + max(10, int(screen_radius * 0.5))
            pygame.draw.circle(surface, (255, 255, 255), (screen_x, screen_y), highlight_radius, 2)

        if self is follow_body:
            follow_ring_radius = screen_radius + max(8, int(screen_radius * 0.7))
            pygame.draw.circle(surface, (255, 220, 0), (screen_x, screen_y), follow_ring_radius, 2)

        if self.is_pinned:
            pin_radius = screen_radius + max(6, int(screen_radius * 0.4))
            pygame.draw.line(surface, (255, 255, 255),
                             (screen_x - pin_radius, screen_y), (screen_x + pin_radius, screen_y), 1)
            pygame.draw.line(surface, (255, 255, 255),
                             (screen_x, screen_y - pin_radius), (screen_x, screen_y + pin_radius), 1)

        if self.is_ghost:
            surface.blit(get_hatch_surface(screen_radius),
                         (screen_x - screen_radius - 1, screen_y - screen_radius - 1))
