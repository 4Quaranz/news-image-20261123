#!/usr/bin/env python3
"""Draw a newspaper front page summing up 23 November 2026 world news.

Pure Python standard library only. Builds a 1024x1024 pixel buffer,
draws shapes and text with a hand-written 5x7 bitmap font, and encodes
the PNG by hand with zlib and struct. Deterministic: no random elements,
no clock, no network, no files read.
"""
import binascii
import math
import os
import struct
import zlib

W = 1024
H = 1024
PAPER = (246, 242, 230)
INK = (16, 16, 16)
RED = (178, 24, 24)
DARK = (74, 74, 74)
WHITE = (255, 255, 255)
BLUE = (28, 60, 170)
LIGHT = (230, 224, 208)
GOLD = (176, 128, 28)
TEAL = (14, 116, 110)

# 5x7 bitmap font. Each glyph is 7 rows of 5 characters, '#' = on.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    "-": ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "%": ["10001", "10010", "00100", "01000", "01001", "10001", "10001"],
}

buf = bytearray(W * H * 3)
for _i in range(W * H):
    buf[_i * 3] = PAPER[0]
    buf[_i * 3 + 1] = PAPER[1]
    buf[_i * 3 + 2] = PAPER[2]


def px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        _o = (y * W + x) * 3
        buf[_o] = color[0]
        buf[_o + 1] = color[1]
        buf[_o + 2] = color[2]


def fill_rect(x, y, w, h, color):
    for _yy in range(y, y + h):
        for _xx in range(x, x + w):
            px(_xx, _yy, color)


def rect_outline(x, y, w, h, color, thick=2):
    fill_rect(x, y, w, thick, color)
    fill_rect(x, y + h - thick, w, thick, color)
    fill_rect(x, y, thick, h, color)
    fill_rect(x + w - thick, y, thick, h, color)


