import numpy as np
from math import sqrt, cos, sin, atan2, pi
from random import randint, uniform, gauss, random, choice, sample
from body import Body, TRAIL_THRESHOLD, BH_BIRTH_FRAMES

G                           = 1.3
SOFTEN                      = 30
SINGULARITY_THRESHOLD       = 10000
SINGULARITY_THRESHOLD_IMPLODE = 30_000
EXPLOSION_THRESHOLD         = 43000
IMPLODE_THRESHOLD           = 50000

BH_SHARD_SPEED_MIN = 50
BH_SHARD_SPEED_MAX = 150
BH_SHARD_MASS      = 0.5

MAX_MASS       = 100_000
MIN_MASS       = 0.5
MAX_VEL        = 500.0
MIN_VEL_SCALE  = 0.001
SPAWN_MAX_VEL  = 200.0

CLEANUP_RADIUS         = 15_000
CLEANUP_FRAME_INTERVAL = 10
MAX_BODIES             = 700

COLLISION_MODE        = "merge"
COLLISION_MODES       = ["merge", "explode", "implode", "elastic"]
COLLISION_MODE_LABELS = {
    "merge":   "Merge  ",
    "explode": "Explode",
    "implode": "Implode",
    "elastic": "Elastic",
}


def compute_accelerations(bodies):
    count = len(bodies)
    if count == 0:
        return [], []

    pos_x    = np.array([b.x    for b in bodies], dtype=np.float64)
    pos_y    = np.array([b.y    for b in bodies], dtype=np.float64)
    masses   = np.array([b.mass for b in bodies], dtype=np.float64)
    # Anomalies exert repulsive gravity
    gravity_signs = np.array(
        [-1 if b.is_anomaly else 1 for b in bodies], dtype=np.float64
    )

    delta_x = pos_x[np.newaxis, :] - pos_x[:, np.newaxis]
    delta_y = pos_y[np.newaxis, :] - pos_y[:, np.newaxis]
    dist_sq = delta_x * delta_x + delta_y * delta_y + SOFTEN
    dist    = np.sqrt(dist_sq)
    inv_d3  = 1.0 / (dist_sq * dist)
    factor  = G * gravity_signs[np.newaxis, :] * masses[np.newaxis, :] * inv_d3
    np.fill_diagonal(factor, 0.0)

    accel_x = (factor * delta_x).sum(axis=1).tolist()
    accel_y = (factor * delta_y).sum(axis=1).tolist()
    return accel_x, accel_y


def update_bodies(bodies, accel_x_list, accel_y_list, dt):
    if not bodies:
        return

    vel_x   = np.array([b.vx for b in bodies], dtype=np.float64)
    vel_y   = np.array([b.vy for b in bodies], dtype=np.float64)
    pos_x   = np.array([b.x  for b in bodies], dtype=np.float64)
    pos_y   = np.array([b.y  for b in bodies], dtype=np.float64)
    accel_x = np.array(accel_x_list, dtype=np.float64)
    accel_y = np.array(accel_y_list, dtype=np.float64)

    vel_x += accel_x * dt
    vel_y += accel_y * dt
    pos_x += vel_x   * dt
    pos_y += vel_y   * dt

    for index, body in enumerate(bodies):
        if body.trail is not None:
            body.trail.append((body.x, body.y))
        if not body.is_pinned:
            body.vx = float(vel_x[index])
            body.vy = float(vel_y[index])
            body.x  = float(pos_x[index])
            body.y  = float(pos_y[index])
        if body.is_singularity and not body.bh_born:
            body.bh_birth_timer += 1
            if body.bh_birth_timer >= BH_BIRTH_FRAMES:
                body.bh_born = True


