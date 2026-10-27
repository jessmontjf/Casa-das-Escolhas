"""Personagens em pixel art no estilo de sprite de RPG top-down:
4 direções × 3 quadros (parado, passo esquerdo, passo direito), cabeça grande,
corpo pequeno. Grade de 20×28 px (mais 1 px de contorno).

O protagonista tem rosto e porte neutros, cabelo curto em camadas com franja
caindo no rosto. As roupas são camadas trocáveis: parte de cima, de baixo e sapatos."""
import pygame

import pixel

SW, SH = 20, 28
OUT = (25, 16, 18)
EYE = (40, 26, 30)
WHITE = (250, 240, 214)


def _shade(c, k):
    return pixel.dark(c, k) if k > 0 else pixel.light(c, -k)


class _P:
    def __init__(self, s, flip=False):
        self.s, self.flip = s, flip

    def r(self, c, x, y, w=1, h=1):
        if w <= 0 or h <= 0 or c is None:
            return
        self.s.fill(c, (x, y, w, h))

    def p(self, c, x, y):
        self.s.set_at((x, y), c)


# ---------------------------------------------------------------- cabeça
def _head(P, look, facing, dy, eyes):
    skin = look["skin"]
    hair = look["hair"]
    hd, hl = _shade(hair, .25), pixel.mix(hair, (236, 184, 142), .45)
    style = look.get("hair_style", "bob")
    y = dy
    if facing in ("down", "up"):
        # volume do cabelo
        P.r(hair, 7, y + 0, 6)
        P.r(hair, 5, y + 1, 10)
        P.r(hair, 4, y + 2, 12, 2)
        P.r(hair, 3, y + 4, 14, 8 if style in ("bob", "long") else 5)
        if facing == "down":
            P.r(skin, 5, y + 5, 10, 8)                 # rosto
            P.r(skin, 6, y + 13, 8)
            P.r(skin, 8, y + 14, 4)                    # pescoço
            P.r(hair, 5, y + 4, 10)                    # franja
            for x in (5, 6, 7, 9, 10, 12, 13, 14):
                P.p(hair, x, y + 5)
            for x in (6, 10, 13):
                P.p(hair, x, y + 6)
            P.r(hd, 5, y + 12, 1)
            P.r(hd, 14, y + 12, 1)
            # olhos
            ex = (7, 12)
            if eyes == "closed" or eyes == "sleepy":
                for x in ex:
                    P.r(EYE, x - (0 if x == 7 else 1), y + 9, 2)
            elif eyes == "happy":
                for x in ex:
                    P.p(EYE, x - 1, y + 9)
                    P.p(EYE, x, y + 8)
                    P.p(EYE, x + 1, y + 9)
            else:
                for x in ex:
                    P.r(EYE, x, y + 8, 1, 2)
                    P.p(WHITE, x, y + 8) if eyes == "shine" else None
            P.p(_shade(skin, .18), 9, y + 11)          # boquinha
            P.p(_shade(skin, .18), 10, y + 11)
            P.p((226, 150, 130), 6, y + 10)            # bochechas
            P.p((226, 150, 130), 13, y + 10)
        else:
            P.r(hd, 4, y + 9, 12, 3)                   # nuca
            P.r(skin, 8, y + 14, 4)
            for x in (4, 7, 10, 13):
                P.p(hd, x, y + 6)
        P.r(hl, 7, y + 2, 5)                           # brilho do cabelo
        if style in ("bob", "long"):
            P.p(hair, 3, y + 12)
            P.p(hair, 16, y + 12)
            P.p(hair, 4, y + 13)
            P.p(hair, 15, y + 13)
        if style == "long":
            P.r(hair, 3, y + 12, 2, 5)
            P.r(hair, 15, y + 12, 2, 5)
        if style == "bun":
            P.r(hair, 8, y - 2, 4, 3)
        if style == "cap":
            cap = look.get("cap", (176, 64, 48))
            P.r(cap, 4, y + 1, 12, 3)
            P.r(cap, 4, y + 4, 12) if facing == "down" else None
            P.r(_shade(cap, .3), 5, y + 5, 10) if facing == "down" else None
    else:  # lateral (direita; a esquerda é espelhada)
        P.r(hair, 6, y + 0, 7)
        P.r(hair, 4, y + 1, 11)
        P.r(hair, 3, y + 2, 13, 2)
        P.r(hair, 3, y + 4, 13, 8 if style in ("bob", "long") else 5)
        P.r(skin, 9, y + 5, 7, 8)
        P.r(skin, 10, y + 13, 5)
        P.r(skin, 9, y + 14, 3)
        P.r(hair, 9, y + 4, 7)                         # franja
        for x in (10, 12, 15):
            P.p(hair, x, y + 5)
        P.p(hair, 13, y + 6)
        P.p(skin, 16, y + 9)                           # nariz
        if eyes in ("closed", "sleepy"):
            P.r(EYE, 13, y + 9, 2)
        elif eyes == "happy":
            P.p(EYE, 13, y + 9)
            P.p(EYE, 14, y + 8)
        else:
            P.r(EYE, 14, y + 8, 1, 2)
        P.p((226, 150, 130), 13, y + 11)
        P.p(_shade(skin, .18), 15, y + 11)
        P.r(hl, 6, y + 2, 5)
        if style in ("bob", "long"):
            P.r(hair, 3, y + 12, 6)
            P.p(hair, 4, y + 13)
            P.p(hair, 7, y + 13)
        if style == "long":
            P.r(hair, 3, y + 12, 4, 6)
        if style == "bun":
            P.r(hair, 2, y + 2, 3, 4)
        if style == "cap":
            cap = look.get("cap", (176, 64, 48))
            P.r(cap, 3, y + 1, 13, 3)
            P.r(cap, 12, y + 4, 6)


