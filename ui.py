import pygame
from math import sqrt

WIDTH  = 1200
HEIGHT = 800

font_large         = None
font_small         = None
font_hud           = None
font_hud_bold      = None
font_ui            = None
font_ui_bold       = None
font_ui_small      = None
font_ui_small_bold = None
font_hint          = None
font_credit        = None
font_instr         = None
font_instr_bold    = None


def init_fonts():
    global font_large, font_small, font_hud, font_hud_bold
    global font_ui, font_ui_bold, font_ui_small, font_ui_small_bold
    global font_hint, font_credit, font_instr, font_instr_bold
    font_large         = pygame.font.SysFont("Consolas", 20, bold=True)
    font_small         = pygame.font.SysFont("Consolas", 14)
    font_hud           = pygame.font.SysFont("Consolas", 12)
    font_hud_bold      = pygame.font.SysFont("Consolas", 12, bold=True)
    font_ui            = pygame.font.SysFont("Consolas", 12)
    font_ui_bold       = pygame.font.SysFont("Consolas", 12, bold=True)
    font_ui_small      = pygame.font.SysFont("Consolas", 11)
    font_ui_small_bold = pygame.font.SysFont("Consolas", 11, bold=True)
    font_hint          = pygame.font.SysFont("Consolas", 14, bold=True)
    font_credit        = pygame.font.SysFont("Consolas", 13, bold=True)
    font_instr         = pygame.font.SysFont("Consolas", 12)
    font_instr_bold    = pygame.font.SysFont("Consolas", 12, bold=True)

PANEL_BG_COLOR     = (8, 10, 28, 188)
PANEL_BORDER_COLOR = (50, 70, 130)
PANEL_TITLE_COLOR  = (255, 220, 80)
LABEL_COLOR        = (90, 120, 175)
VALUE_COLOR        = (200, 255, 200)
SECTION_COLOR      = (160, 130, 60)
SECTION_LINE_COLOR = (40, 55, 100)

SPAWN_LABEL_MAP = {
    "single":      "Single",
    "solar":       "Solar System",
    "cluster":     "Cluster",
    "binary_eq":   "Binary (Eq)",
    "binary_uneq": "Binary (Uneq)",
    "singularity": "Singularity",
    "anomaly":     "Anomaly",
}

COLLISION_MODE_COLORS = {
    "merge":   (120, 255, 140),
    "explode": (255, 130,  50),
    "implode": (80,  190, 255),
    "elastic": (180, 180, 180),
}


def draw_panel(surface, panel_x, panel_y, panel_w, panel_h, title=None):
    bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    bg.fill(PANEL_BG_COLOR)
    surface.blit(bg, (panel_x, panel_y))
    pygame.draw.rect(surface, PANEL_BORDER_COLOR, (panel_x, panel_y, panel_w, panel_h), 1)
    if title:
        surface.blit(font_ui_bold.render(title, True, PANEL_TITLE_COLOR), (panel_x + 10, panel_y + 5))
        pygame.draw.line(surface, PANEL_BORDER_COLOR,
                         (panel_x + 1, panel_y + 18), (panel_x + panel_w - 2, panel_y + 18), 1)
    return panel_y + (20 if title else 0)


def draw_row(surface, panel_x, row_y, label, value, label_width=80,
             value_color=VALUE_COLOR, label_color=LABEL_COLOR):
    surface.blit(font_ui.render(label, True, label_color),    (panel_x + 10, row_y))
    surface.blit(font_ui.render(str(value), True, value_color), (panel_x + 10 + label_width, row_y))
    return row_y + 16


def draw_section_header(surface, panel_x, row_y, panel_w, text):
    surface.blit(font_ui_small_bold.render(text, True, SECTION_COLOR), (panel_x + 10, row_y))
    pygame.draw.line(surface, SECTION_LINE_COLOR,
                     (panel_x + 10, row_y + 13), (panel_x + panel_w - 10, row_y + 13), 1)
    return row_y + 16