def merge_bodies(body_a, body_b, implode_mode=False):
    total_mass     = body_a.mass + body_b.mass
    merged_x       = (body_a.x * body_a.mass + body_b.x * body_b.mass) / total_mass
    merged_y       = (body_a.y * body_a.mass + body_b.y * body_b.mass) / total_mass
    merged_vx      = (body_a.vx * body_a.mass + body_b.vx * body_b.mass) / total_mass
    merged_vy      = (body_a.vy * body_a.mass + body_b.vy * body_b.mass) / total_mass
    merged_radius  = sqrt(body_a.radius ** 2 + body_b.radius ** 2)
    merged         = Body(merged_x, merged_y, merged_vx, merged_vy, total_mass, merged_radius)
    merged.spin    = (body_a.spin * body_a.mass + body_b.spin * body_b.mass) / total_mass

    threshold   = SINGULARITY_THRESHOLD_IMPLODE if implode_mode else SINGULARITY_THRESHOLD
    either_is_bh = body_a.is_singularity or body_b.is_singularity
    merged.is_singularity = either_is_bh or (total_mass > threshold)

    if merged.is_singularity and not either_is_bh:
        merged.bh_birth_timer = 0
        merged.bh_born        = False
    else:
        merged.bh_born = merged.is_singularity
        if either_is_bh:
            parent_bh     = body_a if body_a.is_singularity else body_b
            merged.radius = max(parent_bh.radius, max(3, int(sqrt(sqrt(total_mass)))))

    if merged.is_singularity:
        merged.radius = max(3, int(sqrt(sqrt(total_mass))))

    merged.is_pinned = body_a.is_pinned or body_b.is_pinned
    merged.is_ghost  = body_a.is_ghost  and body_b.is_ghost
    return merged


def elastic_bounce(body_a, body_b):
    delta_x = body_a.x - body_b.x
    delta_y = body_a.y - body_b.y
    dist    = sqrt(delta_x * delta_x + delta_y * delta_y + 1e-6)
    norm_x  = delta_x / dist
    norm_y  = delta_y / dist
    rel_vx  = body_a.vx - body_b.vx
    rel_vy  = body_a.vy - body_b.vy
    dot     = rel_vx * norm_x + rel_vy * norm_y

    if body_a.is_pinned and body_b.is_pinned:
        pass
    elif body_a.is_pinned:
        body_b.vx -= 2 * dot * norm_x
        body_b.vy -= 2 * dot * norm_y
    elif body_b.is_pinned:
        body_a.vx -= 2 * (-dot) * (-norm_x)
        body_a.vy -= 2 * (-dot) * (-norm_y)
    else:
        impulse    = 2 * dot / (body_a.mass + body_b.mass)
        body_a.vx -= impulse * body_b.mass * norm_x
        body_a.vy -= impulse * body_b.mass * norm_y
        body_b.vx += impulse * body_a.mass * norm_x
        body_b.vy += impulse * body_a.mass * norm_y

    overlap = (body_a.radius + body_b.radius) - dist
    if overlap > 0:
        if body_a.is_pinned and not body_b.is_pinned:
            body_b.x -= norm_x * overlap
            body_b.y -= norm_y * overlap
        elif body_b.is_pinned and not body_a.is_pinned:
            body_a.x += norm_x * overlap
            body_a.y += norm_y * overlap
        else:
            body_a.x += norm_x * overlap * 0.5
            body_a.y += norm_y * overlap * 0.5
            body_b.x -= norm_x * overlap * 0.5
            body_b.y -= norm_y * overlap * 0.5


def spawn_explosion_fragments(source_body, count=8):
    fragments = []
    for _ in range(count):
        angle = uniform(0, 2 * pi)
        speed = uniform(4, 12)
        frag  = Body(
            source_body.x + cos(angle) * source_body.radius,
            source_body.y + sin(angle) * source_body.radius,
            source_body.vx + cos(angle) * speed,
            source_body.vy + sin(angle) * speed,
            max(MIN_MASS, source_body.mass / count),
            max(2, int(source_body.radius / 2.5))
        )
        fragments.append(frag)
    return fragments


def spawn_implosion_shards(merged_body, count=None):
    if count is None:
        count = randint(0, 3)
    shard_mass  = max(MIN_MASS, merged_body.mass * 0.03)
    shard_speed = uniform(40, 80)
    shards      = []
    for _ in range(count):
        angle = uniform(0, 2 * pi)
        shard = Body(
            merged_body.x + cos(angle) * (merged_body.radius + 3),
            merged_body.y + sin(angle) * (merged_body.radius + 3),
            merged_body.vx + cos(angle) * shard_speed,
            merged_body.vy + sin(angle) * shard_speed,
            shard_mass, max(2, int(sqrt(shard_mass)))
        )
        shards.append(shard)
    return shards


