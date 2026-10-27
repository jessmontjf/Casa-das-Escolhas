"""Núcleo do visual em pixel art.

Regra de ouro: 1 pixel do mundo = P pixels na tela (P = 3). Sprites são desenhados
em resolução "de mundo" (pequenos), ganham contorno de 1 px e são ampliados ×P sem
suavização. No fim de cada cena o mundo inteiro é 'pixelizado' na mesma grade.
"""
import math
import random

import pygame

P = 3
W, H = 960, 640
LW, LH = W // P, (H + P - 1) // P          # 320 x 214

OUT_DARK = (78, 46, 56)                     # contorno padrão (marrom-vinho quente)


# ============================================================ básicos
def snap(v):
    return int(v) // P * P


def up(small):
    """Amplia um sprite de mundo ×P sem suavizar."""
    return pygame.transform.scale(small, (small.get_width() * P, small.get_height() * P))


GRADE = (232, 204, 172)      # luz quente de fim de tarde / lamparina


def pixelate(surf, rect=None, grade=False):
    """Re-amostra a tela na grade de P px (deixa tudo 'pixel').
    grade=True também aplica a luz quente e aconchegante do mundo."""
    if rect is None:
        small = pygame.transform.scale(surf, (LW, LH))
        if grade:
            small.fill(GRADE, special_flags=pygame.BLEND_RGB_MULT)
            _palette().apply(small)
        surf.blit(pygame.transform.scale(small, (LW * P, LH * P)), (0, 0))
    else:
        r = pygame.Rect(snap(rect.x), snap(rect.y), snap(rect.w + P - 1), snap(rect.h + P - 1)).clip(surf.get_rect())
        if r.w < P or r.h < P:
            return
        sub = surf.subsurface(r).copy()
        small = pygame.transform.scale(sub, (r.w // P, r.h // P))
        surf.blit(pygame.transform.scale(small, (r.w, r.h)), r.topleft)


def outline(small, color=OUT_DARK, alpha_cut=110):
    """Contorno de 1 px em volta de um sprite pequeno (e corta semi-transparências)."""
    w, h = small.get_size()
    m = pygame.mask.from_surface(small, alpha_cut)
    out = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    sil = m.to_surface(setcolor=(*color, 255), unsetcolor=(0, 0, 0, 0))
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
        out.blit(sil, (dx, dy))
    solid = m.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
    body = small.copy()
    body.blit(solid, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)   # alpha 0/255
    out.blit(body, (1, 1))
    return out


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def dark(c, t=.25):
    return mix(c, (60, 30, 40), t)


def light(c, t=.3):
    return mix(c, (255, 248, 230), t)


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def vgrad(surf, rect, top, bottom, levels=5):
    """Degradê em faixas com pontilhado (dithering) no estilo pixel."""
    x0, y0 = snap(rect.left), snap(rect.top)
    cols = [mix(top, bottom, i / (levels - 1)) for i in range(levels)]
    for y in range(y0, rect.bottom, P):
        t = (y - y0) / max(1, rect.height - 1) * (levels - 1)
        i = min(levels - 2, int(t))
        f = t - i
        pygame.draw.rect(surf, cols[i], (rect.left, y, rect.width, P))
        row = (y // P) % 4
        if f > 0.05:
            for x in range(x0, rect.right, P):
                if BAYER[row][(x // P) % 4] / 16 < f:
                    pygame.draw.rect(surf, cols[i + 1], (x, y, P, P))


# ============================================================ grama (técnica: base → manchas → tufos → flores)
GRASS = [(196, 226, 128), (166, 210, 112), (126, 182, 98), (92, 150, 90), (64, 112, 82)]


def _noise(w, h, cell, rng):
    gw, gh = w // cell + 2, h // cell + 2
    g = [[rng.random() for _ in range(gw)] for _ in range(gh)]

    def at(x, y):
        fx, fy = x / cell, y / cell
        ix, iy = int(fx), int(fy)
        tx, ty = fx - ix, fy - iy
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = g[iy][ix] + (g[iy][ix + 1] - g[iy][ix]) * tx
        b = g[iy + 1][ix] + (g[iy + 1][ix + 1] - g[iy + 1][ix]) * tx
        return a + (b - a) * ty
    return at


def tuft(s, x, y, color, kind=0):
    pats = [["x.x", ".x."], ["x...x", ".x.x.", "..x.."], [".x.", "x.x", ".x."], ["x.x.x", ".xxx."]]
    for j, row in enumerate(pats[kind % len(pats)]):
        for i, ch in enumerate(row):
            if ch == "x":
                s.set_at((x + i, y + j), color)


def flower(s, x, y, petal=(255, 250, 240), center=(252, 210, 110)):
    for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
        s.set_at((x + dx, y + dy), petal)
    s.set_at((x, y), center)


def paint_grass(s, rect, rng, density=1.0, palette=GRASS):
    """Pinta grama no estilo das referências, em resolução de mundo."""
    noise = _noise(rect.w, rect.h, 14, rng)
    fine = _noise(rect.w, rect.h, 5, rng)
    base, mid, deep, deeper, darkest = palette[1], palette[2], palette[3], palette[4], palette[4]
    edge = []
    for y in range(rect.h):
        for x in range(rect.w):
            v = noise(x, y) * .75 + fine(x, y) * .25 + (rng.random() - .5) * .06
            if v > .66:
                c = deeper
            elif v > .55:
                c = deep
                if v > .64:
                    edge.append((x, y))
            elif v > .5:
                c = mid
                edge.append((x, y)) if rng.random() < .05 else None
            else:
                c = base
            s.set_at((rect.x + x, rect.y + y), c)
    for _ in range(int(rect.w * rect.h / 90 * density)):          # tufos escuros nas manchas
        if not edge:
            break
        x, y = rng.choice(edge)
        tuft(s, rect.x + x - 1, rect.y + y - 1, darkest if rng.random() < .6 else deep, rng.randint(0, 3))
    for _ in range(int(rect.w * rect.h / 260 * density)):         # tufos claros
        x, y = rng.randrange(rect.w - 4), rng.randrange(rect.h - 3)
        tuft(s, rect.x + x, rect.y + y, palette[0], rng.randint(0, 3))
    for _ in range(int(rect.w * rect.h / 700 * density)):         # florzinhas
        x, y = rng.randrange(1, rect.w - 2), rng.randrange(1, rect.h - 2)
        flower(s, rect.x + x, rect.y + y,
               rng.choice([(255, 250, 240), (255, 250, 240), (252, 170, 186), (214, 180, 232)]))


def paint_dirt(s, rect, rng, base=(234, 202, 154)):
    for y in range(rect.h):
        for x in range(rect.w):
            c = base if rng.random() > .08 else dark(base, .12)
            s.set_at((rect.x + x, rect.y + y), c)
    for _ in range(rect.w * rect.h // 40):
        x, y = rect.x + rng.randrange(rect.w), rect.y + rng.randrange(rect.h)
        s.set_at((x, y), light(base, .4))


# ============================================================ sprites da natureza (em pixel de mundo)
def tree_sprite(rng, kind="green"):
    pal = {"green": [(84, 132, 84), (110, 166, 96), (142, 194, 108), (186, 222, 132)],
           "pink": [(214, 120, 140), (240, 156, 170), (252, 188, 196), (255, 222, 222)],
           "dark": [(66, 112, 82), (88, 140, 92), (116, 170, 104), (160, 206, 124)]}[kind]
    s = pygame.Surface((42, 54), pygame.SRCALPHA)
    pygame.draw.rect(s, (130, 86, 64), (18, 34, 7, 18))
    pygame.draw.rect(s, (104, 66, 52), (22, 34, 3, 18))
    pygame.draw.rect(s, (150, 104, 76), (18, 34, 2, 18))
    blobs = [(21, 22, 15), (10, 27, 10), (32, 27, 10), (15, 13, 10), (28, 13, 10), (21, 8, 8)]
    for bx, by, r in blobs:
        pygame.draw.circle(s, pal[0], (bx, by + 2), r)
    for bx, by, r in blobs:
        pygame.draw.circle(s, pal[1], (bx, by), r - 1)
    for bx, by, r in blobs[3:]:
        pygame.draw.circle(s, pal[2], (bx - 2, by - 2), r - 4)
    for _ in range(26):                                        # folhinhas/textura
        x, y = rng.randrange(4, 38), rng.randrange(2, 34)
        if s.get_at((x, y)).a:
            tuft(s, x, y, pal[0] if y > 18 else pal[3], rng.randint(0, 2))
    if kind == "pink":
        for _ in range(10):
            x, y = rng.randrange(6, 36), rng.randrange(4, 30)
            if s.get_at((x, y)).a:
                s.set_at((x, y), (255, 255, 255))
    return outline(s, dark(pal[0], .45))


def bush_sprite(rng, flowers=True):
    s = pygame.Surface((24, 15), pygame.SRCALPHA)
    pal = [(96, 150, 90), (126, 182, 98), (166, 210, 112)]
    for bx, by, r in ((7, 9, 6), (13, 7, 7), (18, 9, 5)):
        pygame.draw.circle(s, pal[0], (bx, by + 1), r)
        pygame.draw.circle(s, pal[1], (bx, by), r - 1)
    pygame.draw.circle(s, pal[2], (11, 5), 3)
    if flowers:
        c = rng.choice([(255, 250, 240), (252, 150, 170), (252, 210, 110), (214, 170, 232), (246, 120, 110)])
        for _ in range(4):
            flower(s, rng.randrange(3, 20), rng.randrange(3, 11), c)
    return outline(s, (58, 100, 72))


def rock_sprite(rng, size=1.0, moss=True):
    """Pedra em camadas, como na referência: base → rachaduras → luz → musgo → contorno."""
    w, h = int(16 * size) + 4, int(12 * size) + 4
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    base, top, crack, hi = (168, 162, 170), (196, 190, 196), (122, 114, 126), (232, 226, 228)
    pts = [(2, h - 4), (1, h // 2), (w // 3, 2), (w - w // 3, 1), (w - 2, h // 2 - 1), (w - 2, h - 4), (w // 2, h - 2)]
    pygame.draw.polygon(s, base, pts)
    pygame.draw.polygon(s, top, [(3, h // 2), (w // 3, 3), (w - w // 3, 2), (w - 3, h // 2 - 1), (w // 2, h // 2 + 1)])
    x = rng.randrange(w // 3, w - w // 3)
    pygame.draw.lines(s, crack, False, [(x, 3), (x - 1, h // 2 - 1), (x + 1, h // 2 + 2)], 1)
    for k in range(3):
        s.set_at((w // 3 + k, 3), hi)
    s.set_at((4, h // 2 - 1), hi)
    if moss:
        for _ in range(int(5 * size) + 2):
            mx, my = rng.randrange(3, w - 3), rng.randrange(2, h // 2 + 1)
            if s.get_at((mx, my)).a:
                s.set_at((mx, my), rng.choice([(126, 182, 98), (150, 198, 104)]))
    return outline(s, (74, 64, 78))


def stump_sprite():
    s = pygame.Surface((14, 9), pygame.SRCALPHA)
    pygame.draw.rect(s, (130, 86, 64), (1, 3, 12, 6))
    pygame.draw.ellipse(s, (200, 160, 112), (1, 0, 12, 6))
    pygame.draw.ellipse(s, (170, 124, 88), (4, 1, 6, 3), 1)
    return outline(s, (82, 52, 46))


def mushroom_sprite(cap=(240, 120, 110)):
    s = pygame.Surface((7, 7), pygame.SRCALPHA)
    pygame.draw.rect(s, (250, 238, 220), (2, 3, 3, 4))
    pygame.draw.ellipse(s, cap, (0, 0, 7, 4))
    s.set_at((2, 1), (255, 250, 240))
    return outline(s)


def lamp_sprite():
    s = pygame.Surface((9, 40), pygame.SRCALPHA)
    pygame.draw.rect(s, (98, 80, 92), (4, 6, 2, 34))
    pygame.draw.rect(s, (98, 80, 92), (2, 38, 6, 2))
    pygame.draw.rect(s, (98, 80, 92), (1, 0, 8, 2))
    pygame.draw.rect(s, (252, 220, 140), (2, 2, 6, 4))
    return outline(s)


# ============================================================ mãos (adaptadas da referência fotográfica)
SKIN = [(122, 70, 70), (208, 146, 124), (238, 188, 158), (252, 216, 190), (252, 222, 210)]


def _finger(s, base, ang, lengths, curl, width):
    """Dedo com 2 falanges; curl dobra a ponta pra dentro (pegar)."""
    x, y = base
    pts = [(x, y)]
    a = ang
    for i, L in enumerate(lengths):
        a += curl * (0.5 + .45 * i)
        L = L * (1 - curl * .35 * i)
        x, y = x + math.sin(a) * L, y - math.cos(a) * L
        pts.append((x, y))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        pygame.draw.line(s, SKIN[1], (x0 + 1, y0), (x1 + 1, y1), width)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        pygame.draw.line(s, SKIN[2], (x0, y0), (x1, y1), width - 1)
        pygame.draw.circle(s, SKIN[2], (x1, y1), (width - 1) / 2)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        pygame.draw.line(s, SKIN[3], (x0 - 1, y0), (x1 - 1, y1), 1)
    tx, ty = pts[-1]
    s.set_at((int(tx), int(ty)), SKIN[4])                # unha
    jx, jy = pts[1]
    s.set_at((int(jx), int(jy)), SKIN[1])                # dobrinha da junta
    return pts


def hand_sprite(curl=0.0, sleeve=(150, 112, 196)):
    """Mão esquerda (na tela), palma pra frente, polegar pra fora, dedos abertos e curvos.
    curl 0 = aberta (alcançando), 1 = fechando no item."""
    s = pygame.Surface((56, 70), pygame.SRCALPHA)
    # antebraço + manga
    pygame.draw.polygon(s, SKIN[1], [(18, 70), (34, 70), (34, 46), (17, 46)])
    pygame.draw.polygon(s, SKIN[2], [(19, 70), (32, 70), (32, 46), (19, 46)])
    pygame.draw.rect(s, sleeve, (14, 58, 24, 12))
    pygame.draw.rect(s, light(sleeve, .3), (14, 58, 24, 3))
    # palma
    pygame.draw.ellipse(s, SKIN[1], (13, 26, 26, 26))
    pygame.draw.ellipse(s, SKIN[2], (13, 25, 25, 25))
    pygame.draw.ellipse(s, SKIN[3], (18, 30, 12, 10))
    for x, y in ((20, 42), (21, 43), (22, 44), (27, 38), (28, 39)):
        s.set_at((x, y), SKIN[1])                         # linhas da palma
    # dedos: indicador → mindinho (base, ângulo, falanges)
    fingers = [((17, 29), -.30, (9, 8)), ((23, 27), -.08, (10, 9)), ((29, 28), .14, (9, 8)), ((34, 31), .36, (7, 6))]
    for (b, a, L) in fingers:
        _finger(s, b, a, L, curl * 1.05, 5)
    # polegar (pra fora, à esquerda)
    _finger(s, (15, 40), -1.05 + curl * .5, (7, 6), curl * .9, 6)
    return outline(s, SKIN[0])


_hand_cache = {}


def hands(curl):
    """Par de mãos ampliadas (esquerda, direita) já em escala de tela."""
    k = round(curl * 8) / 8
    if k not in _hand_cache:
        left = hand_sprite(k)
        left = pygame.transform.rotate(left, -22)
        left = up(left)
        _hand_cache[k] = (left, pygame.transform.flip(left, True, False))
    return _hand_cache[k]


# ============================================================ efeito de TV CRT
class CRT:
    def __init__(self):
        self.scan = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(0, H, P):
            pygame.draw.line(self.scan, (0, 0, 0, 70), (0, y + P - 1), (W, y + P - 1))
        self.mask = pygame.Surface((W, H))
        cols = [(255, 226, 226), (226, 255, 226), (226, 226, 255)]
        for x in range(W):
            pygame.draw.line(self.mask, cols[x % 3], (x, 0), (x, H))
        self.frame = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(60):                               # vinheta
            a = int(150 * (1 - i / 60) ** 2.2)
            pygame.draw.rect(self.frame, (20, 8, 14, a), (i * 2, i * 2, W - i * 4, H - i * 4), 2, border_radius=60)
        bez = pygame.Surface((W, H), pygame.SRCALPHA)
        bez.fill((24, 14, 20, 255))
        pygame.draw.rect(bez, (0, 0, 0, 0), (10, 10, W - 20, H - 20), border_radius=44)
        pygame.draw.rect(bez, (60, 40, 50, 255), (10, 10, W - 20, H - 20), 2, border_radius=44)
        self.frame.blit(bez, (0, 0))
        self.t = 0

    def apply(self, surf):
        self.t += 1
        glow = pygame.transform.smoothscale(surf, (W // 6, H // 6))
        glow = pygame.transform.smoothscale(glow, (W, H))
        glow.set_alpha(38)
        surf.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        surf.blit(self.mask, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        surf.blit(self.scan, (0, 0))
        if self.t % 3 == 0:                               # leve tremulação
            ov = pygame.Surface((W, H))
            ov.fill((4, 3, 3))
            surf.blit(ov, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
        surf.blit(self.frame, (0, 0))


# ============================================================ paleta única (tons quentes e aconchegantes)
PALETTE = [
    (11, 6, 9), (25, 16, 18), (40, 28, 26), (47, 17, 13), (64, 30, 22), (64, 39, 28), (86, 37, 24),
    (59, 58, 36), (88, 50, 31), (101, 50, 33), (106, 66, 32), (123, 52, 30), (105, 66, 52), (119, 69, 36),
    (127, 69, 40), (145, 68, 39), (120, 86, 57), (135, 80, 52), (149, 86, 53), (137, 94, 64), (150, 99, 66),
    (159, 98, 59), (165, 102, 64), (137, 119, 76), (178, 101, 59), (161, 122, 86), (178, 119, 80),
    (159, 138, 96), (193, 124, 77), (203, 139, 93), (172, 157, 113), (219, 160, 109), (221, 189, 138),
    (240, 223, 171), (250, 240, 214), (255, 232, 170), (252, 206, 120), (238, 140, 82), (214, 96, 62),
    (176, 64, 48), (226, 150, 130), (206, 140, 130), (168, 96, 104), (236, 184, 142), (246, 210, 170),
    (52, 78, 58), (74, 104, 66), (102, 132, 76), (138, 160, 90), (176, 186, 110), (44, 92, 86),
    (70, 124, 110), (110, 156, 138), (44, 52, 80), (60, 96, 120), (96, 140, 156), (150, 190, 190),
    (74, 112, 178), (186, 150, 196), (130, 104, 140), (90, 82, 86), (120, 110, 106), (150, 140, 130),
    (176, 172, 172), (196, 186, 172), (138, 40, 50),
]


_PAL = None


def _palette():
    global _PAL
    if _PAL is None:
        _PAL = Palette()
    return _PAL


class Palette:
    """Remapeia a tela inteira pra paleta do jogo.
    Com numpy: tabela 32×32×32 → cor mais próxima (preciso).
    Sem numpy: usa o mapeamento de 8 bits do SDL (mais grosseiro)."""

    def __init__(self, colors=PALETTE):
        self.colors = list(colors) + [(0, 0, 0)] * (256 - len(colors))
        self.p8 = None
        self.np = None
        try:
            import numpy as np
            import pygame.surfarray  # noqa: F401
            pal = np.array(colors, dtype=np.int32)
            lv = np.arange(32) * 8 + 4
            r, g, b = np.meshgrid(lv, lv, lv, indexing="ij")
            grid = np.stack([r, g, b], -1).reshape(-1, 1, 3)
            wts = np.array([3, 4, 2])
            best = np.empty(grid.shape[0], dtype=np.int32)
            for i in range(0, grid.shape[0], 4096):
                d = (((grid[i:i + 4096] - pal[None]) ** 2) * wts).sum(-1)
                best[i:i + 4096] = d.argmin(1)
            self.lut = pal[best].astype(np.uint8)
            self.np = np
        except Exception as e:  # noqa: BLE001
            print("[paleta] sem numpy, usando modo simples:", e)

    def apply(self, surf):
        if self.np is not None:
            try:
                a = pygame.surfarray.pixels3d(surf)
                idx = ((a[..., 0] >> 3).astype(self.np.int32) << 10) | ((a[..., 1] >> 3).astype(self.np.int32) << 5) | (a[..., 2] >> 3)
                a[...] = self.lut[idx]
                del a
                return
            except Exception:  # noqa: BLE001
                self.np = None
        if self.p8 is None or self.p8.get_size() != surf.get_size():
            self.p8 = pygame.Surface(surf.get_size(), 0, 8)
            self.p8.set_palette(self.colors)
        self.p8.blit(surf, (0, 0))
        surf.blit(self.p8, (0, 0))
