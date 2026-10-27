"""O bairro num sábado de manhã: vizinhos, cachorro, e no fim da rua, o campo."""
import math

import pygame

import art
import art_home as AH
import pixel
from art import BUTTER, CORAL, LILAC, MINT, PEACH, ROSE, W, H
from world import Hotspot, WorldScene

# aparência dos vizinhos
def _look(skin, hair, style, top, tstyle, bottom, bstyle, shoes, **kw):
    d = {"skin": skin, "hair": hair, "hair_style": style,
         "top": {"color": top, "style": tstyle}, "bottom": {"color": bottom, "style": bstyle},
         "shoes": {"color": shoes, "style": "sneaker"}}
    d.update(kw)
    return d


NPCS = [
    # nome, x, y, look, falas, patrulha (x0, x1) ou None
    ("Dona Cida", 640, 300, _look((236, 196, 170), (230, 226, 230), "bun", ROSE, "sweater", (170, 140, 190), "pants", (200, 150, 140)),
     ["Bom dia, {nome}! Sua mãe passou aqui cedinho, toda apressada.",
      "Disse pra eu ficar de olho em você. Hehe."], None),
    ("Seu Jorge", 1050, 340, _look((200, 150, 120), (90, 70, 70), "short", MINT, "plaid", (120, 110, 130), "pants", (120, 90, 80)),
     ["O Biscoito acordou animado hoje. Sábado é sábado!"], (980, 1380)),
    ("Lia", 1500, 300, _look((248, 214, 186), (240, 170, 90), "long", BUTTER, "hoodie", (240, 150, 160), "shorts", (255, 255, 255)),
     ["Você já foi lá pro campo? Dizem que tem flor de todas as cores!",
      "Eu ia, mas minha mãe disse que hoje não."], None),
    ("Carteiro Davi", 1880, 330, _look((190, 140, 110), (60, 50, 60), "cap", (150, 190, 230), "sweater", (90, 100, 140), "pants", (80, 70, 80), cap=(90, 120, 190)),
     ["Nada pra sua casa hoje.", "...ou quase nada. Às vezes as cartas chegam sozinhas, sabia?"], (1800, 2150)),
    ("Bia e Rafa", 1990, 300, _look((230, 190, 160), (110, 70, 60), "long", LILAC, "sweater", (230, 210, 180), "pants", (240, 240, 240)),
     ["A gente vem aqui todo sábado ver o movimento.", "Lá no fim da rua começa o campo. Coisa mais tranquila."], None),
    ("Tito", 700, 380, _look((240, 200, 170), (40, 34, 40), "short", CORAL, "hoodie", (90, 130, 190), "shorts", (255, 255, 255)),
     ["Ei! Cuidado que eu tô treinando corrida!"], (500, 1200)),
]


class NPC:
    def __init__(self, name, x, y, look, lines, patrol):
        self.name, self.x, self.y, self.look, self.lines, self.patrol = name, float(x), y, look, lines, patrol
        self.dir, self.phase, self.facing, self.pause = 1, 0.0, "down", 0.0
        self.speed = 90 if name == "Tito" else 45

    def update(self, dt, talking):
        if not self.patrol or talking:
            return
        if self.pause > 0:
            self.pause -= dt
            return
        self.x += self.dir * self.speed * dt
        self.phase += dt * 10
        self.facing = "right" if self.dir > 0 else "left"
        if self.x > self.patrol[1] or self.x < self.patrol[0]:
            self.dir *= -1
            self.pause = 1.2

    def draw(self, surf, cam_x, t):
        moving = bool(self.patrol) and self.pause <= 0
        art.draw_character(surf, self.x - cam_x, self.y, self.facing, self.phase, moving, self.look, 1.5)


class StreetScene(WorldScene):
    SCALE = 1.5

    def __init__(self, app):
        super().__init__(app, AH.HOME_DOOR, "down")
        self.world_w = AH.STREET_W
        self.bounds = pygame.Rect(10, 262, AH.STREET_W - 20, 140)
        self.npcs = [NPC(*n) for n in NPCS]
        self.talking = None
        self.hotspots = [Hotspot(AH.HOME_DOOR[0], 270, "casa", lambda: self.say("Não esqueci nada em casa. Vamos passear!"), 50)]
        for n in self.npcs:
            self.hotspots.append(Hotspot(0, 0, f"falar com {n.name}", (lambda n=n: self.talk(n)), 60))
        self.lamps = [x for x in range(330, AH.FOREST_X - 60, 360)]
        self.blockers = [pygame.Rect(x - 6, 392, 12, 10) for x in self.lamps]
        self.locked = .8
        self.think("Que dia bonito... vou andar um pouco.", 3.0, .4)
        self.dog_x = 1050.0
        self.ending = False

    def talk(self, n):
        self.talking = n
        n.facing = "left" if self.player.x < n.x else "right"
        name = self.app.profile.get("name", "")
        self.say(*[f"{n.name}: " + ln.format(nome=name) for ln in n.lines], then=self.stop_talk)

    def stop_talk(self):
        self.talking = None

    def tick(self, dt):
        for i, n in enumerate(self.npcs):
            n.update(dt, self.talking is n)
            h = self.hotspots[i + 1]
            h.x, h.y = n.x, n.y
        jorge = self.npcs[1]
        self.dog_x += (jorge.x + 40 * jorge.dir - self.dog_x) * min(1.0, dt * 3)
        if self.player.x > AH.STREET_W - 90 and not self.ending:
            self.ending = True
            from scene_choices import ChoicesScene
            self.app.profile["stage"] = "choices"
            self.app.save()
            self.app.set_scene(ChoicesScene(self.app, arriving=True))

    def draw_bg(self, surf):
        AH.draw_street(surf, self.cam_x)

    def actors(self):
        acts = []
        for n in self.npcs:
            acts.append((n.y, lambda n=n: n.draw(self.app.screen, self.cam_x, self.t)))
        j = self.npcs[1]
        acts.append((j.y + 2, lambda: AH.draw_dog(self.app.screen, self.dog_x - self.cam_x, j.y + 2, self.t,
                                                   j.patrol and j.pause <= 0, j.dir)))
        for x in self.lamps:
            if -60 < x - self.cam_x < W + 60:
                acts.append((398, lambda x=x: AH.lamp_post(self.app.screen, x, 398, self.cam_x, self.t)))
        acts.append((400, lambda: AH.sign_post(self.app.screen, AH.FOREST_X - 30, 400, self.cam_x, "Campo  >")))
        return acts

    def draw_fg(self, surf):
        for k in range(3):                                   # passarinhos
            bx = pixel.snap((self.t * 60 + k * 400) % (W + 200) - 100)
            by = pixel.snap(30 + k * 27)
            for dx, dy in ((-6, -3), (-3, 0), (0, 0), (3, 0), (6, -3)):
                pygame.draw.rect(surf, (110, 80, 92), (bx + dx, by + dy, 3, 3))