def spawn_bh_shards(bh_body, count=None):
    if count is None:
        count = randint(0, 2)
    shards = []
    for _ in range(count):
        angle = uniform(0, 2 * pi)
        speed = uniform(BH_SHARD_SPEED_MIN, BH_SHARD_SPEED_MAX)
        shard = Body(
            bh_body.x + cos(angle) * (bh_body.radius + 1),
            bh_body.y + sin(angle) * (bh_body.radius + 1),
            bh_body.vx + cos(angle) * speed,
            bh_body.vy + sin(angle) * speed,
            BH_SHARD_MASS, 2
        )
        shards.append(shard)
    return shards


def handle_collisions(bodies):
    if len(bodies) < 2:
        return bodies

    pos_x   = np.array([b.x      for b in bodies], dtype=np.float32)
    pos_y   = np.array([b.y      for b in bodies], dtype=np.float32)
    radii   = np.array([b.radius for b in bodies], dtype=np.float32)
    delta_x = pos_x[:, np.newaxis] - pos_x[np.newaxis, :]
    delta_y = pos_y[:, np.newaxis] - pos_y[np.newaxis, :]
    rad_sum = radii[:, np.newaxis] + radii[np.newaxis, :]
    count   = len(bodies)
    rows, cols = np.where(
        (delta_x * delta_x + delta_y * delta_y < rad_sum * rad_sum) &
        (np.arange(count)[:, None] < np.arange(count)[None, :])
    )

    removed   = set()
    new_bodies = []
    extra      = []

    for idx_a, idx_b in zip(rows.tolist(), cols.tolist()):
        if idx_a in removed or idx_b in removed:
            continue
        body_a = bodies[idx_a]
        body_b = bodies[idx_b]

        if body_a.is_ghost or body_b.is_ghost:
            continue

        if body_a.is_anomaly or body_b.is_anomaly:
            anomaly     = body_a if body_a.is_anomaly else body_b
            other       = body_b if body_a.is_anomaly else body_a
            other_index = idx_b  if body_a.is_anomaly else idx_a
            elastic_bounce(body_a, body_b)

            if COLLISION_MODE == "explode":
                rel_mass = body_a.mass * body_b.mass / (body_a.mass + body_b.mass)
                ke = 0.5 * rel_mass * ((body_a.vx - body_b.vx)**2 + (body_a.vy - body_b.vy)**2)
                if ke > EXPLOSION_THRESHOLD and len(bodies) <= MAX_BODIES and not other.is_singularity:
                    removed.add(other_index)
                    extra.extend(spawn_explosion_fragments(other, randint(4, 8)))

            elif COLLISION_MODE == "implode":
                rel_mass = body_a.mass * body_b.mass / (body_a.mass + body_b.mass)
                rel_ke   = 0.5 * rel_mass * ((body_a.vx - body_b.vx)**2 + (body_a.vy - body_b.vy)**2)
                if rel_ke >= IMPLODE_THRESHOLD and not other.is_singularity:
                    ddx  = other.x - anomaly.x
                    ddy  = other.y - anomaly.y
                    dist = sqrt(ddx * ddx + ddy * ddy) + 1e-6
                    push_norm_x = ddx / dist
                    push_norm_y = ddy / dist
                    eject_speed = uniform(60, 120)
                    compressed  = Body(
                        anomaly.x + push_norm_x * (anomaly.radius + other.radius + 2),
                        anomaly.y + push_norm_y * (anomaly.radius + other.radius + 2),
                        anomaly.vx + push_norm_x * eject_speed,
                        anomaly.vy + push_norm_y * eject_speed,
                        other.mass * 1.5, max(2, int(sqrt(other.mass * 1.5)))
                    )
                    compressed.is_pinned = other.is_pinned
                    compressed.is_ghost  = other.is_ghost
                    removed.add(other_index)
                    extra.append(compressed)
                    extra.extend(spawn_implosion_shards(compressed))
            continue

        if COLLISION_MODE == "merge":
            extra.append(merge_bodies(body_a, body_b))
            removed.add(idx_a)
            removed.add(idx_b)

        elif COLLISION_MODE == "explode":
            elastic_bounce(body_a, body_b)
            rel_mass = body_a.mass * body_b.mass / (body_a.mass + body_b.mass)
            ke = 0.5 * rel_mass * ((body_a.vx - body_b.vx)**2 + (body_a.vy - body_b.vy)**2)
            if (ke > EXPLOSION_THRESHOLD and len(bodies) <= MAX_BODIES
                    and not body_a.is_singularity and not body_b.is_singularity):
                removed.add(idx_a)
                extra.extend(spawn_explosion_fragments(body_a, randint(4, 8)))

        elif COLLISION_MODE == "implode":
            if body_a.is_singularity or body_b.is_singularity:
                merged = merge_bodies(body_a, body_b, implode_mode=True)
                extra.append(merged)
                extra.extend(spawn_bh_shards(merged))
                removed.add(idx_a)
                removed.add(idx_b)
            else:
                rel_mass = body_a.mass * body_b.mass / (body_a.mass + body_b.mass)
                rel_ke   = 0.5 * rel_mass * ((body_a.vx - body_b.vx)**2 + (body_a.vy - body_b.vy)**2)
                if rel_ke >= IMPLODE_THRESHOLD:
                    merged = merge_bodies(body_a, body_b, implode_mode=True)
                    extra.append(merged)
                    extra.extend(spawn_implosion_shards(merged))
                    removed.add(idx_a)
                    removed.add(idx_b)
                else:
                    elastic_bounce(body_a, body_b)

        elif COLLISION_MODE == "elastic":
            elastic_bounce(body_a, body_b)

    for index, body in enumerate(bodies):
        if index not in removed:
            new_bodies.append(body)
    new_bodies.extend(extra)
    return new_bodies


