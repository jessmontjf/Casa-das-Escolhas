"""Tarefinhas rápidas de cozinha: omelete, café com leite e pão com manteiga.
Cada jogo é uma lista de etapas:
  timing    → aperte Z/Enter quando a setinha estiver na faixa verde
  alternate → alterne ← e → várias vezes
  hold      → segure Z e solte quando chegar na linha"""
import math
import random

import pygame

import art
import pixel
import ui
from art import BUTTER, CORAL, CREAM, INK, MINT, PAPER, W, H, darker, lighter, mix

ACT = (pygame.K_z, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e)


class Minigame:
    TITLE = ""
    STEPS = []          # (tipo, instrução, parâmetro)

    def __init__(self, app, then=None):
        self.app, self.then = app, then
        self.step, self.t, self.done = 0, 0.0, False
        self.msg, self.msg_t, self.finish_t = "", 0.0, None
        self.reset_step()

    # ---------- etapas ----------
    def reset_step(self):
        kind, _, p = self.STEPS[self.step]
        self.kind, self.param = kind, p
        self.start = getattr(self, "HOLD_START", {}).get(self.step, 0.0)
        self.count, self.level, self.holding, self.last = 0, self.start, False, None
        self.zone = random.uniform(.3, .7)
        self.mark_t = random.uniform(0, 3)

    def ok(self):
        self.app.audio.play("pop")
        self.step += 1
        if self.step >= len(self.STEPS):
            self.finish_t = 0.0
            self.app.audio.play("chime")
        else:
            self.reset_step()

    def fail(self, msg):
        self.app.audio.play("fail")
        self.msg, self.msg_t = msg, 1.4
        self.reset_step()

    def marker(self):
        return (math.sin(self.mark_t * 2.6) + 1) / 2

    def handle(self, e):
        if self.finish_t is not None:
            return
        if e.type == pygame.KEYDOWN:
            if self.kind == "timing" and e.key in ACT:
                if abs(self.marker() - self.zone) < .09:
                    self.count += 1
                    self.app.audio.play("pop")
                    self.zone = random.uniform(.25, .75)
                    if self.count >= self.param:
                        self.ok()
                else:
                    self.fail("Quase! Tenta de novo.")
            elif self.kind == "alternate" and e.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                side = "L" if e.key in (pygame.K_LEFT, pygame.K_a) else "R"
                if side != self.last:
                    self.count += 1
                    self.last = side
                    if self.count % 2 == 0:
                        self.app.audio.play("blip")
                    if self.count >= self.param:
                        self.ok()
            elif self.kind == "hold" and e.key in ACT:
                self.holding = True
        elif e.type == pygame.KEYUP and self.kind == "hold" and e.key in ACT and self.holding:
            self.holding = False
            target = self.param
            if abs(self.level - target) <= .07:
                self.ok()
            elif self.level > self.start + 0.02:
                self.fail("Hmm, não ficou na linha. De novo!")

    def update(self, dt):
        self.t += dt
        self.mark_t += dt
        self.msg_t = max(0.0, self.msg_t - dt)
        if self.kind == "hold" and self.holding and self.finish_t is None:
            self.level += dt * .38
            if self.level > self.param + .12:
                self.holding = False
                self.fail("Transbordou! Vamos de novo.")
        if self.finish_t is not None:
            self.finish_t += dt
            if self.finish_t > 1.1:
                self.done = True

    # ---------- desenho ----------
    def draw_scene(self, surf, area):
        pass

    def draw(self, surf, t):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((80, 40, 40, 120))
        surf.blit(ov, (0, 0))
        box = pygame.Rect(W // 2 - 330, 50, 660, 500)
        ui.paper(surf, box, PAPER, border=CORAL, radius=18)
        area = pygame.Rect(box.left + 40, box.top + 90, box.width - 80, 250)
        self.draw_scene(surf, area)
        pixel.pixelate(surf, area.inflate(40, 40))
        art.text(surf, self.TITLE, art.font(32, bold=True), INK, (box.centerx, box.top + 15), "midtop")
        for i in range(len(self.STEPS)):
            c = MINT if i < self.step else (BUTTER if i == self.step else (230, 210, 196))
            art.notched(surf, pygame.Rect(box.centerx - (len(self.STEPS) - 1) * 15 + i * 30 - 9, box.top + 57, 18, 18), c)
        if self.finish_t is not None:
            art.text(surf, "Pronto!", art.font(40, bold=True), CORAL, (box.centerx, area.centery), "center",
                     shadow=CREAM)
            return
        _, instr, _ = self.STEPS[self.step]
        art.text(surf, instr, art.font(21), INK, (box.centerx, box.top + 352), "midtop")
        bar = pygame.Rect(box.left + 80, box.top + 400, box.width - 160, 30)
        pygame.draw.rect(surf, (240, 222, 206), bar, border_radius=12)
        if self.kind == "timing":
            z = pygame.Rect(0, bar.top, int(bar.width * .18), bar.height)
            z.centerx = bar.left + int(bar.width * self.zone)
            pygame.draw.rect(surf, MINT, z, border_radius=10)
            mx = bar.left + int(bar.width * self.marker())
            ui.arrow_tri(surf, mx, bar.top - 10, 9, CORAL, "down")
            pygame.draw.line(surf, CORAL, (mx, bar.top), (mx, bar.bottom), 3)
            art.text(surf, f"{self.count}/{self.param}", art.font(18), INK, (bar.right + 14, bar.centery), "midleft")
        elif self.kind == "alternate":
            fill = bar.copy()
            fill.width = int(bar.width * self.count / self.param)
            pygame.draw.rect(surf, BUTTER, fill, border_radius=12)
            for k, d in enumerate(("left", "right")):
                lit = (self.last == "L") != (d == "left") and int(t * 4) % 2
                ui.arrow_tri(surf, box.centerx + (k * 2 - 1) * 40, bar.bottom + 30, 12,
                             CORAL if lit else (210, 180, 170), d)
        elif self.kind == "hold":
            fill = bar.copy()
            fill.width = int(bar.width * min(1.0, self.level))
            pygame.draw.rect(surf, (200, 150, 110), fill, border_radius=12)
            tx = bar.left + int(bar.width * self.param)
            pygame.draw.line(surf, CORAL, (tx, bar.top - 6), (tx, bar.bottom + 6), 4)
        pygame.draw.rect(surf, darker((240, 222, 206), .2), bar, 2, border_radius=12)
        if self.msg_t > 0:
            art.text(surf, self.msg, art.font(20, italic=True), CORAL, (box.centerx, box.bottom - 40), "midtop")


class Omelete(Minigame):
    TITLE = "Omelete"
    STEPS = [("timing", "Quebre os ovos! Aperte Z quando a setinha estiver no verde.", 2),
             ("alternate", "Bata os ovos! Alterne as setas ESQ e DIR bem rápido.", 12),
             ("timing", "Vire a omelete! Z no verde.", 1)]

    def draw_scene(self, surf, a):
        cx, cy = a.centerx, a.centery + 20
        if self.step < 2 and self.finish_t is None:
            pygame.draw.ellipse(surf, (200, 226, 236), (cx - 120, cy - 20, 240, 110))
            pygame.draw.ellipse(surf, (230, 242, 248), (cx - 104, cy - 14, 208, 50))
            eggs = self.count if self.step == 0 else 2
            for k in range(eggs):
                pygame.draw.ellipse(surf, (255, 214, 90), (cx - 50 + k * 50, cy - 6, 44, 26))
            if self.step == 0:
                bob = math.sin(self.t * 6) * 4
                pygame.draw.ellipse(surf, (255, 246, 232), (cx - 26, cy - 120 + bob, 52, 66))
                pygame.draw.ellipse(surf, (230, 210, 190), (cx - 26, cy - 120 + bob, 52, 66), 2)
            else:
                ang = self.count * .9
                wx, wy = cx + math.cos(ang) * 40, cy + math.sin(ang) * 10
                pygame.draw.line(surf, (170, 160, 170), (wx, wy), (wx + 50, wy - 120), 6)
                pygame.draw.ellipse(surf, (190, 190, 200), (wx - 16, wy - 30, 32, 44), 3)
        else:
            pygame.draw.rect(surf, (90, 80, 86), (cx + 120, cy + 6, 120, 18), border_radius=8)
            pygame.draw.ellipse(surf, (90, 80, 86), (cx - 140, cy - 30, 270, 90))
            pygame.draw.ellipse(surf, (120, 110, 116), (cx - 126, cy - 24, 242, 70))
            jump = 0 if self.finish_t is None else math.sin(min(1.0, self.finish_t * 2) * math.pi) * 90
            pygame.draw.ellipse(surf, (252, 210, 90), (cx - 80, cy - 18 - jump, 160, 50))
            pygame.draw.ellipse(surf, (255, 232, 140), (cx - 50, cy - 10 - jump, 90, 20))


class CafeComLeite(Minigame):
    TITLE = "Café com leite"
    HOLD_START = {1: .45}
    STEPS = [("hold", "Segure Z pra pôr o café. Solte na linha!", .45),
             ("hold", "Agora o leite! Segure Z e solte na linha de cima.", .85)]

    def draw_scene(self, surf, a):
        cx, base = a.centerx, a.bottom - 10
        mug = pygame.Rect(cx - 70, base - 170, 140, 170)
        level = self.level if self.finish_t is None else .85
        col = mix((120, 76, 56), (226, 190, 150), min(1.0, max(0.0, (level - .45) / .4)))
        h = int(mug.height * min(1.0, level))
        pygame.draw.rect(surf, (255, 252, 246), mug, border_radius=14)
        pygame.draw.rect(surf, col, (mug.left, mug.bottom - h, mug.width, h), border_bottom_left_radius=14, border_bottom_right_radius=14)
        pygame.draw.rect(surf, CORAL, mug, 5, border_radius=14)
        pygame.draw.circle(surf, CORAL, (mug.right + 20, mug.centery), 32, 10)
        for lv in (.45, .85):
            y = mug.bottom - int(mug.height * lv)
            pygame.draw.line(surf, MINT, (mug.left - 14, y), (mug.left + 10, y), 4)
        if self.holding:
            c = (110, 70, 52) if self.step == 0 else (255, 250, 244)
            pygame.draw.line(surf, c, (cx, a.top), (cx, mug.bottom - h), 8)
            pot = (60, 50, 56) if self.step == 0 else (240, 240, 250)
            pygame.draw.rect(surf, pot, (cx - 60, a.top - 10, 70, 40), border_radius=10)


class PaoComManteiga(Minigame):
    TITLE = "Pão com manteiga"
    STEPS = [("timing", "Corte o pão! Aperte Z no verde.", 1),
             ("alternate", "Passe a manteiga! Alterne as setas ESQ e DIR.", 10)]

    def draw_scene(self, surf, a):
        cx, cy = a.centerx, a.centery + 10
        pygame.draw.rect(surf, (226, 176, 126), (cx - 200, cy + 30, 400, 40), border_radius=10)
        if self.step == 0 and self.finish_t is None:
            pygame.draw.ellipse(surf, (226, 160, 90), (cx - 140, cy - 60, 280, 110))
            for k in range(4):
                pygame.draw.line(surf, (190, 120, 60), (cx - 80 + k * 50, cy - 50), (cx - 100 + k * 50, cy - 10), 4)
            kx = cx + math.sin(self.t * 3) * 40
            pygame.draw.polygon(surf, (210, 214, 224), [(kx - 6, cy - 150), (kx + 6, cy - 150), (kx + 4, cy - 60), (kx - 4, cy - 60)])
            pygame.draw.rect(surf, (150, 100, 80), (kx - 6, cy - 190, 12, 40), border_radius=4)
        else:
            sl = pygame.Rect(cx - 90, cy - 80, 180, 140)
            pygame.draw.rect(surf, (214, 150, 86), sl, border_radius=40)
            pygame.draw.rect(surf, (255, 236, 196), sl.inflate(-22, -22), border_radius=32)
            k = 1.0 if self.finish_t is not None or self.step > 1 else self.count / self.param
            rng = random.Random(3)
            for i in range(int(k * 14)):
                pygame.draw.ellipse(surf, (255, 222, 110), (sl.left + 18 + rng.randint(0, 110), sl.top + 18 + rng.randint(0, 80), 34, 22))
            if self.finish_t is None:
                kx = cx + (40 if self.last == "R" else -40)
                pygame.draw.rect(surf, (210, 214, 224), (kx - 30, cy - 40, 60, 12), border_radius=6)
                pygame.draw.rect(surf, (150, 100, 80), (kx + 26, cy - 42, 40, 16), border_radius=6)
