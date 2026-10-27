"""Cenários da casa do protagonista, do bairro e os quadros de história.
Tudo procedural; se existir assets/<nome>.png, ele substitui o desenho."""
import math
import random

import pygame

import art
import assets
import pixel
from art import (W, H, BUTTER, CORAL, CREAM, INK, LILAC, MINT, PEACH, ROSE, WOOD, WOOD_D,
                 blit_glow, darker, lighter, mix, rr, sparkle)

_cache = {}


def _cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


def _planks(s, rect, base, step=None):
    """Piso de tábuas (técnica da referência): linhas horizontais regulares,
    emendas verticais espalhadas, algumas tábuas num 2º tom e frestas mais escuras."""
    rng = random.Random(rect.x * 7 + rect.y)
    P = pixel.P
    w, h = rect.w // P + 1, rect.h // P + 1
    t = pygame.Surface((w, h))
    base = (196, 146, 112)           # madeira quente (depois da luz vira o marrom da paleta)
    alt = pixel.mix(base, (193, 124, 77), .6)
    gap = pixel.dark(base, .35)
    line = pixel.dark(base, .2)
    t.fill(base)
    row_h = 7
    for r, y in enumerate(range(0, h, row_h)):
        x = -rng.randint(0, 30)
        while x < w:
            L = rng.randint(28, 64)
            if rng.random() < .25:
                pygame.draw.rect(t, alt, (x, y + 1, L, row_h - 1))
            pygame.draw.line(t, gap, (x, y), (x, y + row_h - 1))
            if rng.random() < .3:
                t.set_at((x + rng.randint(3, max(4, L - 3)), y + rng.randint(2, row_h - 2)), line)
            x += L
        pygame.draw.line(t, gap if r % 3 == 0 else line, (0, y), (w, y))
    s.blit(pixel.up(t), rect.topleft, pygame.Rect(0, 0, rect.w, rect.h))


