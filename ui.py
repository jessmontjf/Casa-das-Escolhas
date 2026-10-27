"""Peças de interface: caixa de diálogo, balão de pensamento, aviso, botão
flutuante, quadros de história (cutscene) e pausa."""
import math

import pygame

import art
import pixel
from art import CORAL, CREAM, INK, PAPER, BUTTER, W, H, lighter, darker, mix

ADVANCE = (pygame.K_z, pygame.K_x, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_RIGHT)
CONFIRM = (pygame.K_z, pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER)


def paper(surf, rect, color=PAPER, border=None, lines=False, shadow=True, radius=10):
    """Caixa estilo pixel: borda de 1 px do mundo (3 px), cantos mordidos, sombra dura."""
    S = pixel.snap
    rect = pygame.Rect(S(rect.x), S(rect.y), S(rect.w), S(rect.h))
    if shadow:
        sh = pygame.Surface(rect.size, pygame.SRCALPHA)
        art.notched(sh, sh.get_rect(), (70, 30, 40, 80))
        surf.blit(sh, rect.move(6, 6))
    art.notched(surf, rect, border or darker(color, .3))
    art.notched(surf, rect.inflate(-6, -6), color)
    pygame.draw.rect(surf, lighter(color, .5), (rect.left + 6, rect.top + 3, rect.width - 12, 3))
    if lines:
        for y in range(rect.top + 24, rect.bottom - 9, 21):
            for x in range(rect.left + 12, rect.right - 12, 6):
                pygame.draw.rect(surf, mix(color, (190, 150, 140), .3), (x, y, 3, 3))


def arrow_tri(surf, x, y, size, color, direction="right"):
    s = size
    pts = {"right": [(x - s * .5, y - s), (x - s * .5, y + s), (x + s * .7, y)],
           "left": [(x + s * .5, y - s), (x + s * .5, y + s), (x - s * .7, y)],
           "down": [(x - s, y - s * .5), (x + s, y - s * .5), (x, y + s * .7)]}[direction]
    pygame.draw.polygon(surf, color, pts)


_fb = {}


def float_button(surf, x, y, t, color=CORAL):
    """Botão flutuante (pixel) que indica pra onde ir."""
    if color not in _fb:
        sm = pygame.Surface((13, 13), pygame.SRCALPHA)
        pygame.draw.circle(sm, color, (6, 6), 6)
        pygame.draw.circle(sm, CREAM, (6, 6), 6, 1)
        pygame.draw.polygon(sm, CREAM, [(3, 5), (9, 5), (6, 9)])
        sm.set_at((4, 3), lighter(color, .5))
        _fb[color] = pixel.up(pixel.outline(sm, darker(color, .5)))
    y = y - 70 + (6 if math.sin(t * 4) > 0 else 0)
    art.blit_glow(surf, (x, y), 46, color, .45)
    img = _fb[color]
    surf.blit(img, (pixel.snap(x - img.get_width() / 2), pixel.snap(y - img.get_height() / 2)))


class Dialog:
    """Caixa de fala embaixo da tela. Z/Enter/E avançam."""

    def __init__(self, lines, then=None, speed=45):
        self.lines, self.then, self.speed = [ln for ln in lines if ln], then, speed
        self.i, self.t, self.done = 0, 0.0, not self.lines

    def full(self):
        return self.t * self.speed >= len(self.lines[self.i])

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key in CONFIRM + (pygame.K_x,):
            self.next()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.next()

    def next(self):
        if not self.full():
            self.t = 999
            return
        self.i += 1
        self.t = 0
        if self.i >= len(self.lines):
            self.done = True

    def update(self, dt):
        self.t += dt

    def draw(self, surf, t):
        if self.done:
            return
        r = pygame.Rect(60, H - 150, W - 120, 120)
        paper(surf, r, CREAM, border=CORAL, radius=16)
        txt = self.lines[self.i][: int(self.t * self.speed)]
        f = art.font(22)
        for k, ln in enumerate(art.wrap(txt, f, r.width - 60)):
            art.text(surf, ln, f, INK, (r.left + 30, r.top + 22 + k * 30))
        if self.full():
            arrow_tri(surf, r.right - 30, r.bottom - 22 + math.sin(t * 6) * 3, 7, CORAL, "down")


