"""Efeitos: o mundo se desfazendo em pedaços, partículas e sons sintetizados
(sem arquivos de áudio)."""
import math
import random

import pygame

from art import sparkle


class Shatter:
    """Quebra uma imagem em ladrilhos que se espalham e somem."""

    def __init__(self, surf, offset=(0, 0), tile=20, origin=None, speed=(40, 170),
                 up=-60, gravity=0, life=1.4, wave=0.6, skip_empty=False):
        self.pieces, self.t, self.gravity, self.life = [], 0.0, gravity, life
        w, h = surf.get_size()
        cx, cy = origin if origin else (w / 2, h / 2)
        diag = math.hypot(w, h) or 1
        for y in range(0, h, tile):
            for x in range(0, w, tile):
                r = pygame.Rect(x, y, tile, tile).clip(surf.get_rect())
                piece = surf.subsurface(r).copy()
                if skip_empty and pygame.mask.from_surface(piece).count() == 0:
                    continue
                dx, dy = x + tile / 2 - cx, y + tile / 2 - cy
                d = math.hypot(dx, dy) or 1
                sp = random.uniform(*speed)
                self.pieces.append([piece, offset[0] + x, offset[1] + y,
                                    dx / d * sp + random.uniform(-30, 30),
                                    dy / d * sp + up + random.uniform(-30, 30),
                                    d / diag * wave + random.uniform(0, .25)])
        self.end = max((p[5] for p in self.pieces), default=0) + life

    @property
    def done(self):
        return self.t >= self.end

    def update(self, dt):
        self.t += dt
        for p in self.pieces:
            if self.t > p[5]:
                p[1] += p[3] * dt
                p[2] += p[4] * dt
                p[4] += self.gravity * dt

    def draw(self, surf):
        for piece, x, y, _, _, delay in self.pieces:
            lt = self.t - delay
            a = 1.0 if lt < 0 else 1 - lt / self.life
            if a <= 0:
                continue
            piece.set_alpha(int(255 * a))
            surf.blit(piece, (int(x), int(y)))


class Particles:
    def __init__(self):
        self.p = []

    def emit(self, x, y, n, color, speed=60, life=1.0, size=3, kind="spark", gravity=0.0, up=0.0):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            sp = random.uniform(.3, 1) * speed
            self.p.append([x, y, math.cos(a) * sp, math.sin(a) * sp + up, life * random.uniform(.6, 1),
                           life, color, size, kind, gravity, random.uniform(0, math.tau)])

    def update(self, dt):
        alive = []
        for q in self.p:
            q[4] -= dt
            if q[4] <= 0:
                continue
            q[0] += q[2] * dt
            q[1] += q[3] * dt
            q[3] += q[9] * dt
            if q[8] == "petal":
                q[0] += math.sin(q[10] + q[4] * 4) * 30 * dt
            alive.append(q)
        self.p = alive

    def draw(self, surf):
        for x, y, _, _, l, life, col, size, kind, _, ph in self.p:
            k = max(0.0, l / life)
            c = col
            if kind == "spark":
                if k > .15:
                    sparkle(surf, x, y, max(1, int(size * k)), c)
            elif kind == "petal":
                w = 4 + 3 * abs(math.sin(ph + l * 5))
                pygame.draw.ellipse(surf, col, (int(x), int(y), int(w), 5))
            else:
                pygame.draw.circle(surf, c, (int(x), int(y)), max(1, int(size * k)))