def _wall(s, rect, base, pattern="dots"):
    art._vgrad(s, rect, lighter(base, .08), base)
    rng = random.Random(rect.width)
    if pattern == "dots":
        for y in range(rect.top + 14, rect.bottom - 40, 28):
            for x in range(rect.left + (y // 28 % 2) * 14 + 10, rect.right, 28):
                pygame.draw.circle(s, lighter(base, .25), (x, y), 3)
    elif pattern == "stripes":
        for x in range(rect.left, rect.right, 36):
            pygame.draw.rect(s, lighter(base, .12), (x, rect.top, 16, rect.height))
    elif pattern == "hearts":
        for y in range(rect.top + 16, rect.bottom - 40, 34):
            for x in range(rect.left + (y // 34 % 2) * 17 + 12, rect.right, 34):
                c = lighter(base, .22)
                pygame.draw.circle(s, c, (x - 2, y), 3)
                pygame.draw.circle(s, c, (x + 2, y), 3)
                pygame.draw.polygon(s, c, [(x - 5, y + 1), (x + 5, y + 1), (x, y + 6)])


def _wainscot(s, top, bottom, x0=0, x1=W):
    pygame.draw.rect(s, (255, 242, 228), (x0, top, x1 - x0, bottom - top))
    for x in range(x0 + 10, x1, 24):
        pygame.draw.line(s, (240, 220, 204), (x, top + 4), (x, bottom - 4), 2)
    pygame.draw.rect(s, (236, 206, 186), (x0, top, x1 - x0, 5))
    pygame.draw.rect(s, WOOD_D, (x0, bottom - 6, x1 - x0, 6))


def _caps(s, openings=()):
    """Topo das paredes em tijolinho escuro (moldura do cômodo, estilo RPG)."""
    cap, mort = (25, 16, 18), (40, 28, 26)
    for r in ((0, 0, W, 15), (0, 0, 15, H), (W - 15, 0, 15, H), (0, H - 15, W, 15)):
        pygame.draw.rect(s, cap, r)
    for y in range(0, H, 9):
        for x in range(0 if y // 9 % 2 else 9, W, 18):
            for r in ((0, 0, W, 15), (0, 0, 15, H), (W - 15, 0, 15, H), (0, H - 15, W, 15)):
                if pygame.Rect(r).collidepoint(x, y):
                    pygame.draw.rect(s, mort, (x, y, 3, 9))
                    break
    for r in ((15, 15, W - 30, 3), (15, 15, 3, H - 30), (W - 18, 15, 3, H - 30), (15, H - 18, W - 30, 3)):
        pygame.draw.rect(s, (88, 50, 31), r)                         # rodapé de madeira
    for x0, x1 in openings:
        pygame.draw.rect(s, (106, 66, 32), (x0, H - 18, x1 - x0, 18))


def _window(s, x, y, w, h, curtain=CORAL):
    pygame.draw.rect(s, (255, 248, 236), (x - 6, y - 6, w + 12, h + 12), border_radius=6)
    art._vgrad(s, pygame.Rect(x, y, w, h), (255, 196, 170), (255, 236, 186))
    pygame.draw.circle(s, (255, 246, 210), (x + w * .7, y + h * .45), 14)
    pygame.draw.line(s, (255, 248, 236), (x + w // 2, y), (x + w // 2, y + h), 5)
    pygame.draw.line(s, (255, 248, 236), (x, y + h // 2), (x + w, y + h // 2), 5)
    for cx, sgn in ((x - 10, 1), (x + w + 10, -1)):
        pts = [(cx, y - 10), (cx + sgn * 30, y - 10), (cx + sgn * 14, y + h + 16), (cx, y + h + 20)]
        pygame.draw.polygon(s, curtain, pts)
        pygame.draw.line(s, darker(curtain, .15), (cx + sgn * 10, y - 6), (cx + sgn * 8, y + h + 14), 2)
    pygame.draw.rect(s, WOOD_D, (x - 20, y - 16, w + 40, 6), border_radius=3)
    pygame.draw.rect(s, (255, 244, 230), (x - 10, y + h + 6, w + 20, 8), border_radius=3)


def _plant(s, x, y, size=1.0, pot=CORAL):
    k = size
    for a in range(-3, 4):
        ang = -math.pi / 2 + a * .35
        tip = (x + math.cos(ang) * 46 * k, y - 30 * k + math.sin(ang) * 40 * k)
        mid = ((x + tip[0]) / 2, (y - 24 * k + tip[1]) / 2)
        nx, ny = -(tip[1] - (y - 24 * k)) * .22, (tip[0] - x) * .22
        pygame.draw.polygon(s, (112, 176, 102) if a % 2 else (138, 196, 112),
                            [(x, y - 24 * k), (mid[0] + nx, mid[1] + ny), tip, (mid[0] - nx, mid[1] - ny)])
    pygame.draw.polygon(s, pot, [(x - 22 * k, y - 26 * k), (x + 22 * k, y - 26 * k), (x + 16 * k, y), (x - 16 * k, y)])
    pygame.draw.rect(s, darker(pot, .12), rr(x - 24 * k, y - 30 * k, 48 * k, 8 * k), border_radius=3)


def _shadow(s, rect, alpha=50):
    sh = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (90, 40, 40, alpha), sh.get_rect())
    s.blit(sh, rect)


def _rug(s, rect, color, rim):
    pygame.draw.ellipse(s, rim, rect)
    pygame.draw.ellipse(s, color, rect.inflate(-16, -12))
    pygame.draw.ellipse(s, rim, rect.inflate(-46, -34), 3)


def _clock(s, cx, cy, r):
    pygame.draw.circle(s, CORAL, (cx, cy), r + 3)
    pygame.draw.circle(s, CREAM, (cx, cy), r)
    pygame.draw.line(s, INK, (cx, cy), (cx, cy - r * .7), 2)       # 12
    pygame.draw.line(s, INK, (cx, cy), (cx, cy + r * .5), 3)       # 6
    pygame.draw.circle(s, CORAL, (cx - r * .7, cy - r - 2), r * .35)
    pygame.draw.circle(s, CORAL, (cx + r * .7, cy - r - 2), r * .35)


# ============================================================ quarto
BED = pygame.Rect(56, 118, 180, 255)


def _bedroom_static():
    s = pygame.Surface((W, H))
    _wall(s, pygame.Rect(0, 0, W, 190), (252, 210, 186), "hearts")
    _wainscot(s, 140, 190)
    _planks(s, pygame.Rect(0, 190, W, H - 190), (230, 172, 128))
    pygame.draw.rect(s, (236, 184, 160), (0, 0, 14, H))
    pygame.draw.rect(s, (236, 184, 160), (W - 14, 0, 14, H))
    pygame.draw.rect(s, (236, 184, 160), (0, H - 16, W, 16))
    pygame.draw.rect(s, (204, 150, 120), (430, H - 16, 100, 16))
    pygame.draw.rect(s, (246, 196, 120), (440, H - 40, 80, 26), border_radius=6)
    _window(s, 290, 30, 110, 90)
    # quadro de gatinho
    pygame.draw.rect(s, WOOD_D, (100, 20, 100, 76), border_radius=4)
    pygame.draw.rect(s, (255, 236, 214), (106, 26, 88, 64))
    pygame.draw.circle(s, (70, 60, 76), (150, 66), 14)
    pygame.draw.polygon(s, (70, 60, 76), [(138, 58), (141, 44), (148, 54)])
    pygame.draw.polygon(s, (70, 60, 76), [(162, 58), (159, 44), (152, 54)])
    # cama
    _shadow(s, pygame.Rect(BED.x - 6, BED.bottom - 18, BED.w + 12, 30))
    pygame.draw.rect(s, WOOD_D, (BED.x, BED.y, BED.w, 46), border_radius=10)
    pygame.draw.rect(s, (255, 244, 234), (BED.x + 8, BED.y + 36, BED.w - 16, BED.h - 40), border_radius=10)
    pygame.draw.rect(s, (255, 252, 246), (BED.x + 26, BED.y + 44, BED.w - 52, 50), border_radius=18)
    quilt = pygame.Rect(BED.x + 4, BED.y + 108, BED.w - 8, BED.h - 112)
    cols = [PEACH, MINT, BUTTER, ROSE, LILAC]
    for i, y in enumerate(range(quilt.top, quilt.bottom, 36)):
        for j, x in enumerate(range(quilt.left, quilt.right, 43)):
            pygame.draw.rect(s, cols[(i + j) % 5], (x, y, min(43, quilt.right - x), min(36, quilt.bottom - y)))
    pygame.draw.rect(s, (255, 250, 240), (quilt.x, quilt.y, quilt.w, 12))
    pygame.draw.rect(s, darker(PEACH, .2), quilt, 2, border_radius=6)
    # criado-mudo + despertador
    pygame.draw.rect(s, WOOD, (244, 148, 60, 66), border_radius=6)
    pygame.draw.rect(s, WOOD_D, (244, 148, 60, 66), 2, border_radius=6)
    pygame.draw.circle(s, WOOD_D, (274, 186), 3)
    _clock(s, 274, 136, 13)
    # banheiro
    pygame.draw.rect(s, (255, 248, 238), (582, 42, 106, 150), border_radius=8)
    pygame.draw.rect(s, (238, 196, 150), (590, 50, 90, 142), border_top_left_radius=8, border_top_right_radius=8)
    pygame.draw.circle(s, (190, 230, 236), (635, 88), 18)
    pygame.draw.circle(s, (255, 248, 238), (635, 88), 18, 4)
    pygame.draw.circle(s, WOOD_D, (668, 128), 5)
    pygame.draw.rect(s, MINT, (596, 194, 78, 16), border_radius=8)
    art.text(s, "banho", art.font(14, bold=True), INK, (635, 116), "midtop")
    # guarda-roupa
    pygame.draw.rect(s, WOOD_D, (754, 18, 162, 194), border_radius=8)
    pygame.draw.rect(s, WOOD, (762, 30, 70, 172), border_radius=4)
    pygame.draw.rect(s, WOOD, (838, 30, 70, 172), border_radius=4)
    for x in (822, 848):
        pygame.draw.circle(s, BUTTER, (x, 118), 5)
    pygame.draw.rect(s, darker(WOOD_D, .1), (748, 10, 174, 14), border_radius=6)
    # escrivaninha + cadeira
    _shadow(s, pygame.Rect(790, 420, 150, 24))
    pygame.draw.rect(s, WOOD, (796, 356, 140, 72), border_radius=6)
    pygame.draw.rect(s, WOOD_D, (796, 356, 140, 72), 2, border_radius=6)
    pygame.draw.rect(s, (255, 252, 244), (812, 366, 54, 40))
    pygame.draw.circle(s, (70, 60, 76), (838, 388), 9)
    pygame.draw.rect(s, CORAL, (880, 368, 14, 22), border_radius=3)
    for k in range(3):
        pygame.draw.line(s, [CORAL, MINT, BUTTER][k], (882 + k * 4, 368), (880 + k * 6, 356), 2)
    pygame.draw.rect(s, ROSE, (842, 448, 46, 30), border_radius=8)
    # tapete, planta, caixa de brinquedos
    _rug(s, pygame.Rect(330, 340, 300, 150), (220, 186, 232), (250, 214, 240))
    _plant(s, 90, 590, 1.1)
    pygame.draw.rect(s, BUTTER, (40, 420, 70, 50), border_radius=6)
    pygame.draw.rect(s, darker(BUTTER, .2), (40, 420, 70, 50), 3, border_radius=6)
    pygame.draw.circle(s, CORAL, (60, 418), 9)
    pygame.draw.rect(s, MINT, (76, 408, 18, 14), border_radius=3)
    # pufe, pilha de livros, varal de luzinhas, quadro de estrelas
    pygame.draw.ellipse(s, darker(BUTTER, .15), (612, 520, 90, 62))
    pygame.draw.ellipse(s, BUTTER, (614, 516, 86, 54))
    for k, c in enumerate((CORAL, MINT, LILAC, PEACH)):
        pygame.draw.rect(s, c, (730, 560 - k * 12, 48 - k * 4, 11))
    for k in range(14):
        x = 420 + k * 24
        pygame.draw.circle(s, [BUTTER, ROSE, MINT][k % 3], (x, 18 + int(6 * math.sin(k * .9))), 5)
    pygame.draw.lines(s, WOOD_D, False, [(420 + k * 24, 18 + int(6 * math.sin(k * .9))) for k in range(14)], 1)
    pygame.draw.rect(s, (90, 70, 110), (460, 44, 90, 64))
    for x, y in ((476, 60), (500, 82), (528, 58), (520, 96), (482, 92)):
        pygame.draw.circle(s, BUTTER, (x, y), 3)
    pygame.draw.rect(s, WOOD_D, (460, 44, 90, 64), 4)
    _caps(s, [(430, 530)])
    return s


def draw_bedroom(s, t):
    if not assets.blit_bg(s, "bg_quarto"):
        s.blit(_cached("bedroom", _bedroom_static), (0, 0))
    rays = pygame.Surface((W, H))
    for k in range(3):
        x0 = 300 + k * 36
        pygame.draw.polygon(rays, (34, 22, 10), [(x0, 125), (x0 + 30, 125), (x0 + 200, 470), (x0 + 120, 470)])
    s.blit(rays, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    blit_glow(s, (886, 360), 50, (120, 90, 40), .6 + .1 * math.sin(t * 2))


# ============================================================ corredor
def _hall_static():
    s = pygame.Surface((W, H))
    _wall(s, pygame.Rect(0, 0, W, 210), (250, 198, 160), "stripes")
    _wainscot(s, 160, 210)
    _planks(s, pygame.Rect(0, 210, W, H - 210), (226, 166, 122))
    pygame.draw.rect(s, (240, 180, 146), (0, 0, 14, H))
    pygame.draw.rect(s, (240, 180, 146), (0, H - 16, W, 16))
    pygame.draw.rect(s, (204, 146, 112), (110, H - 16, 110, 16))
    # tapete passadeira (do quarto até a escada)
    for r in (pygame.Rect(118, 250, 96, 380), pygame.Rect(118, 250, 640, 86)):
        pygame.draw.rect(s, (236, 130, 120), r, border_radius=10)
        pygame.draw.rect(s, BUTTER, r.inflate(-14, -14), 2, border_radius=8)
    _window(s, 50, 34, 100, 84, curtain=MINT)
    # porta da mãe (mais acima)
    pygame.draw.rect(s, (255, 248, 238), (418, 48, 124, 162), border_radius=8)
    pygame.draw.rect(s, (246, 226, 206), (428, 58, 104, 152), border_top_left_radius=8, border_top_right_radius=8)
    pygame.draw.rect(s, (236, 212, 190), (440, 74, 80, 52), 3, border_radius=4)
    pygame.draw.rect(s, (236, 212, 190), (440, 140, 80, 52), 3, border_radius=4)
    pygame.draw.circle(s, (120, 170, 100), (480, 100), 22, 7)
    for a in range(8):
        pygame.draw.circle(s, [CORAL, BUTTER, ROSE][a % 3], (480 + math.cos(a * .8) * 22, 100 + math.sin(a * .8) * 22), 4)
    pygame.draw.circle(s, BUTTER, (520, 140), 5)
    pygame.draw.rect(s, MINT, (440, 212, 80, 14), border_radius=7)
    # fotos de família
    for x, y, w, h in ((236, 40, 70, 56), (318, 30, 56, 70), (262, 104, 90, 48)):
        pygame.draw.rect(s, WOOD_D, (x, y, w, h), border_radius=3)
        pygame.draw.rect(s, (255, 226, 196), (x + 5, y + 5, w - 10, h - 10))
        art._vgrad(s, pygame.Rect(x + 5, y + 5, w - 10, (h - 10) // 2), (160, 210, 230), (255, 226, 196))
        pygame.draw.circle(s, (150, 82, 64), (x + w * .4, y + h * .62), 6)
        pygame.draw.circle(s, (124, 76, 56), (x + w * .6, y + h * .7), 4)
    # aparador com girassóis + abajur
    pygame.draw.rect(s, WOOD, (590, 156, 130, 50), border_radius=6)
    pygame.draw.rect(s, WOOD_D, (590, 156, 130, 50), 2, border_radius=6)
    pygame.draw.rect(s, (130, 190, 200), (622, 120, 26, 38), border_radius=8)
    for dx, dy in ((-14, -8), (0, -22), (14, -10)):
        pygame.draw.line(s, (100, 160, 90), (635, 130), (635 + dx, 112 + dy), 3)
        pygame.draw.circle(s, (252, 200, 70), (635 + dx, 110 + dy), 11)
        pygame.draw.circle(s, (150, 96, 60), (635 + dx, 110 + dy), 5)
    pygame.draw.polygon(s, PEACH, [(676, 108), (706, 108), (714, 134), (668, 134)])
    pygame.draw.rect(s, WOOD_D, (688, 134, 6, 22))
    # banco com almofadas
    pygame.draw.rect(s, WOOD, (24, 330, 70, 130), border_radius=8)
    pygame.draw.rect(s, ROSE, (32, 340, 54, 50), border_radius=12)
    pygame.draw.rect(s, BUTTER, (32, 396, 54, 50), border_radius=12)
    _plant(s, 70, 610, 1.0, pot=MINT)
    _plant(s, 735, 236, .8, pot=CORAL)
    pygame.draw.rect(s, (236, 206, 160), (560, 540, 64, 44), border_radius=8)       # cesto de roupas
    for x in range(564, 622, 8):
        pygame.draw.line(s, (200, 160, 110), (x, 544), (x, 582), 2)
    pygame.draw.ellipse(s, (255, 250, 244), (566, 528, 52, 22))
    _rug(s, pygame.Rect(330, 420, 200, 120), (250, 214, 160), (242, 160, 140))
    for x, y, w, h in ((560, 60, 26, 34), (390, 120, 18, 22)):
        pygame.draw.rect(s, WOOD_D, (x, y, w, h))
        pygame.draw.rect(s, MINT, (x + 3, y + 3, w - 6, h - 6))
    # escada descendo (direita)
    for i in range(9):
        y = 240 + i * 40
        pygame.draw.rect(s, mix((236, 184, 140), (150, 100, 80), i / 9), (780, y, 168, 40))
        pygame.draw.line(s, darker(WOOD, .3), (780, y), (948, y), 2)
    pygame.draw.line(s, WOOD_D, (772, 230), (772, 600), 6)
    for i in range(9):
        pygame.draw.line(s, WOOD_D, (772, 240 + i * 40), (790, 240 + i * 40), 4)
    _caps(s, [(110, 220)])
    return s


def draw_hall(s, t, name=""):
    if not assets.blit_bg(s, "bg_corredor"):
        s.blit(_cached("hall", _hall_static), (0, 0))
    for x in (200, 740):
        pygame.draw.rect(s, BUTTER, (x - 8, 60, 16, 22), border_radius=6)
        blit_glow(s, (x, 70), 60, (140, 100, 50), .7 + .08 * math.sin(t * 3 + x))
    blit_glow(s, (691, 120), 50, (140, 100, 50), .7)
    if name:
        r = pygame.Rect(0, 0, max(70, art.font(14, bold=True).size(name)[0] + 20), 22)
        r.midbottom = (165, H - 18)
        pygame.draw.rect(s, CREAM, r, border_radius=8)
        pygame.draw.rect(s, CORAL, r, 2, border_radius=8)
        art.text(s, name, art.font(14, bold=True), INK, r.center, "center")


# ============================================================ térreo
KITCHEN_X = 340


def _ground_static():
    s = pygame.Surface((W, H))
    _wall(s, pygame.Rect(0, 0, W, 200), (250, 204, 170), "dots")
    for y in range(110, 200, 14):                       # azulejos da cozinha
        for x in range(0, KITCHEN_X, 14):
            pygame.draw.rect(s, (220, 238, 226) if (x + y) // 14 % 2 else (250, 246, 236), (x, y, 13, 13))
    _wall(s, pygame.Rect(630, 0, W - 630, 200), (244, 196, 196), "stripes")
    _wainscot(s, 160, 200, 340, W)
    for y in range(200, H, 40):                          # piso xadrez
        for x in range(0, KITCHEN_X, 40):
            pygame.draw.rect(s, (255, 236, 214) if (x + y) // 40 % 2 else (250, 200, 170), (x, y, 40, 40))
    _planks(s, pygame.Rect(KITCHEN_X, 200, W - KITCHEN_X, H - 200), (228, 168, 124))
    pygame.draw.rect(s, (236, 176, 146), (0, H - 16, W, 16))
    pygame.draw.rect(s, (204, 146, 112), (430, H - 16, 100, 16))
    pygame.draw.rect(s, CORAL, (436, H - 46, 88, 30), border_radius=6)
    art.text(s, "Bem-vindo", art.font(13, bold=True), CREAM, (480, H - 31), "center")
    # escada subindo (centro)
    for i in range(7):
        w = 130 - i * 6
        pygame.draw.rect(s, mix((232, 178, 134), (255, 226, 196), i / 7), (480 - w // 2, 190 - i * 24, w, 24))
        pygame.draw.line(s, WOOD_D, (480 - w // 2, 190 - i * 24), (480 + w // 2, 190 - i * 24), 2)
    pygame.draw.line(s, WOOD_D, (412, 214), (430, 30), 5)
    pygame.draw.line(s, WOOD_D, (548, 214), (530, 30), 5)
    # cozinha
    pygame.draw.rect(s, (176, 222, 200), (8, 50, 76, 168), border_radius=10)
    pygame.draw.line(s, darker(MINT, .25), (12, 110), (80, 110), 2)
    pygame.draw.rect(s, CREAM, (66, 70, 6, 30), border_radius=3)
    pygame.draw.rect(s, CREAM, (66, 120, 6, 40), border_radius=3)
    for x, y, c in ((20, 66, CORAL), (40, 130, BUTTER), (22, 150, LILAC)):
        pygame.draw.circle(s, c, (x, y), 5)
    pygame.draw.rect(s, (255, 252, 244), (28, 74, 26, 22))
    for x0 in range(92, 330, 60):
        pygame.draw.rect(s, (250, 226, 200), (x0, 24, 54, 66), border_radius=6)
        pygame.draw.rect(s, WOOD_D, (x0, 24, 54, 66), 2, border_radius=6)
        pygame.draw.circle(s, WOOD_D, (x0 + 27, 80), 3)
    pygame.draw.rect(s, (246, 222, 196), (86, 150, 248, 68), border_radius=6)
    pygame.draw.rect(s, (214, 174, 140), (86, 146, 248, 14), border_radius=6)
    for x0 in range(92, 330, 60):
        pygame.draw.rect(s, darker((246, 222, 196), .08), (x0, 166, 54, 46), 2, border_radius=4)
    # fogão
    pygame.draw.rect(s, (238, 236, 232), (96, 120, 66, 40), border_radius=6)
    for bx, by in ((112, 132), (146, 132), (112, 150), (146, 150)):
        pygame.draw.circle(s, (90, 80, 86), (bx, by), 7, 2)
    pygame.draw.ellipse(s, (70, 62, 70), (100, 120, 34, 22))
    # pia
    pygame.draw.rect(s, (200, 214, 222), (176, 126, 58, 26), border_radius=8)
    pygame.draw.line(s, (170, 180, 190), (205, 112), (205, 128), 4)
    # tábua com pão
    pygame.draw.rect(s, WOOD, (242, 128, 44, 22), border_radius=6)
    pygame.draw.ellipse(s, (226, 170, 100), (246, 118, 36, 22))
    for k in range(3):
        pygame.draw.line(s, (196, 136, 76), (254 + k * 9, 122), (250 + k * 9, 134), 2)
    # cafeteira
    pygame.draw.rect(s, (110, 80, 76), (292, 96, 34, 58), border_radius=6)
    pygame.draw.rect(s, (190, 230, 236), (298, 122, 22, 24), border_radius=4)
    pygame.draw.rect(s, (80, 56, 52), (300, 134, 18, 12), border_radius=3)
    # mesa com toalha xadrez + cadeiras
    _shadow(s, pygame.Rect(80, 470, 170, 26))
    for cx in (70, 250):
        pygame.draw.rect(s, WOOD, (cx - 18, 420, 36, 40), border_radius=8)
        pygame.draw.rect(s, PEACH, (cx - 14, 424, 28, 20), border_radius=6)
    pygame.draw.rect(s, (255, 250, 244), (88, 396, 148, 80), border_radius=8)
    for x in range(88, 236, 18):
        pygame.draw.rect(s, (246, 170, 168), (x, 396, 9, 80))
    for y in range(396, 476, 18):
        pygame.draw.rect(s, (250, 196, 192), (88, y, 148, 9))
    pygame.draw.rect(s, darker(CORAL, .1), (88, 396, 148, 80), 2, border_radius=8)
    pygame.draw.rect(s, (130, 190, 200), (152, 410, 18, 22), border_radius=6)
    pygame.draw.circle(s, BUTTER, (161, 404), 7)
    # sala de estar
    pygame.draw.rect(s, WOOD, (638, 30, 52, 178), border_radius=4)
    for y in range(44, 200, 38):
        pygame.draw.line(s, WOOD_D, (640, y + 30), (688, y + 30), 3)
        for k in range(5):
            pygame.draw.rect(s, [CORAL, MINT, BUTTER, LILAC, ROSE][(k + y) % 5], (644 + k * 9, y, 8, 30))
    pygame.draw.rect(s, WOOD_D, (700, 150, 124, 48), border_radius=6)
    pygame.draw.rect(s, (90, 80, 90), (716, 86, 92, 66), border_radius=10)
    pygame.draw.rect(s, (160, 200, 210), (724, 94, 76, 50), border_radius=6)
    # porta do quintal
    pygame.draw.rect(s, (255, 248, 238), (848, 40, 92, 162), border_radius=8)
    pygame.draw.rect(s, (226, 190, 150), (856, 48, 76, 154))
    art._vgrad(s, pygame.Rect(866, 60, 56, 70), (180, 220, 140), (140, 196, 110))
    pygame.draw.rect(s, (255, 248, 238), (866, 60, 56, 70), 4)
    pygame.draw.circle(s, BUTTER, (922, 150), 5)
    _rug(s, pygame.Rect(676, 370, 250, 190), (246, 208, 150), (240, 150, 130))
    pygame.draw.rect(s, WOOD, (728, 400, 134, 40), border_radius=8)
    pygame.draw.rect(s, WOOD_D, (728, 400, 134, 40), 2, border_radius=8)
    pygame.draw.rect(s, (255, 246, 236), (744, 406, 30, 24), border_radius=4)
    pygame.draw.rect(s, CORAL, (690, 466, 216, 74), border_radius=18)
    pygame.draw.rect(s, darker(CORAL, .12), (690, 500, 216, 40), border_radius=14)
    for x, c in ((708, BUTTER), (850, MINT)):
        pygame.draw.rect(s, c, (x, 474, 40, 30), border_radius=10)
    _plant(s, 930, 300, 1.0, pot=BUTTER)
    pygame.draw.line(s, WOOD_D, (590, 600), (590, 520), 4)
    for a in (-1, 1):
        pygame.draw.line(s, WOOD_D, (590, 524), (590 + a * 14, 532), 3)
    pygame.draw.circle(s, MINT, (578, 540), 10)
    # hall central: tapete, aparador, sapateira, guarda-chuva, caminha de gato vazia, relógio
    _rug(s, pygame.Rect(380, 300, 200, 170), (240, 196, 220), (230, 150, 170))
    pygame.draw.rect(s, WOOD, (350, 236, 56, 30), border_radius=4)
    pygame.draw.rect(s, (130, 190, 200), (368, 214, 18, 24), border_radius=6)
    for dx in (-8, 0, 8):
        pygame.draw.circle(s, [CORAL, BUTTER, ROSE][dx // 8 + 1], (377 + dx, 208), 6)
    pygame.draw.rect(s, WOOD_D, (360, 560, 64, 40), border_radius=4)
    for k, c in enumerate((CORAL, (110, 90, 100), BUTTER)):
        pygame.draw.ellipse(s, c, (364 + k * 20, 566, 18, 10))
        pygame.draw.ellipse(s, c, (364 + k * 20, 582, 18, 10))
    pygame.draw.rect(s, LILAC, (548, 556, 26, 40), border_radius=6)
    pygame.draw.line(s, CORAL, (556, 556), (552, 520), 4)
    pygame.draw.ellipse(s, darker(ROSE, .2), (560, 240, 70, 40))
    pygame.draw.ellipse(s, ROSE, (566, 244, 58, 28))
    pygame.draw.circle(s, BUTTER, (612, 258), 5)          # sininho de brinquedo
    pygame.draw.circle(s, CREAM, (585, 60), 22)
    pygame.draw.circle(s, WOOD_D, (585, 60), 22, 4)
    pygame.draw.line(s, INK, (585, 60), (585, 46), 2)
    pygame.draw.line(s, INK, (585, 60), (596, 62), 2)
    _caps(s, [(430, 530)])
    return s


def draw_ground(s, t):
    if not assets.blit_bg(s, "bg_terreo"):
        s.blit(_cached("ground", _ground_static), (0, 0))
    blit_glow(s, (762, 118), 60, (40, 60, 70), .5 + .2 * math.sin(t * 5))


# ============================================================ bairro (condensado, sem vazios)
STREET_W = 2700
HOUSE_COLORS = [((255, 214, 186), (236, 120, 110)), ((206, 232, 210), (232, 150, 110)),
                ((255, 230, 170), (210, 120, 100)), ((240, 206, 232), (180, 120, 150)),
                ((214, 226, 246), (226, 140, 120)), ((255, 220, 206), (200, 110, 110)),
                ((246, 236, 200), (170, 140, 110)), ((226, 214, 250), (232, 130, 140)),
                ((255, 204, 204), (190, 120, 110))]
HOUSES = 9
HOUSE_X = [4 + i * 78 for i in range(HOUSES)]           # em pixel de mundo
HOME_DOOR = ((HOUSE_X[0] + 36) * 3, 300)
FOREST_X = (HOUSE_X[-1] + 78) * 3                       # onde a rua vira floresta


def _house_small(s, x, wall, roof, rng, own=False):
    o = pixel.OUT_DARK
    pygame.draw.rect(s, (150, 120, 120), (x + 52, 8, 7, 14))                 # chaminé
    pygame.draw.rect(s, wall, (x + 4, 24, 64, 48))
    pygame.draw.rect(s, pixel.dark(wall, .15), (x + 4, 66, 64, 6))
    pygame.draw.polygon(s, roof, [(x, 26), (x + 36, 4), (x + 72, 26)])
    for k in range(4):
        y = 9 + k * 5
        half = (y - 4) / 22 * 36
        pygame.draw.line(s, pixel.dark(roof, .2), (x + 36 - half, y), (x + 36 + half, y))
    pygame.draw.lines(s, o, True, [(x, 26), (x + 36, 4), (x + 72, 26)])
    pygame.draw.rect(s, o, (x + 4, 24, 64, 48), 1)
    for wx in (x + 10, x + 50):
        pygame.draw.rect(s, (255, 236, 186), (wx, 34, 12, 11))
        pygame.draw.rect(s, (255, 252, 244), (wx, 34, 12, 11), 1)
        pygame.draw.line(s, (255, 252, 244), (wx + 6, 34), (wx + 6, 44))
        pygame.draw.rect(s, (160, 110, 80), (wx - 1, 45, 14, 2))
        for k in range(4):
            s.set_at((wx + 1 + k * 3, 44), rng.choice([CORAL, BUTTER, ROSE]))
    door = CORAL if own else pixel.dark(wall, .35)
    pygame.draw.rect(s, door, (x + 31, 50, 10, 22))
    pygame.draw.rect(s, o, (x + 31, 50, 10, 22), 1)
    s.set_at((x + 39, 61), BUTTER)
    pygame.draw.rect(s, rng.choice([CORAL, MINT, LILAC]), (x + 62, 74, 5, 4))      # caixa de correio


def _street_static():
    rng = random.Random(5)
    LWs = STREET_W // 3
    s = pygame.Surface((LWs, pixel.LH))
    fx = FOREST_X // 3
    # fundo: mata densa atrás das casas
    pixel.paint_grass(s, pygame.Rect(0, 0, LWs, 88), rng, 1.3)
    for x in range(-10, LWs + 20, 14):
        t = pixel.tree_sprite(rng, rng.choice(["dark", "green", "dark"]))
        s.blit(t, (x - 20, -30 + rng.randint(-4, 4)))
    # casas, quintais, cercas
    for i, x in enumerate(HOUSE_X):
        wall, roof = HOUSE_COLORS[i]
        _house_small(s, x, wall, roof, rng, own=(i == 0))
        for k in range(10):                                                   # canteiro florido
            fx_ = x + 2 + k * 7
            if x + 28 < fx_ < x + 44:
                continue
            pygame.draw.circle(s, (120, 178, 96), (fx_, 77), 3)
            pixel.flower(s, fx_, 76, rng.choice([CORAL, BUTTER, ROSE, LILAC, CREAM]))
        for px_ in range(x - 2, x + 76, 3):                                   # cerquinha
            if x + 29 < px_ < x + 43:
                continue
            pygame.draw.rect(s, (255, 250, 242), (px_, 79, 2, 7))
            s.set_at((px_, 79), (230, 214, 200))
        pygame.draw.rect(s, (255, 250, 242), (x - 2, 82, 78, 1))
        pygame.draw.rect(s, (238, 204, 160), (x + 31, 72, 10, 14))           # caminho até a porta
        if i < HOUSES - 1:                                                    # arvorezinha entre as casas
            t = pixel.tree_sprite(rng, rng.choice(["green", "pink"]))
            s.blit(t, (x + 74 - 21, 30))
    # calçada de ladrilhos com rachaduras e matinhos
    for y in range(86, 134):
        for x in range(0, fx):
            gx, gy = x % 10, (y - 86) % 8
            c = (246, 224, 196) if (x // 10 + (y - 86) // 8) % 2 else (252, 234, 210)
            if gx == 0 or gy == 0:
                c = (226, 198, 170)
            s.set_at((x, y), c)
    for _ in range(fx // 5):
        x, y = rng.randrange(fx), rng.randrange(87, 133)
        if rng.random() < .6:
            pixel.tuft(s, x // 10 * 10, y, (126, 182, 98), rng.randint(0, 1))
        else:
            pygame.draw.line(s, (206, 176, 150), (x, y), (x + rng.randint(-3, 3), y + 3))
    # meio-fio, rua, faixa, faixas de pedestre, bueiros
    pygame.draw.rect(s, (226, 192, 162), (0, 134, fx, 3))
    for y in range(137, 180):
        for x in range(0, fx):
            s.set_at((x, y), (162, 140, 144) if rng.random() > .1 else (150, 128, 134))
    for x in range(4, fx, 28):
        pygame.draw.rect(s, BUTTER, (x, 157, 14, 3))
    for cx in (300, 640):
        for k in range(7):
            pygame.draw.rect(s, (250, 240, 228), (cx, 140 + k * 6, 22, 3))
    for x in (120, 460):
        pygame.draw.rect(s, (110, 96, 104), (x, 172, 10, 4))
    pygame.draw.rect(s, (226, 192, 162), (0, 180, fx, 3))
    # gramado de baixo
    pixel.paint_grass(s, pygame.Rect(0, 183, fx, pixel.LH - 183), rng, 1.2)
    # floresta no fim da rua: trilha de terra entre árvores
    pixel.paint_grass(s, pygame.Rect(fx, 84, LWs - fx, pixel.LH - 84), rng, 1.3)
    for x in range(fx, LWs):
        w = 16 + int(4 * math.sin(x * .07))
        cy = 110 + int(4 * math.sin(x * .03))
        pixel.paint_dirt(s, pygame.Rect(x, cy - w // 2, 1, w), rng)
    pygame.draw.rect(s, (226, 192, 162), (fx - 2, 84, 2, 100))
    for x in range(fx - 6, LWs + 10, 13):
        for y in (70 + rng.randint(-4, 8), 92 + rng.randint(-6, 0), 208 + rng.randint(-4, 6), 228):
            t = pixel.tree_sprite(rng, rng.choice(["dark", "green", "green", "pink"]))
            s.blit(t, (x - 21 + rng.randint(-3, 3), y - 50))
    for k in range(12):
        x = fx + rng.randrange(0, LWs - fx)
        s.blit(pixel.rock_sprite(rng, rng.choice([.6, .9])), (x, rng.choice([86, 128, 136])))
    # fileira de árvores, arbustos e pedras na beira de baixo
    for x in range(0, fx, 30):
        t = pixel.tree_sprite(rng, rng.choice(["green", "pink", "dark"]))
        s.blit(t, (x - 4 + rng.randint(-4, 4), 186 + rng.randint(-2, 6)))
    for x in range(12, fx, 30):
        b = pixel.bush_sprite(rng) if rng.random() < .7 else pixel.rock_sprite(rng, .7)
        s.blit(b, (x, 196 + rng.randint(0, 6)))
    return pixel.up(s)


def draw_street(s, cam_x):
    if assets.blit_bg(s, "bg_bairro", cam_x):
        return
    bg = _cached("street", _street_static)
    s.blit(bg, (0, 0), pygame.Rect(pixel.snap(cam_x), 0, W, H))


_lamp = None


def lamp_post(s, x, y, cam_x, t):
    global _lamp
    if _lamp is None:
        _lamp = pixel.up(pixel.lamp_sprite())
    s.blit(_lamp, (pixel.snap(x - cam_x - _lamp.get_width() / 2), pixel.snap(y - _lamp.get_height())))


def sign_post(s, x, y, cam_x, label):
    x -= cam_x
    pygame.draw.rect(s, WOOD_D, (pixel.snap(x - 4), pixel.snap(y - 69), 9, 69))
    r = pygame.Rect(pixel.snap(x - 51), pixel.snap(y - 93), 102, 33)
    art.notched(s, r, WOOD_D)
    art.notched(s, r.inflate(-6, -6), WOOD)
    art.text(s, label, art.font(18, bold=True), INK, r.center, "center")


def draw_dog(s, x, y, t, moving, facing=1, color=(230, 190, 140)):
    ph = t * 12 if moving else 0
    d = pygame.Surface((60, 40), pygame.SRCALPHA)
    pygame.draw.ellipse(d, (90, 40, 40, 50), (8, 32, 44, 8))
    for i, lx in enumerate((14, 20, 36, 42)):
        off = math.sin(ph + i * 1.6) * 3 if moving else 0
        pygame.draw.rect(d, darker(color, .1), (lx + off, 24, 5, 12), border_radius=2)
    pygame.draw.ellipse(d, color, (10, 14, 38, 18))
    pygame.draw.circle(d, color, (48, 14), 10)
    pygame.draw.ellipse(d, darker(color, .25), (50, 6, 8, 14))
    pygame.draw.circle(d, INK, (51, 12), 2)
    pygame.draw.circle(d, (90, 60, 60), (57, 16), 2)
    pygame.draw.line(d, color, (11, 18), (2, 8 + math.sin(t * 14) * 3), 4)
    if facing < 0:
        d = pygame.transform.flip(d, True, False)
    s.blit(d, (int(x - 30), int(y - 36)))


# ============================================================ quadros de história
def _bg_warm(s, top=(255, 206, 178), bottom=(250, 170, 160)):
    art._vgrad(s, s.get_rect(), top, bottom)


def cut_sleep(s, t, look, open_at=2.0):
    """Close no rosto: do ombro até a metade da cabeça. Abre os olhos em open_at s."""
    if assets.blit_bg(s, "cut_dormindo" if t < open_at else "cut_acordando"):
        return
    _bg_warm(s, (170, 120, 140), (120, 80, 110))
    pygame.draw.rect(s, (255, 244, 234), (60, 40, 840, 520), border_radius=120)
    pygame.draw.rect(s, (246, 230, 222), (60, 40, 840, 520), 6, border_radius=120)
    layer = pygame.Surface((W + 200, H + 200), pygame.SRCALPHA)
    cx, cy = (W + 200) // 2, 330
    skin, hair = look["skin"], look["hair"]
    pygame.draw.circle(layer, darker(skin, .12), (cx + 280, cy + 40), 48)
    pygame.draw.circle(layer, skin, (cx + 276, cy + 40), 40)
    pygame.draw.circle(layer, skin, (cx, cy + 40), 290)
    pygame.draw.ellipse(layer, hair, (cx - 320, cy - 330, 640, 300))
    for k in range(7):
        pygame.draw.circle(layer, hair, (cx - 240 + k * 80, cy - 40), 56)
    ink = (80, 46, 54)
    open_k = max(0.0, min(1.0, (t - open_at) / .5))
    blink = open_k >= 1 and (t - open_at) % 2.6 < .12
    for ex in (cx - 110, cx + 110):
        ey = cy + 70
        if open_k <= 0 or blink:
            pygame.draw.arc(layer, ink, (ex - 46, ey - 20, 92, 40), math.pi + .2, math.tau - .2, 8)
            for k in (-1, 0, 1):
                pygame.draw.line(layer, ink, (ex + k * 26, ey + 16), (ex + k * 32, ey + 30), 4)
        else:
            h = 70 * open_k
            pygame.draw.ellipse(layer, (255, 255, 255), (ex - 42, ey - h / 2, 84, h))
            pygame.draw.circle(layer, (90, 60, 60), (ex + 6, ey), min(30, h / 2))
            pygame.draw.circle(layer, (40, 26, 30), (ex + 6, ey), min(16, h / 3))
            pygame.draw.circle(layer, (255, 255, 255), (ex + 16, ey - 10), min(8, h / 6))
            pygame.draw.arc(layer, ink, (ex - 46, ey - h / 2 - 4, 92, h + 8), .2, math.pi - .2, 7)
    for ex in (cx - 190, cx + 190):
        pygame.draw.ellipse(layer, (250, 160, 160), (ex - 40, cy + 120, 80, 40))
    pygame.draw.arc(layer, ink, (cx - 30, cy + 170, 60, 30), math.pi + .4, math.tau - .4, 5)
    rot = pygame.transform.rotate(layer, -14)
    s.blit(rot, rot.get_rect(center=(W // 2 - 20, H // 2 - 120)))
    # cobertor no ombro
    pts = [(0, 470), (200, 430), (420, 460), (640, 420), (960, 450), (960, 640), (0, 640)]
    pygame.draw.polygon(s, PEACH, pts)
    for i in range(0, W, 80):
        pygame.draw.line(s, darker(PEACH, .1), (i, 450), (i + 30, 640), 3)
        pygame.draw.circle(s, BUTTER, (i + 40, 540), 8)
    pygame.draw.lines(s, (255, 236, 220), False, pts[:5], 8)
    rays = pygame.Surface((W, H))
    pygame.draw.polygon(rays, (34, 24, 8), [(700, 0), (820, 0), (500, 640), (300, 640)])
    s.blit(rays, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    if open_k <= 0:
        for k in range(3):
            ph = (t * .6 + k / 3) % 1
            art.text(s, "z" if k % 2 else "Z", art.font(int(30 + 20 * ph), bold=True), (255, 246, 240),
                     (700 + ph * 120 + k * 10, 200 - ph * 140), "center")


def cut_sit(s, t, look):
    if assets.blit_bg(s, "cut_sentado"):
        return
    _bg_warm(s, (252, 214, 190), (250, 196, 170))
    pygame.draw.rect(s, (255, 242, 228), (0, 300, W, 40))
    art._vgrad(s, pygame.Rect(0, 340, W, 300), (230, 172, 128), (214, 156, 116))
    _window(s, 640, 60, 200, 160)
    rays = pygame.Surface((W, H))
    pygame.draw.polygon(rays, (44, 30, 12), [(640, 220), (840, 220), (620, 640), (300, 640)])
    s.blit(rays, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    pygame.draw.rect(s, WOOD_D, (110, 250, 440, 120), border_radius=24)
    pygame.draw.rect(s, (255, 246, 236), (100, 340, 470, 60), border_radius=20)
    pygame.draw.rect(s, PEACH, (100, 380, 470, 120), border_radius=20)
    for x in range(110, 560, 70):
        pygame.draw.rect(s, [MINT, BUTTER, ROSE, LILAC][x // 70 % 4], (x, 400, 50, 80), border_radius=8)
    rub = (t % 2.4) < 1.4
    art.draw_character(s, 320, 500, "down", 0, False, look, 4.0, "sit_rub" if rub else "sit",
                       "sleepy", sprite_hook=False)
    pygame.draw.rect(s, WOOD, (600, 380, 140, 140), border_radius=12)
    pygame.draw.rect(s, WOOD_D, (600, 380, 140, 140), 3, border_radius=12)
    r = pygame.Rect(612, 310, 116, 64)
    pygame.draw.rect(s, CORAL, r, border_radius=16)
    pygame.draw.rect(s, (60, 40, 46), r.inflate(-16, -16), border_radius=10)
    on = (t % 1) < .6
    art.text(s, "06:00" if on else "06 00", art.font(28, bold=True), (255, 190, 150), r.center, "center")
    blit_glow(s, r.center, 70, (90, 40, 30), .8 if on else .4)


def cut_shower(s, t):
    if assets.blit_bg(s, "cut_banho"):
        return
    s.fill((236, 226, 220))
    for y in range(0, H, 40):
        for x in range(0, W, 40):
            pygame.draw.rect(s, (214, 238, 230) if (x + y) // 40 % 2 else (250, 244, 236), (x, y, 39, 39))
    pygame.draw.line(s, (180, 170, 180), (180, 80), (780, 80), 6)
    for i in range(14):
        x = 190 + i * 42
        wave = math.sin(t * 2 + i) * 4
        pygame.draw.rect(s, PEACH if i % 2 else ROSE, (x + wave, 84, 40, 470), border_radius=10)
        pygame.draw.circle(s, CREAM, (x + 20, 84), 6)
    for k in range(9):
        ph = (t * .25 + k / 9) % 1
        x = 200 + (k * 97) % 560 + math.sin(t + k) * 30
        y = 520 - ph * 460
        c = pygame.Surface((160, 100), pygame.SRCALPHA)
        pygame.draw.ellipse(c, (255, 255, 255, int(120 * math.sin(ph * math.pi))), c.get_rect())
        s.blit(c, (x - 80, y - 50))
    for k in range(4):
        ph = (t * .5 + k / 4) % 1
        x, y = 650 + k * 40, 300 - ph * 200
        pygame.draw.circle(s, INK, (int(x), int(y)), 7)
        pygame.draw.line(s, INK, (x + 6, y), (x + 6, y - 26), 3)
        pygame.draw.line(s, INK, (x + 6, y - 26), (x + 16, y - 20), 3)


def cut_dressed(s, t, look):
    if assets.blit_bg(s, "cut_pronto"):
        return
    _bg_warm(s, (255, 226, 196), (250, 186, 170))
    pygame.draw.ellipse(s, WOOD_D, (330, 40, 300, 520))
    pygame.draw.ellipse(s, (232, 240, 246), (348, 58, 264, 484))
    pygame.draw.ellipse(s, (246, 250, 252), (380, 90, 80, 300))
    blit_glow(s, (480, 320), 230, (90, 60, 40), .6)
    art.draw_character(s, 480, 480, "down", 0, False, look, 4.0, "stand", "happy", sprite_hook=False)
    for k in range(8):
        a = t * .8 + k * math.tau / 8
        sparkle(s, 480 + math.cos(a) * 250, 300 + math.sin(a) * 200, 6 + int(3 * math.sin(t * 4 + k)), BUTTER)


def cut_mom(s, t, look):
    if assets.blit_bg(s, "cut_lembranca"):
        return
    _bg_warm(s, (255, 230, 204), (246, 196, 170))
    for y in range(380, H, 40):
        for x in range(0, W, 40):
            pygame.draw.rect(s, (255, 236, 214) if (x + y) // 40 % 2 else (250, 206, 176), (x, y, 40, 40))
    art.draw_character(s, 190, 500, "right", 0, False, look, 4.2, "stand", "open", sprite_hook=False)
    for k, (x, y, r) in enumerate(((300, 230, 12), (340, 190, 20))):
        pygame.draw.circle(s, CREAM, (x, y + math.sin(t * 2 + k) * 4), r)
    cloud = pygame.Rect(390, 30, 500, 300)
    for k in range(12):
        a = k * math.tau / 12
        pygame.draw.circle(s, CREAM, (cloud.centerx + math.cos(a) * 220, cloud.centery + math.sin(a) * 120), 70)
    pygame.draw.ellipse(s, CREAM, cloud)
    art.draw_mom(s, cloud.centerx, cloud.centery - 6 + math.sin(t * 1.5) * 4, 120, t)
    for k in range(4):
        a = t * .7 + k * 1.6
        x, y = cloud.centerx + math.cos(a) * 170, cloud.centery + math.sin(a) * 90
        pygame.draw.circle(s, ROSE, (x - 4, y), 6)
        pygame.draw.circle(s, ROSE, (x + 4, y), 6)
        pygame.draw.polygon(s, ROSE, [(x - 10, y + 2), (x + 10, y + 2), (x, y + 13)])


def cut_eat(s, t):
    if assets.blit_bg(s, "cut_cafe"):
        return
    for x in range(0, W, 40):
        pygame.draw.rect(s, (255, 250, 244) if x // 40 % 2 else (250, 196, 192), (x, 0, 40, H))
    pygame.draw.circle(s, (240, 236, 230), (420, 300), 190)
    pygame.draw.circle(s, (255, 252, 248), (420, 300), 160)
    pygame.draw.ellipse(s, (252, 214, 100), (300, 220, 240, 150))
    pygame.draw.ellipse(s, (255, 230, 140), (330, 240, 160, 70))
    for x, y in ((360, 300), (450, 270), (480, 330)):
        pygame.draw.circle(s, (120, 180, 90), (x, y), 6)
    pygame.draw.rect(s, (226, 170, 100), (680, 380, 190, 150), border_radius=40)
    pygame.draw.rect(s, (255, 236, 196), (696, 396, 158, 118), border_radius=30)
    pygame.draw.ellipse(s, (255, 226, 120), (716, 420, 110, 70))
    pygame.draw.circle(s, (214, 140, 120), (760, 210), 90)
    pygame.draw.circle(s, (196, 150, 110), (760, 210), 72)
    pygame.draw.circle(s, (236, 200, 170), (750, 200), 30)
    pygame.draw.circle(s, (214, 140, 120), (860, 210), 30, 12)
    for k in range(3):
        ph = (t * .6 + k / 3) % 1
        x = 730 + k * 30 + math.sin(t * 3 + k) * 8
        pygame.draw.circle(s, (255, 255, 255), (int(x), int(110 - ph * 80)), int(10 * (1 - ph)) + 2, 2)


def cut_full(s, t, look):
    if assets.blit_bg(s, "cut_satisfeito"):
        return
    _bg_warm(s, (255, 230, 200), (250, 196, 172))
    _window(s, 600, 60, 260, 220)
    art.draw_character(s, 330, 510, "down", 0, False, look, 5.0, "belly", "happy", sprite_hook=False)
    for k in range(6):
        a = t * 1.2 + k
        x, y = 330 + math.cos(a) * 200, 260 + math.sin(a * 1.3) * 80
        sparkle(s, x, y, 8, BUTTER)