def draw_spawn_status(surface, state):
    grav_color    = (255, 80, 80)   if state["gravity_sign"] == -1 else VALUE_COLOR
    grav_label    = "REPULSIVE"     if state["gravity_sign"] == -1 else "Normal"
    mode_color    = COLLISION_MODE_COLORS.get(state["collision_mode"], VALUE_COLOR)
    preserve_color = (100, 255, 140) if state["preserve_params"] else (120, 120, 140)
    ghost_color   = (140, 200, 255) if state["spawn_ghost"]     else (120, 120, 140)
    pin_color     = (255, 255, 140) if state["spawn_pinned"]    else (120, 120, 140)

    display_body  = state["follow_target"] if (state["follow_mode"] and state["follow_target"]) else state["nearest"]
    section_label = "FOLLOWING" if (state["follow_mode"] and state["follow_target"]) else "SELECTED"

    PAD = 8
    LH  = 16
    SH  = 16
    TH  = 20
    panel_w = 190
    panel_h = (TH + PAD + SH + 7 * LH + PAD + SH + 2 * LH + PAD
               + (SH + 6 * LH + PAD if display_body else 0))

    credit_h = font_small.get_height() + 10
    panel_x  = WIDTH  - panel_w - 12
    panel_y  = HEIGHT - credit_h - panel_h - 8

    y = draw_panel(surface, panel_x, panel_y, panel_w, panel_h, "METRICS") + PAD - 4

    scale        = state["spawn_mass"] / 50.0
    spawn_mode   = state["spawn_mode"]
    from physics import SINGULARITY_THRESHOLD
    if spawn_mode in ("singularity", "anomaly"):
        display_mass = int((SINGULARITY_THRESHOLD + 250) * scale)
    elif spawn_mode == "solar":
        display_mass = int(2300 * scale + 5 * 60 * scale + 2 * 5 * scale)
    elif spawn_mode == "cluster":
        display_mass = int(40 * 50 * scale)
    elif spawn_mode in ("binary_eq", "binary_uneq"):
        display_mass = int(2 * 700 * scale)
    else:
        display_mass = state["spawn_mass"]

    if state["spawning"] and not state["preserve_params"]:
        mx, my   = pygame.mouse.get_pos()
        live_vel = sqrt(
            ((mx - state["spawn_screen_x"]) * state["spawn_vel_scale"])**2 +
            ((my - state["spawn_screen_y"]) * state["spawn_vel_scale"])**2
        )
    else:
        live_vel = state["spawn_vel"]

    y = draw_section_header(surface, panel_x, y, panel_w, "SPAWN")
    y = draw_row(surface, panel_x, y, "Type",     SPAWN_LABEL_MAP.get(spawn_mode, spawn_mode))
    y = draw_row(surface, panel_x, y, "Mass",     f"~{display_mass}")
    y = draw_row(surface, panel_x, y, "Spin",     f"{state['spawn_spin']:+.2f}")
    y = draw_row(surface, panel_x, y, "Velocity", f"{live_vel:.1f}")
    y = draw_row(surface, panel_x, y, "Preserve", "ON" if state["preserve_params"] else "off", value_color=preserve_color)
    y = draw_row(surface, panel_x, y, "Pin   ",   "ON" if state["spawn_pinned"] else "off",    value_color=pin_color)
    y = draw_row(surface, panel_x, y, "Ghost",    "ON" if state["spawn_ghost"]  else "off",    value_color=ghost_color)
    y += PAD

    y = draw_section_header(surface, panel_x, y, panel_w, "SIMULATION")
    from physics import COLLISION_MODE_LABELS
    y = draw_row(surface, panel_x, y, "Collision", COLLISION_MODE_LABELS.get(state["collision_mode"], state["collision_mode"]), value_color=mode_color)
    y = draw_row(surface, panel_x, y, "Gravity",   grav_label, value_color=grav_color)
    y += PAD

    if display_body:
        speed  = sqrt(display_body.vx**2 + display_body.vy**2)
        tags   = []
        if display_body.is_singularity:
            tags.append("singularity")
        if display_body.is_anomaly:
            tags.append("anomaly")
        pin_value_color   = (255, 255, 140) if display_body.is_pinned else (120, 120, 140)
        ghost_value_color = (140, 200, 255) if display_body.is_ghost  else (120, 120, 140)
        y = draw_section_header(surface, panel_x, y, panel_w, section_label)
        y = draw_row(surface, panel_x, y, "Type",     ", ".join(tags) if tags else "normal")
        y = draw_row(surface, panel_x, y, "Mass",     f"{display_body.mass:.0f}")
        y = draw_row(surface, panel_x, y, "Velocity", f"{speed:.1f}")
        y = draw_row(surface, panel_x, y, "Pinned",   "YES" if display_body.is_pinned else "no",  value_color=pin_value_color)
        y = draw_row(surface, panel_x, y, "Ghost",    "YES" if display_body.is_ghost  else "no",  value_color=ghost_value_color)


