# physics.py
from math import sqrt

# gravity strength and softening
G = 1.0
SOFTEN = 5.0

def compute_accelerations(bodies):
    # compute gravitational acceleration for each body
    n = len(bodies)
    ax = [0.0] * n
    ay = [0.0] * n

    for i in range(n):
        bi = bodies[i]
        for j in range(i + 1, n):
            bj = bodies[j]

            # vector between bodies
            dx = bj.x - bi.x
            dy = bj.y - bi.y

            # softened distance
            dist2 = dx*dx + dy*dy + SOFTEN
            dist = sqrt(dist2)

            # Newtonian gravity
            force = G * bi.mass * bj.mass / dist2

            # acceleration components
            ax_i = force * dx / (dist * bi.mass)
            ay_i = force * dy / (dist * bi.mass)
            ax_j = -force * dx / (dist * bj.mass)
            ay_j = -force * dy / (dist * bj.mass)

            # accumulate
            ax[i] += ax_i
            ay[i] += ay_i
            ax[j] += ax_j
            ay[j] += ay_j

    return ax, ay
