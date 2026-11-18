#!/usr/bin/env python3
"""news-image-20261117: draw one image summing up the world news of
Tuesday 17 November 2026 and write it to /output/entry.png
(or $MAKEFUN_OUTPUT_DIR when that is set).

Pure Python 3 standard library, no network, fully deterministic:
the same bytes come out on every run.

The image is a newspaper front page, 1024x1024. A navy masthead names
the day, one wide hero panel carries the day's biggest story, four
panels below carry four more, and a red ticker band adds a sixth.
Every story happened, or was first reported, on Tuesday 17 November
2026 (BBC / Reuters / Al Jazeera / AP reports and same-day digests):

  HERO  Ukraine's strike collapses part of the Kerch bridge linking
        Russia to Crimea; Zelenskyy hails an "unprecedented
        operation"; Russian missiles hit Kyiv's Dnipro bridges in
        reply, cutting heat, water and power.
  1     Iran's IRGC says two tankers hit naval mines in the Strait of
        Hormuz (a claim not independently verified); a third US
        aircraft carrier arrives in the region, and Bahrain says it
        intercepted Iranian drones aimed at a US radar base.
  2     Trump lands in Manila for the ASEAN summit, first stop of an
        Asia trip that ends in China with talks alongside Xi Jinping
        and Vladimir Putin; a US-Thailand trade statement is signed.
  3     Nvidia reports its first earnings since CEO Jensen Huang's
        resignation, after Tuesday's close.
  4     Delegates of 128 states at the UN in Geneva debate drafting a
        treaty to ban lethal autonomous weapons ("killer robots").
  TICKER  A ULA Vulcan rocket failure destroys 40 Amazon Leo
        internet satellites.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- font
# 5x7 bitmap font stored as bit rows: each glyph is 7 integers, and in
# each integer bit 4 is the leftmost of the 5 columns, bit 0 the last.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1C, 0x12, 0x11, 0x11, 0x11, 0x12, 0x1C),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x11, 0x19, 0x15, 0x13, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x0E, 0x11, 0x01, 0x06, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x0E, 0x10, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x01, 0x0E),
    " ": (0, 0, 0, 0, 0, 0, 0),
    "-": (0, 0, 0, 0x0E, 0, 0, 0),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x0C, 0x08),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0x08),
    "+": (0, 0x04, 0x04, 0x0E, 0x04, 0x04, 0),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "/": (0x01, 0x02, 0x02, 0x04, 0x08, 0x08, 0x10),
    "?": (0x0E, 0x11, 0x01, 0x06, 0x04, 0, 0x04),
}

# ------------------------------------------------------------- colours
PAPER = (247, 243, 234)
WHITE = (255, 255, 255)
INK = (20, 26, 38)
NAVY = (20, 33, 61)
GOLD = (242, 193, 78)
RED = (179, 0, 27)
PANEL_LINE = (96, 102, 112)
SKY = (198, 220, 242)
SEA = (42, 109, 176)
SEA_LT = (120, 175, 220)
STEEL = (70, 80, 92)
STEEL_LT = (148, 156, 166)
SMOKE = (168, 172, 178)
FIRE = (240, 140, 30)
FIRE_LT = (250, 200, 60)
UA_BLUE = (0, 91, 187)
UA_YELLOW = (255, 213, 0)
GREEN = (118, 185, 0)
UN_BLUE = (0, 91, 172)

# -------------------------------------------------------------- canvas
PIX = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PIX[i] = c[0]
        PIX[i + 1] = c[1]
        PIX[i + 2] = c[2]


def rect(x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            px(xx, yy, c)


def circle(cx, cy, r, c):
    r2 = r * r
    for yy in range(cy - r, cy + r + 1):
        dy = yy - cy
        for xx in range(cx - r, cx + r + 1):
            dx = xx - cx
            if dx * dx + dy * dy <= r2:
                px(xx, yy, c)


def ring(cx, cy, r, thick, c):
    lo = (r - thick) * (r - thick)
    hi = r * r
    for yy in range(cy - r, cy + r + 1):
        dy = yy - cy
        for xx in range(cx - r, cx + r + 1):
            dx = xx - cx
            d2 = dx * dx + dy * dy
            if lo < d2 <= hi:
                px(xx, yy, c)


def semicircle(cx, cy, r, c):
    """Filled upper half-disc: flat base along y=cy, dome above it."""
    r2 = r * r
    for yy in range(cy - r, cy + 1):
        dy = yy - cy
        for xx in range(cx - r, cx + r + 1):
            dx = xx - cx
            if dx * dx + dy * dy <= r2:
                px(xx, yy, c)


def polygon(points, c):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    n = len(points)
    for yy in range(min(ys), max(ys) + 1):
        nodes = []
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            if (y1 <= yy < y2) or (y2 <= yy < y1):
                nodes.append(x1 + (yy - y1) * (x2 - x1) // (y2 - y1))
        nodes.sort()
        for i in range(0, len(nodes) - 1, 2):
            for xx in range(nodes[i], nodes[i + 1] + 1):
                px(xx, yy, c)


def line(x0, y0, x1, y1, w, c):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    r = max(w // 2, 1)
    for i in range(steps + 1):
        x = x0 + (x1 - x0) * i // steps
        y = y0 + (y1 - y0) * i // steps
        circle(x, y, r, c)


def star(cx, cy, r_out, r_in, c):
    """Filled 8-point burst, used for explosions and flames."""
    import math
    pts = []
    for i in range(16):
        a = i * math.pi / 8.0
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + int(r * math.cos(a)), cy + int(r * math.sin(a))))
    polygon(pts, c)


def text(s, cx, y, scale, c, bold=False):
    """Draw s centred at cx, top edge at y. Advance is 6*scale a glyph."""
    adv = 6 * scale
    width = len(s) * adv - scale
    x = cx - width // 2
    dx = max(1, scale // 2) if bold else 0
    for ch in s:
        glyph = FONT[ch]
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (0x10 >> col):
                    rect(x + col * scale, y + row * scale, scale, scale, c)
                    if dx:
                        rect(x + col * scale + dx, y + row * scale,
                             scale, scale, c)
        x += adv


def text_xy(s, x, y, scale, c):
    adv = 6 * scale
    for ch in s:
        glyph = FONT[ch]
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (0x10 >> col):
                    rect(x + col * scale, y + row * scale, scale, scale, c)
        x += adv


# ---------------------------------------------------------- PNG writer
def png_bytes():
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    raw = bytearray()
    stride = W * 3
    for yy in range(H):
        raw.append(0)  # filter: none
        raw += PIX[yy * stride:(yy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# --------------------------------------------------------------- icons
# Hero scene: the Kerch bridge, drawn inside the hero panel whose
# top-left corner is (x, y); the scene zone is 992 wide, y .. y+184.

def scene_bridge(x, y):
    deck_y = y + 118
    sea_y = y + 140
    # sky and sea
    rect(x, y, 992, sea_y - y, SKY)
    rect(x, sea_y, 992, y + 184 - sea_y, SEA)
    for wx, wy in ((70, 156), (250, 168), (470, 158), (760, 170),
                   (880, 156), (560, 174), (150, 176)):
        rect(x + wx, y + wy, 40, 3, SEA_LT)
    circle(x + 900, y + 30, 17, FIRE_LT)                 # low sun
    # bridge towers (pylons) and deck
    for tx in (300, 636):
        rect(x + tx, y + 34, 14, deck_y - (y + 34), STEEL)
        rect(x + tx - 5, y + 30, 24, 8, STEEL)
    rect(x + 24, deck_y, 592, 9, STEEL)                  # deck, left run
    rect(x + 806, deck_y, 162, 9, STEEL)                 # deck, right run
    rect(x + 24, deck_y + 9, 944, 3, STEEL_LT)           # deck shadow line
    # cable stays from both tower tops
    for tx, spans in ((307, (60, 140, 220, 470, 540)),
                      (643, (400, 470, 830, 900, 950))):
        for sx in spans:
            line(x + tx, y + 36, x + sx, deck_y, 2, STEEL_LT)
    # the fallen span: a deck segment tipped down into the sea
    polygon([(x + 616, deck_y), (x + 806, deck_y + 34),
             (x + 800, deck_y + 44), (x + 616, deck_y + 10)], STEEL)
    line(x + 700, deck_y + 22, x + 700, sea_y + 16, 3, SEA_LT)  # splash
    line(x + 748, deck_y + 30, x + 748, sea_y + 12, 3, SEA_LT)
    # explosion burst and smoke at the break
    star(x + 618, deck_y - 4, 26, 11, FIRE)
    circle(x + 618, deck_y - 4, 9, FIRE_LT)
    circle(x + 600, y + 62, 14, SMOKE)
    circle(x + 622, y + 50, 18, SMOKE)
    circle(x + 650, y + 40, 22, (186, 190, 196))
    # a small drone that did it, upper left, dotted path to the break
    dcx, dcy = x + 128, y + 34
    circle(dcx, dcy, 6, INK)
    for rx, ry in ((106, 24), (150, 24), (106, 46), (150, 46)):
        ring(x + rx, y + ry, 7, 2, INK)
        line(dcx, dcy, x + rx, y + ry, 3, INK)
    circle(dcx, dcy, 3, RED)
    for i in range(9):
        px(x + 190 + i * 46, y + 44 + i * 7, INK)
        px(x + 191 + i * 46, y + 44 + i * 7, INK)
        px(x + 190 + i * 46, y + 45 + i * 7, INK)
    # Ukrainian flag flying from the left tower
    rect(x + 288, y + 8, 4, 26, INK)
    rect(x + 292, y + 8, 36, 9, UA_BLUE)
    rect(x + 292, y + 17, 36, 9, UA_YELLOW)


# Panel icons draw inside a panel whose top-left corner is (x, y);
# the icon zone is roughly y+12 .. y+108, panel width 488.

def icon_tanker(x, y):
    sea_y = y + 78
    rect(x + 16, sea_y, 456, 30, SEA)
    for wx, wy in ((40, 88), (200, 96), (330, 86), (420, 98)):
        rect(x + wx, y + wy, 30, 3, SEA_LT)
    # aircraft carrier behind, grey and smaller: flat deck and island
    polygon([(x + 52, y + 66), (x + 300, y + 66), (x + 282, y + 52),
             (x + 66, y + 52)], STEEL_LT)
    rect(x + 58, y + 47, 236, 6, STEEL)
    rect(x + 238, y + 30, 20, 17, STEEL)
    rect(x + 244, y + 22, 8, 8, STEEL)
    # the tanker in front: black topsides over a red hull, bow right
    polygon([(x + 120, y + 84), (x + 428, y + 84), (x + 452, y + 66),
             (x + 452, y + 58), (x + 120, y + 58)], INK)
    polygon([(x + 120, y + 84), (x + 428, y + 84), (x + 440, y + 72),
             (x + 120, y + 72)], RED)
    rect(x + 132, y + 50, 300, 8, STEEL_LT)              # deck line
    rect(x + 128, y + 30, 34, 22, WHITE)                 # superstructure
    rect(x + 134, y + 35, 22, 5, NAVY)                   # bridge windows
    rect(x + 168, y + 38, 10, 14, STEEL)                 # funnel
    line(x + 300, y + 56, x + 300, y + 28, 4, STEEL)     # mast
    line(x + 300, y + 28, x + 330, y + 40, 3, STEEL)
    # a naval mine in the water by the bow, and a small fire at it
    circle(x + 446, y + 96, 9, INK)
    for dx, dy in ((-12, 0), (12, 0), (0, -12), (-9, -9), (9, -9)):
        line(x + 446, y + 96, x + 446 + dx, y + 96 + dy, 3, INK)
    star(x + 428, y + 62, 13, 6, FIRE)
    circle(x + 428, y + 62, 4, FIRE_LT)


def icon_plane(x, y):
    # a presidential jet in side view, white over a blue belly
    polygon([(x + 108, y + 44), (x + 150, y + 30), (x + 330, y + 26),
             (x + 396, y + 36), (x + 404, y + 44), (x + 396, y + 52),
             (x + 150, y + 56), (x + 112, y + 52)], WHITE)
    polygon([(x + 112, y + 50), (x + 398, y + 44), (x + 396, y + 52),
             (x + 150, y + 56)], (43, 108, 178))
    polygon([(x + 108, y + 44), (x + 84, y + 20), (x + 104, y + 18),
             (x + 130, y + 38)], (43, 108, 178))          # tail fin
    rect(x + 92, y + 24, 16, 4, WHITE)
    polygon([(x + 216, y + 52), (x + 262, y + 76), (x + 286, y + 76),
             (x + 258, y + 52)], STEEL_LT)                 # wing
    circle(x + 246, y + 62, 7, STEEL)                      # engine
    for i in range(9):                                     # windows
        rect(x + 176 + i * 20, y + 38, 8, 5, NAVY)
    rect(x + 372, y + 36, 12, 5, NAVY)                     # cockpit
    # two flags on poles below: the United States and the Philippines
    for fx in (x + 140, x + 316):
        rect(fx - 2, y + 66, 4, 40, INK)
    fx = x + 142
    for i in range(6):
        rect(fx, y + 66 + i * 4, 56, 4, RED if i % 2 == 0 else WHITE)
    rect(fx, y + 66, 26, 12, NAVY)
    for r in range(2):
        for cix in range(3):
            rect(fx + 4 + cix * 7, y + 69 + r * 6, 3, 3, WHITE)
    fx = x + 318
    rect(fx, y + 66, 56, 12, (0, 56, 147))                 # blue over red
    rect(fx, y + 78, 56, 12, (206, 17, 38))
    polygon([(fx, y + 66), (fx + 22, y + 78), (fx, y + 90)], WHITE)
    circle(fx + 8, y + 78, 4, GOLD)                        # the sun
    rect(x + 96, y + 104, 296, 4, PANEL_LINE)              # ground line


def icon_chip(x, y):
    cx, cy = x + 244, y + 58
    # circuit traces running out of the chip to solder dots
    for sx, sy, ex, ey in ((190, 30, 130, 16), (190, 86, 124, 98),
                           (298, 30, 358, 16), (298, 86, 364, 98),
                           (244, 14, 244, 4), (160, 58, 108, 58),
                           (328, 58, 380, 58)):
        line(x + sx, y + sy, x + ex, y + ey, 3, STEEL_LT)
        circle(x + ex, y + ey, 4, STEEL_LT)
    # pins on all four sides
    for i in range(5):
        rect(cx - 44 + i * 20, cy - 52, 8, 12, STEEL)
        rect(cx - 44 + i * 20, cy + 40, 8, 12, STEEL)
        rect(cx - 66, cy - 36 + i * 18, 12, 8, STEEL)
        rect(cx + 54, cy - 36 + i * 18, 12, 8, STEEL)
    # the chip body and its green core, marked AI
    rect(cx - 54, cy - 40, 108, 80, INK)
    rect(cx - 34, cy - 24, 68, 48, GREEN)
    text("AI", cx, cy - 14, 4, INK, bold=True)


def icon_robot(x, y):
    import math
    cx, cy = x + 244, y + 58
    # a UN-blue roundel: meridians, parallels and a rim
    circle(cx, cy, 47, UN_BLUE)
    ring(cx, cy, 47, 3, WHITE)
    for dy in (-24, 0, 24):
        hw = int(math.sqrt(47 * 47 - dy * dy)) - 3
        line(cx - hw, cy + dy, cx + hw, cy + dy, 2, WHITE)
    for i in range(41):
        a = i * math.pi / 20.0
        ex = cx + int(19 * math.cos(a))
        ey = cy + int(44 * math.sin(a))
        rect(ex - 1, ey - 1, 2, 2, WHITE)
    # the robot in front of it: head, antenna, eyes, grille mouth
    rect(cx - 36, cy - 20, 72, 56, WHITE)
    rect(cx - 42, cy - 6, 6, 26, STEEL_LT)                # ears
    rect(cx + 36, cy - 6, 6, 26, STEEL_LT)
    line(cx, cy - 20, cx, cy - 34, 4, INK)                # antenna
    circle(cx, cy - 38, 6, RED)
    circle(cx - 17, cy - 2, 6, INK)                       # eyes
    circle(cx + 17, cy - 2, 6, INK)
    circle(cx - 17, cy - 2, 2, (80, 200, 230))
    circle(cx + 17, cy - 2, 2, (80, 200, 230))
    for i in range(4):                                    # mouth grille
        rect(cx - 15 + i * 9, cy + 16, 4, 10, INK)
    rect(cx - 24, cy + 36, 48, 10, STEEL)                 # shoulders


# ------------------------------------------------------------- compose
def panel(x, y, draw, accent, head1, head2, detail):
    rect(x, y, 488, 236, WHITE)
    rect(x, y, 488, 6, accent)
    rect(x, y, 488, 2, PANEL_LINE)
    rect(x, y + 234, 488, 2, PANEL_LINE)
    rect(x, y, 2, 236, PANEL_LINE)
    rect(x + 486, y, 2, 236, PANEL_LINE)
    draw(x, y)
    cx = x + 244
    text(head1, cx, y + 116, 5, INK, bold=True)
    text(head2, cx, y + 156, 5, INK, bold=True)
    text(detail, cx, y + 200, 3, (70, 76, 86))


def compose():
    rect(0, 0, W, H, PAPER)
    # masthead
    rect(0, 0, W, 112, NAVY)
    rect(0, 112, W, 6, GOLD)
    text("THE WORLD TODAY", W // 2, 10, 9, WHITE, bold=True)
    text("TUESDAY 17 NOVEMBER 2026", W // 2, 82, 4, GOLD, bold=True)
    # hero panel: the Crimea bridge
    hx, hy = 16, 134
    rect(hx, hy, 992, 336, WHITE)
    rect(hx, hy, 992, 6, UA_BLUE)
    rect(hx, hy, 992, 2, PANEL_LINE)
    rect(hx, hy + 334, 992, 2, PANEL_LINE)
    rect(hx, hy, 2, 336, PANEL_LINE)
    rect(hx + 990, hy, 2, 336, PANEL_LINE)
    scene_bridge(hx, hy + 10)
    text("UKRAINE STRIKE COLLAPSES", W // 2, hy + 206, 6, INK, bold=True)
    text("PART OF CRIMEA BRIDGE", W // 2, hy + 254, 6, INK, bold=True)
    text("RUSSIAN MISSILES HIT KYIV BRIDGES IN REPLY",
         W // 2, hy + 304, 3, (70, 76, 86))
    # four panels, two by two
    panel(16, 486, icon_tanker, (150, 60, 40),
          "TANKERS HIT IN", "HORMUZ STRAIT",
          "IRAN SAYS NAVAL MINES")
    panel(520, 486, icon_plane, (43, 108, 178),
          "TRUMP LANDS IN", "MANILA: ASEAN",
          "NEXT: XI + PUTIN TALKS")
    panel(16, 738, icon_chip, GREEN,
          "NVIDIA EARNINGS", "1ST SINCE HUANG",
          "CEO JENSEN HUANG HAS QUIT")
    panel(520, 738, icon_robot, UN_BLUE,
          "UN TALKS TO BAN", "KILLER ROBOTS",
          "128 NATIONS IN GENEVA")
    # ticker band
    rect(0, 986, W, 32, RED)
    text("VULCAN ROCKET FAILS - 40 AMAZON SATELLITES LOST",
         W // 2, 992, 3, WHITE, bold=True)


def main():
    compose()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png_bytes())


if __name__ == "__main__":
    main()


