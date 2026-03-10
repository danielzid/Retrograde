import pygame
import sys
from math import sqrt
from random import randint, seed

from body import Body, get_body_color
from physics import (
    G, SOFTEN, MAX_MASS, MIN_MASS, MAX_VEL, MIN_VEL_SCALE, SPAWN_MAX_VEL,
    SINGULARITY_THRESHOLD, COLLISION_MODES, MAX_BODIES,
    CLEANUP_RADIUS, CLEANUP_FRAME_INTERVAL,
    compute_accelerations, update_bodies, handle_collisions, cleanup_bodies,
    spawn_single_body, spawn_cluster, spawn_binary, spawn_singularity,
    spawn_anomaly, spawn_solar_system, apply_spawn_spin,
)
from ui import draw_hud, draw_instructions, init_fonts, WIDTH, HEIGHT

pygame.init()
init_fonts()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Retrograde: N Body Problem")
clock  = pygame.time.Clock()

FLASH_FRAMES    = 12
SPAWN_VEL_SCALE = 0.02
SPIN_STEP       = 0.25

initial_zoom = 0.25
cam_x        = 0.0
cam_y        = 0.0
zoom         = initial_zoom
ZOOM_MIN     = 0.1
ZOOM_MAX     = 5.0


def world_to_screen(world_x, world_y):
    sx = (world_x - cam_x) * zoom + WIDTH  / 2
    sy = (world_y - cam_y) * zoom + HEIGHT / 2
    return int(sx), int(sy)


def screen_to_world(screen_x, screen_y):
    wx = (screen_x - WIDTH  / 2) / zoom + cam_x
    wy = (screen_y - HEIGHT / 2) / zoom + cam_y
    return wx, wy


def build_star_background():
    bg = pygame.Surface((WIDTH, HEIGHT))
    bg.fill((4, 4, 18))
    seed(42)
    for _ in range(200):
        star_x      = randint(0, WIDTH)
        star_y      = randint(0, HEIGHT)
        brightness  = randint(60, 160)
        bg.set_at((star_x, star_y), (brightness, brightness, brightness))
    seed()
    return bg


def scale_body_mass(body, scale_up):
    body.mass   = min(MAX_MASS, max(MIN_MASS, body.mass * (1.01 if scale_up else 1 / 1.01)))
    body.radius = max(2, int(sqrt(body.mass)))
    was_singularity      = body.is_singularity
    body.is_singularity  = body.mass > SINGULARITY_THRESHOLD
    if body.is_singularity and not was_singularity:
        body.bh_birth_timer = 0
        body.bh_born        = False


def scale_body_velocity(body, scale_up):
    speed = sqrt(body.vx**2 + body.vy**2)
    if scale_up and speed > 0:
        new_speed = min(MAX_VEL, speed * 1.01)
        body.vx  *= new_speed / speed
        body.vy  *= new_speed / speed
    elif not scale_up and speed > MIN_VEL_SCALE:
        body.vx /= 1.01
        body.vy /= 1.01


bodies              = []
paused              = False
show_instructions   = False
running             = True
frame               = 0
flash_timer         = 0
cleanup_frame_count = 0

nearest       = None
follow_mode   = False
follow_target = None

spawning     = False
spawn_world_x = 0.0
spawn_world_y = 0.0
spawn_mass    = 50
spawn_mode    = "single"
spawn_ghost   = False
spawn_pinned  = False
spawn_spin    = 0.0
spawn_vel     = 0.0
spawn_vx      = 0.0
spawn_vy      = 0.0
preserve_params = False

right_held    = False
gravity_sign  = 1

notify_text  = ""
notify_color = (200, 255, 200)
notify_timer = 0

pan_dragging = False
pan_last     = (0, 0)

star_background = build_star_background()

SPAWN_TYPE_LABELS = {
    "single":      "Single Body",
    "solar":       "Solar System",
    "cluster":     "Cluster",
    "binary_eq":   "Binary (Equal)",
    "binary_uneq": "Binary (Unequal)",
    "singularity": "Singularity",
    "anomaly":     "Anomaly",
}

SPAWN_MODE_KEYS = {
    pygame.K_s: "solar",
    pygame.K_c: "cluster",
    pygame.K_b: "binary_eq",
    pygame.K_u: "binary_uneq",
    pygame.K_x: "singularity",
    pygame.K_a: "anomaly",
    pygame.K_q: "single",
}

