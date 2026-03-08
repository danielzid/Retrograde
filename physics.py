import numpy as np
from math import sqrt, pi, cos, sin
from random import uniform, randint
from body import Body

G = 1.3
SOFTEN = 30
CLEANUP_RADIUS = 13000
MAX_BODIES = 500

def calc_accel(bodies):
    n = len(bodies)
    ax = [0.0] * n
    ay = [0.0] * n
    for i in range(n):
        bi = bodies[i]
        for j in range(i + 1, n):
            bj = bodies[j]
            dx = bj.x - bi.x
            dy = bj.y - bi.y
            d2 = dx*dx + dy*dy + SOFTEN
            d = sqrt(d2)
            f = G / (d2 * d)
            ax[i] += f * bj.mass * dx
            ay[i] += f * bj.mass * dy
            ax[j] -= f * bi.mass * dx
            ay[j] -= f * bi.mass * dy
    return ax, ay

def update_bodies(bodies, ax, ay, dt):
    vx = np.array([b.vx for b in bodies], float)
    vy = np.array([b.vy for b in bodies], float)
    x  = np.array([b.x  for b in bodies], float)
    y  = np.array([b.y  for b in bodies], float)
    vx += np.array(ax) * dt
    vy += np.array(ay) * dt
    x  += vx * dt
    y  += vy * dt
    for i, b in enumerate(bodies):
        b.vx = float(vx[i])
        b.vy = float(vy[i])
        b.x  = float(x[i])
        b.y  = float(y[i])
        b.update(dt)

def merge_bodies(b1, b2):
    m = b1.mass + b2.mass
    x = (b1.x*b1.mass + b2.x*b2.mass) / m
    y = (b1.y*b1.mass + b2.y*b2.mass) / m
    vx = (b1.vx*b1.mass + b2.vx*b2.mass) / m
    vy = (b1.vy*b1.mass + b2.vy*b2.mass) / m
    nb = Body(x, y, m)
    nb.vx = vx
    nb.vy = vy
    return nb

def handle_collisions(bodies):
    new = []
    removed = set()
    extra = []
    for i in range(len(bodies)):
        if i in removed:
            continue
        b1 = bodies[i]
        for j in range(i + 1, len(bodies)):
            if j in removed:
                continue
            b2 = bodies[j]
            dx = b1.x - b2.x
            dy = b1.y - b2.y
            d = sqrt(dx*dx + dy*dy)
            if d < b1.radius + b2.radius:
                extra.append(merge_bodies(b1, b2))
                removed.add(i)
                removed.add(j)
                break
    for i, b in enumerate(bodies):
        if i not in removed:
            new.append(b)
    new.extend(extra)
    return new

def cleanup_bodies(bodies, ref, radius, max_count):
    if len(bodies) > max_count:
        bodies = bodies[-max_count:]
    return bodies, 0
