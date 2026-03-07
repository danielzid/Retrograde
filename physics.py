from math import sqrt

G = 8.0
SOFTEN = 20
ELASTICITY = 0.9   

def calc_accel(bodies):
    n = len(bodies)
    if n == 0:
        return [], []

    ax = [0.0] * n
    ay = [0.0] * n

    for i in range(n):
        bi = bodies[i]
        for j in range(i + 1, n):
            bj = bodies[j]
            dx = bj.x - bi.x
            dy = bj.y - bi.y
            dist2 = dx*dx + dy*dy + SOFTEN
            dist = sqrt(dist2)
            f = G / (dist2 * dist)

            ax[i] += f * bj.mass * dx
            ay[i] += f * bj.mass * dy
            ax[j] -= f * bi.mass * dx
            ay[j] -= f * bi.mass * dy

    return ax, ay


def handle_collisions(bodies):
    n = len(bodies)
    for i in range(n):
        for j in range(i + 1, n):
            a = bodies[i]
            b = bodies[j]

            dx = b.x - a.x
            dy = b.y - a.y
            dist = sqrt(dx*dx + dy*dy)
            min_dist = a.radius + b.radius

            if dist < min_dist and dist > 0:
                nx = dx / dist
                ny = dy / dist

                overlap = min_dist - dist
                a.x -= nx * overlap * 0.5
                a.y -= ny * overlap * 0.5
                b.x += nx * overlap * 0.5
                b.y += ny * overlap * 0.5

                rvx = b.vx - a.vx
                rvy = b.vy - a.vy
                vel_along_normal = rvx * nx + rvy * ny

                if vel_along_normal > 0:
                    continue

                impulse = -(1 + ELASTICITY) * vel_along_normal
                impulse /= (1/a.mass + 1/b.mass)

                ix = impulse * nx
                iy = impulse * ny

                a.vx -= ix / a.mass
                a.vy -= iy / a.mass
                b.vx += ix / b.mass