def line(x0, y0, x1, y1, color):
    _dx = abs(x1 - x0)
    _dy = -abs(y1 - y0)
    _sx = 1 if x0 < x1 else -1
    _sy = 1 if y0 < y1 else -1
    _err = _dx + _dy
    while True:
        px(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        _e2 = 2 * _err
        if _e2 >= _dy:
            _err += _dy
            x0 += _sx
        if _e2 <= _dx:
            _err += _dx
            y0 += _sy


def circle(cx, cy, r, color, filled=False):
    if filled:
        for _dy in range(-r, r + 1):
            _dx = int(math.sqrt(max(0, r * r - _dy * _dy)))
            for _xx in range(cx - _dx, cx + _dx + 1):
                px(_xx, cy + _dy, color)
    else:
        for _a in range(360):
            _rad = math.radians(_a)
            px(cx + int(r * math.cos(_rad)), cy + int(r * math.sin(_rad)), color)


def fill_polygon(points, color):
    _ys = [p[1] for p in points]
    for _y in range(min(_ys), max(_ys) + 1):
        _xs = []
        for _i in range(len(points)):
            _x1, _y1 = points[_i]
            _x2, _y2 = points[(_i + 1) % len(points)]
            if (_y1 <= _y < _y2) or (_y2 <= _y < _y1):
                _xs.append(_x1 + (_y - _y1) * (_x2 - _x1) / (_y2 - _y1))
        _xs.sort()
        for _k in range(0, len(_xs) - 1, 2):
            for _xx in range(int(_xs[_k]), int(_xs[_k + 1]) + 1):
                px(_xx, _y, color)


def star_points(cx, cy, r_out, r_in):
    _pts = []
    for _i in range(10):
        _r = r_out if _i % 2 == 0 else r_in
        _ang = math.radians(-90 + _i * 36)
        _pts.append((cx + int(_r * math.cos(_ang)), cy + int(_r * math.sin(_ang))))
    return _pts


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def draw_text(x, y, text, scale, color):
    text = text.upper()
    _cx = x
    for _ch in text:
        _glyph = FONT.get(_ch, FONT[" "])
        for _row in range(7):
            for _col in range(5):
                if _glyph[_row][_col] == "1":
                    fill_rect(_cx + _col * scale, y + _row * scale, scale, scale, color)
        _cx += 6 * scale
    return _cx


def draw_text_center(x, y, w, text, scale, color):
    _tw = text_width(text, scale)
    draw_text(x + (w - _tw) // 2, y, text, scale, color)


def wrap(text, max_w, scale):
    _words = text.split(" ")
    _lines = []
    _cur = ""
    for _wd in _words:
        _try = (_cur + " " + _wd).strip()
        if text_width(_try, scale) <= max_w:
            _cur = _try
        else:
            if _cur:
                _lines.append(_cur)
            _cur = _wd
    if _cur:
        _lines.append(_cur)
    return _lines


def pictogram(kind, x, y, w, h):
    _cx = x + w // 2
    _cy = y + h // 2
    if kind == "cop31":
        # Cracked earth globe: globe with a jagged crack, sun behind.
        circle(_cx, _cy, 44, GOLD, filled=True)
        circle(_cx, _cy, 38, TEAL, filled=True)
        fill_polygon([(_cx - 20, _cy - 30), (_cx - 4, _cy - 12),
                      (_cx - 18, _cy + 2), (_cx + 2, _cy + 18),
                      (_cx - 8, _cy + 34)], LIGHT)
        line(_cx - 26, _cy - 34, _cx - 6, _cy - 8, INK)
        line(_cx - 6, _cy - 8, _cx - 22, _cy + 12, INK)
        line(_cx - 22, _cy + 12, _cx + 4, _cy + 34, INK)
        fill_polygon(star_points(_cx + 52, y + 20, 15, 6), RED)
    elif kind == "hormuz":
        # Oil tanker on waves, smoke plume, mine star.
        fill_rect(x + 8, y + h - 24, w - 16, 3, BLUE)
        fill_rect(x + 8, y + h - 14, w - 16, 3, BLUE)
        _hull = [(x + 26, _cy + 8), (x + w - 26, _cy + 8),
                 (x + w - 52, _cy + 32), (x + 52, _cy + 32)]
        fill_polygon(_hull, INK)
        fill_rect(_cx - 34, _cy - 12, 30, 20, RED)
        fill_rect(_cx + 8, _cy - 6, 22, 14, WHITE)
        rect_outline(_cx + 8, _cy - 6, 22, 14, INK, 2)
        line(_cx + 40, _cy + 8, _cx + 40, _cy - 24, INK)
        fill_polygon(star_points(x + w - 44, y + 22, 18, 8), RED)
        circle(x + w - 44, y + 22, 4, GOLD, filled=True)
    elif kind == "libya":
        # Warship listing hard to one side, waves, explosion star.
        fill_rect(x + 8, y + h - 22, w - 16, 3, BLUE)
        fill_rect(x + 8, y + h - 12, w - 16, 3, BLUE)
        _hull = [(x + 30, _cy - 2), (x + w - 24, _cy + 22),
                 (x + w - 48, _cy + 40), (x + 56, _cy + 26)]
        fill_polygon(_hull, INK)
        line(_cx - 30, _cy - 2, _cx - 30, _cy - 30, INK)
        line(_cx - 30, _cy - 30, _cx + 6, _cy - 18, RED)
        fill_polygon(star_points(_cx + 46, y + 18, 20, 8), GOLD)
        circle(_cx + 46, y + 18, 5, RED, filled=True)
    elif kind == "ukraine":
        # Damaged apartment block, broken windows, falling debris.
        fill_rect(_cx - 42, _cy - 34, 84, 68, LIGHT)
        rect_outline(_cx - 42, _cy - 34, 84, 68, INK, 3)
        for _wy in (-22, 2):
            for _wx in (-30, -6, 18):
                fill_rect(_cx + _wx, _cy + _wy, 14, 12, INK)
        fill_polygon([(_cx - 42, _cy - 34), (_cx - 10, _cy - 34),
                      (_cx - 26, _cy - 10), (_cx - 42, _cy - 6)], RED)
        for _dx, _dy in [(52, 30), (60, 12), (44, -6)]:
            circle(_cx + _dx, _cy + _dy, 3, RED, filled=True)
        fill_polygon(star_points(_cx - 58, y + 16, 14, 6), GOLD)
    elif kind == "mercury":
        # Small cratered planet on an orbit ring, probe dot.
        circle(_cx, _cy, 46, LIGHT)
        circle(_cx, _cy, 40, GOLD, filled=True)
        for _dx, _dy, _r in [(-14, -10, 7), (10, 6, 9), (-2, 16, 5), (16, -16, 4)]:
            circle(_cx + _dx, _cy + _dy, _r, (140, 96, 20), filled=True)
        circle(_cx, _cy, 46, INK)
        circle(_cx + 58, _cy - 40, 5, RED, filled=True)
        line(_cx + 58, _cy - 40, _cx + 34, _cy - 22, RED)
    elif kind == "houthi":
        # Refinery towers with flame and smoke.
        fill_rect(_cx - 52, _cy - 6, 16, 40, INK)
        fill_rect(_cx - 26, _cy - 20, 16, 54, INK)
        fill_rect(_cx + 2, _cy + 4, 16, 30, INK)
        fill_rect(_cx + 28, _cy - 12, 16, 46, INK)
        fill_polygon([(_cx - 18, _cy - 20), (_cx - 30, _cy - 44),
                      (_cx - 6, _cy - 44), (_cx - 18, _cy - 20)], RED)
        fill_polygon([(_cx + 36, _cy - 12), (_cx + 24, _cy - 36),
                      (_cx + 48, _cy - 36), (_cx + 36, _cy - 12)], GOLD)
        circle(_cx - 44, _cy - 40, 7, DARK, filled=True)
        circle(_cx + 52, _cy - 34, 6, DARK, filled=True)
    elif kind == "factory":
        # Factory with sawtooth roof and big flame.
        fill_rect(_cx - 56, _cy - 2, 112, 36, LIGHT)
        rect_outline(_cx - 56, _cy - 2, 112, 36, INK, 3)
        fill_polygon([(_cx - 56, _cy - 2), (_cx - 28, _cy - 26),
                      (_cx, _cy - 2), (_cx + 28, _cy - 26),
                      (_cx + 56, _cy - 2)], INK)
        fill_polygon([(_cx - 12, _cy - 2), (_cx - 26, _cy - 34),
                      (_cx - 2, _cy - 52), (_cx + 14, _cy - 30),
                      (_cx + 10, _cy - 2)], RED)
        fill_polygon([(_cx - 4, _cy - 2), (_cx - 12, _cy - 22),
                      (_cx + 2, _cy - 34), (_cx + 8, _cy - 2)], GOLD)
    elif kind == "castle":
        # Shuri Castle: red tiered roof, stone base.
        fill_rect(_cx - 48, _cy + 6, 96, 28, LIGHT)
        rect_outline(_cx - 48, _cy + 6, 96, 28, INK, 3)
        fill_polygon([(_cx - 58, _cy + 6), (_cx, _cy - 34),
                      (_cx + 58, _cy + 6)], RED)
        fill_polygon([(_cx - 40, _cy - 26), (_cx, _cy - 52),
                      (_cx + 40, _cy - 26)], RED)
        fill_rect(_cx - 4, _cy - 58, 8, 10, GOLD)
        for _wx in (-34, -10, 14):
            fill_rect(_cx + _wx, _cy + 14, 12, 12, INK)


def panel(x, y, w, h, kicker, headline, head_scale, summary, kind, date_tag):
    fill_rect(x, y, w, h, WHITE)
    rect_outline(x, y, w, h, INK, 3)
    fill_rect(x, y, w, 30, RED)
    draw_text(x + 12, y + 8, kicker, 2, WHITE)
    fill_rect(x + w - 112, y + 3, 100, 24, WHITE)
    draw_text_center(x + w - 112, y + 9, 100, date_tag, 2, RED)
    _lines = wrap(headline, w - 24, head_scale)
    _hy = y + 42
    for _ln in _lines:
        draw_text(x + 12, _hy, _ln, head_scale, INK)
        _hy += 7 * head_scale + 6
    _pic_y = _hy + 4
    _pic_h = 92 if w > 400 else 78
    pictogram(kind, x + 12, _pic_y, w - 24, _pic_h)
    _sy = _pic_y + _pic_h + 8
    for _ln in wrap(summary, w - 24, 2):
        draw_text(x + 12, _sy, _ln, 2, DARK)
        _sy += 18


def lead_panel(x, y, w, h):
    fill_rect(x, y, w, h, WHITE)
    rect_outline(x, y, w, h, INK, 3)
    fill_rect(x, y, w, 34, RED)
    draw_text(x + 14, y + 9, "CLIMATE - COP31 COLLAPSES", 2, WHITE)
    fill_rect(x + w - 118, y + 4, 104, 26, WHITE)
    draw_text_center(x + w - 118, y + 10, 104, "22 NOV", 2, RED)
    draw_text(x + 14, y + 48, "NO DEAL ON FOSSIL FUELS", 4, INK)
    draw_text(x + 14, y + 84, "AS LONGEST COP EVER ENDS", 4, INK)
    pictogram("cop31", x + w - 240, y + 46, 220, 120)
    for _i, _ln in enumerate(wrap(
            "Antalya: EU and 100+ states reject the Antalya Pact - it never mentions fossil fuels. "
            "Guterres 'deeply disappointed'. Worst COP since 2009.", w - 280, 2)):
        draw_text(x + 14, y + 122 + _i * 18, _ln, 2, DARK)


def draw_page():
    draw_text_center(0, 24, W, "THE WORLD TODAY", 8, INK)
    fill_rect(24, 94, W - 48, 3, INK)
    draw_text_center(0, 106, W, "23 NOVEMBER 2026", 3, RED)
    draw_text_center(0, 132, W, "MONDAY - WORLD NEWS IN ONE IMAGE", 2, DARK)
    fill_rect(24, 154, W - 48, 4, INK)
    lead_panel(24, 168, 976, 196)
    panel(24, 380, 488, 280, "STRAIT OF HORMUZ",
          "25 TANKERS HIT IN 7 DAYS", 3,
          "3 struck Fri-Sat, 2 more hit mines Sun. Shipping attacks at highest level since war began.",
          "hormuz", "23 NOV")
    panel(528, 380, 472, 280, "LIBYA - BENGHAZI",
          "RUSSIAN WARSHIP SUNK BY SEA DRONES", 3,
          "Corvette Merkury capsizes at naval base. 10 hurt. Kyiv, Moscow silent.",
          "libya", "22 NOV")
    panel(24, 676, 314, 200, "UKRAINE",
          "DRONE HITS DYMER FLAT", 2,
          "2 killed, 11 missing north of Kyiv.",
          "ukraine", "23 NOV")
    panel(354, 676, 314, 200, "SPACE",
          "MERCURY ORBIT REACHED", 2,
          "8-year trip ends: only 2nd ever in orbit.",
          "mercury", "21 NOV")
    panel(684, 676, 316, 200, "SAUDI ARABIA",
          "HOUTHIS HIT REFINERY", 2,
          "Saudi refinery and radar hit, 3rd day running.",
          "houthi", "23 NOV")
    fill_rect(24, 892, 488, 76, WHITE)
    rect_outline(24, 892, 488, 76, INK, 3)
    draw_text(36, 902, "INDONESIA - FACTORY FIRE", 2, RED)
    for _i, _ln in enumerate(wrap("Candy factory blaze in Cikande, Banten: 24 dead.", 488 - 24, 2)):
        draw_text(36, 928 + _i * 18, _ln, 2, DARK)
    fill_rect(528, 892, 472, 76, WHITE)
    rect_outline(528, 892, 472, 76, INK, 3)
    draw_text(540, 902, "JAPAN - SHURI CASTLE REOPENS", 2, RED)
    for _i, _ln in enumerate(wrap("Restored main hall opens to public, 7 years after fire.", 472 - 24, 2)):
        draw_text(540, 928 + _i * 18, _ln, 2, DARK)
    fill_rect(24, 980, W - 48, 2, INK)
    draw_text_center(0, 992, W, "SOURCES: REUTERS, BBC, AP, CNN, UN NEWS - 23 NOV 2026", 2, DARK)


def chunk(kind, data):
    _out = struct.pack(">I", len(data)) + kind + data
    _out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return _out


def encode_png():
    _raw = bytearray()
    for _y in range(H):
        _raw.append(0)
        _raw.extend(buf[_y * W * 3:(_y + 1) * W * 3])
    _ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    _png = b"\x89PNG\r\n\x1a\n"
    _png += chunk(b"IHDR", _ihdr)
    _png += chunk(b"IDAT", zlib.compress(bytes(_raw), 9))
    _png += chunk(b"IEND", b"")
    return _png


def main():
    draw_page()
    _out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(_out_dir, exist_ok=True)
    with open(os.path.join(_out_dir, "entry.png"), "wb") as _f:
        _f.write(encode_png())


if __name__ == "__main__":
    main()