def cleanup_bodies(bodies, reference_body, max_radius, max_count):
    if not bodies:
        return bodies, 0
    ref     = reference_body if (reference_body and reference_body in bodies) else None
    removed = 0

    if ref is not None:
        radius_sq = max_radius * max_radius
        kept      = []
        for body in bodies:
            if body is ref:
                kept.append(body)
            else:
                dx = body.x - ref.x
                dy = body.y - ref.y
                if dx * dx + dy * dy <= radius_sq:
                    kept.append(body)
                else:
                    removed += 1
        bodies = kept

    if len(bodies) > max_count:
        excess = len(bodies) - max_count
        ref_x, ref_y = (ref.x, ref.y) if ref is not None else (0.0, 0.0)
        bodies.sort(key=lambda b: 0 if b is ref else -((b.x - ref_x)**2 + (b.y - ref_y)**2))
        bodies   = bodies[excess:]
        removed += excess

    return bodies, removed


def spawn_single_body(world_x, world_y, mass=None):
    if mass is None:
        mass = randint(5, 200)
    return Body(world_x, world_y, uniform(-2, 2), uniform(-2, 2), mass, max(3, int(sqrt(mass))))


def spawn_cluster(world_x, world_y, spawn_mass, count=20):
    scale  = spawn_mass / 50.0
    bodies = []
    for _ in range(count):
        offset_x = gauss(0, 250)
        offset_y = gauss(0, 250)
        dist     = sqrt(offset_x * offset_x + offset_y * offset_y) + 1
        speed    = sqrt(G * 500 / dist) * 0.4
        angle    = atan2(offset_y, offset_x) + pi / 2
        body     = spawn_single_body(world_x + offset_x, world_y + offset_y)
        body.mass   = max(1, body.mass * scale)
        body.radius = max(2, int(sqrt(body.mass)))
        body.vx    += cos(angle) * speed
        body.vy    += sin(angle) * speed
        bodies.append(body)
    apply_spawn_spin(bodies, choice([0.05, -0.05]), "cluster")
    return bodies


def spawn_binary(world_x, world_y, spawn_mass, equal=True):
    scale = spawn_mass / 50.0
    if equal:
        mass_a = mass_b = randint(400, 1000) * scale
    else:
        mass_a = randint(200, 1200) * scale
        mass_b = randint(50, 200) * scale
    mass_a = max(1, mass_a)
    mass_b = max(1, mass_b)
    separation  = randint(60, 140)
    total_mass  = mass_a + mass_b
    orbit_a     = separation * mass_b / total_mass
    orbit_b     = separation * mass_a / total_mass
    orbit_vel_a = sqrt(G * mass_b ** 2 / (total_mass * orbit_a)) if orbit_a > 0 else 0
    orbit_vel_b = sqrt(G * mass_a ** 2 / (total_mass * orbit_b)) if orbit_b > 0 else 0
    body_a = Body(world_x - orbit_a, world_y, 0, -orbit_vel_a, mass_a, max(3, int(sqrt(mass_a))))
    body_b = Body(world_x + orbit_b, world_y, 0,  orbit_vel_b, mass_b, max(3, int(sqrt(mass_b))))
    return [body_a, body_b]


