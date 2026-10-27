"""Tudo é desenhado por código (sem imagens externas): itens, mãos, molduras,
salas, campo, casa, jogador e o gato."""
import math
import random

import os

import pygame

import pixel

W, H = 960, 640
TAU = math.tau

# ---------- paleta: tons quentes, pastéis e vívidos ----------
INK = (98, 56, 62)          # texto / contornos
CREAM = (255, 246, 232)
PAPER = (255, 240, 220)
CORAL = (242, 128, 112)
PEACH = (250, 192, 156)
BUTTER = (252, 216, 128)
MINT = (162, 214, 178)
LILAC = (210, 172, 222)
ROSE = (244, 164, 178)
WOOD = (218, 160, 116)
WOOD_D = (172, 112, 82)
DUSK = (74, 42, 52)         # fundo escuro quente (painéis)


# ============================================================ cores / texto
def hexc(s, default=(200, 200, 200)):
    try:
        s = s.lstrip("#")
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:  # noqa: BLE001
        return default


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def lighter(c, t=0.35):
    return mix(c, (255, 255, 255), t)


def darker(c, t=0.35):
    return mix(c, (0, 0, 0), t)


def scale(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def rr(x, y, w, h):
    return pygame.Rect(int(x), int(y), max(1, int(w)), max(1, int(h)))


_fonts = {}


FONT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts", "PixelifySans.ttf")


def font(size, bold=False, italic=False):
    """Fonte pixel (Pixelify Sans, licença OFL). Itálico vira normal (não existe em pixel)."""
    size = max(16, int(size))
    key = (size, bold)
    if key not in _fonts:
        try:
            f = pygame.font.Font(FONT_FILE, size)
        except Exception:  # noqa: BLE001
            f = pygame.font.SysFont("consolas,couriernew,monospace", size)
        f.set_bold(bold)
        _fonts[key] = f
    return _fonts[key]


def wrap(text, f, max_w):
    lines = []
    for para in text.split("\n"):
        line = ""
        for word in para.split(" "):
            test = (line + " " + word).strip()
            if f.size(test)[0] <= max_w:
                line = test
            else:
                if line:
                    lines.append(line)
                line = word
        lines.append(line)
    return lines


def text(surf, s, f, color, pos, anchor="topleft", shadow=None):
    img = f.render(s, False, color)
    r = img.get_rect(**{anchor: (int(pos[0]), int(pos[1]))})
    if shadow:
        surf.blit(f.render(s, False, shadow), r.move(2, 2))
    surf.blit(img, r)
    return r


def notched(surf, rect, color, cut=3):
    """Retângulo com cantos 'mordidos' (estilo pixel)."""
    pygame.draw.rect(surf, color, rect.inflate(-cut * 2, 0))
    pygame.draw.rect(surf, color, rect.inflate(0, -cut * 2))


def panel(surf, rect, color=DUSK, alpha=200, radius=14, border=None):
    rect = pygame.Rect(pixel.snap(rect.x), pixel.snap(rect.y), pixel.snap(rect.w), pixel.snap(rect.h))
    p = pygame.Surface(rect.size, pygame.SRCALPHA)
    if border:
        notched(p, p.get_rect(), (*border, alpha))
        notched(p, p.get_rect().inflate(-6, -6), (*color, alpha))
    else:
        notched(p, p.get_rect(), (*color, alpha))
    surf.blit(p, rect)


def star_pts(cx, cy, ro, ri, n=5, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        r = ro if i % 2 == 0 else ri
        a = rot + i * math.pi / n
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


# ============================================================ brilho
_glow = {}


def glow(radius, color):
    radius = max(4, int(radius) // 4 * 4)
    key = (radius, color)
    if key not in _glow:
        if len(_glow) > 600:
            _glow.clear()
        s = pygame.Surface((radius * 2, radius * 2))
        steps = 5                                    # halo em anéis (pixel)
        for i in range(steps):
            k = ((i + 1) / steps) ** 2 * .9
            pygame.draw.circle(s, scale(color, k), (radius, radius), radius * (1 - i / steps))
        _glow[key] = s
    return _glow[key]


def blit_glow(surf, center, radius, color, strength=1.0):
    k = round(max(0.0, min(1.5, strength)) * 10) / 10
    if k <= 0:
        return
    g = glow(radius, scale(color, k))
    surf.blit(g, g.get_rect(center=(int(center[0]), int(center[1]))), special_flags=pygame.BLEND_RGB_ADD)


def sparkle(surf, x, y, size, color):
    x, y = pixel.snap(x), pixel.snap(y)
    size = max(3, pixel.snap(size))
    pygame.draw.line(surf, color, (x - size, y), (x + size, y), 2)
    pygame.draw.line(surf, color, (x, y - size), (x, y + size), 2)
    s2 = max(1, size // 2)
    pygame.draw.line(surf, color, (x - s2, y - s2), (x + s2, y + s2), 1)
    pygame.draw.line(surf, color, (x - s2, y + s2), (x + s2, y - s2), 1)


# ============================================================ itens
def _orbe(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.34
    pygame.draw.circle(sf, darker(D, .35), (cx, cy), R + 3)
    n = 22
    for i in range(n):
        t = i / (n - 1)
        pygame.draw.circle(sf, mix(D, L, t), (cx - R * .28 * t, cy - R * .28 * t), R * (1 - .82 * t))
    pygame.draw.arc(sf, G, rr(cx - R * .65, cy - R * .25, R * 1.3, R * .9), 0.3, 2.7, 3)
    pygame.draw.arc(sf, lighter(G, .3), rr(cx - R * .5, cy - R * .05, R * 1.0, R * .6), 3.4, 5.9, 2)
    pygame.draw.circle(sf, lighter(L, .7), (cx - R * .4, cy - R * .42), R * .13)


def _cristal(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.4
    top, bot = (cx, cy - R * 1.05), (cx, cy + R * 1.0)
    lu, ld = (cx - R * .5, cy - R * .35), (cx - R * .42, cy + R * .55)
    ru, rd = (cx + R * .5, cy - R * .35), (cx + R * .42, cy + R * .55)
    pygame.draw.polygon(sf, L, [top, lu, ld, bot])
    pygame.draw.polygon(sf, D, [top, ru, rd, bot])
    pygame.draw.polygon(sf, c, [(cx, cy - R * .6), (cx + R * .24, cy), (cx, cy + R * .6), (cx - R * .24, cy)])
    for p in (lu, ru, ld, rd):
        pygame.draw.line(sf, darker(c, .15), p, (cx, cy), 1)
    pygame.draw.polygon(sf, lighter(G, .4), [(cx - R * .14, cy - R * .78), (cx - R * .04, cy - R * .62), (cx - R * .34, cy - R * .22)])
    pygame.draw.polygon(sf, darker(D, .4), [top, ru, rd, bot, ld, lu], 3)


def _chave(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.4
    rc = (cx, cy - R * .55)
    pygame.draw.circle(sf, darker(D, .3), rc, R * .44)
    pygame.draw.circle(sf, c, rc, R * .4)
    pygame.draw.circle(sf, L, (rc[0] - R * .08, rc[1] - R * .08), R * .3, 3)
    pygame.draw.circle(sf, (0, 0, 0, 0), rc, R * .2)
    pygame.draw.circle(sf, G, rc, R * .2, 3)
    pygame.draw.rect(sf, darker(D, .3), rr(cx - R * .11, cy - R * .2, R * .22, R * 1.25))
    pygame.draw.rect(sf, c, rr(cx - R * .07, cy - R * .18, R * .14, R * 1.2))
    pygame.draw.line(sf, L, (cx - R * .03, cy - R * .15), (cx - R * .03, cy + R * .95), 2)
    for yy, ww in ((.72, .38), (.92, .26)):
        r = rr(cx + R * .04, cy + R * yy, R * ww, R * .14)
        pygame.draw.rect(sf, c, r)
        pygame.draw.rect(sf, darker(D, .3), r, 2)
    pygame.draw.circle(sf, G, (cx, cy - R * .02), R * .09)


def _pena(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.44
    left, right, spine = [], [], []
    for i in range(21):
        t = i / 20
        y = cy - R + 1.75 * R * t
        sx = cx + R * .16 * math.sin(t * math.pi * .9)
        w = R * .36 * math.sin(math.pi * min(1.0, t * 1.08)) ** .8
        spine.append((sx, y))
        left.append((sx - w, y))
        right.append((sx + w * .85, y))
    pygame.draw.polygon(sf, darker(D, .2), [(x - 2, y) for x, y in left] + [(x + 2, y) for x, y in right[::-1]])
    pygame.draw.polygon(sf, c, left + right[::-1])
    for i in range(2, 19, 2):
        pygame.draw.line(sf, D, spine[i], left[min(20, i + 2)], 2)
        pygame.draw.line(sf, L, spine[i], right[min(20, i + 2)], 2)
    pygame.draw.lines(sf, lighter(G, .3), False, spine, 3)
    pygame.draw.line(sf, darker(D, .3), spine[-1], (spine[-1][0] - R * .05, cy + R * 1.0), 3)


def _frasco(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.4
    glass = (222, 232, 245)
    bc, br = (cx, cy + R * .3), R * .62
    pygame.draw.circle(sf, (110, 120, 145), bc, br + 3)
    pygame.draw.circle(sf, glass, bc, br)
    liq = pygame.Surface((s, s), pygame.SRCALPHA)
    pygame.draw.circle(liq, c, bc, br - 5)
    pygame.draw.circle(liq, L, (bc[0] - br * .3, bc[1] + br * .2), br * .3)
    liq.fill((0, 0, 0, 0), rr(0, 0, s, bc[1] - br * .2))
    sf.blit(liq, (0, 0))
    pygame.draw.line(sf, G, (bc[0] - br * .92, bc[1] - br * .2), (bc[0] + br * .92, bc[1] - br * .2), 3)
    neck = rr(cx - R * .17, cy - R * .78, R * .34, R * .62)
    pygame.draw.rect(sf, glass, neck)
    pygame.draw.line(sf, (110, 120, 145), neck.topleft, neck.bottomleft, 3)
    pygame.draw.line(sf, (110, 120, 145), neck.topright, neck.bottomright, 3)
    pygame.draw.rect(sf, (150, 100, 62), rr(cx - R * .22, cy - R * .98, R * .44, R * .24), border_radius=4)
    pygame.draw.rect(sf, (110, 70, 40), rr(cx - R * .22, cy - R * .98, R * .44, R * .24), 2, border_radius=4)
    for bx, by, b in ((.1, .45, .07), (-.2, .62, .05), (.25, .7, .04)):
        pygame.draw.circle(sf, lighter(G, .4), (cx + R * bx, cy + R * by), R * b)
    pygame.draw.arc(sf, (255, 255, 255), rr(bc[0] - br * .8, bc[1] - br * .8, br * 1.6, br * 1.6), 2.0, 2.9, 3)


def _livro(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.4
    x0, y0, w, h = cx - R * .62, cy - R * .82, R * 1.24, R * 1.64
    pages = rr(x0 + w * .1, y0 + 5, w * .92, h - 10)
    pygame.draw.rect(sf, (245, 238, 220), pages, border_radius=3)
    for i in range(5):
        pygame.draw.line(sf, (210, 200, 180), (pages.right - 3, pages.top + 4 + i * 3), (pages.right - 3, pages.bottom - 4 - i * 3), 1)
    cover = rr(x0, y0, w * .92, h)
    pygame.draw.rect(sf, c, cover, border_radius=6)
    pygame.draw.rect(sf, darker(D, .3), cover, 3, border_radius=6)
    pygame.draw.rect(sf, D, rr(x0, y0, w * .16, h), border_radius=5)
    ex, ey, e = x0 + w * .54, cy, R * .3
    pygame.draw.polygon(sf, G, [(ex, ey - e), (ex + e * .75, ey), (ex, ey + e), (ex - e * .75, ey)])
    pygame.draw.polygon(sf, lighter(G, .5), [(ex, ey - e * .5), (ex + e * .35, ey), (ex, ey + e * .5), (ex - e * .35, ey)])
    pygame.draw.rect(sf, L, rr(x0 + w * .22, y0 + 10, w * .62, h - 20), 2, border_radius=4)


def _espada(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.42
    blade = mix(c, (228, 232, 242), .55)
    tip = (cx, cy - R * 1.1)
    pts = [tip, (cx + R * .14, cy - R * .88), (cx + R * .14, cy + R * .32), (cx - R * .14, cy + R * .32), (cx - R * .14, cy - R * .88)]
    pygame.draw.polygon(sf, blade, pts)
    pygame.draw.polygon(sf, darker(blade, .15), [tip, (cx + R * .14, cy - R * .88), (cx + R * .14, cy + R * .32), (cx, cy + R * .32)])
    pygame.draw.polygon(sf, darker(D, .4), pts, 2)
    pygame.draw.line(sf, G, (cx, cy - R * .8), (cx, cy + R * .25), 3)
    guard = rr(cx - R * .55, cy + R * .3, R * 1.1, R * .16)
    pygame.draw.rect(sf, c, guard, border_radius=5)
    pygame.draw.rect(sf, darker(D, .3), guard, 2, border_radius=5)
    for gx in (guard.left, guard.right):
        pygame.draw.circle(sf, G, (gx, guard.centery), R * .1)
    grip = rr(cx - R * .08, cy + R * .46, R * .16, R * .42)
    pygame.draw.rect(sf, (82, 52, 40), grip)
    for i in range(4):
        y = grip.top + 4 + i * grip.height / 4
        pygame.draw.line(sf, (130, 90, 60), (grip.left, y), (grip.right, y + 4), 2)
    pygame.draw.circle(sf, c, (cx, cy + R * .95), R * .14)
    pygame.draw.circle(sf, G, (cx, cy + R * .95), R * .09)


def _flor(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.42
    hc = (cx, cy - R * .25)
    pygame.draw.line(sf, (70, 140, 70), (cx, hc[1]), (cx + R * .05, cy + R * 1.0), 7)
    for side in (-1, 1):
        base = (cx + R * .02, cy + R * (.45 if side < 0 else .65))
        tip = (cx + side * R * .55, base[1] - R * .25)
        mid = ((base[0] + tip[0]) / 2, (base[1] + tip[1]) / 2)
        nx, ny = -(tip[1] - base[1]) * .25, (tip[0] - base[0]) * .25
        pygame.draw.polygon(sf, (96, 176, 90), [base, (mid[0] + nx, mid[1] + ny), tip, (mid[0] - nx, mid[1] - ny)])
    for k in range(6):
        a = k * TAU / 6 + .3
        p = (hc[0] + math.cos(a) * R * .42, hc[1] + math.sin(a) * R * .42)
        pygame.draw.circle(sf, darker(D, .2), p, R * .33)
    for k in range(6):
        a = k * TAU / 6 + .3
        p = (hc[0] + math.cos(a) * R * .42, hc[1] + math.sin(a) * R * .42)
        pygame.draw.circle(sf, c, p, R * .29)
        pygame.draw.circle(sf, L, (p[0] - R * .06, p[1] - R * .06), R * .13)
    pygame.draw.circle(sf, G, hc, R * .22)
    for k in range(7):
        a = k * TAU / 7
        pygame.draw.circle(sf, darker(G, .3), (hc[0] + math.cos(a) * R * .11, hc[1] + math.sin(a) * R * .11), 2)


def _anel(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.42
    rc = (cx, cy + R * .25)
    pygame.draw.circle(sf, darker(D, .3), rc, R * .64, int(R * .22))
    pygame.draw.circle(sf, c, rc, R * .61, int(R * .16))
    pygame.draw.circle(sf, L, rc, R * .56, 2)
    pygame.draw.polygon(sf, c, [(cx - R * .26, cy - R * .38), (cx + R * .26, cy - R * .38), (cx + R * .16, cy - R * .2), (cx - R * .16, cy - R * .2)])
    gem = [(cx, cy - R * .98), (cx + R * .32, cy - R * .6), (cx, cy - R * .28), (cx - R * .32, cy - R * .6)]
    pygame.draw.polygon(sf, G, gem)
    pygame.draw.polygon(sf, lighter(G, .5), [gem[0], gem[3], (cx, cy - R * .6)])
    pygame.draw.polygon(sf, darker(G, .45), gem, 2)


def _lanterna(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.42
    pygame.draw.arc(sf, darker(D, .2), rr(cx - R * .3, cy - R * 1.08, R * .6, R * .6), 0, math.pi, 5)
    pygame.draw.polygon(sf, c, [(cx - R * .48, cy - R * .55), (cx + R * .48, cy - R * .55), (cx + R * .3, cy - R * .78), (cx - R * .3, cy - R * .78)])
    body = rr(cx - R * .38, cy - R * .55, R * .76, R * 1.05)
    pygame.draw.rect(sf, mix(G, (255, 255, 255), .35), body)
    pygame.draw.circle(sf, G, (cx, cy), R * .3)
    pygame.draw.polygon(sf, lighter(G, .6), [(cx, cy - R * .32), (cx + R * .13, cy + R * .05), (cx, cy + R * .18), (cx - R * .13, cy + R * .05)])
    for x in (body.left, cx, body.right):
        pygame.draw.line(sf, c, (x, body.top), (x, body.bottom), 4)
    pygame.draw.rect(sf, c, rr(cx - R * .5, cy + R * .48, R * 1.0, R * .2), border_radius=4)
    pygame.draw.rect(sf, darker(D, .3), rr(cx - R * .5, cy + R * .48, R * 1.0, R * .2), 2, border_radius=4)


def _estrela(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.44
    pygame.draw.polygon(sf, darker(D, .2), star_pts(cx, cy, R * 1.0, R * .46))
    pygame.draw.polygon(sf, c, star_pts(cx, cy, R * .9, R * .41))
    pygame.draw.polygon(sf, L, star_pts(cx - R * .05, cy - R * .06, R * .45, R * .2))
    pygame.draw.circle(sf, lighter(G, .4), (cx - R * .05, cy - R * .06), R * .1)


def _concha(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.42
    base = (cx, cy + R * .75)
    arc = []
    for i in range(13):
        a = math.pi + i / 12 * math.pi
        arc.append((cx + math.cos(a) * R * .95, cy + R * .15 + math.sin(a) * R * .95))
    for p in arc:
        pygame.draw.circle(sf, darker(D, .2), p, R * .14)
    for i in range(12):
        pygame.draw.polygon(sf, L if i % 2 else c, [base, arc[i], arc[i + 1]])
    for p in arc:
        pygame.draw.line(sf, D, base, p, 1)
    pygame.draw.polygon(sf, D, [(cx - R * .25, cy + R * .62), (cx + R * .25, cy + R * .62), (cx + R * .15, cy + R * .9), (cx - R * .15, cy + R * .9)])
    pygame.draw.circle(sf, G, (cx, cy + R * .1), R * .1)


def _ampulheta(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.42
    glass = (226, 236, 248)
    pygame.draw.polygon(sf, glass, [(cx - R * .42, cy - R * .8), (cx + R * .42, cy - R * .8), (cx + R * .06, cy), (cx - R * .06, cy)])
    pygame.draw.polygon(sf, glass, [(cx - R * .42, cy + R * .8), (cx + R * .42, cy + R * .8), (cx + R * .06, cy), (cx - R * .06, cy)])
    pygame.draw.polygon(sf, G, [(cx - R * .26, cy - R * .42), (cx + R * .26, cy - R * .42), (cx + R * .05, cy - R * .04), (cx - R * .05, cy - R * .04)])
    pygame.draw.polygon(sf, G, [(cx - R * .38, cy + R * .79), (cx + R * .38, cy + R * .79), (cx, cy + R * .42)])
    pygame.draw.line(sf, G, (cx, cy), (cx, cy + R * .45), 2)
    for x in (cx - R * .5, cx + R * .5):
        pygame.draw.line(sf, darker(c, .2), (x, cy - R * .85), (x, cy + R * .85), 6)
    for y in (cy - R * .98, cy + R * .8):
        r = rr(cx - R * .6, y, R * 1.2, R * .18)
        pygame.draw.rect(sf, c, r, border_radius=4)
        pygame.draw.rect(sf, darker(D, .3), r, 2, border_radius=4)


def _coracao(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.4

    def heart(k, ox=0, oy=0):
        pts = []
        for i in range(60):
            t = i / 60 * TAU
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            pts.append((cx + ox + x * R / 16 * k, cy + oy - y * R / 16 * k))
        return pts

    pygame.draw.polygon(sf, darker(D, .25), heart(1.05))
    pygame.draw.polygon(sf, c, heart(.97))
    pygame.draw.polygon(sf, L, heart(.35, -R * .32, -R * .3))
    pygame.draw.circle(sf, lighter(G, .5), (cx - R * .45, cy - R * .45), R * .08)


def _mascara(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.42
    for k in range(5):
        x = cx + (k - 2) * R * .3
        h = R * (.55 if k == 2 else .35)
        pygame.draw.polygon(sf, G, [(x - R * .1, cy - R * .3), (x + R * .1, cy - R * .3), (x, cy - R * .3 - h)])
    pts = []
    for i in range(48):
        a = i / 48 * TAU
        yk = .48 if math.sin(a) < 0 else .55
        dip = -R * .12 * max(0, math.cos((a - math.pi / 2) * 3)) if abs(a - math.pi / 2) < .5 else 0
        pts.append((cx + math.cos(a) * R * .95, cy + math.sin(a) * R * yk + dip))
    pygame.draw.polygon(sf, darker(D, .3), [(x * 1.0, y + 3) for x, y in pts])
    pygame.draw.polygon(sf, c, pts)
    pygame.draw.polygon(sf, L, [(x, y) for x, y in pts[30:42]] + [(cx, cy - R * .1)])
    for side in (-1, 1):
        e = rr(cx + side * R * .4 - R * .23, cy - R * .14, R * .46, R * .26)
        pygame.draw.ellipse(sf, (0, 0, 0, 0), e)
        pygame.draw.ellipse(sf, G, e.inflate(4, 4), 2)
        pygame.draw.line(sf, L, (cx + side * R * .95, cy), (cx + side * R * 1.08, cy + R * .4), 3)


def _bussola(sf, s, c, L, D, G):
    cx = cy = s / 2
    R = s * 0.4
    pygame.draw.circle(sf, c, (cx, cy - R * 1.0), R * .14, 4)
    pygame.draw.circle(sf, darker(D, .3), (cx, cy), R * .95)
    pygame.draw.circle(sf, c, (cx, cy), R * .88)
    pygame.draw.circle(sf, (242, 234, 214), (cx, cy), R * .72)
    for k in range(16):
        a = k * TAU / 16
        r0 = R * (.58 if k % 4 == 0 else .64)
        pygame.draw.line(sf, (120, 100, 80), (cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                         (cx + math.cos(a) * R * .7, cy + math.sin(a) * R * .7), 2)
    a = .5
    n = (cx + math.sin(a) * R * .6, cy - math.cos(a) * R * .6)
    so = (cx - math.sin(a) * R * .6, cy + math.cos(a) * R * .6)
    side = (math.cos(a) * R * .12, math.sin(a) * R * .12)
    pygame.draw.polygon(sf, G, [n, (cx + side[0], cy + side[1]), (cx - side[0], cy - side[1])])
    pygame.draw.polygon(sf, darker(G, .5), [n, (cx + side[0], cy + side[1]), (cx - side[0], cy - side[1])], 1)
    pygame.draw.polygon(sf, (90, 90, 112), [so, (cx + side[0], cy + side[1]), (cx - side[0], cy - side[1])])
    pygame.draw.circle(sf, c, (cx, cy), R * .08)


SHAPE_FUNCS = {
    "orbe": _orbe, "cristal": _cristal, "chave": _chave, "pena": _pena, "frasco": _frasco,
    "livro": _livro, "espada": _espada, "flor": _flor, "anel": _anel, "lanterna": _lanterna,
    "estrela": _estrela, "concha": _concha, "ampulheta": _ampulheta, "coracao": _coracao,
    "mascara": _mascara, "bussola": _bussola,
}
_items = {}


def item_small(item, size):
    """Item em pixel de mundo (size/3), com contorno."""
    key = ("s", item.get("shape"), item.get("color"), item.get("glow"), size)
    if key not in _items:
        base = 220
        sf = pygame.Surface((base, base), pygame.SRCALPHA)
        c, g = hexc(item.get("color")), hexc(item.get("glow"), (255, 255, 255))
        SHAPE_FUNCS.get(item.get("shape"), _orbe)(sf, base, c, lighter(c, .4), darker(c, .3), g)
        n = max(6, size // pixel.P - 2)
        small = pygame.transform.smoothscale(sf, (n, n))
        _items[key] = pixel.outline(small, darker(c, .65))
    return _items[key]


def item_surface(item, size):
    key = ("b", item.get("shape"), item.get("color"), item.get("glow"), size)
    if key not in _items:
        _items[key] = pixel.up(item_small(item, size))
    return _items[key]


def spin_item(item, size, angle, alpha=255):
    """Giro em pixel: achata em colunas inteiras e escurece o verso."""
    sm = item_small(item, size)
    w, h = sm.get_size()
    k = math.cos(angle)
    img = pygame.transform.scale(sm, (max(1, round(w * (0.15 + 0.85 * abs(k)))), h))
    if k < 0:
        img.fill((175, 160, 175, 255), special_flags=pygame.BLEND_RGBA_MULT)
    img = pixel.up(img)
    if alpha < 255:
        img.set_alpha(alpha)
    return img


def spin_view(base, angle, tilt=0.0, alpha=255):
    """Giro em torno do eixo vertical: achata na horizontal e escurece o 'verso'."""
    w, h = base.get_size()
    k = math.cos(angle)
    img = pygame.transform.smoothscale(base, (max(2, int(w * (0.12 + 0.88 * abs(k)))), h))
    if k < 0:
        img.fill((165, 160, 185, 255), special_flags=pygame.BLEND_RGBA_MULT)
    if tilt:
        img = pygame.transform.rotate(img, tilt)
    if alpha < 255:
        img.set_alpha(alpha)
    return img


def draw_floating_item(surf, item, center, size, t, strength=1.0, alpha=255):
    G = hexc(item["glow"], (255, 255, 255))
    x, y = center
    y += math.sin(t * 2.0) * size * .06
    blit_glow(surf, (x, y), size * .95, G, (0.55 + 0.15 * math.sin(t * 3)) * strength * alpha / 255)
    img = spin_item(item, size, t * 1.5, alpha)
    r = img.get_rect(center=(int(x), int(y)))
    surf.blit(img, (pixel.snap(r.x), pixel.snap(r.y)))
    return y


# ============================================================ mãos
_hands = None


def hands_surface():
    """Mão esquerda e direita em concha, palmas viradas pro item."""
    global _hands
    if _hands is None:
        skin, sd, sleeve = (240, 196, 162), (200, 146, 116), (112, 82, 168)
        hs = pygame.Surface((190, 300), pygame.SRCALPHA)
        # antebraço + manga (vem de baixo)
        pygame.draw.rect(hs, sd, (66, 150, 62, 90), border_radius=24)
        pygame.draw.rect(hs, skin, (68, 150, 58, 90), border_radius=24)
        pygame.draw.rect(hs, sleeve, (52, 205, 92, 100), border_radius=20)
        pygame.draw.rect(hs, lighter(sleeve, .25), (48, 200, 100, 24), border_radius=12)
        # palma
        pygame.draw.ellipse(hs, sd, (40, 70, 110, 110))
        pygame.draw.ellipse(hs, skin, (43, 72, 104, 104))
        pygame.draw.ellipse(hs, lighter(skin, .25), (62, 96, 56, 50))
        # dedos curvados por cima (em concha)
        for fx, fy, fw, fh in ((44, 46, 22, 58), (66, 30, 22, 66), (88, 30, 22, 66), (110, 42, 21, 58)):
            pygame.draw.rect(hs, sd, (fx - 1, fy - 1, fw + 2, fh + 2), border_radius=11)
            pygame.draw.rect(hs, skin, (fx, fy, fw, fh), border_radius=11)
            pygame.draw.ellipse(hs, (248, 214, 196), (fx + 4, fy + 3, fw - 8, 10))
            pygame.draw.line(hs, sd, (fx + 4, fy + fh * .55), (fx + fw - 4, fy + fh * .55), 1)
        # polegar
        pygame.draw.ellipse(hs, sd, (128, 104, 54, 32))
        pygame.draw.ellipse(hs, skin, (130, 106, 50, 28))
        pygame.draw.arc(hs, sd, (66, 120, 60, 40), 3.4, 6.0, 2)
        left = pygame.transform.rotozoom(hs, -38, .9)
        right = pygame.transform.flip(left, True, False)
        _hands = (left, right)
    return _hands


def draw_hands(surf, cx, palm_y, t, glow_col):
    left, right = hands_surface()
    dy = math.sin(t * 2.0) * 3
    blit_glow(surf, (cx, palm_y - 10), 130, glow_col, .3)
    surf.blit(left, left.get_rect(center=(int(cx - 135), int(palm_y + 55 + dy))))
    surf.blit(right, right.get_rect(center=(int(cx + 135), int(palm_y + 55 + dy))))


# ============================================================ molduras
def _fr_runas(surf, r, c, G, t):
    rng = random.Random(7)
    for y in (r.top + 2, r.bottom - 2):
        for x in range(r.left + 30, r.right - 20, 38):
            k = .55 + .45 * math.sin(t * 2 + x * .05)
            col = scale(G, k)
            pts = [(x + rng.randint(-6, 6), y + rng.randint(-7, 7)) for _ in range(3)]
            pygame.draw.lines(surf, col, False, pts, 2)


def _fr_vinhas(surf, r, c, G, t):
    vine = mix(G, (110, 200, 110), .55)
    for y0, sgn in ((r.top, 1), (r.bottom, -1)):
        pts = [(x, y0 + sgn * 2 + 5 * math.sin(x * .06 + t)) for x in range(r.left + 14, r.right - 14, 6)]
        pygame.draw.lines(surf, vine, False, pts, 3)
        for i, (x, y) in enumerate(pts[::5]):
            pygame.draw.ellipse(surf, (90, 170, 90), rr(x - 5, y - 4 + (i % 2) * 6 - 3, 11, 7))
            if i % 3 == 0:
                pygame.draw.circle(surf, lighter(G, .3), (x, y), 3)


def _fr_estrelas(surf, r, c, G, t):
    for i, (x, y) in enumerate(((r.left, r.top), (r.right, r.top), (r.left, r.bottom), (r.right, r.bottom))):
        k = 13 + 4 * math.sin(t * 3 + i)
        pygame.draw.polygon(surf, G, star_pts(x, y, k, k * .42))
    rng = random.Random(3)
    for _ in range(14):
        x = rng.randint(r.left + 20, r.right - 20)
        y = rng.choice((r.top + 6, r.bottom - 6))
        if math.sin(t * 4 + x) > .3:
            sparkle(surf, x, y, 4, lighter(G, .4))


def _fr_chamas(surf, r, c, G, t):
    outer, inner = mix(G, (255, 120, 40), .5), (255, 220, 120)
    for i, x in enumerate(range(r.left + 18, r.right - 10, 22)):
        h = 14 + 8 * math.sin(t * 9 + i * 1.7)
        pygame.draw.polygon(surf, outer, [(x - 9, r.bottom), (x + 9, r.bottom), (x + 2, r.bottom - h)])
        pygame.draw.polygon(surf, inner, [(x - 4, r.bottom), (x + 4, r.bottom), (x + 1, r.bottom - h * .55)])
        if i % 2 == 0:
            h2 = 7 + 4 * math.sin(t * 8 + i)
            pygame.draw.polygon(surf, outer, [(x - 5, r.top), (x + 5, r.top), (x, r.top - h2)])


def _fr_ondas(surf, r, c, G, t):
    for y0, ph in ((r.top + 2, 0), (r.top + 9, 1.4), (r.bottom - 2, 2), (r.bottom - 9, 3.4)):
        pts = [(x, y0 + 4 * math.sin(x * .05 + t * 2 + ph)) for x in range(r.left + 12, r.right - 12, 5)]
        pygame.draw.lines(surf, G if ph < 1 or ph == 2 else scale(G, .6), False, pts, 2)


def _gear(surf, x, y, R, a, col):
    pts = []
    for i in range(32):
        ang = a + i / 32 * TAU
        rad = R if (i // 2) % 2 == 0 else R * .75
        pts.append((x + math.cos(ang) * rad, y + math.sin(ang) * rad))
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.circle(surf, darker(col, .5), (x, y), R * .35)


def _fr_engrenagens(surf, r, c, G, t):
    for i, (x, y) in enumerate(((r.left + 4, r.top + 4), (r.right - 4, r.top + 4), (r.left + 4, r.bottom - 4), (r.right - 4, r.bottom - 4))):
        _gear(surf, x, y, 18, t * (1 if i % 2 else -1), mix(c, G, .4))
    _gear(surf, r.centerx, r.top + 2, 12, -t * 1.5, scale(G, .8))


def _fr_espinhos(surf, r, c, G, t):
    col = lighter(c, .3)
    for x in range(r.left + 20, r.right - 14, 26):
        pygame.draw.polygon(surf, col, [(x - 6, r.top + 1), (x + 6, r.top + 1), (x, r.top - 12)])
        pygame.draw.polygon(surf, col, [(x - 6, r.bottom - 1), (x + 6, r.bottom - 1), (x, r.bottom + 12)])
    for x in (r.left, r.right):
        pygame.draw.circle(surf, G, (x, r.centery), 7 + 2 * math.sin(t * 3))


def _fr_nuvens(surf, r, c, G, t):
    cloud = mix(G, (255, 255, 255), .5)
    for y0 in (r.top, r.bottom):
        for i, x in enumerate(range(r.left + 10, r.right, 34)):
            xx = x + 6 * math.sin(t * .8 + i)
            pygame.draw.circle(surf, cloud, (xx, y0), 11 + (i % 3) * 3)


FRAME_FUNCS = {
    "runas": _fr_runas, "vinhas": _fr_vinhas, "estrelas": _fr_estrelas, "chamas": _fr_chamas,
    "ondas": _fr_ondas, "engrenagens": _fr_engrenagens, "espinhos": _fr_espinhos, "nuvens": _fr_nuvens,
}


def draw_caption(surf, rect, item, t, title, body, reveal=1.0):
    c, G = hexc(item["color"]), hexc(item["glow"], (255, 255, 255))
    bg = mix(darker(c, .78), (18, 14, 28), .35)
    panel(surf, rect, bg, 238, 18)
    pygame.draw.rect(surf, lighter(c, .4), rect, 3, border_radius=18)
    pygame.draw.rect(surf, scale(G, .75), rect.inflate(-12, -12), 1, border_radius=14)
    FRAME_FUNCS.get(item.get("frame"), _fr_estrelas)(surf, rect, c, G, t)
    pixel.pixelate(surf, rect.inflate(36, 36))
    text(surf, title, font(30, bold=True), G, (rect.centerx, rect.top + 22), "midtop", shadow=darker(c, .7))
    f = font(22, italic=True)
    shown = body[: int(len(body) * max(0.0, min(1.0, reveal)))]
    for i, ln in enumerate(wrap(shown, f, rect.width - 70)):
        text(surf, ln, f, (240, 234, 246), (rect.centerx, rect.top + 70 + i * 28), "midtop")


# ============================================================ salas
WALL_Y = 300
THEME_STYLE = {
    "biblioteca": dict(wall=(176, 112, 86), floor=(160, 104, 74), accent=(255, 214, 140)),
    "floresta": dict(wall=(118, 160, 96), floor=(150, 176, 98), accent=(236, 255, 160)),
    "forja": dict(wall=(178, 112, 92), floor=(132, 90, 76), accent=(255, 150, 80)),
    "oceano": dict(wall=(98, 182, 190), floor=(246, 216, 172), accent=(190, 246, 255)),
    "ceu": dict(wall=(246, 168, 150), floor=(255, 222, 200), accent=(255, 236, 170)),
    "cripta": dict(wall=(150, 104, 126), floor=(118, 82, 100), accent=(255, 196, 150)),
    "jardim": dict(wall=(250, 222, 196), floor=(150, 196, 110), accent=(255, 170, 204)),
    "tesouro": dict(wall=(190, 92, 116), floor=(150, 100, 70), accent=(255, 220, 110)),
}
_rooms = {}


_grads = {}


def _vgrad(surf, rect, top, bottom):
    key = (rect.w, rect.h, rect.x % 3, rect.y % 3, tuple(top), tuple(bottom))
    if key not in _grads:
        if len(_grads) > 80:
            _grads.clear()
        g = pygame.Surface((rect.w, rect.h))
        pixel.vgrad(g, pygame.Rect(0, 0, rect.w, rect.h), top, bottom)
        _grads[key] = g
    surf.blit(_grads[key], rect.topleft)


def _room_static(theme):
    st = THEME_STYLE[theme]
    s = pygame.Surface((W, H))
    rng = random.Random(theme)
    wall, floor = st["wall"], st["floor"]
    _vgrad(s, pygame.Rect(0, 0, W, WALL_Y), darker(wall, .25), wall)
    _vgrad(s, pygame.Rect(0, WALL_Y, W, H - WALL_Y), darker(floor, .2), lighter(floor, .08))

    if theme == "biblioteca":
        for bx in (30, 250, 490, 730):
            pygame.draw.rect(s, darker(wall, .45), (bx, 30, 200, 270))
            pygame.draw.rect(s, darker(wall, .6), (bx, 30, 200, 270), 6)
            for sy in (60, 140, 220):
                x = bx + 10
                while x < bx + 186:
                    w, h = rng.randint(9, 18), rng.randint(46, 66)
                    col = rng.choice([(150, 50, 50), (50, 90, 150), (60, 120, 70), (170, 130, 60), (110, 70, 140)])
                    pygame.draw.rect(s, col, (x, sy + 70 - h, w, h))
                    pygame.draw.line(s, lighter(col, .3), (x + 2, sy + 72 - h), (x + 2, sy + 66), 1)
                    x += w + 1
                pygame.draw.rect(s, darker(wall, .2), (bx, sy + 70, 200, 8))
        for y in range(WALL_Y + 20, H, 34):
            pygame.draw.line(s, darker(floor, .2), (0, y), (W, y), 2)
        pygame.draw.ellipse(s, (128, 40, 52), (W // 2 - 300, 430, 600, 170))
        pygame.draw.ellipse(s, (176, 130, 70), (W // 2 - 280, 440, 560, 150), 4)
    elif theme == "floresta":
        for x in (60, 190, 780, 900):
            pygame.draw.rect(s, darker(wall, .4), (x - 22, 0, 44, WALL_Y))
        for i in range(22):
            x = rng.randint(0, W)
            ln = rng.randint(60, 220)
            pts = [(x + 8 * math.sin(k * .7 + i), k) for k in range(0, ln, 8)]
            pygame.draw.lines(s, (60, 130, 70), False, pts, 3)
            for px, py in pts[2::3]:
                pygame.draw.ellipse(s, (90, 170, 90), (px - 6, py - 3, 12, 7))
        for _ in range(140):
            x, y = rng.randint(0, W), rng.randint(WALL_Y + 5, H)
            pygame.draw.line(s, lighter(floor, .2), (x, y), (x + rng.randint(-3, 3), y - rng.randint(5, 11)), 2)
        for x, y in ((120, 560), (840, 520), (180, 380)):
            pygame.draw.rect(s, (235, 225, 205), (x - 3, y - 12, 7, 14))
            pygame.draw.ellipse(s, (200, 60, 60), (x - 14, y - 22, 28, 14))
    elif theme == "forja":
        for row, y in enumerate(range(0, WALL_Y, 28)):
            for x in range(-40 if row % 2 else -10, W, 64):
                pygame.draw.rect(s, mix(wall, (206, 130, 104), rng.random() * .4), (x + 2, y + 2, 60, 24))
        pygame.draw.rect(s, (60, 50, 50), (740, 120, 180, 180), border_radius=10)
        pygame.draw.ellipse(s, (20, 12, 10), (770, 150, 120, 130))
        pygame.draw.rect(s, (20, 12, 10), (770, 215, 120, 85))
        pygame.draw.polygon(s, (40, 40, 46), [(90, 480), (230, 480), (200, 500), (120, 500)])
        pygame.draw.rect(s, (40, 40, 46), (140, 500, 40, 40))
        pygame.draw.polygon(s, (60, 60, 68), [(70, 470), (250, 470), (230, 482), (90, 482)])
        for x in (300, 340, 380):
            pygame.draw.line(s, (40, 36, 36), (x, 60), (x, 150), 4)
            pygame.draw.rect(s, (90, 86, 90), (x - 10, 140, 20, 18))
    elif theme == "oceano":
        for i in range(6):
            x = 80 + i * 170
            pygame.draw.polygon(s, lighter(wall, .08), [(x, 0), (x + 60, 0), (x + 140, WALL_Y), (x + 40, WALL_Y)])
        for _ in range(120):
            x, y = rng.randint(0, W), rng.randint(WALL_Y, H)
            pygame.draw.circle(s, darker(floor, .1), (x, y), rng.randint(1, 3))
        for x, y in ((90, 600), (860, 560), (300, 590)):
            pygame.draw.ellipse(s, (120, 116, 112), (x - 40, y - 26, 80, 40))
    elif theme == "ceu":
        _vgrad(s, pygame.Rect(0, 0, W, WALL_Y), (232, 150, 170), (255, 206, 160))
        pygame.draw.circle(s, (255, 236, 180), (800, 120), 58)
        pygame.draw.circle(s, (255, 246, 210), (800, 120), 44)
        _vgrad(s, pygame.Rect(0, WALL_Y, W, H - WALL_Y), (246, 184, 176), (255, 232, 214))
        for _ in range(55):
            x, y = rng.randint(-40, W + 40), rng.randint(WALL_Y - 20, H)
            k = (y - WALL_Y) / (H - WALL_Y)
            pygame.draw.circle(s, mix((246, 178, 178), (255, 244, 232), k * .7 + rng.random() * .3), (x, y), rng.randint(26, 50))
    elif theme == "cripta":
        for row, y in enumerate(range(0, WALL_Y, 40)):
            for x in range(-30 if row % 2 else 0, W, 80):
                pygame.draw.rect(s, mix(wall, (176, 130, 140), rng.random() * .5), (x + 2, y + 2, 76, 36))
        for ax in (160, W // 2, W - 160):
            pygame.draw.rect(s, darker(wall, .55), (ax - 55, 110, 110, 190))
            pygame.draw.ellipse(s, darker(wall, .55), (ax - 55, 60, 110, 110))
        for y in range(WALL_Y, H, 50):
            pygame.draw.line(s, darker(floor, .3), (0, y), (W, y), 2)
        for cx, cy in ((0, 0), (W, 0)):
            for k in range(6):
                a = k * .3 + (0 if cx == 0 else math.pi / 2)
                pygame.draw.line(s, (120, 120, 130), (cx, cy), (cx + math.cos(a) * 90 * (1 if cx == 0 else -1), cy + math.sin(a) * 90), 1)
    elif theme == "jardim":
        for x in range(0, W, 40):
            pygame.draw.rect(s, lighter(wall, .25), (x, 0, 18, WALL_Y))
        pygame.draw.rect(s, (255, 255, 255), (W // 2 - 120, 40, 240, 180), border_radius=8)
        _vgrad(s, pygame.Rect(W // 2 - 110, 50, 220, 160), (150, 205, 250), (220, 240, 255))
        pygame.draw.circle(s, (255, 230, 120), (W // 2 + 50, 100), 26)
        pygame.draw.line(s, (255, 255, 255), (W // 2, 50), (W // 2, 210), 6)
        pygame.draw.line(s, (255, 255, 255), (W // 2 - 110, 130), (W // 2 + 110, 130), 6)
        for x in (90, 860):
            pygame.draw.polygon(s, (190, 100, 70), [(x - 40, 520), (x + 40, 520), (x + 28, 590), (x - 28, 590)])
            for k in range(7):
                pygame.draw.circle(s, (80, 160, 80), (x + rng.randint(-40, 40), 500 - rng.randint(0, 50)), rng.randint(16, 26))
            for k in range(6):
                pygame.draw.circle(s, rng.choice([(255, 120, 170), (255, 220, 100), (200, 140, 255)]), (x + rng.randint(-34, 34), 490 - rng.randint(0, 50)), 7)
    elif theme == "tesouro":
        pygame.draw.rect(s, (200, 160, 60), (0, 30, W, 6))
        pygame.draw.rect(s, (200, 160, 60), (0, WALL_Y - 12, W, 6))
        for x in (120, W - 120):
            pygame.draw.polygon(s, (150, 40, 60), [(x - 40, 40), (x + 40, 40), (x + 40, 220), (x, 190), (x - 40, 220)])
            pygame.draw.circle(s, (230, 190, 80), (x, 110), 16)
        for cx0, cy0, n in ((110, 560, 40), (850, 540, 50), (300, 610, 18), (680, 615, 22)):
            for _ in range(n):
                x = cx0 + rng.randint(-70, 70)
                y = cy0 - abs(rng.gauss(0, 1)) * 18 + rng.randint(-10, 10)
                pygame.draw.ellipse(s, rng.choice([(240, 200, 70), (220, 175, 50), (255, 225, 120)]), (x - 8, y - 4, 16, 8))
        pygame.draw.rect(s, (110, 60, 30), (760, 230, 110, 80), border_radius=6)
        pygame.draw.rect(s, (220, 180, 70), (760, 230, 110, 80), 4, border_radius=6)

    if theme != "ceu":
        pygame.draw.rect(s, darker(wall, .45), (0, WALL_Y - 4, W, 10))
    vig = pygame.Surface((W, H), pygame.SRCALPHA)
    for i in range(40):
        pygame.draw.rect(vig, (0, 0, 0, int((40 - i) * 2.2)), (i * 3, i * 3, W - i * 6, H - i * 6), 3)
    s.blit(vig, (0, 0))
    return s


def draw_room(surf, theme, t):
    if theme not in THEME_STYLE:
        theme = "cripta"
    if theme not in _rooms:
        _rooms[theme] = _room_static(theme)
    surf.blit(_rooms[theme], (0, 0))
    acc = THEME_STYLE[theme]["accent"]
    if theme == "biblioteca":
        for i in range(30):
            x = (i * 131 + t * 8 * (1 + i % 3)) % W
            y = 40 + (i * 53 + math.sin(t + i) * 30) % 400
            pygame.draw.circle(surf, (230, 210, 170), (int(x), int(y)), 1 + i % 2)
    elif theme == "floresta":
        for i in range(18):
            x = (i * 173) % W + math.sin(t * .7 + i) * 40
            y = 80 + (i * 97) % 420 + math.cos(t * .9 + i * 1.3) * 26
            blit_glow(surf, (x, y), 16, acc, .5 + .5 * math.sin(t * 3 + i))
    elif theme == "forja":
        for i in range(7):
            h = 50 + 25 * math.sin(t * 8 + i * 1.9)
            x = 785 + i * 15
            pygame.draw.polygon(surf, (255, 120, 40), [(x - 12, 300), (x + 12, 300), (x + 2, 300 - h)])
            pygame.draw.polygon(surf, (255, 220, 120), [(x - 5, 300), (x + 5, 300), (x + 1, 300 - h * .5)])
        blit_glow(surf, (830, 260), 140, acc, .6)
        for i in range(14):
            yy = 300 - ((t * 60 + i * 47) % 280)
            pygame.draw.circle(surf, (255, 190, 90), (int(800 + (i * 23) % 70 + math.sin(t * 3 + i) * 10), int(yy)), 2)
    elif theme == "oceano":
        for x in (40, 120, 880, 930):
            pts = [(x + math.sin(t * 1.5 + k * .4 + x) * k * .8, H - k * 9) for k in range(28)]
            pygame.draw.lines(surf, (40, 140, 90), False, pts, 6)
        for i in range(24):
            y = H - ((t * 50 + i * 97) % (H + 20))
            x = (i * 151) % W + math.sin(t * 2 + i) * 8
            pygame.draw.circle(surf, (200, 240, 255), (int(x), int(y)), 3 + i % 4, 1)
    elif theme == "ceu":
        for i in range(14):
            if math.sin(t * 2.5 + i * 7) > .6:
                sparkle(surf, (i * 211) % W, (i * 67) % 200 + 10, 4, (255, 255, 236))
        k = (t % 7) / 7
        if k < .15:
            x, y = 100 + k * 3000, 30 + k * 600
            pygame.draw.line(surf, (255, 255, 255), (x, y), (x - 60, y - 12), 2)
    elif theme == "cripta":
        for x, y in ((60, 230), (300, 200), (W - 300, 200), (W - 60, 230), (W // 2, 90)):
            pygame.draw.rect(surf, (230, 225, 210), (x - 5, y, 10, 28))
            f = 1 + .25 * math.sin(t * 12 + x)
            pygame.draw.ellipse(surf, (255, 200, 110), rr(x - 4, y - 14 * f, 8, 14 * f))
            blit_glow(surf, (x, y - 4), 50, acc, .55 + .15 * math.sin(t * 9 + x))
    elif theme == "jardim":
        for i in range(5):
            x = (i * 230 + t * 30) % (W + 100) - 50
            y = 340 + i * 40 + math.sin(t * 2 + i) * 30
            wing = abs(math.sin(t * 14 + i)) * 9 + 2
            col = [(255, 150, 200), (255, 210, 90), (180, 150, 255)][i % 3]
            pygame.draw.ellipse(surf, col, rr(x - wing - 1, y - 7, wing, 12))
            pygame.draw.ellipse(surf, col, rr(x + 1, y - 7, wing, 12))
    elif theme == "tesouro":
        for i in range(16):
            if math.sin(t * 3 + i * 5) > .5:
                sparkle(surf, [110, 850, 300, 680][i % 4] + (i * 37) % 120 - 60, [550, 530, 600, 605][i % 4] - (i * 13) % 30, 5, (255, 245, 180))


def draw_pedestal(surf, x, base_y, theme):
    stone = mix(THEME_STYLE.get(theme, THEME_STYLE["cripta"])["wall"], (170, 165, 175), .55)
    sh = pygame.Surface((110, 30), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
    surf.blit(sh, (x - 55, base_y - 14))
    pygame.draw.rect(surf, darker(stone, .2), rr(x - 40, base_y - 18, 80, 18), border_radius=4)
    pygame.draw.rect(surf, stone, rr(x - 26, base_y - 80, 52, 64))
    pygame.draw.rect(surf, lighter(stone, .15), rr(x - 26, base_y - 80, 12, 64))
    pygame.draw.ellipse(surf, darker(stone, .15), rr(x - 46, base_y - 96, 92, 26))
    pygame.draw.ellipse(surf, lighter(stone, .2), rr(x - 46, base_y - 100, 92, 24))


def prompt_bubble(surf, x, y, label, t):
    y += 3 if math.sin(t * 4) > 0 else 0
    f = font(18)
    w = f.size(label)[0] + 24
    r = rr(x - w / 2, y - 33, w, 30)
    panel(surf, r, CREAM, 255, border=INK)
    text(surf, label, f, INK, r.center, "center")


# ============================================================ campo, casa, jogador
HOUSE_POS = (W // 2 - 140, 62)
HOUSE_SIZE = (280, 210)
DOOR_POS = (W // 2, 272)
HOUSE_BLOCK = pygame.Rect(W // 2 - 125, 160, 250, 108)
FINAL_POS = (W - 120, H - 120)
FIELD_BOUNDS = pygame.Rect(60, 108, W - 120, H - 112)
GRASS = pixel.GRASS[1]


class Field:
    """Clareira na floresta: grama em camadas, trilha, pedras, arbustos e uma
    parede de árvores nas bordas (nenhum pedaço vazio)."""

    def __init__(self, seed=11):
        rng = random.Random(seed)
        P = pixel.P
        g = pygame.Surface((pixel.LW, pixel.LH))
        pixel.paint_grass(g, g.get_rect(), rng)
        dx0 = DOOR_POS[0] // P
        for y in range(DOOR_POS[1] // P - 3, pixel.LH):                 # trilha de terra
            w = 9 + int(2 * math.sin(y * .15))
            cx = dx0 + int(4 * math.sin(y * .05))
            pixel.paint_dirt(g, pygame.Rect(cx - w, y, w * 2, 1), rng)
            for side in (cx - w, cx + w - 1):
                if rng.random() < .35:
                    pixel.tuft(g, side - 1, y, pixel.GRASS[3], rng.randint(0, 2))
        self.ground = pixel.up(g)
        self.sprites, self.blockers = [], []

        def add(img, x, y, block=None):
            self.sprites.append((y, img, (pixel.snap(x - img.get_width() / 2), pixel.snap(y - img.get_height()))))
            if block:
                self.blockers.append(pygame.Rect(x - block[0] // 2, y - block[1], block[0], block[1]))

        def tree(x, y, kind=None, block=True):
            k = kind or rng.choice(["green", "green", "dark", "pink"])
            add(pixel.up(pixel.tree_sprite(rng, k)), x, y + 6, (24, 16) if block else None)

        # parede de árvores (fundo e laterais)
        for x in range(-20, W + 40, 52):
            tree(x + rng.randint(-8, 8), 70 + rng.randint(-10, 10), block=False)
        for x in range(-10, W + 40, 64):
            if not (290 < x < 670):
                tree(x + rng.randint(-8, 8), 128 + rng.randint(-8, 8), block=False)
        for y in range(170, H + 120, 62):
            tree(18 + rng.randint(-8, 8), y, block=False)
            tree(W - 18 + rng.randint(-8, 8), y, block=False)
        for x in range(70, W - 60, 58):                                   # borda de baixo
            if not (380 < x < 590) and not (x > 700):
                tree(x + rng.randint(-6, 6), H + 105 + rng.randint(-6, 6), block=False)

        def free(x, y, d, placed):
            if pygame.Rect(300, 40, 360, 285).collidepoint(x, y):
                return False
            if abs(x - DOOR_POS[0]) < 80 and y > 250:
                return False
            if x > 720 and y > 400:
                return False
            return all(math.hypot(x - px, y - py) > d for px, py in placed)

        placed = []
        for _ in range(400):                                            # árvores soltas
            if len(placed) >= 5:
                break
            x, y = rng.randint(110, W - 110), rng.randint(220, H - 60)
            if free(x, y, 150, placed):
                placed.append((x, y))
                tree(x, y)
        for _ in range(600):                                            # pedras, arbustos, tocos, cogumelos
            if len(placed) >= 30:
                break
            x, y = rng.randint(90, W - 90), rng.randint(170, H - 30)
            if not free(x, y, 62, placed):
                continue
            placed.append((x, y))
            r = rng.random()
            if r < .38:
                add(pixel.up(pixel.bush_sprite(rng)), x, y, (54, 14))
            elif r < .72:
                img = pixel.up(pixel.rock_sprite(rng, rng.choice([.6, .8, 1.0, 1.3])))
                add(img, x, y, (img.get_width() - 12, 14))
            elif r < .82:
                add(pixel.up(pixel.stump_sprite()), x, y, (36, 12))
            else:
                for k in range(rng.randint(2, 3)):
                    add(pixel.up(pixel.mushroom_sprite(rng.choice([(240, 120, 110), (252, 200, 110)]))),
                        x + k * 15, y + (k % 2) * 6)
        for x, y in ((W - 200, H - 40), (W - 50, H - 220), (W - 240, H - 150), (W - 60, H - 40)):
            add(pixel.up(pixel.bush_sprite(rng)), x, y, (54, 14))      # moldura florida do canto do item
        add(pixel.up(pixel.rock_sprite(rng, 1.4)), W - 70, H - 120, (60, 14))


def draw_house(surf, ox, oy, window_col, t):
    wall, beam, roof = (255, 240, 222), (176, 116, 86), (236, 120, 110)
    sh = pygame.Surface((300, 40), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 60), sh.get_rect())
    surf.blit(sh, (ox - 10, oy + 192))
    pygame.draw.rect(surf, (140, 120, 120), (ox + 200, oy + 10, 30, 60))
    pygame.draw.rect(surf, wall, (ox + 20, oy + 80, 240, 130))
    pygame.draw.rect(surf, darker(wall, .15), (ox + 20, oy + 80, 240, 130), 3)
    for x in (ox + 20, ox + 255):
        pygame.draw.rect(surf, beam, (x, oy + 80, 6, 130))
    pygame.draw.rect(surf, beam, (ox + 20, oy + 140, 240, 6))
    pygame.draw.polygon(surf, darker(roof, .25), [(ox - 6, oy + 92), (ox + 140, oy - 2), (ox + 286, oy + 92)])
    pygame.draw.polygon(surf, roof, [(ox, oy + 86), (ox + 140, oy + 4), (ox + 280, oy + 86)])
    for k in range(1, 5):
        y = oy + 4 + k * 18
        half = (y - oy - 4) / 82 * 140
        pygame.draw.line(surf, darker(roof, .15), (ox + 140 - half, y), (ox + 140 + half, y), 2)
    pygame.draw.circle(surf, window_col, (ox + 140, oy + 50), 14)
    pygame.draw.circle(surf, beam, (ox + 140, oy + 50), 14, 3)
    pulse = .5 + .25 * math.sin(t * 2)
    for wx in (ox + 46, ox + 190):
        pygame.draw.rect(surf, window_col, (wx, oy + 100, 44, 40))
        pygame.draw.rect(surf, beam, (wx, oy + 100, 44, 40), 4)
        pygame.draw.line(surf, beam, (wx + 22, oy + 100), (wx + 22, oy + 140), 3)
        pygame.draw.line(surf, beam, (wx, oy + 120), (wx + 44, oy + 120), 3)
        pygame.draw.rect(surf, (140, 90, 60), (wx - 4, oy + 142, 52, 10))
        for k in range(5):
            pygame.draw.circle(surf, [(255, 120, 170), (255, 220, 90), (190, 140, 255)][k % 3], (wx + 3 + k * 10, oy + 141), 4)
        blit_glow(surf, (wx + 22, oy + 120), 48, window_col, pulse * .5)
    door = pygame.Rect(ox + 118, oy + 142, 44, 68)
    pygame.draw.rect(surf, (120, 76, 52), door, border_top_left_radius=22, border_top_right_radius=22)
    pygame.draw.rect(surf, (90, 56, 38), door, 3, border_top_left_radius=22, border_top_right_radius=22)
    pygame.draw.line(surf, (90, 56, 38), (door.centerx, door.top + 8), (door.centerx, door.bottom), 2)
    pygame.draw.circle(surf, (240, 200, 90), (door.right - 9, door.centery + 6), 4)


def house_surface(window_col, t):
    s = pygame.Surface((HOUSE_SIZE[0] + 20, HOUSE_SIZE[1] + 30), pygame.SRCALPHA)
    draw_house(s, 10, 6, window_col, t)
    return s


DEFAULT_LOOK = {
    "skin": (248, 208, 174), "hair": (124, 76, 56), "hair_style": "short",
    "top": {"color": (190, 172, 232), "style": "pajama"},
    "bottom": {"color": (190, 172, 232), "style": "pajama"},
    "shoes": {"color": (255, 232, 214), "style": "slipper"},
}


def _shade(c, k):
    return darker(c, k) if k > 0 else lighter(c, -k)


class _Pen:
    """Desenha com coordenadas 'base' multiplicadas por k (pra ficar nítido em close)."""

    def __init__(self, S, k):
        self.S, self.k = S, k

    def _p(self, p):
        return (round(p[0] * self.k), round(p[1] * self.k))

    def _r(self, r):
        x, y, w, h = r
        k = self.k
        return pygame.Rect(round(x * k), round(y * k), max(1, round(w * k)), max(1, round(h * k)))

    def _w(self, w):
        return max(1, round(w * self.k)) if w else 0

    def rect(self, c, r, width=0, border_radius=0):
        pygame.draw.rect(self.S, c, self._r(r), self._w(width), border_radius=int(border_radius * self.k))

    def circle(self, c, p, r, width=0):
        rk = r * self.k
        if rk < 1.2:
            x, y = self._p(p)
            pygame.draw.rect(self.S, c, (x - (1 if rk > .9 else 0), y, 1 + (1 if rk > .9 else 0), 1))
            return
        pygame.draw.circle(self.S, c, self._p(p), rk, self._w(width))

    def line(self, c, a, b, width=1):
        pygame.draw.line(self.S, c, self._p(a), self._p(b), self._w(width))

    def lines(self, c, closed, pts, width=1):
        pygame.draw.lines(self.S, c, closed, [self._p(p) for p in pts], self._w(width))

    def polygon(self, c, pts, width=0):
        pygame.draw.polygon(self.S, c, [self._p(p) for p in pts], self._w(width))

    def ellipse(self, c, r, width=0):
        pygame.draw.ellipse(self.S, c, self._r(r), self._w(width))

    def arc(self, c, r, a0, a1, width=1):
        pygame.draw.arc(self.S, c, self._r(r), a0, a1, self._w(width))


def draw_character(surf, x, y, facing="down", phase=0.0, moving=False, look=None,
                   scale=1.0, pose="stand", eyes="open", sprite_hook=True):
    """Personagem em camadas (corpo + parte de cima + parte de baixo + sapatos).
    (x, y) = ponto entre os pés. Se existirem sprites em assets/, usa elas."""
    look = look or DEFAULT_LOOK
    if not pose.startswith("sit"):
        sw_ = int(28 * scale)
        sh = pygame.Surface((pixel.snap(sw_) or 3, max(3, pixel.snap(8 * scale))), pygame.SRCALPHA)
        notched(sh, sh.get_rect(), (90, 40, 40, 60))
        surf.blit(sh, (pixel.snap(x - sh.get_width() / 2), pixel.snap(y - sh.get_height() / 2)))
    if sprite_hook and look.get("sprite"):
        import assets
        fr = assets.frames(f"{look['sprite']}_{'walk' if moving else 'idle'}_{facing}")
        if fr:
            img = fr[int(phase / 2) % len(fr)] if moving else fr[0]
            img = pygame.transform.smoothscale_by(img, scale) if scale != 1 else img
            surf.blit(img, img.get_rect(midbottom=(int(x), int(y))))
            return
    K = scale / pixel.P                           # 1 px do sprite = 1 px do mundo
    S = pygame.Surface((math.ceil(48 * K), math.ceil(78 * K)), pygame.SRCALPHA)
    P = _Pen(S, K)
    skin, hair = look["skin"], look["hair"]
    top, bot, sho = look["top"], look["bottom"], look["shoes"]
    tc, bc, sc = top["color"], bot["color"], sho["color"]
    side = facing in ("left", "right")
    sit = pose.startswith("sit")
    pass  # a sombra é desenhada fora do sprite (pra não ganhar contorno)
    swing = math.sin(phase) * 3 if moving else 0
    bob = -abs(math.sin(phase)) * 2 if moving else 0
    up = 8 if sit else 0                      # sentado: tronco desce

    # ---------- pernas ----------
    robe = top["style"] == "robe"
    legs = [(17, swing), (25, -swing)] if not side else [(21, swing), (21, -swing)]
    for lx, sw in legs:
        lx = lx + (sw * .8 if side else 0)
        y0 = 58 if sit else 51
        ly = (0 if side else sw * .5)
        if bot["style"] == "shorts":
            P.rect(skin, (lx, y0 + ly, 6, 66 - y0))
            P.rect(bc, (lx - 1, y0 + ly, 8, 6 if not sit else 3))
        else:
            P.rect(darker(bc, .08) if lx > 22 else bc, (lx, y0 + ly, 6, 66 - y0))
            if bot["style"] == "pajama":
                P.circle(lighter(bc, .45), (lx + 3, y0 + ly + 6), 1)
        sh_y = 65 + ly
        if sho["style"] == "boot":
            P.rect(sc, (lx - 1, sh_y - 4, 8, 11), border_radius=2)
            P.rect(darker(sc, .3), (lx - 1, sh_y + 5, 8, 2))
        elif sho["style"] == "slipper":
            P.ellipse(sc, (lx - 2, sh_y, 10, 7))
            P.ellipse((255, 255, 255), (lx, sh_y + 1, 6, 3))
        else:
            P.rect(sc, (lx - 1, sh_y, 8 + (3 if side else 0), 6), border_radius=3)
            P.rect(darker(sc, .25) if sum(sc) > 600 else lighter(sc, .5), (lx - 1, sh_y + 4, 8 + (3 if side else 0), 2))
    if sit:  # coxas vindo pra frente (sentado na beira da cama)
        P.rect(darker(bc, .05), (14, 54, 20, 7), border_radius=3)
    # ---------- tronco ----------
    ty = 31 + bob + up
    body = pygame.Rect(14, ty, 20, 23 if not robe else 31)
    if robe:
        P.polygon(tc, [(14, ty + 3), (34, ty + 3), (36, ty + 32), (12, ty + 32)])
    P.rect(tc, body, border_radius=6)
    st = top["style"]
    if st == "hoodie":
        P.arc(darker(tc, .2), (14, ty - 4, 20, 12), math.pi, TAU, 3)
        if facing != "up":
            P.rect(lighter(tc, .2), (18, ty + 13, 12, 7), border_radius=3)
            if not side:
                P.line((255, 255, 255), (21, ty + 2), (21, ty + 8), 1)
                P.line((255, 255, 255), (27, ty + 2), (27, ty + 8), 1)
    elif st == "plaid":
        for k in range(16, 34, 5):
            P.line(darker(tc, .22), (k, ty + 1), (k, ty + 22), 1)
        for k in range(2, 22, 5):
            P.line(lighter(tc, .25), (15, ty + k), (33, ty + k), 1)
        if facing != "up":
            P.polygon((255, 250, 240), [(20, ty), (28, ty), (24, ty + 5)])
    elif st == "sweater":
        for k in range(3):
            P.line(darker(tc, .15), (15, ty + 19 + k * 1.5), (33, ty + 19 + k * 1.5), 1)
        P.rect(darker(tc, .12), (19, ty - 1, 10, 4), border_radius=2)
        if facing != "up":
            P.circle(lighter(tc, .4), (24, ty + 10), 3)
    elif st == "pajama":
        for dx, dy in ((18, 6), (28, 9), (21, 15), (30, 18), (17, 19)):
            P.circle(lighter(tc, .5), (dx, ty + dy), 1)
        P.polygon(lighter(tc, .3), [(19, ty), (29, ty), (24, ty + 5)])
    elif st == "robe":
        if facing != "up":
            P.polygon(skin, [(20, ty), (28, ty), (24, ty + 9)])
            P.line(darker(tc, .15), (20, ty), (24, ty + 14), 2)
            P.line(darker(tc, .15), (28, ty), (24, ty + 14), 2)
        P.rect(darker(tc, .2), (14, ty + 14, 20, 3))
    # ---------- braços ----------
    arm_sw = -swing if moving else 0
    if side:
        P.rect(darker(tc, .1), (21 - arm_sw * .6, ty + 3, 6, 15), border_radius=3)
        P.circle(skin, (24 - arm_sw * .6, ty + 19), 3)
    else:
        if pose == "belly":
            for ax in (10, 32):
                P.rect(darker(tc, .08), (ax, ty + 2, 6, 12), border_radius=3)
            P.circle(skin, (20, ty + 15), 3)
            P.circle(skin, (28, ty + 15), 3)
        else:
            P.rect(darker(tc, .08), (10, ty + 2 + arm_sw * .5, 5, 15), border_radius=3)
            P.circle(skin, (12, ty + 18 + arm_sw * .5), 3)
            if pose == "sit_rub":
                P.line(darker(tc, .08), (33, ty + 4), (29, ty - 6), 5)
                P.circle(skin, (28, ty - 8), 3)
            else:
                P.rect(darker(tc, .08), (33, ty + 2 - arm_sw * .5, 5, 15), border_radius=3)
                P.circle(skin, (36, ty + 18 - arm_sw * .5), 3)
    # ---------- cabeça ----------
    hy = 18 + bob + up
    hs = look.get("hair_style", "short")
    if hs == "long":
        P.rect(hair, (11, hy - 4, 26, 22), border_radius=8)
    if facing == "up":
        P.circle(hair, (24, hy), 12)
        if hs == "bun":
            P.circle(hair, (24, hy - 12), 5)
    else:
        P.circle(hair, (24, hy - 2), 12)
        fx = {"left": -2, "right": 2}.get(facing, 0)
        P.circle(skin, (24 + fx, hy + 2), 10)
        # franja
        for k in range(4):
            P.circle(hair, (17 + k * 5 + fx, hy - 7), 4)
        if hs == "bun":
            P.circle(hair, (24, hy - 14), 5)
        if hs == "cap":
            P.rect(look.get("cap", CORAL), (12, hy - 13, 24, 8), border_radius=4)
            P.rect(look.get("cap", CORAL), (12 + (6 if facing == "right" else -4 if facing == "left" else 4), hy - 7, 16, 3))
        ink = (70, 42, 50)
        ey = hy + 2
        if side:
            ex = 24 + fx + (5 if facing == "right" else -5)
            P.circle(ink, (ex, ey), 2)
            P.circle((250, 160, 160), (ex - (3 if facing == "right" else -3), ey + 4), 2)
        else:
            for ex in (20, 28):
                if eyes == "closed":
                    P.arc(ink, (ex - 3, ey - 2, 6, 4), math.pi, TAU, 1)
                elif eyes == "happy":
                    P.arc(ink, (ex - 3, ey - 1, 6, 5), 0, math.pi, 2)
                elif eyes == "sleepy":
                    P.line(ink, (ex - 2, ey), (ex + 2, ey), 2)
                else:
                    P.circle(ink, (ex, ey), 2)
                    P.circle((255, 255, 255), (ex + 1, ey - 1), 1)
            P.circle((250, 160, 160), (17, ey + 4), 2)
            P.circle((250, 160, 160), (31, ey + 4), 2)
            if eyes in ("happy",):
                P.arc(ink, (21, ey + 2, 6, 5), math.pi, TAU, 1)
    S = pixel.up(pixel.outline(S, (70, 40, 50)))
    surf.blit(S, (pixel.snap(x - 24 * scale) - pixel.P, pixel.snap(y - 72 * scale) - pixel.P))


def draw_mom(surf, cx, cy, size, t):
    """Retrato da mãe sorrindo (busto), pra nuvem de lembrança."""
    k = size / 100
    hair, skin, card = (150, 82, 64), (250, 212, 180), (244, 190, 112)
    pygame.draw.ellipse(surf, hair, rr(cx - 62 * k, cy - 70 * k, 124 * k, 150 * k))
    pygame.draw.ellipse(surf, card, rr(cx - 70 * k, cy + 45 * k, 140 * k, 90 * k))
    pygame.draw.polygon(surf, (255, 246, 236), [(cx - 18 * k, cy + 46 * k), (cx + 18 * k, cy + 46 * k), (cx, cy + 74 * k)])
    pygame.draw.rect(surf, skin, rr(cx - 11 * k, cy + 22 * k, 22 * k, 28 * k))
    pygame.draw.circle(surf, skin, (cx, cy), 46 * k)
    pygame.draw.ellipse(surf, hair, rr(cx - 50 * k, cy - 58 * k, 100 * k, 52 * k))
    pygame.draw.ellipse(surf, hair, rr(cx - 52 * k, cy - 40 * k, 34 * k, 70 * k))
    pygame.draw.ellipse(surf, hair, rr(cx + 18 * k, cy - 40 * k, 34 * k, 70 * k))
    ink = (90, 50, 56)
    for ex in (-17, 17):
        pygame.draw.arc(surf, ink, rr(cx + ex * k - 9 * k, cy + 2 * k, 18 * k, 12 * k), 0, math.pi, max(2, int(3 * k)))
    pygame.draw.arc(surf, ink, rr(cx - 14 * k, cy + 10 * k, 28 * k, 22 * k), math.pi + .3, TAU - .3, max(2, int(3 * k)))
    for ex in (-28, 28):
        pygame.draw.circle(surf, (250, 150, 150), (cx + ex * k, cy + 16 * k), 7 * k)
    pygame.draw.circle(surf, BUTTER, (cx - 44 * k, cy + 20 * k), 4 * k)
    pygame.draw.circle(surf, BUTTER, (cx + 44 * k, cy + 20 * k), 4 * k)


# ============================================================ gato
def draw_cat(surf, x, y, t, mode="walk", facing=-1, paw_up=0.0):
    """mode: 'walk' ou 'sit'. facing -1 = olhando pra esquerda. paw_up 0..1."""
    s = pygame.Surface((140, 120), pygame.SRCALPHA)
    fur, fur2, eye = (44, 40, 54), (72, 66, 86), (255, 214, 80)
    pygame.draw.ellipse(s, (0, 0, 0, 60), (25, 106, 90, 12))
    if mode == "walk":
        ph = t * 10
        for i, lx in enumerate((40, 52, 86, 98)):
            off = math.sin(ph + (i % 2) * math.pi + (i // 2) * .5) * 5
            pygame.draw.rect(s, fur, (lx + off * .4, 82, 9, 28), border_radius=4)
        pygame.draw.ellipse(s, fur, (32, 56, 80, 38))
        tail = [(106 + k * 2.5, 70 - k * 4 + math.sin(t * 4 + k * .5) * k * .6) for k in range(12)]
        pygame.draw.lines(s, fur, False, tail, 8)
        hx, hy = 34, 56
    else:
        tail = [(92 + math.cos(k * .3 - 1 + math.sin(t * 2) * .2) * 24, 100 - math.sin(k * .3) * 6 - k) for k in range(12)]
        pygame.draw.lines(s, fur, False, tail, 8)
        pygame.draw.ellipse(s, fur, (46, 52, 54, 60))
        pygame.draw.ellipse(s, fur2, (56, 66, 26, 30))
        pygame.draw.rect(s, fur, (50, 88, 11, 22), border_radius=5)
        if paw_up < .05:
            pygame.draw.rect(s, fur, (64, 88, 11, 22), border_radius=5)
        hx, hy = 60, 44
    pygame.draw.polygon(s, fur, [(hx - 18, hy - 6), (hx - 14, hy - 30), (hx - 2, hy - 14)])
    pygame.draw.polygon(s, fur, [(hx + 18, hy - 6), (hx + 14, hy - 30), (hx + 2, hy - 14)])
    pygame.draw.polygon(s, (200, 120, 140), [(hx - 14, hy - 10), (hx - 13, hy - 24), (hx - 6, hy - 14)])
    pygame.draw.polygon(s, (200, 120, 140), [(hx + 14, hy - 10), (hx + 13, hy - 24), (hx + 6, hy - 14)])
    pygame.draw.circle(s, fur, (hx, hy), 19)
    blink = (t % 4) < .12
    for ex in (hx - 8, hx + 8):
        if blink:
            pygame.draw.line(s, eye, (ex - 4, hy - 2), (ex + 4, hy - 2), 2)
        else:
            pygame.draw.ellipse(s, eye, (ex - 5, hy - 7, 10, 11))
            pygame.draw.ellipse(s, (20, 16, 24), (ex - 1 - 3, hy - 6, 3, 9))
    pygame.draw.polygon(s, (230, 140, 160), [(hx - 3, hy + 5), (hx + 3, hy + 5), (hx, hy + 8)])
    for sgn in (-1, 1):
        for k in (-1, 1):
            pygame.draw.line(s, (200, 200, 210), (hx + sgn * 6, hy + 7), (hx + sgn * 24, hy + 5 + k * 4), 1)
    col_y = hy + 18
    pygame.draw.arc(s, (210, 50, 60), (hx - 16, col_y - 10, 32, 16), math.pi, TAU, 4)
    bell = (hx, col_y + 4)
    pygame.draw.circle(s, (250, 205, 70), bell, 6)
    pygame.draw.circle(s, (170, 130, 30), bell, 6, 1)
    pygame.draw.line(s, (120, 90, 20), (bell[0] - 3, bell[1] + 1), (bell[0] + 3, bell[1] + 1), 1)
    if mode == "sit" and paw_up >= .05:
        px = 70 - 8 * paw_up
        py = 100 - (100 - bell[1]) * paw_up + 4
        pygame.draw.line(s, fur, (70, 92), (px, py), 10)
        pygame.draw.circle(s, fur2, (int(px), int(py)), 6)
    if facing > 0:
        s = pygame.transform.flip(s, True, False)
    surf.blit(s, (int(x - 70), int(y - 112)))
    bx = x - 70 + (bell[0] if facing < 0 else 140 - bell[0])
    return bx, y - 112 + bell[1]
