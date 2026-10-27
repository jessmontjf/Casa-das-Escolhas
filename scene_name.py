"""Escolha do nome: as letras balançam, e a selecionada levanta."""
import math

import pygame

import art
import ui
from art import BUTTER, CORAL, CREAM, INK, PAPER, W, H, lighter
from world import Scene

ROWS = ["ABCDEFGHIJ", "KLMNOPQRST", "UVWXYZÇÁÉÍ", "ÓÚÃÕÂÊÔ"]
ACTIONS = ["Apagar", "Espaço", "Continuar"]
CELL_W, CELL_H = 58, 54
MAX = 12


class NameScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.name = app.profile.get("name", "")
        self.r, self.c = 0, 0
        self.lift = {}
        self.shake, self.msg_t = 0.0, 0.0

    def cell_pos(self, r, c):
        if r < len(ROWS):
            x0 = W // 2 - (10 * CELL_W) // 2 + CELL_W // 2
            return x0 + c * CELL_W, 250 + r * CELL_H
        return W // 2 + (c - 1) * 200, 250 + len(ROWS) * CELL_H + 20

    def cell_rect(self, r, c):
        x, y = self.cell_pos(r, c)
        if r < len(ROWS):
            return pygame.Rect(x - 25, y - 24, 50, 48)
        return pygame.Rect(x - 85, y - 24, 170, 48)

    def cells(self):
        for r, row in enumerate(ROWS):
            for c in range(len(row)):
                yield r, c
        for c in range(3):
            yield len(ROWS), c

    def move(self, dr, dc):
        self.app.audio.play("blip")
        r, c = self.r, self.c
        if dr:
            nr = (r + dr) % (len(ROWS) + 1)
            if nr == len(ROWS):
                c = min(2, c * 3 // 10)
            elif r == len(ROWS):
                c = min(len(ROWS[nr]) - 1, c * 4 + 1)
            else:
                c = min(c, len(ROWS[nr]) - 1)
            r = nr
        if dc:
            n = 3 if r == len(ROWS) else len(ROWS[r])
            c = (c + dc) % n
        self.r, self.c = r, c

    def press(self):
        if self.r < len(ROWS):
            ch = ROWS[self.r][self.c]
            if len(self.name) < MAX:
                self.name += ch if not self.name or self.name.endswith(" ") else ch.lower()
                self.app.audio.play("pop")
        else:
            action = ACTIONS[self.c]
            if action == "Apagar":
                self.erase()
            elif action == "Espaço":
                if self.name and not self.name.endswith(" ") and len(self.name) < MAX:
                    self.name += " "
            else:
                self.confirm()

    def erase(self):
        if self.name:
            self.name = self.name[:-1]
            self.app.audio.play("paper")

    def confirm(self):
        name = self.name.strip()
        if not name:
            self.shake, self.msg_t = .4, 2.2
            self.app.audio.play("fail")
            return
        from scene_home import IntroScene
        self.app.audio.play("chime")
        self.app.profile["name"] = name
        self.app.profile["stage"] = "intro"
        self.app.save()
        self.app.set_scene(IntroScene(self.app))

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            k = e.key
            if k in (pygame.K_UP, pygame.K_w):
                self.move(-1, 0)
            elif k in (pygame.K_DOWN, pygame.K_s):
                self.move(1, 0)
            elif k in (pygame.K_LEFT, pygame.K_a):
                self.move(0, -1)
            elif k in (pygame.K_RIGHT, pygame.K_d):
                self.move(0, 1)
            elif k in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.press()
            elif k in (pygame.K_x, pygame.K_BACKSPACE):
                self.erase()
            elif k == pygame.K_ESCAPE:
                self.app.back_to_menu(save=False)
        elif e.type == pygame.MOUSEMOTION:
            for r, c in self.cells():
                if self.cell_rect(r, c).collidepoint(e.pos):
                    self.r, self.c = r, c
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for r, c in self.cells():
                if self.cell_rect(r, c).collidepoint(e.pos):
                    self.r, self.c = r, c
                    self.press()

    def update(self, dt):
        self.t += dt
        self.shake = max(0.0, self.shake - dt)
        self.msg_t = max(0.0, self.msg_t - dt)
        for r, c in self.cells():
            target = 1.0 if (r, c) == (self.r, self.c) else 0.0
            v = self.lift.get((r, c), 0.0)
            self.lift[(r, c)] = v + (target - v) * min(1.0, dt * 14)

    def draw(self, s):
        art._vgrad(s, s.get_rect(), (255, 218, 190), (250, 186, 172))
        card = pygame.Rect(W // 2 - 280, 40, 560, 140)
        ui.paper(s, card, PAPER, border=CORAL, lines=True)
        art.text(s, "Qual é o seu nome?", art.font(28, bold=True), INK, (card.centerx, card.top + 16), "midtop")
        sx = math.sin(self.t * 50) * 8 * self.shake
        shown = self.name + ("|" if int(self.t * 2) % 2 == 0 else " ")
        art.text(s, shown, art.font(40, bold=True), CORAL, (card.centerx + sx, card.top + 88), "center")
        pygame.draw.line(s, INK, (card.centerx - 180, card.bottom - 22), (card.centerx + 180, card.bottom - 22), 2)
        if self.msg_t > 0:
            art.text(s, "Seu nome precisa de pelo menos uma letra!", art.font(16, italic=True), CORAL,
                     (card.centerx, card.bottom + 6), "midtop")
        board = pygame.Rect(W // 2 - 320, 210, 640, 330)
        ui.paper(s, board, CREAM, border=lighter(CORAL, .3))
        for r, c in self.cells():
            x, y = self.cell_pos(r, c)
            i = r * 10 + c
            lift = self.lift.get((r, c), 0.0)
            wob_y = math.sin(self.t * 2.4 + i * .7) * 3
            wob_x = math.cos(self.t * 1.9 + i * .5) * 1.5
            y = y + wob_y - lift * 14
            x = x + wob_x
            sel = (r, c) == (self.r, self.c)
            if r < len(ROWS):
                f = art.font(int(28 + 10 * lift), bold=sel)
                if lift > .05:
                    art.blit_glow(s, (x, y), 34, (80, 50, 20), lift * .8)
                art.text(s, ROWS[r][c], f, CORAL if sel else INK, (x, y), "center",
                         shadow=BUTTER if sel else None)
            else:
                rect = self.cell_rect(r, c).move(wob_x, wob_y - lift * 8)
                ui.paper(s, rect, BUTTER if sel else (255, 236, 220), border=CORAL if sel else None, shadow=False)
                art.text(s, ACTIONS[c], art.font(22, bold=sel), INK, rect.center, "center")
        art.text(s, "setas: escolher · Z/Enter: confirmar · X: apagar · Esc: voltar", art.font(15), INK,
                 (W // 2, H - 40), "midtop")