def spawn_singularity(world_x, world_y, spawn_mass):
    scale = spawn_mass / 50.0
    mass  = (SINGULARITY_THRESHOLD + randint(0, 500)) * scale
    bh    = Body(world_x, world_y, 0, 0, mass, max(3, int(sqrt(mass)) // 5 * 4))
    bh.is_singularity = True
    bh.bh_born        = True
    return bh


def spawn_anomaly(world_x, world_y, spawn_mass):
    scale = spawn_mass / 50.0
    mass  = (SINGULARITY_THRESHOLD + randint(0, 500)) * scale
    an    = Body(world_x, world_y, 0, 0, mass, max(3, int(sqrt(mass)) // 5 * 4))
    an.is_anomaly = True
    return an


def spawn_solar_system(world_x, world_y, spawn_mass):
    scale     = spawn_mass / 50.0
    bodies    = []
    star_mass = randint(1800, 2800) * scale
    star      = Body(world_x, world_y, 0, 0, star_mass, int(sqrt(star_mass)))
    bodies.append(star)

    planet_configs = [
        (60,  (8,  18),  False),
        (110, (12, 25),  False),
        (170, (20, 50),  True),
        (240, (80, 180), True),
        (330, (60, 130), True),
        (430, (15, 35),  False),
        (540, (10, 20),  False),
    ]
    selected = sorted(sample(planet_configs, randint(4, len(planet_configs))), key=lambda c: c[0])

    for orbit_radius, mass_range, can_have_moon in selected:
        orbit_radius  *= uniform(0.85, 1.15)
        planet_mass    = max(1, randint(*mass_range) * scale)
        angle          = uniform(0, 2 * pi)
        planet_x       = world_x + cos(angle) * orbit_radius
        planet_y       = world_y + sin(angle) * orbit_radius
        orbital_speed  = sqrt(G * star_mass / orbit_radius) * uniform(0.92, 1.08)
        perp_angle     = angle + pi / 2
        planet = Body(planet_x, planet_y,
                      cos(perp_angle) * orbital_speed,
                      sin(perp_angle) * orbital_speed,
                      planet_mass, max(3, int(sqrt(planet_mass))))
        bodies.append(planet)

        if can_have_moon and random() < 0.6:
            moon_orbit_radius = planet.radius * randint(5, 10)
            moon_mass         = max(1, randint(2, max(3, int(planet_mass // 10))))
            moon_angle        = uniform(0, 2 * pi)
            moon_x            = planet_x + cos(moon_angle) * moon_orbit_radius
            moon_y            = planet_y + sin(moon_angle) * moon_orbit_radius
            moon_speed        = sqrt(G * planet_mass / moon_orbit_radius)
            moon_perp         = moon_angle + pi / 2
            moon = Body(moon_x, moon_y,
                        planet.vx + cos(moon_perp) * moon_speed,
                        planet.vy + sin(moon_perp) * moon_speed,
                        moon_mass, max(2, int(sqrt(moon_mass))))
            bodies.append(moon)
    return bodies


def apply_spawn_spin(bodies, spin_amount, spawn_mode_name=""):
    if abs(spin_amount) < 1e-6 or not bodies:
        return bodies
    if spawn_mode_name == "solar":
        pivot_x = bodies[0].x
        pivot_y = bodies[0].y
    else:
        total_mass = sum(b.mass for b in bodies)
        pivot_x    = sum(b.x * b.mass for b in bodies) / total_mass
        pivot_y    = sum(b.y * b.mass for b in bodies) / total_mass
    for body in bodies:
        dx   = body.x - pivot_x
        dy   = body.y - pivot_y
        dist = sqrt(dx * dx + dy * dy) + 1e-6
        tx   = -dy / dist
        ty   =  dx / dist
        body.vx += tx * spin_amount * sqrt(dist)
        body.vy += ty * spin_amount * sqrt(dist)
    return bodies