def draw_instructions(surface):
    columns = [
        [
            "SIMULATION",
            "Space         Pause / Resume",
            "M             Cycle collision mode",
            "Alt           Flip gravity sign",
            "R             Reset",
            "I             Toggle this panel",
            "",
            "CAMERA",
            "Scroll        Zoom",
            "Mid drag      Pan",
            "F             Follow nearest",
            "F  (again)    Jump to nearest",
            "Esc           Exit follow",
            "",
            "BODY TOOLS",
            "P             Pin / Unpin",
            "G             Ghost / Solid",
            "Del           Remove highlighted",
        ],
        [
            "SPAWNING",
            "Click         Spawn (drag: direction + vel)",
            "+ / -         Mass",
            "< / >         Spin",
            "[ / ]         Velocity",
            "BACKSPACE     Preserve spawn stats",
            "",
            "SPAWN TYPES",
            "Q             Single body",
            "S             Solar system",
            "C             Cluster",
            "B             Binary (equal)",
            "U             Binary (unequal)",
            "X             Singularity",
            "A             Anomaly",
            "",
            "MODIFIERS  (toggle)",
            "\\             Pinned spawn",
            "Enter         Ghost spawn",
            "",
            "SCALE  (hold modifier)",
            "Ctrl + / -    Mass  (all)",
            "Ctrl [ / ]    Vel   (all)",
            "Shift + / -   Mass  (followed)",
            "Shift [ / ]   Vel   (followed)",
        ],
    ]

    LH      = 16
    PAD     = 10
    col_w   = 250
    row_count = max(len(columns[0]), len(columns[1]))
    panel_h = row_count * LH + PAD * 2 + 22
    panel_w = col_w * 2 + PAD * 3
    panel_x = WIDTH  - panel_w - 10
    panel_y = 10

    bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    bg.fill((6, 8, 24, 220))
    surface.blit(bg, (panel_x, panel_y))
    pygame.draw.rect(surface, PANEL_BORDER_COLOR, (panel_x, panel_y, panel_w, panel_h), 1)
    surface.blit(font_instr_bold.render("CONTROLS  I to close", True, PANEL_TITLE_COLOR),
                 (panel_x + PAD, panel_y + 6))
    pygame.draw.line(surface, PANEL_BORDER_COLOR,
                     (panel_x + 1, panel_y + 20), (panel_x + panel_w - 2, panel_y + 20), 1)

    for col_index, col_lines in enumerate(columns):
        col_x = panel_x + PAD + col_index * (col_w + PAD)
        col_y = panel_y + 22 + PAD
        for line in col_lines:
            if line.isupper() and line.strip():
                rendered = font_instr_bold.render(line, True, (255, 210, 60))
            elif line == "":
                col_y += LH // 2
                continue
            else:
                rendered = font_instr.render(line, True, (155, 195, 255))
            surface.blit(rendered, (col_x, col_y))
            col_y += LH

    credit = font_credit.render("Zid Daniel  2026", True, (100, 130, 180))
    surface.blit(credit, (WIDTH - credit.get_width() - 12, HEIGHT - credit.get_height() - 8))


