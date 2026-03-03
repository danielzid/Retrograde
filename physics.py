from math import sqrt

def compute_gravity(bodies, G=1.0, soften=1.0):
    n = len(bodies)
    ax = [0.0] * n
    ay = [0.0] * n

    for i in range(n):
        bi = bodies[i]
        for j in range(i + 1, n):
            bj = bodies[j]
            dx = bj.x - bi.x
            dy = bj.y - bi.y
            dist2 = dx*dx + dy*dy + soften
            dist = sqrt(dist2)
            force = G / (dist2 * dist)

            ax[i] += force * bj.mass * dx
            ay[i] += force * bj.mass * dy
            ax[j] -= force * bi.mass * dx
            ay[j] -= force * bi.mass * dy

    return ax, ay
