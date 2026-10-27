"""Tela inicial: uma caixa de correio com cartas jogadas lá dentro. Cada carta
voa, se abre, e o papel de dentro vira uma opção: Acordar, Opções, Sair."""
import math
import random

import pygame

import art
import assets
import pixel
import ui
from art import BUTTER, CORAL, CREAM, INK, LILAC, MINT, PAPER, PEACH, ROSE, W, H, WOOD, WOOD_D, darker, lighter, mix
from world import Scene

LABELS = ["Acordar", "Opções", "Sair"]
ENV = [PEACH, MINT, LILAC]
TARGETS = [(240, 380), (480, 380), (720, 380)]
INSIDE = [(420, 205, -18), (486, 196, 10), (548, 212, -6)]
PAPER_W, PAPER_H = 200, 82
STAGE_LABEL = {"name": "escolhendo o nome", "intro": "acordando", "bedroom": "no quarto",
               "hall": "no corredor", "ground": "em casa, no térreo", "street": "passeando no bairro",
               "choices": "na casa do campo", "done": "história concluída"}
HOVER = BUTTER          # cor do botão com o cursor em cima
IDLE = CREAM            # cor padrão


def ease(k):
    k = max(0.0, min(1.0, k))
    return 1 - (1 - k) ** 3


def envelope(color, flap_open, paper_rise, paper_text=None):
    """Envelope (200x120) com o papel saindo. flap_open 0..1, paper_rise 0..1."""
    s = pygame.Surface((240, 260), pygame.SRCALPHA)
    ox, oy = 20, 120
    body = pygame.Rect(ox, oy, 200, 120)
    pygame.draw.rect(s, darker(color, .12), body, border_radius=8)
    apex = oy + 64 - flap_open * 128
    if flap_open > .5:
        pygame.draw.polygon(s, darker(color, .05), [(ox, oy), (ox + 200, oy), (ox + 100, apex)])
    if paper_rise > 0:
        p = pygame.Rect(ox + 14, oy + 20 - paper_rise * 100, 172, 92)
        pygame.draw.rect(s, PAPER, p, border_radius=4)
        for y in range(p.top + 18, p.bottom - 6, 14):
            pygame.draw.line(s, (236, 214, 196), (p.left + 10, y), (p.right - 10, y), 1)
        if paper_text and paper_rise > .6:
            art.text(s, paper_text, art.font(24, bold=True), INK, (p.centerx, p.top + 30), "center")
    pygame.draw.polygon(s, color, [(ox, oy + 120), (ox + 200, oy + 120), (ox + 200, oy + 30), (ox + 100, oy + 80), (ox, oy + 30)])
    pygame.draw.lines(s, darker(color, .2), False, [(ox, oy + 30), (ox + 100, oy + 80), (ox + 200, oy + 30)], 2)
    if flap_open <= .5:
        pygame.draw.polygon(s, lighter(color, .12), [(ox, oy), (ox + 200, oy), (ox + 100, apex)])
        pygame.draw.polygon(s, darker(color, .2), [(ox, oy), (ox + 200, oy), (ox + 100, apex)], 2)
        cx, cy = ox + 100, apex - 6
        pygame.draw.circle(s, CORAL, (cx - 5, cy), 7)
        pygame.draw.circle(s, CORAL, (cx + 5, cy), 7)
        pygame.draw.polygon(s, CORAL, [(cx - 11, cy + 2), (cx + 11, cy + 2), (cx, cy + 14)])
    pygame.draw.rect(s, ROSE, (ox + 160, oy + 86, 26, 26), border_radius=3)
    pygame.draw.rect(s, CREAM, (ox + 164, oy + 90, 18, 18), border_radius=2)
    return s


class MenuScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.anim = 0.0
        self.hover, self.open, self.sub_t, self.sub_focus = 0, None, 0.0, 0
        self.confirm_delete = None
        self.mouse_mode = False
        self.slots = [app.read_slot(i) for i in range(3)]
        self.clouds = [(random.uniform(0, W), random.uniform(20, 140), random.uniform(.6, 1.2)) for _ in range(5)]

    # ---------- timeline das cartas ----------
    def letter_t(self, i):
        return self.anim - (0.5 + i * 0.55)

    @property
    def ready(self):
        return self.letter_t(2) > 1.6

    def skip(self):
        self.anim = max(self.anim, 0.5 + 2 * 0.55 + 1.7)

    # ---------- layout ----------
    def paper_rect(self, i):
        r = pygame.Rect(0, 0, PAPER_W, PAPER_H)
        r.center = TARGETS[i]
        if self.ready and i == self.hover:
            r.y -= 6
        return r

    def nrows(self):
        return 4 if self.open == "options" else 3

    def sub_rect(self):
        k = ease(self.sub_t / .35)
        h = 15 + self.nrows() * 42 + 27
        r = pygame.Rect(159, 0, 642, h)
        end = min(447, H - 9 - h)
        r.top = pixel.snap(300 + (end - 300) * k)
        return r

    def rows(self):
        sub = self.sub_rect()
        return [pygame.Rect(sub.left + 30, sub.top + 15 + i * 42, sub.width - 60, 36) for i in range(self.nrows())]

    # ---------- ações ----------
    def select(self, i):
        self.app.audio.play("paper")
        if i == 2:
            self.app.quit()
            return
        kind = ["slots", "options"][i]
        if self.open == kind:
            self.open = None
        else:
            self.open, self.sub_t, self.sub_focus, self.confirm_delete = kind, 0.0, 0, None
            self.slots = [self.app.read_slot(k) for k in range(3)]

    def slot_action(self, i):
        data = self.slots[i]
        self.app.audio.play("chime")
        if data is None or data.get("stage") == "done":
            self.app.new_game(i)
        else:
            self.app.continue_game(i)

    def delete(self, i):
        if self.slots[i] is None:
            return
        if self.confirm_delete == i:
            self.app.delete_slot(i)
            self.slots[i] = None
            self.confirm_delete = None
            self.app.audio.play("paper")
        else:
            self.confirm_delete = i
            self.app.audio.play("blip")

    def adjust(self, row, d):
        if row < 2:
            key = ["music", "sfx"][row]
            self.app.set_volume(key, self.app.settings[key] + d * .1)
            self.app.audio.play("blip")
        elif row == 2:
            self.app.toggle_fullscreen()
        else:
            self.app.toggle_crt()
            self.app.audio.play("blip")

    def opt_controls(self, row):
        r = self.rows()[row]
        minus = pygame.Rect(r.left + 171, r.top + 6, 27, 24)
        plus = pygame.Rect(r.left + 471, r.top + 6, 27, 24)
        win = pygame.Rect(r.left + 171, r.top + 3, 150, 30)
        full = pygame.Rect(r.left + 339, r.top + 3, 162, 30)
        return minus, plus, win, full

    # ---------- entrada ----------
    def handle(self, e):
        if not self.ready:
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.skip()
            return
        if e.type == pygame.MOUSEMOTION:
            for i in range(3):
                if self.paper_rect(i).collidepoint(e.pos):
                    self.hover = i
            if self.open:
                for i, r in enumerate(self.rows()):
                    if r.collidepoint(e.pos):
                        self.sub_focus = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i in range(3):
                if self.paper_rect(i).collidepoint(e.pos):
                    self.select(i)
                    return
            if self.open == "slots":
                for i, r in enumerate(self.rows()):
                    xr = pygame.Rect(r.right - 36, r.top + 9, 26, 26)
                    if xr.collidepoint(e.pos) and self.slots[i]:
                        self.delete(i)
                    elif r.collidepoint(e.pos):
                        self.slot_action(i)
            elif self.open == "options":
                for i in range(4):
                    minus, plus, win, full = self.opt_controls(i)
                    if i < 2 and minus.collidepoint(e.pos):
                        self.adjust(i, -1)
                    elif i < 2 and plus.collidepoint(e.pos):
                        self.adjust(i, 1)
                    elif i == 2 and win.collidepoint(e.pos) and self.app.settings["fullscreen"]:
                        self.adjust(2, 0)
                    elif i == 2 and full.collidepoint(e.pos) and not self.app.settings["fullscreen"]:
                        self.adjust(2, 0)
                    elif i == 3 and (win.collidepoint(e.pos) or full.collidepoint(e.pos)):
                        if full.collidepoint(e.pos) != bool(self.app.settings.get("crt")):
                            self.adjust(3, 0)
        elif e.type == pygame.KEYDOWN:
            k = e.key
            if self.open:
                if k in (pygame.K_UP, pygame.K_w):
                    self.sub_focus = (self.sub_focus - 1) % self.nrows()
                    self.app.audio.play("blip")
                elif k in (pygame.K_DOWN, pygame.K_s):
                    self.sub_focus = (self.sub_focus + 1) % self.nrows()
                    self.app.audio.play("blip")
                elif k in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self.open = None
                elif self.open == "slots":
                    if k in ui.CONFIRM:
                        self.slot_action(self.sub_focus)
                    elif k in (pygame.K_DELETE, pygame.K_x):
                        self.delete(self.sub_focus)
                elif self.open == "options":
                    if k in (pygame.K_LEFT, pygame.K_a):
                        self.adjust(self.sub_focus, -1)
                    elif k in (pygame.K_RIGHT, pygame.K_d) or (k in ui.CONFIRM and self.sub_focus >= 2):
                        self.adjust(self.sub_focus, 1)
            else:
                if k in (pygame.K_LEFT, pygame.K_a):
                    self.hover = (self.hover - 1) % 3
                    self.app.audio.play("blip")
                elif k in (pygame.K_RIGHT, pygame.K_d):
                    self.hover = (self.hover + 1) % 3
                    self.app.audio.play("blip")
                elif k in ui.CONFIRM:
                    self.select(self.hover)

    def update(self, dt):
        prev = [self.letter_t(i) for i in range(3)]
        self.t += dt
        self.anim += dt
        for i in range(3):
            if prev[i] < .6 <= self.letter_t(i):
                self.app.audio.play("paper")
        if self.open:
            self.sub_t += dt

    # ---------- desenho ----------
    def draw_bg(self, s):
        if assets.blit_bg(s, "bg_correio"):
            return
        art._vgrad(s, pygame.Rect(0, 0, W, 330), (255, 196, 170), (255, 230, 196))
        pygame.draw.circle(s, (255, 240, 200), (820, 90), 50)
        for i, (x, y, sp) in enumerate(self.clouds):
            cx = (x + self.t * 12 * sp) % (W + 200) - 100
            for k in range(4):
                pygame.draw.circle(s, (255, 246, 236), (cx + k * 26, y + (k % 2) * 6), 22 + (k % 2) * 6)
        art._vgrad(s, pygame.Rect(0, 300, W, H - 300), (184, 218, 128), (160, 200, 110))
        rng = random.Random(4)
        for _ in range(70):
            x, y = rng.randint(0, W), rng.randint(310, H)
            pygame.draw.circle(s, rng.choice([CORAL, BUTTER, ROSE, CREAM, LILAC]), (x, y), 3)

    def draw_mailbox(self, s):
        pygame.draw.rect(s, WOOD_D, (466, 240, 28, 220), border_radius=4)
        pygame.draw.rect(s, WOOD, (470, 240, 10, 220))
        body = pygame.Rect(330, 120, 300, 130)
        pygame.draw.ellipse(s, darker(CORAL, .15), (326, 68, 308, 112))
        pygame.draw.rect(s, darker(CORAL, .15), body.inflate(8, 6))
        pygame.draw.ellipse(s, CORAL, (330, 72, 300, 104))
        pygame.draw.rect(s, CORAL, body)
        inner = (164, 92, 92)
        pygame.draw.ellipse(s, inner, (352, 98, 256, 80))
        pygame.draw.rect(s, inner, (352, 138, 256, 104))
        for x, y, r, c in ((400, 226, 14, ROSE), (520, 222, -10, BUTTER), (460, 232, 4, CREAM)):
            img = pygame.transform.rotozoom(envelope(c, 0, 0), r, .36)
            s.blit(img, img.get_rect(center=(x, y)))
        pygame.draw.polygon(s, darker(CORAL, .08), [(352, 242), (608, 242), (630, 288), (330, 288)])
        pygame.draw.polygon(s, darker(CORAL, .25), [(352, 242), (608, 242), (630, 288), (330, 288)], 3)
        pygame.draw.rect(s, BUTTER, (466, 268, 28, 10), border_radius=4)
        pygame.draw.rect(s, (110, 90, 100), (640, 110, 8, 90))
        pygame.draw.rect(s, BUTTER, (648, 110, 44, 28), border_radius=4)

    def draw_letter(self, s, i):
        lt = self.letter_t(i)
        x0, y0, r0 = INSIDE[i]
        tx, ty = TARGETS[i]
        if lt < 0:
            img = pygame.transform.rotozoom(envelope(ENV[i], 0, 0), r0, .42)
            s.blit(img, img.get_rect(center=(x0, y0 + 30)))
            return
        if lt > 1.6:
            return
        fly = ease(lt / .6)
        flap = ease((lt - .6) / .3)
        rise = ease((lt - .9) / .4)
        x = x0 + (tx - x0) * fly
        y = y0 + (ty + 40 - y0) * fly - math.sin(fly * math.pi) * 90
        rot = r0 * (1 - fly) + (i - 1) * 3 * fly
        scl = .42 + .58 * fly
        img = pygame.transform.rotozoom(envelope(ENV[i], flap, rise, LABELS[i]), rot, scl)
        fade = 1 - ease((lt - 1.3) / .3)
        img.set_alpha(int(255 * fade))
        s.blit(img, img.get_rect(center=(int(x), int(y))))

    def draw_paper_button(self, s, i):
        lt = self.letter_t(i)
        if lt < 1.3:
            return
        k = ease((lt - 1.3) / .3)
        r = self.paper_rect(i)
        r.y += int((1 - k) * -20)
        active = (i == 0 and self.open == "slots") or (i == 1 and self.open == "options")
        hot = self.ready and i == self.hover
        col = HOVER if hot else (lighter(CORAL, .55) if active else IDLE)
        ui.paper(s, r, col, border=CORAL if hot or active else None, lines=True)
        art.text(s, LABELS[i], art.font(30, bold=True), INK, r.center, "center")
        if hot:
            pygame.draw.rect(s, CORAL, (pixel.snap(r.centerx - 48), pixel.snap(r.bottom - 18), 96, 3))

    def draw_sub(self, s):
        if not self.open:
            return
        sub = self.sub_rect()
        ui.paper(s, sub, PAPER, border=CORAL, lines=False, radius=14)
        rows = self.rows()
        if self.open == "slots":
            for i, r in enumerate(rows):
                d = self.slots[i]
                foc = i == self.sub_focus
                ui.paper(s, r, HOVER if foc else IDLE, shadow=False, radius=8)
                if d is None:
                    label = f"Carta {i + 1}  ·  Novo jogo"
                elif d.get("stage") == "done":
                    label = f"Carta {i + 1}  ·  {d.get('name', '?')}  ·  concluída (começar de novo)"
                else:
                    label = f"Carta {i + 1}  ·  {d.get('name') or '...'}  ·  {STAGE_LABEL.get(d.get('stage'), '')}"
                art.text(s, label, art.font(19, bold=foc), INK, (r.left + 16, r.centery), "midleft")
                if d is not None:
                    xr = pygame.Rect(r.right - 36, r.top + 9, 26, 26)
                    red = self.confirm_delete == i
                    pygame.draw.rect(s, CORAL if red else (236, 214, 200), xr, border_radius=6)
                    art.text(s, "x", art.font(16, bold=True), CREAM if red else INK, xr.center, "center")
                    if red:
                        art.text(s, "apagar?", art.font(14, italic=True), CORAL, (xr.left - 6, r.centery), "midright")
        else:
            labels = ["Música", "Efeitos", "Tela", "TV (CRT)"]
            for i, r in enumerate(rows):
                foc = i == self.sub_focus
                ui.paper(s, r, HOVER if foc else IDLE, shadow=False, radius=8)
                art.text(s, labels[i], art.font(20, bold=True), INK, (r.left + 18, r.centery), "midleft")
                minus, plus, win, full = self.opt_controls(i)
                if i < 2:
                    v = self.app.settings[["music", "sfx"][i]]
                    for b, sym in ((minus, "-"), (plus, "+")):
                        art.notched(s, b, CORAL)
                        art.text(s, sym, art.font(22, bold=True), CREAM, b.center, "center")
                    for k in range(10):
                        seg = pygame.Rect(minus.right + 15 + k * 24, r.top + 9, 18, 18)
                        on = k < round(v * 10)
                        art.notched(s, seg, CORAL if on else (240, 222, 208))
                    art.text(s, f"{int(round(v * 100))}%", art.font(16), INK, (plus.right + 12, r.centery), "midleft")
                else:
                    st = self.app.settings["fullscreen"] if i == 2 else bool(self.app.settings.get("crt"))
                    names = ("Janela", "Tela cheia") if i == 2 else ("Desligado", "Ligado")
                    for b, lab, on in ((win, names[0], not st), (full, names[1], st)):
                        art.notched(s, b, CORAL if on else (240, 222, 208))
                        art.text(s, lab, art.font(17), CREAM if on else INK, b.center, "center")
        hint = ("setas: escolher · Enter: jogar · X: apagar · Esc: fechar" if self.open == "slots"
                else "setas: escolher e ajustar · Esc: fechar")
        art.text(s, hint, art.font(16), INK, (sub.centerx, sub.bottom - 6), "midbottom")

    def draw(self, s):
        self.draw_bg(s)
        self.draw_mailbox(s)
        for i in range(3):
            self.draw_letter(s, i)
        pixel.pixelate(s, grade=True)
        art.text(s, "A Casa das Escolhas", art.font(48, bold=True), INK, (W // 2, 12), "midtop", shadow=CREAM)
        self.draw_sub(s)
        for i in range(3):
            self.draw_paper_button(s, i)
        if not self.ready and self.anim > 1:
            art.text(s, "qualquer tecla para pular", art.font(13, italic=True), INK, (W // 2, H - 22), "midtop")
