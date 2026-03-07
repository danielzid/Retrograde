# RETROGRADE
### N-Body Physics Simulator

> *Galaxies, black holes, solar systems, atomic chaos. Set the rules and see what the universe does with them.*

Retrograde is an interactive N-body physcis simulator built with Python and Pygame. Spawn stars, binary systems, solar systems, singularities, and anomalies, then watch Newtonian (and not so Newtonian) physics do the rest.

Retrograde grew out of a 5th grade science fair project where a model solar system was built and animated by hand, filmed using the camera on a brand new Nintendo 3DS. That project sparked a fascination with orbital mechanics and how so much complexity can emerge from such a simple rule. This is the grown up version of that idea.

---

## Demo

[![Watch the demo](https://img.shields.io/badge/Watch-Demo-red?style=for-the-badge&logo=youtube)](YOUR_VIDEO_LINK_HERE)

---

## Previews

**Solar system forming and settling into orbit**
![Solar system](gifs/solar_system.gif)

**Singularity birth sequence**
![Singularity](gifs/singularity.gif)

**Cluster collision and dominant rotation**
![Cluster collision](gifs/cluster_collision.gif)

**Gravity inversion**
![Gravity inversion](gifs/gravity_inversion.gif)

---

## Features

- **Vectorised O(n²) gravity** powered by NumPy for smooth simulation of hundreds of bodies
- **4 collision modes** — Merge, Explode, Implode, or Elastic; switch on the fly
- **7 spawn types** — Single body, Solar System, Cluster, Binary (equal/unequal), Singularity, Anomaly
- **Black hole formation** — Bodies that accumulate enough mass collapse into singularities with an animated birth sequence
- **Anomalies** — Anti-gravity bodies that repel everything around them
- **Ghost and Pinned bodies** — Ghosts pass through collisions; pinned bodies are fixed in space
- **Camera system** — Zoom, pan, and follow any body
- **Cursor attractor** — Hold right mouse button to pull bodies toward your cursor
- **Live HUD** — Body count, kinetic energy, total mass, FPS, and per-body stats
- **Gravity inversion** — Flip the sign of gravity for chaotic repulsive simulations

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

An `icon.ico` file is expected in the same directory. If running as a bundled executable (PyInstaller), assets are loaded from the bundle automatically.

---

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

## More Than a Sandbox

Retrograde started as a gravity simulator, but the set of tools it gives you pushes it closer to a lightweight physics engine. Pinned bodies act as fixed gravitational anchors, ghost bodies pull and push without taking part in collisions, and gravity itself can be flipped from attractive to repulsive. You can place anything from a lone particle to a full solar system in a few clicks, with control over mass, spin, and starting velocity.

That flexibility means you can model a pretty wide range of real world and theoretical setups. Bodies can be celestial objects, with planets carving stable orbits around a star, binary pairs locked in mutual rotation, or a black hole tearing through a cluster. Or they can stand in for atomic scale particles, with repulsive anomalies behaving like like charges, pinned bodies acting as fixed nuclei, and ghosts representing fields that exert influence without making contact. Flip gravity and you are in stranger territory, expansion dynamics, configurations with no real world equivalent, whatever you want to try.

What makes it genuinely interesting though is what you did not program. Spiral arms trail off rotating clusters without any special logic for them. Bodies in stable orbits get flung into escape trajectories the moment a third mass wanders too close, exactly the way the three-body problem plays out in reality. Clusters slowly lose their outer members over time as energy shuffles through repeated close passes, which mirrors how real stellar clusters gradually evaporate. After a violent event like a merger or a singularity forming, the surviving system tends to settle into a dominant rotational direction, clockwise or anticlockwise, as angular momentum finds a new equilibrium. None of it was planned. It just falls out of the physics.

It does not pretend to be physically accurate, but set things up right and it gets surprisingly close to the real thing.

---

## Performance & Technical Notes

The most physically accurate approach to N-body gravity is to calculate the gravitational influence of every body on every other body each frame. This produces realistic results but is difficult to run efficiently, since the number of calculations grows with the square of the body count.

**Switching to NumPy** was the single biggest performance win. The original implementation used pure Python loops to compute gravitational forces, which became noticeably slow beyond around 50 bodies. Rewriting the force calculations using NumPy, which executes in compiled C under the hood, brought the simulation to a comfortable 60fps with several hundred bodies at once.

**Spatial partitioning** was explored as a way to reduce the per-frame calculation cost further. The approach divided the simulation space into a grid of cells, treating the total mass of each cell as a single gravitational source located at the cell's centre, rather than computing interactions with every individual body inside it. In theory this should have been significantly faster at high body counts, but it ran into a fundamental problem: gravity causes bodies to cluster. As the simulation progresses, bodies naturally pull toward each other and collapse into the same region of space, which means they end up in the same cells. At that point the algorithm loses most of its advantage, since a cell containing many bodies still requires individual calculations between them, pushing the cost back toward the same square scaling the partitioning was meant to avoid. Combined with the overhead of rebuilding the grid each frame, the fully vectorised NumPy approach turned out to be faster in practice, so spatial partitioning was ultimately set aside.

**Collision detection** follows the same strategy: distances between all body pairs are computed in a single NumPy pass each frame, and only pairs that are actually overlapping get handed off to the collision resolver. This keeps collision handling fast even with hundreds of bodies on screen.

The 700-body cap and periodic out-of-bounds cleanup exist as practical guardrails. The simulation stays smooth up to the cap, beyond which frame time degrades noticeably.

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