while running:
    dt  = clock.tick(60) / 60.0
    fps = clock.get_fps()
    frame += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused

            elif event.key == pygame.K_m:
                from physics import COLLISION_MODE
                import physics
                physics.COLLISION_MODE = COLLISION_MODES[
                    (COLLISION_MODES.index(physics.COLLISION_MODE) + 1) % len(COLLISION_MODES)
                ]

            elif event.key == pygame.K_f:
                if follow_mode:
                    follow_target = nearest if nearest else follow_target
                else:
                    follow_mode   = True
                    follow_target = nearest

            elif event.key == pygame.K_ESCAPE:
                if follow_mode and show_instructions:
                    show_instructions = False
                elif follow_mode:
                    follow_mode   = False
                    follow_target = None
                else:
                    show_instructions = False

            elif event.key == pygame.K_i:
                show_instructions = not show_instructions

            elif event.key == pygame.K_r:
                bodies              = []
                cam_x, cam_y        = 0.0, 0.0
                zoom                = initial_zoom
                follow_mode         = False
                follow_target       = None
                cleanup_frame_count = 0
                screen.fill((4, 4, 18))
                flash_timer  = FLASH_FRAMES
                notify_text  = "Simulation reset"
                notify_color = (255, 220, 80)
                notify_timer = 180

            elif event.key == pygame.K_BACKSPACE:
                preserve_params = not preserve_params
                if preserve_params:
                    if spawning:
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        end_x, end_y     = screen_to_world(mouse_x, mouse_y)
                        spawn_vx         = (end_x - spawn_world_x) * SPAWN_VEL_SCALE
                        spawn_vy         = (end_y - spawn_world_y) * SPAWN_VEL_SCALE
                        spawn_vel        = sqrt(spawn_vx**2 + spawn_vy**2)
                else:
                    spawn_mass = 50
                    spawn_spin = 0.0
                    spawn_vel  = 0.0
                    spawn_vx   = 0.0
                    spawn_vy   = 0.0

            elif event.key in (pygame.K_LALT, pygame.K_RALT):
                gravity_sign = -gravity_sign

            elif event.key == pygame.K_p:
                if nearest and nearest in bodies:
                    nearest.is_pinned = not nearest.is_pinned
                    notify_text  = "Pinned" if nearest.is_pinned else "Unpinned"
                    notify_color = (255, 255, 160) if nearest.is_pinned else (160, 160, 160)
                    notify_timer = 120

            elif event.key == pygame.K_g:
                if nearest and nearest in bodies:
                    nearest.is_ghost = not nearest.is_ghost
                    notify_text  = "Ghost ON" if nearest.is_ghost else "Ghost OFF"
                    notify_color = (160, 200, 255) if nearest.is_ghost else (160, 160, 160)
                    notify_timer = 120

            elif event.key == pygame.K_DELETE:
                if nearest and nearest in bodies:
                    bodies.remove(nearest)
                    if follow_target is nearest:
                        follow_mode   = False
                        follow_target = None

            if event.key in SPAWN_MODE_KEYS:
                spawn_mode   = SPAWN_MODE_KEYS[event.key]
                notify_text  = f"Spawn: {SPAWN_TYPE_LABELS[spawn_mode]}"
                notify_color = (120, 255, 120)
                notify_timer = 150

            elif event.key == pygame.K_RETURN:
                spawn_ghost  = not spawn_ghost
                notify_text  = "Spawn Ghost ON" if spawn_ghost else "Spawn Ghost OFF"
                notify_color = (140, 200, 255) if spawn_ghost else (160, 160, 160)
                notify_timer = 120

            elif event.key == pygame.K_BACKSLASH:
                spawn_pinned = not spawn_pinned
                notify_text  = "Spawn Pinned ON" if spawn_pinned else "Spawn Pinned OFF"
                notify_color = (255, 255, 140) if spawn_pinned else (160, 160, 160)
                notify_timer = 120

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y      = event.pos
                spawn_world_x, spawn_world_y = screen_to_world(mouse_x, mouse_y)
                spawning = True
                if not preserve_params:
                    spawn_spin = 0.0
            elif event.button == 2:
                pan_dragging = True
                pan_last     = event.pos
            elif event.button == 3:
                right_held = True
            elif event.button == 4:
                zoom = min(ZOOM_MAX, zoom * 1.1)
            elif event.button == 5:
                zoom = max(ZOOM_MIN, zoom / 1.1)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and spawning:
                import physics
                mouse_x, mouse_y = event.pos
                end_x, end_y     = screen_to_world(mouse_x, mouse_y)
                drag_vx          = (end_x - spawn_world_x) * SPAWN_VEL_SCALE
                drag_vy          = (end_y - spawn_world_y) * SPAWN_VEL_SCALE

                if preserve_params:
                    drag_speed = sqrt(drag_vx**2 + drag_vy**2)
                    if drag_speed > 0.01:
                        vx = drag_vx / drag_speed * spawn_vel
                        vy = drag_vy / drag_speed * spawn_vel
                    else:
                        vx, vy = 0.0, 0.0
                else:
                    vx, vy = drag_vx, drag_vy

                total_speed = sqrt(vx**2 + vy**2)
                if total_speed > SPAWN_MAX_VEL:
                    vx *= SPAWN_MAX_VEL / total_speed
                    vy *= SPAWN_MAX_VEL / total_speed

                if spawn_mode == "single":
                    new_body = Body(spawn_world_x, spawn_world_y, vx, vy,
                                   spawn_mass, max(3, int(sqrt(spawn_mass))))
                    new_body.is_singularity = spawn_mass > SINGULARITY_THRESHOLD
                    new_body.bh_born        = new_body.is_singularity
                    new_bodies_list = [new_body]
                    bodies.append(new_body)
                else:
                    spawner_map = {
                        "solar":       lambda: spawn_solar_system(spawn_world_x, spawn_world_y, spawn_mass),
                        "cluster":     lambda: spawn_cluster(spawn_world_x, spawn_world_y, spawn_mass, 30),
                        "binary_eq":   lambda: spawn_binary(spawn_world_x, spawn_world_y, spawn_mass, equal=True),
                        "binary_uneq": lambda: spawn_binary(spawn_world_x, spawn_world_y, spawn_mass, equal=False),
                        "singularity": lambda: [spawn_singularity(spawn_world_x, spawn_world_y, spawn_mass)],
                        "anomaly":     lambda: [spawn_anomaly(spawn_world_x, spawn_world_y, spawn_mass)],
                    }
                    new_bodies_list = spawner_map.get(spawn_mode, lambda: [])()
                    new_bodies_list = apply_spawn_spin(new_bodies_list, spawn_spin, spawn_mode)
                    for body in new_bodies_list:
                        body.vx += vx
                        body.vy += vy
                    bodies += new_bodies_list

                for body in new_bodies_list:
                    if spawn_ghost:  body.is_ghost  = True
                    if spawn_pinned: body.is_pinned = True

                spawning    = False
                final_speed = sqrt(vx**2 + vy**2)
                if not preserve_params or final_speed > 0.01:
                    spawn_vel = final_speed
                    spawn_vx  = vx
                    spawn_vy  = vy
                if not preserve_params:
                    spawn_mass = 50
                    spawn_spin = 0.0

            elif event.button == 2:
                pan_dragging = False
            elif event.button == 3:
                right_held = False

        if event.type == pygame.MOUSEMOTION and pan_dragging:
            delta_x  = event.pos[0] - pan_last[0]
            delta_y  = event.pos[1] - pan_last[1]
            cam_x   -= delta_x / zoom
            cam_y   -= delta_y / zoom
            pan_last = event.pos

    keys  = pygame.key.get_pressed()
    ctrl  = keys[pygame.K_LCTRL]  or keys[pygame.K_RCTRL]
    shift = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

    if not ctrl and not shift:
        if keys[pygame.K_EQUALS] or keys[pygame.K_KP_PLUS]:
            spawn_mass = min(50000, max(spawn_mass + 1, int(spawn_mass * 1.03)))
        if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
            spawn_mass = max(5, min(spawn_mass - 1, int(spawn_mass / 1.03)))
        if keys[pygame.K_COMMA]:
            spawn_spin += SPIN_STEP * 0.2
        if keys[pygame.K_PERIOD]:
            spawn_spin -= SPIN_STEP * 0.2
        if keys[pygame.K_RIGHTBRACKET]:
            spawn_vel = min(SPAWN_MAX_VEL, spawn_vel * 1.02 + 0.1)
            sv = sqrt(spawn_vx**2 + spawn_vy**2)
            if sv > 0.01:
                spawn_vx = spawn_vx / sv * spawn_vel
                spawn_vy = spawn_vy / sv * spawn_vel
        if keys[pygame.K_LEFTBRACKET]:
            spawn_vel = max(0.0, spawn_vel / 1.02 - 0.1)
            sv = sqrt(spawn_vx**2 + spawn_vy**2)
            if sv > 0.01:
                spawn_vx = spawn_vx / sv * spawn_vel
                spawn_vy = spawn_vy / sv * spawn_vel

    if ctrl and bodies:
        if keys[pygame.K_EQUALS] or keys[pygame.K_KP_PLUS]:
            for body in bodies: scale_body_mass(body, True)
        if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
            for body in bodies: scale_body_mass(body, False)
        if keys[pygame.K_RIGHTBRACKET]:
            for body in bodies: scale_body_velocity(body, True)
        if keys[pygame.K_LEFTBRACKET]:
            for body in bodies: scale_body_velocity(body, False)

    if shift and follow_mode and follow_target in bodies:
        focused = follow_target
        if keys[pygame.K_EQUALS] or keys[pygame.K_KP_PLUS]:   scale_body_mass(focused, True)
        if keys[pygame.K_MINUS]  or keys[pygame.K_KP_MINUS]:  scale_body_mass(focused, False)
        if keys[pygame.K_RIGHTBRACKET]: scale_body_velocity(focused, True)
        if keys[pygame.K_LEFTBRACKET]:  scale_body_velocity(focused, False)

    if not paused and bodies:
        import physics
        accel_x, accel_y = compute_accelerations(bodies)

        # Apply global gravity sign to all accelerations
        if gravity_sign != 1:
            accel_x = [a * gravity_sign for a in accel_x]
            accel_y = [a * gravity_sign for a in accel_y]

        update_bodies(bodies, accel_x, accel_y, dt)
        bodies = handle_collisions(bodies)

        if right_held:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            cursor_world_x, cursor_world_y = screen_to_world(mouse_x, mouse_y)
            ATTRACTOR_MASS = 500000
            for body in bodies:
                dx     = cursor_world_x - body.x
                dy     = cursor_world_y - body.y
                dist2  = dx * dx + dy * dy + SOFTEN
                dist   = sqrt(dist2)
                force  = G * ATTRACTOR_MASS / dist2
                body.vx += force * dx / dist * dt
                body.vy += force * dy / dist * dt

    cleanup_frame_count += 1
    if cleanup_frame_count >= CLEANUP_FRAME_INTERVAL:
        cleanup_frame_count = 0
        ref_body = follow_target if (follow_mode and follow_target) else nearest
        bodies, removed_count = cleanup_bodies(bodies, ref_body, CLEANUP_RADIUS, MAX_BODIES)
        if removed_count > 0:
            notify_text  = f"Cleanup: -{removed_count}"
            notify_color = (60, 60, 80)
            notify_timer = 60

    nearest     = None
    mouse_x, mouse_y         = pygame.mouse.get_pos()
    cursor_world_x, cursor_world_y = screen_to_world(mouse_x, mouse_y)
    best_dist_sq = float("inf")
    for body in bodies:
        dx = body.x - cursor_world_x
        dy = body.y - cursor_world_y
        dist_sq = dx * dx + dy * dy
        if dist_sq < best_dist_sq:
            best_dist_sq = dist_sq
            nearest      = body

    if follow_mode:
        if follow_target in bodies:
            cam_x = follow_target.x
            cam_y = follow_target.y
        else:
            if bodies and follow_target is not None:
                follow_target = min(
                    bodies,
                    key=lambda b: (b.x - follow_target.x)**2 + (b.y - follow_target.y)**2
                )
            else:
                follow_mode   = False
                follow_target = None

    screen.blit(star_background, (0, 0))

    for body in bodies:
        screen_bx, screen_by = world_to_screen(body.x, body.y)
        screen_br = max(2, int(body.radius * zoom))
        if (screen_bx + screen_br < 0 or screen_bx - screen_br > WIDTH or
                screen_by + screen_br < 0 or screen_by - screen_br > HEIGHT):
            continue
        body.draw(screen, zoom, world_to_screen, nearest, follow_target)

    if right_held:
        mx, my = pygame.mouse.get_pos()
        pygame.draw.circle(screen, (180, 0, 255), (mx, my), 10, 2)
        pygame.draw.circle(screen, (100, 0, 180), (mx, my), 24, 1)
        pygame.draw.circle(screen, (60,  0, 120), (mx, my), 42, 1)

    if spawning:
        mouse_x, mouse_y   = pygame.mouse.get_pos()
        end_world_x, end_world_y = screen_to_world(mouse_x, mouse_y)
        drag_vx      = (end_world_x - spawn_world_x) * SPAWN_VEL_SCALE
        drag_vy      = (end_world_y - spawn_world_y) * SPAWN_VEL_SCALE
        display_speed = spawn_vel if preserve_params else sqrt(drag_vx**2 + drag_vy**2)
        preview_radius = max(3, int(sqrt(spawn_mass) * zoom))
        spawn_screen_x, spawn_screen_y = world_to_screen(spawn_world_x, spawn_world_y)
        preview_color  = get_body_color(Body(0, 0, 0, 0, spawn_mass, 1))
        pygame.draw.circle(screen, preview_color, (spawn_screen_x, spawn_screen_y), preview_radius, 2)

        line_dx    = mouse_x - spawn_screen_x
        line_dy    = mouse_y - spawn_screen_y
        line_len   = sqrt(line_dx**2 + line_dy**2) + 1e-6
        norm_x     = line_dx / line_len
        norm_y     = line_dy / line_len

        if preserve_params:
            fixed_len = spawn_vel / SPAWN_VEL_SCALE * zoom
            arrow_end_x = int(spawn_screen_x + norm_x * fixed_len)
            arrow_end_y = int(spawn_screen_y + norm_y * fixed_len)
        else:
            arrow_end_x = mouse_x
            arrow_end_y = mouse_y

        line_color = (255, 255, 100)
        pygame.draw.line(screen, line_color, (spawn_screen_x, spawn_screen_y), (arrow_end_x, arrow_end_y), 2)
        arrow_size = 7
        perp_x     = -norm_y
        perp_y     =  norm_x
        pygame.draw.polygon(screen, line_color, [
            (arrow_end_x, arrow_end_y),
            (int(arrow_end_x - norm_x * arrow_size + perp_x * arrow_size * 0.4),
             int(arrow_end_y - norm_y * arrow_size + perp_y * arrow_size * 0.4)),
            (int(arrow_end_x - norm_x * arrow_size - perp_x * arrow_size * 0.4),
             int(arrow_end_y - norm_y * arrow_size - perp_y * arrow_size * 0.4)),
        ])

        scale = spawn_mass / 50.0
        spawn_mass_estimates = {
            "singularity": int((SINGULARITY_THRESHOLD + 250) * scale),
            "anomaly":     int((SINGULARITY_THRESHOLD + 250) * scale),
            "solar":       int(2300 * scale + 5 * 60 * scale + 2 * 5 * scale),
            "cluster":     int(40 * 50 * scale),
            "binary_eq":   int(2 * 700 * scale),
            "binary_uneq": int(2 * 700 * scale),
        }
        total_spawn_mass = spawn_mass_estimates.get(spawn_mode, spawn_mass)

        from ui import font_small
        screen.blit(font_small.render(f"Type: {SPAWN_TYPE_LABELS.get(spawn_mode, spawn_mode)}",
                    True, (200, 255, 200)), (spawn_screen_x + preview_radius + 6, spawn_screen_y - 10))
        screen.blit(font_small.render(f"Mass: ~{total_spawn_mass}  Velo: {display_speed:.1f}  Spin: {spawn_spin:.2f}",
                    True, (200, 255, 200)), (spawn_screen_x + preview_radius + 6, spawn_screen_y + 8))

    import physics
    ui_state = {
        "zoom":             zoom,
        "paused":           paused,
        "gravity_sign":     gravity_sign,
        "follow_mode":      follow_mode,
        "follow_target":    follow_target,
        "nearest":          nearest,
        "preserve_params":  preserve_params,
        "spawn_ghost":      spawn_ghost,
        "spawn_pinned":     spawn_pinned,
        "spawn_mode":       spawn_mode,
        "spawn_mass":       spawn_mass,
        "spawn_spin":       spawn_spin,
        "spawn_vel":        spawn_vel,
        "spawn_vx":         spawn_vx,
        "spawn_vy":         spawn_vy,
        "spawn_vel_scale":  SPAWN_VEL_SCALE,
        "spawning":         spawning,
        "spawn_screen_x":   spawn_world_x,
        "spawn_screen_y":   spawn_world_y,
        "collision_mode":   physics.COLLISION_MODE,
        "notify_text":      notify_text,
        "notify_color":     notify_color,
        "notify_timer":     notify_timer,
        "show_instructions": show_instructions,
    }

    draw_hud(screen, bodies, fps, frame, paused, ui_state)

    if notify_timer > 0:
        notify_timer -= 1

    if flash_timer > 0:
        alpha       = int(35 * (flash_timer / FLASH_FRAMES))
        flash_surf  = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash_surf.fill((160, 220, 255, alpha))
        screen.blit(flash_surf, (0, 0))
        flash_timer -= 1

    pygame.display.flip()

pygame.quit()
sys.exit()
