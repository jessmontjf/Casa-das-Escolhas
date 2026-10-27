"""A casa do protagonista: introdução, quarto (banho + guarda-roupa), corredor
e térreo (cozinha, sala, entrada, quintal)."""
import math

import pygame

import art
import art_home as AH
import pixel
import ui
from art import BUTTER, CORAL, CREAM, INK, MINT, PAPER, W, H, WOOD, WOOD_D, darker, hexc, lighter
from content import BOTTOMS, SHOES, TOPS
from minigames import CafeComLeite, Omelete, PaoComManteiga
from world import Hotspot, Scene, WorldScene


# ============================================================ introdução
class IntroScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        look = app.look()
        self.cut = ui.Cutscene([
            {"draw": lambda s, t: AH.cut_sleep(s, t, look, 2.2), "dur": 5.0},
            {"draw": lambda s, t: AH.cut_sit(s, t, look), "caption": "Já são 6h... melhor levantar."},
        ], then=self.finish)

    def finish(self):
        self.app.profile["stage"] = "bedroom"
        self.app.save()
        self.app.set_scene(BedroomScene(self.app, intro=True))

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.finish_now()
        self.cut.handle(e)

    def finish_now(self):
        self.cut.done = True

    def update(self, dt):
        self.t += dt
        if not self.cut.done:
            self.cut.update(dt)
        elif self.cut.then:
            then, self.cut.then = self.cut.then, None
            then()

    def draw(self, surf):
        self.cut.draw(surf, self.t)


