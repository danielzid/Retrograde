# physics.py
from math import sqrt

G = 3
SOFTEN = 30

def compute_accelerations(bodies):
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