class Thoughts:
    """Balões de pensamento que seguem uma posição (ex.: a cabeça do jogador)."""

    def __init__(self):
        self.items = []

    def add(self, text, anchor, secs=3.5, delay=0.0):
        self.items.append({"text": text, "anchor": anchor, "t": -delay, "dur": secs})

    def clear(self):
        self.items = []

    @property
    def busy(self):
        return bool(self.items)

    def update(self, dt):
        for it in self.items:
            it["t"] += dt
        self.items = [it for it in self.items if it["t"] < it["dur"]]

    def draw(self, surf):
        for it in self.items:
            if it["t"] < 0:
                continue
            a = min(1.0, it["t"] * 4, (it["dur"] - it["t"]) * 3)
            x, y = it["anchor"]()
            f = art.font(19, italic=True)
            lines = art.wrap(it["text"], f, 300)
            w = max(f.size(ln)[0] for ln in lines) + 36
            h = len(lines) * 24 + 22
            r = pygame.Rect(0, 0, w, h)
            r.midbottom = (int(x), int(y - 30))
            r.clamp_ip(pygame.Rect(8, 8, W - 16, H - 16))
            r = pygame.Rect(pixel.snap(r.x), pixel.snap(r.y), pixel.snap(r.w), pixel.snap(r.h))
            sm = pygame.Surface((pixel.LW, pixel.LH), pygame.SRCALPHA)
            rs = pygame.Rect(r.x // 3, r.y // 3, r.w // 3, r.h // 3)
            for k in range(0, rs.w, 7):
                pygame.draw.circle(sm, CREAM, (rs.left + 3 + k, rs.top + 1), 4)
                pygame.draw.circle(sm, CREAM, (rs.left + 3 + k, rs.bottom - 1), 4)
            pygame.draw.rect(sm, CREAM, rs)
            pygame.draw.circle(sm, CREAM, (int(x) // 3 + 2, rs.bottom + 4), 2)
            pygame.draw.circle(sm, CREAM, (int(x) // 3 + 1, rs.bottom + 8), 1)
            layer = pixel.up(pixel.outline(sm, INK))
            for k, ln in enumerate(lines):
                art.text(layer, ln, f, INK, (r.centerx, r.top + 11 + k * 24), "midtop")
            layer.set_alpha(int(255 * a))
            surf.blit(layer, (0, 0))


class Toast:
    def __init__(self):
        self.msg, self.t = None, 0.0

    def show(self, msg, secs=3.5):
        self.msg, self.t = msg, secs

    def update(self, dt):
        self.t = max(0.0, self.t - dt)

    def draw(self, surf, y=None):
        if not self.msg or self.t <= 0:
            return
        a = min(1.0, self.t)
        f = art.font(20, italic=True)
        w = min(W - 80, f.size(self.msg)[0] + 40)
        lines = art.wrap(self.msg, f, w - 40)
        r = pygame.Rect(0, 0, w, 20 + 26 * len(lines))
        r.midbottom = (W // 2, y or H - 18)
        art.panel(surf, r, art.DUSK, int(200 * a), 12)
        for i, ln in enumerate(lines):
            art.text(surf, ln, f, mix(art.DUSK, CREAM, a), (r.centerx, r.top + 10 + i * 26), "midtop")


class Cutscene:
    """Quadros de história: rolam sozinhos; Z, X, Enter ou → passam pro próximo.
    frames: lista de dicts {draw: fn(surf, t), caption: str|None, dur: float|None}"""

    def __init__(self, frames, then=None):
        self.frames, self.then = frames, then
        self.i, self.t, self.done = 0, 0.0, False
        self.prev, self.fade = None, 0.0
        self.canvas = pygame.Surface((W, H))

    def dur(self):
        f = self.frames[self.i]
        if f.get("dur"):
            return f["dur"]
        return 2.6 + len(f.get("caption") or "") / 16

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key in ADVANCE:
            self.advance()

    def advance(self):
        self.prev = self.canvas.copy()
        self.fade = 1.0
        self.i += 1
        self.t = 0.0
        if self.i >= len(self.frames):
            self.done = True

    def update(self, dt):
        self.t += dt
        self.fade = max(0.0, self.fade - dt * 2.2)
        if not self.done and self.t >= self.dur():
            self.advance()

    def draw(self, surf, t):
        if self.done:
            if self.prev:
                surf.blit(self.prev, (0, 0))
            return
        fr = self.frames[self.i]
        fr["draw"](self.canvas, self.t)
        pixel.pixelate(self.canvas, grade=True)
        cap = fr.get("caption")
        if cap:
            r = pygame.Rect(70, H - 118, W - 140, 86)
            paper(self.canvas, r, CREAM, border=CORAL, radius=16)
            shown = cap[: int(max(0.0, self.t - .3) * 34)]
            f = art.font(23, italic=True)
            lines = art.wrap(shown, f, r.width - 60)
            for k, ln in enumerate(lines):
                art.text(self.canvas, ln, f, INK, (r.centerx, r.top + 18 + k * 28), "midtop")
        art.text(self.canvas, "Z / Enter: avançar", art.font(16), (255, 240, 225), (W - 14, H - 14), "bottomright")
        surf.blit(self.canvas, (0, 0))
        if self.prev and self.fade > 0:
            self.prev.set_alpha(int(255 * self.fade))
            surf.blit(self.prev, (0, 0))


class Pause:
    def __init__(self, app, close):
        self.app, self.close = app, close
        self.sel, self.done = 0, False
        self.items = [("Continuar", self.close),
                      ("Efeito TV (CRT)", self.app.toggle_crt),
                      ("Salvar e voltar ao correio", self.app.back_to_menu)]

    def rects(self):
        return [pygame.Rect(W // 2 - 180, 237 + i * 63, 360, 51) for i in range(len(self.items))]

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + (1 if e.key in (pygame.K_DOWN, pygame.K_s) else -1)) % len(self.items)
                self.app.audio.play("blip")
            elif e.key in CONFIRM:
                self.items[self.sel][1]()
            elif e.key == pygame.K_ESCAPE:
                self.close()
        elif e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rects()):
                if r.collidepoint(e.pos):
                    self.sel = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects()):
                if r.collidepoint(e.pos):
                    self.items[i][1]()

    def update(self, dt):
        pass

    def draw(self, surf, t):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((60, 30, 36, 150))
        surf.blit(ov, (0, 0))
        box = pygame.Rect(W // 2 - 225, 159, 450, 330)
        paper(surf, box, PAPER, lines=True)
        art.text(surf, "Pausa", art.font(32, bold=True), INK, (W // 2, 182), "midtop")
        for i, (r, (label, _)) in enumerate(zip(self.rects(), self.items)):
            sel = i == self.sel
            paper(surf, r.move(0, -3 if sel else 0), BUTTER if sel else CREAM, shadow=False)
            if i == 1:
                label += ": ligado" if self.app.settings.get("crt") else ": desligado"
            art.text(surf, label, art.font(21, bold=sel), INK, r.move(0, -3 if sel else 0).center, "center")
        art.text(surf, "F11: tela cheia", art.font(14), INK, (W // 2, box.bottom - 24), "midtop")