# ---------------------------------------------------------------- roupas
def _top(P, look, facing, dy, arm_l, arm_r, pose):
    top = look["top"]
    st, c = top["style"], top.get("color", (200, 120, 90))
    skin = look["skin"]
    side = facing in ("left", "right")
    y0 = 14 + dy
    body_x, body_w = (6, 8) if side else (5, 10)
    main = {"hoodie_blue": (74, 112, 178), "rugby": (44, 46, 76), "zip_grey": (176, 172, 172),
            "pajama": (186, 150, 196), "robe": (244, 230, 204)}.get(st, c)
    dark = _shade(main, .25)
    P.r(main, body_x, y0, body_w, 7)
    sleeve_up, sleeve_lo = main, main
    # ----- detalhes por estilo
    if st == "hoodie_blue":                                  # moletom azul sobre manga longa branca
        sleeve_lo = WHITE
        if facing == "down":
            P.r(_shade(main, -.2), 6, y0, 8)
            P.p(WHITE, 8, y0 + 1)
            P.p(WHITE, 8, y0 + 2)
            P.p(WHITE, 11, y0 + 1)
            P.p(WHITE, 11, y0 + 2)
            P.r(dark, 7, y0 + 4, 6, 2)                       # bolso canguru
        elif facing == "up":
            P.r(dark, 6, y0, 8, 2)                           # capuz
        else:
            P.r(dark, 6, y0, 3, 2)
        P.r(WHITE, body_x, y0 + 6, body_w)                   # barra da camiseta por baixo
    elif st == "rugby":                                      # polo listrada marinho e rosa
        pink = (226, 160, 150)
        for k in range(0, 7, 2):
            P.r(pink, body_x, y0 + k, body_w)
        if facing == "down":
            P.r(WHITE, 8, y0, 4)
            P.p(WHITE, 9, y0 + 1)
            P.p(WHITE, 10, y0 + 1)
        sleeve_up, sleeve_lo = pink, main
    elif st == "zip_grey":                                   # jaqueta cinza aberta + camisa branca
        if facing == "down":
            P.r(WHITE, 8, y0, 4, 7)
            P.r(dark, 8, y0 + 1, 1, 6)
            P.r(dark, 11, y0 + 1, 1, 6)
            P.p((40, 46, 80), 12, y0 + 2)                    # crachá
        elif facing == "up":
            P.r(dark, 6, y0, 8, 2)
    elif st == "pajama":
        for x, yy in ((6, 1), (10, 2), (8, 4), (12, 5), (6, 5)):
            if x < body_x + body_w:
                P.p(_shade(main, -.35), x, y0 + yy)
        if facing == "down":
            P.r(_shade(main, -.25), 8, y0, 4)
    elif st == "robe":
        P.r(main, body_x, y0 + 7, body_w, 3)
        if facing == "down":
            P.r(skin, 9, y0, 2, 2)
            P.p(dark, 8, y0 + 2)
            P.p(dark, 11, y0 + 2)
        P.r(_shade(main, .2), body_x, y0 + 4, body_w)       # faixa
    elif st == "plaid":
        for x in range(body_x, body_x + body_w, 3):
            P.r(dark, x, y0, 1, 7)
        for k in (1, 4):
            P.r(_shade(main, -.25), body_x, y0 + k, body_w)
    elif st == "sweater":
        P.r(dark, body_x, y0 + 6, body_w)
        if facing == "down":
            P.r(dark, 8, y0, 4)
    elif st == "hoodie":
        if facing == "down":
            P.p(WHITE, 8, y0 + 1)
            P.p(WHITE, 11, y0 + 1)
            P.r(dark, 7, y0 + 4, 6, 2)
        else:
            P.r(dark, body_x, y0, body_w, 2)
    # ----- braços
    if pose == "belly":
        for ax in (4, 15):
            P.r(sleeve_up, ax, y0 + 1, 1, 3)
        P.r(sleeve_lo, 5, y0 + 4, 3, 1)
        P.r(sleeve_lo, 12, y0 + 4, 3, 1)
        P.r(skin, 8, y0 + 4, 1, 2)
        P.r(skin, 11, y0 + 4, 1, 2)
        return
    if side:
        ax = 9 + arm_l
        P.r(sleeve_up, ax, y0 + 1, 2, 3)
        P.r(sleeve_lo, ax, y0 + 4, 2, 2)
        P.r(skin, ax, y0 + 6, 2)
        return
    for ax, a in ((3, arm_l), (15, arm_r)):
        P.r(sleeve_up, ax, y0 + 1 + a, 2, 3)
        P.r(sleeve_lo, ax, y0 + 4 + a, 2, 2)
        P.r(skin, ax, y0 + 6 + a, 2)
    if pose == "rub":
        P.r(main, 15, y0 + 1, 2, 7)                          # cobre o braço normal
        P.r(sleeve_lo, 13, y0 - 2, 2, 3)
        P.r(skin, 12, y0 - 4, 2, 2)