def draw_feedback(surface, state):
    rows = []

    if state["paused"]:
        rows.append(("PAUSED", "Space to resume", (255, 210, 60)))
    if state["gravity_sign"] == -1:
        rows.append(("GRAVITY", "Repulsive  Alt to restore", (255, 80, 80)))
    if state["follow_mode"] and state["follow_target"]:
        rows.append(("FOLLOW", "F: jump nearest  Esc: exit", (80, 220, 120)))
    if state["preserve_params"]:
        rows.append(("PRESERVE", "+/- mass  [/] vel  Backspace: OFF", (100, 200, 255)))

    keys  = pygame.key.get_pressed()
    ctrl  = keys[pygame.K_LCTRL]  or keys[pygame.K_RCTRL]
    shift = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
    if ctrl:
        rows.append(("CTRL",  "+/- mass   [/] vel  (all bodies)", (200, 140, 255)))
    if shift and state["follow_mode"] and state["follow_target"]:
        rows.append(("SHIFT", "+/- mass   [/] vel  (followed)",   (255, 160, 80)))
    elif shift and not state["follow_mode"]:
        rows.append(("SHIFT", "Follow a body first  (F)",         (180, 100, 60)))

    timed_row = None
    if state["notify_timer"] > 0:
        timed_row = (state["notify_text"], state["notify_color"])

    if not rows and not timed_row:
        return WIDTH // 2

    PAD       = 8
    LH        = 16
    TH        = 18
    label_w   = 72
    panel_w   = label_w + max((font_ui.size(r[1])[0] for r in rows), default=0) + PAD * 2 + 10
    if timed_row:
        panel_w = max(panel_w, font_ui.size(timed_row[0])[0] + PAD * 2 + 20)
    panel_w   = max(panel_w, 240)
    panel_h   = TH + len(rows) * LH + (LH + 4 if timed_row else 0) + PAD

    info_panel_w = 520 if state["show_instructions"] else 0
    panel_x      = (WIDTH - info_panel_w) // 2 - panel_w // 2
    panel_y      = 10

    bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    bg.fill(PANEL_BG_COLOR)
    surface.blit(bg, (panel_x, panel_y))
    pygame.draw.rect(surface, PANEL_BORDER_COLOR, (panel_x, panel_y, panel_w, panel_h), 1)
    surface.blit(font_ui_small_bold.render("STATUS", True, PANEL_TITLE_COLOR), (panel_x + PAD, panel_y + 4))
    pygame.draw.line(surface, PANEL_BORDER_COLOR,
                     (panel_x + 1, panel_y + TH), (panel_x + panel_w - 2, panel_y + TH), 1)

    row_y = panel_y + TH + 4
    for label, value, color in rows:
        surface.blit(font_ui.render(label, True, LABEL_COLOR), (panel_x + PAD, row_y))
        surface.blit(font_ui.render(value, True, color),       (panel_x + PAD + label_w, row_y))
        row_y += LH

    if timed_row:
        if rows:
            pygame.draw.line(surface, SECTION_LINE_COLOR,
                             (panel_x + PAD, row_y + 1), (panel_x + panel_w - PAD, row_y + 1), 1)
            row_y += 4
        notif_surf = font_ui.render(timed_row[0], True, timed_row[1])
        notif_surf.set_alpha(min(255, state["notify_timer"] * 5))
        surface.blit(notif_surf, (panel_x + PAD, row_y))

    return panel_x


def draw_hud(surface, bodies, fps, frame, paused, state):
    from physics import MAX_BODIES
    PAD   = 8
    LH    = 16
    TH    = 20
    pw    = 210
    rows  = [
        ("FPS",    f"{fps:>5.0f}",                                               (180, 220, 255)),
        ("Bodies", f"{len(bodies)}/{MAX_BODIES}",                                (180, 220, 255)),
        ("Zoom",   f"{state['zoom']:.2f}x",                                      (180, 220, 255)),
        ("Mass",   f"{sum(b.mass for b in bodies):.0f}",                         (180, 220, 255)),
        ("KE",     f"{sum(0.5*b.mass*(b.vx**2+b.vy**2) for b in bodies):.0f}",  (180, 220, 255)),
        ("State",  "PAUSED" if paused else "running" + "." * ((frame // 20) % 4),
                   (255, 200, 80) if paused else (100, 180, 100)),
    ]
    ph = TH + len(rows) * LH + PAD
    draw_panel(surface, 10, 10, pw, ph, "RETROGRADE")
    row_y = 10 + TH + 4
    for label, value, color in rows:
        surface.blit(font_hud.render(label, True, LABEL_COLOR), (20, row_y))
        surface.blit(font_hud.render(value, True, color),       (20 + 70, row_y))
        row_y += LH

    surface.blit(font_hint.render("Space: Pause    R: Reset    I: Info", True, (130, 160, 220)),
                 (12, HEIGHT - font_hint.get_height() - 8))

    if state["notify_timer"] > 0:
        alpha     = min(100, state["notify_timer"] * 3)
        notif     = font_ui_small.render(state["notify_text"], True, (80, 80, 100))
        notif.set_alpha(alpha)
        surface.blit(notif, (14, HEIGHT - 26))

    draw_feedback(surface, state)
    if state["show_instructions"]:
        draw_instructions(surface)
    else:
        draw_spawn_status(surface, state)