# ============================================================ guarda-roupa
class Wardrobe:
    CATS = [("Parte de cima", TOPS), ("Parte de baixo", BOTTOMS), ("Sapatos", SHOES)]

    def __init__(self, app, then):
        self.app, self.then_cb = app, then
        self.sel = list(app.profile.get("outfit") or [0, 0, 0])
        self.focus, self.done, self.then, self.t = 0, False, None, 0.0

    def rows(self):
        return [pygame.Rect(470, 120 + i * 112, 420, 96) for i in range(3)]

    def button(self):
        return pygame.Rect(580, 470, 200, 58)

    def cycle(self, i, d):
        self.sel[i] = (self.sel[i] + d) % 3
        self.app.audio.play("paper")

    def confirm(self):
        self.app.audio.play("chime")
        self.app.profile["outfit"] = self.sel
        self.done = True
        self.then = self.then_cb

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                self.focus = (self.focus - 1) % 4
                self.app.audio.play("blip")
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.focus = (self.focus + 1) % 4
                self.app.audio.play("blip")
            elif e.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d) and self.focus < 3:
                self.cycle(self.focus, -1 if e.key in (pygame.K_LEFT, pygame.K_a) else 1)
            elif e.key in ui.CONFIRM:
                if self.focus == 3:
                    self.confirm()
                else:
                    self.focus += 1
                    self.app.audio.play("blip")
            elif e.key == pygame.K_ESCAPE:
                self.done = True
        elif e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rows()):
                if r.collidepoint(e.pos):
                    self.focus = i
            if self.button().collidepoint(e.pos):
                self.focus = 3
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rows()):
                if r.collidepoint(e.pos):
                    self.cycle(i, -1 if e.pos[0] < r.centerx else 1)
            if self.button().collidepoint(e.pos):
                self.confirm()

    def update(self, dt):
        self.t += dt

    def look(self):
        return self.app.look(outfit=self.sel)

    def draw(self, surf, t):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((80, 40, 40, 140))
        surf.blit(ov, (0, 0))
        frame = pygame.Rect(40, 30, 880, 580)
        pygame.draw.rect(surf, WOOD_D, frame, border_radius=22)
        pygame.draw.rect(surf, (250, 226, 200), frame.inflate(-30, -30), border_radius=14)
        pygame.draw.line(surf, WOOD_D, (80, 90), (420, 90), 6)
        for x in range(110, 420, 50):
            pygame.draw.arc(surf, (170, 150, 150), (x - 10, 84, 20, 18), 0, math.pi, 3)
        pygame.draw.ellipse(surf, (240, 200, 176), (120, 520, 280, 40))
        art.blit_glow(surf, (260, 330), 180, (60, 40, 30), .7)
        art.draw_character(surf, 260, 540, "down", 0, False, self.look(), 5.4, "stand",
                           "happy" if int(t * .7) % 3 == 0 else "open", sprite_hook=False)
        pixel.pixelate(surf)
        art.text(surf, "Guarda-roupa", art.font(32, bold=True), INK, (680, 57), "midtop")
        for i, (r, (cat, opts)) in enumerate(zip(self.rows(), self.CATS)):
            sel = i == self.focus
            rr_ = r.move(0, -4 if sel else 0)
            ui.paper(surf, rr_, BUTTER if sel else CREAM, border=CORAL if sel else None)
            it = opts[self.sel[i]]
            art.text(surf, cat, art.font(15, bold=True), darker(CORAL, .2), (rr_.centerx, rr_.top + 10), "midtop")
            art.text(surf, it["name"], art.font(22, bold=True), INK, (rr_.centerx, rr_.top + 38), "midtop")
            for k in range(3):
                c = hexc(opts[k]["color"])
                pygame.draw.circle(surf, c, (rr_.centerx - 24 + k * 24, rr_.bottom - 16), 8 if k == self.sel[i] else 5)
            for side, x in (("left", rr_.left + 26), ("right", rr_.right - 26)):
                ui.arrow_tri(surf, x, rr_.centery, 12, CORAL if sel else (210, 170, 160), side)
        b = self.button().move(0, -4 if self.focus == 3 else 0)
        ui.paper(surf, b, CORAL if self.focus == 3 else PAPER, border=darker(CORAL, .2))
        art.text(surf, "Vestir", art.font(24, bold=True), CREAM if self.focus == 3 else INK, b.center, "center")
        n = self.sel[0] * 9 + self.sel[1] * 3 + self.sel[2] + 1
        art.text(surf, f"combinação {n} de 27", art.font(15, italic=True), INK, (680, 540), "midtop")
        art.text(surf, "setas: escolher e trocar · Enter: vestir · Esc: fechar", art.font(16), INK, (W // 2, 586), "midtop")


# ============================================================ quarto
class BedroomScene(WorldScene):
    SCALE = 1.5
    BATH, WARD, DOOR = (635, 222), (835, 228), (480, 612)

    def __init__(self, app, intro=False):
        super().__init__(app, (300, 400) if intro else AH_spawn_bed(), "down")
        self.bounds = pygame.Rect(18, 210, 924, 418)
        self.blockers = [pygame.Rect(56, 150, 180, 226), pygame.Rect(240, 150, 66, 76),
                         pygame.Rect(750, 150, 170, 66), pygame.Rect(792, 356, 148, 78),
                         pygame.Rect(36, 410, 80, 64), pygame.Rect(60, 548, 64, 50),
                         pygame.Rect(612, 520, 90, 54), pygame.Rect(728, 524, 52, 50)]
        f = self.flags()
        self.hotspots = [
            Hotspot(*self.DOOR, "sair", self.exit, 70),
            Hotspot(*self.BATH, "tomar banho", self.bath, 70),
            Hotspot(*self.WARD, "guarda-roupa", self.wardrobe, 70),
            Hotspot(150, 400, "cama", lambda: self.say("Ainda quentinha... mas não. Hoje não!"), 70),
            Hotspot(345, 222, "janela", lambda: self.say("O sol já tá aparecendo. Vai ser um dia bonito."), 60),
            Hotspot(272, 240, "despertador", lambda: self.say("Seis em ponto. Quem coloca despertador num sábado?", "...Eu. Eu coloco."), 45),
            Hotspot(866, 462, "desenhos", lambda: self.say("Meu desenho de gatinho preto. Ainda falta o sininho na coleira."), 60),
            Hotspot(130, 548, "planta", lambda: self.say("A Dona Folha. Ela gosta de sol de manhã."), 60),
            Hotspot(76, 490, "brinquedos", lambda: self.say("Minha caixa de tesouros. Não é bagunça, é coleção."), 50),
        ]
        if intro:
            self.locked = 1.4
            self.think("Hmm... hora de começar o dia.", 3.0, .4)
        self.update_arrows()

    def update_arrows(self):
        f = self.flags()
        self.arrows = []
        if f.get("dressed"):
            self.arrows = [self.DOOR]
        elif f.get("showered"):
            self.arrows = [self.WARD]
        elif f.get("tried_exit"):
            self.arrows = [self.BATH]

    def exit(self):
        f = self.flags()
        if not f.get("dressed"):
            f["tried_exit"] = True
            self.say("Opa, espera aí!",
                     "Tenho que tomar banho e trocar de roupa antes de sair...",
                     "Senão eu vou ficar com preguiça o dia inteiro depois.",
                     then=self.update_arrows)
            return
        self.app.profile["stage"] = "hall"
        self.app.save()
        self.app.set_scene(HallScene(self.app))

    def bath(self):
        f = self.flags()
        if f.get("showered"):
            self.say("Já tomei banho. Tô cheirosinho!")
            return
        self.app.audio.play("whoosh")
        self.play([{"draw": AH.cut_shower, "caption": "Ahh... água quentinha. Lá-lá-lá..."},
                   {"draw": AH.cut_shower, "caption": "Pronto! Novinho em folha."}], then=self.after_bath)

    def after_bath(self):
        self.flags()["showered"] = True
        self.refresh_look()
        self.player.x, self.player.y, self.player.facing = self.BATH[0], self.BATH[1] + 30, "down"
        self.app.save()
        self.update_arrows()
        self.think("Agora, a roupa!", 2.5, .3)

    def wardrobe(self):
        f = self.flags()
        if not f.get("showered"):
            self.say("Melhor tomar banho antes de me trocar.")
            return
        first = not f.get("dressed")
        self.overlay = Wardrobe(self.app, lambda: self.after_dress(first))

    def after_dress(self, first):
        self.flags()["dressed"] = True
        self.refresh_look()
        self.app.save()
        self.update_arrows()
        if first:
            look = self.app.look()
            self.play([{"draw": lambda s, t: AH.cut_dressed(s, t, look),
                        "caption": "Agora é um bom momento pra tomar café da manhã."}])

    def draw_bg(self, surf):
        AH.draw_bedroom(surf, self.t)


def AH_spawn_bed():
    return (480, 560)


# ============================================================ corredor
class HallScene(WorldScene):
    SCALE = 1.5
    STAIRS = (840, 420)

    def __init__(self, app, from_stairs=False):
        spawn = (740, 400) if from_stairs else (165, 600)
        super().__init__(app, spawn, "left" if from_stairs else "up")
        self.bounds = pygame.Rect(18, 230, 924, 398)
        self.blockers = [pygame.Rect(20, 330, 80, 140), pygame.Rect(586, 210, 138, 26),
                         pygame.Rect(40, 570, 64, 40), pygame.Rect(558, 528, 68, 58),
                         pygame.Rect(712, 210, 48, 30)]
        self.hotspots = [
            Hotspot(480, 248, "quarto da mamãe", lambda: self.say(
                "O quarto da mamãe.", "Ela não está em casa... melhor não entrar sem ela."), 70),
            Hotspot(300, 250, "fotos", lambda: self.say(
                "Eu e a mamãe naquela viagem pra praia.",
                "Eu tinha medo do mar. Ela segurou minha mão o tempo todo."), 70),
            Hotspot(650, 250, "girassóis", lambda: self.say(
                "Girassóis. A mamãe diz que eles deixam a casa mais feliz."), 60),
            Hotspot(100, 250, "janela", lambda: self.say("Dá pra ver a rua daqui. Tá tudo calminho."), 60),
            Hotspot(110, 400, "banco", lambda: self.say("As almofadas que a vovó costurou. Macias demais."), 50),
            Hotspot(165, 612, "meu quarto", lambda: self.say("Já tá tudo arrumado lá dentro."), 50),
            Hotspot(*self.STAIRS, "descer", self.down, 90),
        ]
        if not self.flags().get("breakfast"):
            self.arrows = [self.STAIRS]

    def down(self):
        self.app.profile["stage"] = "ground"
        self.app.save()
        self.app.set_scene(GroundScene(self.app))

    def draw_bg(self, surf):
        AH.draw_hall(surf, self.t, self.app.profile.get("name", ""))


# ============================================================ térreo
TASKS = [("omelete", "Omelete", Omelete, (130, 232)),
         ("cafe", "Café com leite", CafeComLeite, (308, 232)),
         ("pao", "Pão com manteiga", PaoComManteiga, (262, 232))]


class GroundScene(WorldScene):
    SCALE = 1.5
    TABLE, DOOR, YARD = (162, 512), (480, 612), (894, 222)

    def __init__(self, app):
        super().__init__(app, (480, 250), "down")
        self.bounds = pygame.Rect(16, 214, 928, 414)
        self.blockers = [pygame.Rect(8, 150, 78, 70), pygame.Rect(84, 150, 252, 70),
                         pygame.Rect(84, 392, 156, 88), pygame.Rect(48, 416, 40, 46), pygame.Rect(232, 416, 40, 46),
                         pygame.Rect(636, 150, 58, 60), pygame.Rect(696, 150, 132, 52),
                         pygame.Rect(724, 398, 142, 46), pygame.Rect(686, 464, 224, 78),
                         pygame.Rect(570, 530, 36, 70), pygame.Rect(904, 230, 52, 70),
                         pygame.Rect(348, 236, 60, 32), pygame.Rect(358, 558, 68, 44),
                         pygame.Rect(546, 554, 30, 44), pygame.Rect(560, 240, 70, 40)]
        f = self.flags()
        self.hotspots = [
            Hotspot(480, 232, "subir", lambda: self.say("Não preciso subir agora."), 50),
            Hotspot(*self.DOOR, "sair", self.front_door, 70),
            Hotspot(*self.YARD, "quintal", lambda: self.say(
                "O quintal tá cheio de folhas..." if f.get("breakfast") else "Depois do café, quem sabe.",
                "Fica pra outro dia." if f.get("breakfast") else ""), 70),
            Hotspot(46, 232, "geladeira", lambda: self.say("Ovos, leite, manteiga... tá tudo aqui."), 50),
            Hotspot(205, 232, "pia", lambda: self.say("Louça lavada ontem. Ponto pra mim."), 30),
            Hotspot(760, 220, "TV", lambda: self.say("Desenho de sábado de manhã... mas hoje eu quero fazer outra coisa."), 70),
            Hotspot(664, 222, "estante", lambda: self.say("Os livros de receita da mamãe. Tem um bilhete dela no meio de um.",
                                                          "\"Não esquece de comer direito, viu? Te amo.\""), 50),
            Hotspot(595, 290, "caminha", lambda: self.say(
                "Uma caminha de gato com um sininho de brinquedo...",
                "...mas a gente nem tem gato. Tem?"), 55),
            Hotspot(800, 560, "sofá", lambda: self.say("Fofinho. Perigosamente fofinho."), 60),
            Hotspot(*self.TABLE, "comer", self.eat, 70, when=self.all_done),
        ]
        for key, label, game, pos in TASKS:
            self.hotspots.append(Hotspot(pos[0], pos[1], f"fazer {label.lower()}",
                                         (lambda g=game, k=key: self.cook(g, k)), 44,
                                         when=lambda k=key: self.cooking() and not f.get(k)))
        if not f.get("ground_seen"):
            f["ground_seen"] = True
            self.locked = 1.0
            self.think("Hora do café da manhã! Vou pra cozinha.", 3.4, .3)
        self.refresh_arrows()

    def cooking(self):
        f = self.flags()
        return f.get("kitchen_seen") and not f.get("breakfast")

    def all_done(self):
        f = self.flags()
        return self.cooking() and all(f.get(k) for k, *_ in TASKS)

    def refresh_arrows(self):
        f = self.flags()
        if f.get("breakfast"):
            self.arrows = [self.DOOR]
        elif not f.get("kitchen_seen"):
            self.arrows = [(170, 300)]
        elif self.all_done():
            self.arrows = [self.TABLE]
        else:
            self.arrows = [pos for k, _, _, pos in TASKS if not f.get(k)]

    def tick(self, dt):
        f = self.flags()
        if not f.get("kitchen_seen") and self.player.x < AH.KITCHEN_X and not self.busy():
            f["kitchen_seen"] = True
            look = self.app.look()
            draw = lambda s, t: AH.cut_mom(s, t, look)  # noqa: E731
            self.play([{"draw": draw, "caption": "Ah, é mesmo... a mamãe saiu cedinho pra resolver umas coisas."},
                       {"draw": draw, "caption": "Ela disse que só volta mais tarde, lá pra perto da noite."},
                       {"draw": draw, "caption": "Então hoje o café da manhã é por minha conta!"}],
                      then=self.after_memory)

    def after_memory(self):
        self.app.save()
        self.refresh_arrows()
        self.think("Omelete, café com leite e pão com manteiga!", 3.2, .2)

    def cook(self, game, key):
        self.overlay = game(self.app, then=lambda: self.cooked(key))

    def cooked(self, key):
        self.flags()[key] = True
        self.app.save()
        self.refresh_arrows()
        if self.all_done():
            self.think("Tudo pronto! Agora é só sentar e comer.", 3.0, .2)

    def eat(self):
        look = self.app.look()
        self.play([{"draw": AH.cut_eat, "caption": "Omelete, café com leite e pão com manteiga. Perfeito."},
                   {"draw": lambda s, t: AH.cut_full(s, t, look), "caption": "Ahh... tô satisfeito!"},
                   {"draw": lambda s, t: AH.cut_full(s, t, look),
                    "caption": "Hoje é sábado... acho que vou dar uma volta lá fora."}],
                  then=self.after_eat)

    def after_eat(self):
        self.flags()["breakfast"] = True
        self.app.save()
        self.refresh_arrows()

    def front_door(self):
        if not self.flags().get("breakfast"):
            self.say("Ainda nem tomei café... minha barriga tá roncando.")
            return
        from scene_street import StreetScene
        self.app.profile["stage"] = "street"
        self.app.save()
        self.app.set_scene(StreetScene(self.app))

    def draw_bg(self, surf):
        AH.draw_ground(surf, self.t)

    def draw_hud(self, surf):
        f = self.flags()
        if not self.cooking():
            return
        r = pygame.Rect(W - 250, 14, 236, 30 + 28 * len(TASKS))
        ui.paper(surf, r, CREAM, border=CORAL, lines=False)
        art.text(surf, "Café da manhã", art.font(17, bold=True), INK, (r.left + 14, r.top + 8))
        for i, (k, label, _, _) in enumerate(TASKS):
            y = r.top + 36 + i * 28
            box = pygame.Rect(r.left + 14, y, 16, 16)
            pygame.draw.rect(surf, MINT if f.get(k) else CREAM, box, border_radius=4)
            pygame.draw.rect(surf, INK, box, 2, border_radius=4)
            if f.get(k):
                pygame.draw.lines(surf, INK, False, [(box.left + 3, box.centery), (box.centerx - 1, box.bottom - 4), (box.right - 3, box.top + 3)], 2)
            art.text(surf, label, art.font(16), INK, (box.right + 10, y - 1))