def _legs(P, look, facing, lift_l, lift_r, pose):
    bot, sho = look["bottom"], look["shoes"]
    bst, bc = bot["style"], bot.get("color", (90, 90, 110))
    sst, sc = sho["style"], sho.get("color", (240, 230, 220))
    skin = look["skin"]
    side = facing in ("left", "right")
    sit = pose in ("sit", "rub")
    bcol = {"denim_shorts": (46, 58, 92), "sweat_shorts": (168, 166, 170), "track_pants": (72, 72, 80),
            "pajama": (186, 150, 196)}.get(bst, bc)
    long_ = bst in ("track_pants", "pajama", "pants")
    short_end = {"denim_shorts": 24, "sweat_shorts": 23, "shorts": 23, "skirt": 24}.get(bst, 25)
    top_st = look["top"]["style"]
    if top_st == "robe":
        long_, bcol = True, (244, 230, 204)
    legs = [(6, lift_l), (11, lift_r)] if not side else [(8 - lift_l * 2, 0), (10 + lift_r * 2, 0)]
    if sit:
        P.r(bcol, 5, 21, 10, 2)                               # coxas pra frente
        legs = [(6, -1), (11, -1)]
    # cintura
    P.r(bcol, 5 if not side else 6, 21, 10 if not side else 8, 1)
    for lx, lift in legs:
        y = 21 - lift + (1 if sit else 0)
        w = 3
        if long_:
            wide = bst == "track_pants"
            P.r(bcol, lx - (1 if wide and not side else 0), y, w + (1 if wide and not side else 0), 25 - y)
            if bst == "track_pants":
                P.p(WHITE, lx + (2 if lx > 9 else 0), y + 3)  # friso branco
        else:
            P.r(bcol, lx - 1, y, w + 1, short_end - y)
            P.r(skin, lx, short_end - lift, w, 25 - short_end)
            if bst == "sweat_shorts":
                P.r((44, 46, 76), lx - 1 if lx < 9 else lx + w - 1, y, 1, short_end - y)
            if bst == "denim_shorts":
                P.p(_shade(bcol, -.3), lx, short_end - 1)
        # meias + sapatos
        sy = 25 - lift
        if sst == "loafer":
            P.r(WHITE, lx, max(y, short_end - lift) if not long_ else sy - 1, w, sy - (max(y, short_end - lift) if not long_ else sy - 1))
            P.r((30, 26, 30), lx - (0 if not side else 0), sy, w + 1, 2)
            P.p((110, 100, 110), lx + 1, sy)
        elif sst == "slipper":
            P.r((250, 236, 214), lx - 1, sy, w + 2, 2)
        else:
            if not long_:
                P.r(WHITE, lx, sy - 1, w, 1)                  # meia
            col = {"navy_sneaker": (44, 52, 80), "burgundy_sneaker": (246, 240, 230)}.get(sst, sc)
            P.r(col, lx - (1 if side else 0), sy, w + 1, 2)
            if sst == "navy_sneaker":
                P.p(WHITE, lx + 1, sy)
                P.r((176, 120, 72), lx - (1 if side else 0), sy + 2, w + 1, 1)
            elif sst == "burgundy_sneaker":
                P.r((138, 40, 50), lx, sy, 2, 1)
                P.r((138, 40, 50), lx - (1 if side else 0), sy + 2, w + 1, 1)
            elif sst == "boot":
                P.r(col, lx, sy - 2, w, 2)
                P.r(_shade(col, .3), lx - (1 if side else 0), sy + 2, w + 1, 1)
            else:
                P.r(_shade(col, .3), lx - (1 if side else 0), sy + 2, w + 1, 1)


