# RETROGRADE
### N-Body Physics Simulator
![demo_GIF2](https://github.com/user-attachments/assets/08ca8df9-e91f-4fe4-98ab-8f407027d055)

> *Celestial systems, atomic-scale interactions, and emergent complexity.*

Retrograde is an interactive N-body physics simulator built with Python, NumPy, and Pygame. Spawn stars, binary systems, solar systems, singularities, and anomalies, then watch Newtonian (and not so Newtonian) physics do the rest.

Retrograde grew out of a 5th-grade science fair project where a model solar system was hand built and manually animated using the camera of a Nintendo 3DS. That project sparked a fascination with orbital mechanics and how so much complexity can emerge from such simple rules. This project is the natural evolution of that idea.

Tech Stack: Python, NumPy, Pygame

---

## Demo

[![Watch the demo](https://img.shields.io/badge/Watch-Demo-red?style=for-the-badge&logo=youtube)](YOUR_VIDEO_LINK_HERE)

---

## Features
- **Real-Time** interactive physics sandbox
- **Vectorized O(n²) gravity** using NumPy matrix operations
- **Supports ~700** interacting bodies at real-time frame rates
- **Multiple collision modes** - Merge, Explode, Implode, or Elastic; switch on the fly
- **Camera system** - Zoom, pan, and follow any body
- **Live HUD** - Body count, kinetic energy, total mass, FPS, and per-body stats
- **7 spawn types** - Single body, Solar System, Cluster, Binary (equal/unequal), Singularity, Anomaly
- **Black hole formation** - Bodies that accumulate enough mass collapse into singularities with an animated birth sequence
- **Anomalies** - Anti-gravity bodies that repel everything around them
- **Ghost and Pinned bodies** - Ghosts pass through collisions; pinned bodies are fixed in space
- **Gravity inversion** - Flip the sign of gravity for chaotic repulsive simulations

---
## Performance & Technical Notes

The most physically accurate approach to N-body gravity is to calculate the gravitational influence of every body on every other body each frame. This produces realistic results but is difficult to run efficiently, since the number of calculations grows with the square of the body count.

**Switching to NumPy** was the single biggest performance win. The original implementation used pure Python loops to compute gravitational forces, which became noticeably slow beyond around 50 bodies. Rewriting the force calculations using NumPy, which executes in compiled C under the hood, brought the simulation to a comfortable 60fps with several hundred bodies at once.

**Spatial partitioning** was explored next, inspired by the Barnes-Hut algorithm which achieves O(n log n) scaling by treating grouped bodies as single mass points. A simpler grid based version was implemented here, but it ran into a problem inherent to gravitational simulations: bodies cluster. As gravity pulls everything together, bodies collapse into the same cells, losing most of the advantage the partitioning was meant to provide. Given that and the already solid NumPy performance, it was set aside.

**Collision detection** follows the same vectorized strategy, computing distances between all body pairs in a single NumPy pass and only processing pairs that are actually overlapping. The 700-body cap and periodic out-of-bounds cleanup keep the simulation running smoothly in practice.

---

## More Than a Toy

Retrograde began as a gravity simulator, but the tools push it closer to a lightweight physics engine. Pinned bodies act as fixed gravitational anchors. Ghost bodies exert force without participating in collisions. Gravity itself can even be flipped from attractive to repulsive.

You can spawn anything from a single particle to a full solar system with control over mass, spin, and initial velocity. That flexibility makes it possible to model a wide range of systems.

Bodies can represent celestial objects, with planets settling into stable orbits, binary pairs rotating around each other, or a black hole tearing through a cluster. They can also represent atomic scale systems, where repulsive anomalies behave like like charged particles, pinned bodies act as fixed nuclei, and ghost bodies represent fields that influence motion without direct contact. Flip gravity and the simulation enters stranger territory, expansion dynamics and configurations with no real world equivalent.

What makes the simulation interesting is what was never explicitly programmed. Spiral arms emerge from rotating clusters without special logic. Stable orbits collapse when a third body passes too close, just as in the real three body problem. Clusters gradually lose outer members as energy redistributes through repeated interactions, similar to the evaporation of real stellar clusters. After violent events like mergers or singularity formation, systems often settle into a dominant rotational direction as angular momentum redistributes.

None of that behavior was scripted. It emerges naturally from the physics.

The simulation is not intended to be perfectly accurate, but under the right conditions it can come surprisingly close.

---


## Requirements

- Python 3.8+
- `pygame`
- `numpy`

Install dependencies:

```bash
pip install pygame numpy
```

---

## Running

```bash
python retrograde.py
```

## Controls

### Simulation
| Key | Action |
|-----|--------|
| `Space` | Pause / Resume |
| `M` | Cycle collision mode |
| `Alt` | Flip gravity sign |
| `R` | Reset |
| `I` | Toggle controls panel |

### Camera
| Key / Input | Action |
|-------------|--------|
| Scroll wheel | Zoom in / out |
| Middle click drag | Pan |
| `F` | Follow nearest body |
| `F` (again) | Jump to nearest while following |
| `Esc` | Exit follow mode |

### Spawning
| Key / Input | Action |
|-------------|--------|
| Left click | Spawn at cursor |
| Left click drag | Spawn with velocity (drag sets direction and speed) |
| `+` / `-` | Adjust spawn mass |
| `<` / `>` | Adjust spawn spin |
| `[` / `]` | Adjust spawn velocity |
| `Backspace` | Toggle preserve spawn parameters |
| `\` | Toggle pinned spawn |
| `Enter` | Toggle ghost spawn |

### Spawn Types
| Key | Type |
|-----|------|
| `Q` | Single body |
| `S` | Solar system |
| `C` | Cluster |
| `B` | Binary (equal mass) |
| `U` | Binary (unequal mass) |
| `X` | Singularity (black hole) |
| `A` | Anomaly (repulsive) |

### Body Tools
| Key | Action |
|-----|--------|
| `P` | Pin / Unpin nearest body |
| `G` | Toggle ghost on nearest body |
| `Delete` | Remove nearest body |

### Scale Modifiers (hold while pressing `+`/`-`/`[`/`]`)
| Modifier | Affects |
|----------|---------|
| `Ctrl` | All bodies |
| `Shift` | Followed body only |

---

## Physics Notes

- Gravitational constant `G = 1.3` (tuned for interactive feel, not physical accuracy)
- Softening factor prevents singularities in the force calculation at close range
- Bodies are automatically cleaned up beyond a radius of 15,000 units from the reference body, and total body count is capped at 700
- Mass color ramp runs from red dwarf (low mass) through solar white to blue giant (high mass)
- A body becomes a singularity when its mass exceeds ~10,000 units (merge mode) or ~30,000 units (implode mode)

---

## Project Structure

```
retrograde.py
body.py
physics.py
ui.py
```

---

## Author

**Zid Daniel** 2026