_cache = {}


def _key(look):
    def t(v):
        if isinstance(v, dict):
            return tuple(sorted((k, t(x)) for k, x in v.items()))
        if isinstance(v, (list, tuple)):
            return tuple(v)
        return v
    return t({k: v for k, v in look.items() if k != "sprite"})


def make(look, facing="down", frame=0, pose="stand", eyes="open"):
    """Sprite pequeno (22×30 com contorno). frame: 0 parado, 1/2 passos."""
    key = (_key(look), facing, frame, pose, eyes)
    if key in _cache:
        return _cache[key]
    s = pygame.Surface((SW, SH), pygame.SRCALPHA)
    P = _P(s)
    f = "right" if facing == "left" else facing
    lift_l = 1 if frame == 1 else 0
    lift_r = 1 if frame == 2 else 0
    arm_l = 1 if frame == 2 else (-1 if frame == 1 else 0)
    arm_r = -arm_l
    if f == "right":
        lift_l, lift_r = (1, 0) if frame == 1 else ((0, 1) if frame == 2 else (0, 0))
        arm_l = 1 if frame == 1 else (-1 if frame == 2 else 0)
    bob = -1 if frame else 0
    sit = pose in ("sit", "rub")
    dy = bob + (2 if sit else 0)
    _legs(P, look, f, lift_l, lift_r, pose)
    _top(P, look, f, dy, arm_l, arm_r, pose)
    _head(P, look, f, dy, eyes)
    if facing == "left":
        s = pygame.transform.flip(s, True, False)
    out = pixel.outline(s, OUT)
    if len(_cache) > 600:
        _cache.clear()
    _cache[key] = out
    return out


def frame_for(phase, moving):
    """Sequência clássica: parado, passo, parado, outro passo."""
    if not moving:
        return 0
    return (0, 1, 0, 2)[int(phase / 1.6) % 4]
