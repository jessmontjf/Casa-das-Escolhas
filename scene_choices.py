"""A casa no campo: 5 escolhas entre 3 itens. Um 'Arquiteto' invisível
(Claude + MCP) tenta prever o que você vai escolher e põe o palpite SEMPRE no meio."""
import math
import random

import pygame

import art
import pixel
import ui
from art import (DOOR_POS, FIELD_BOUNDS, FINAL_POS, GRASS, HOUSE_BLOCK, HOUSE_POS, TAU, H, W,
                 hexc, lighter, darker, mix)
from content import TRAIT_LABEL
from fx import Particles, Shatter
from world import Player, Scene

REVEAL_AT_END = True          # no final "Sim", conta que o meio era o palpite
PED_X = [W * .25, W * .5, W * .75]
PED_Y = 400
ROOM_BOUNDS = pygame.Rect(30, 330, W - 60, H - 342)
NO_LINE = "você sabe o que tá acontecendo aqui, né?"


class ChoicesScene(Scene):
    SCALE = 0.8

    def __init__(self, app, arriving=False):
        super().__init__(app)
        self.field = art.Field()
        self.agent = app.agent()
        prof = app.profile
        if prof.get("mcp"):
            self.agent.load(prof["mcp"])
        else:
            self.agent.reset()
        self.state = self.agent.get_state()
        self.pending = self.agent.ensure()

        self.scene = "outside"
        self.player = self.mkplayer(W / 2, H - 40, "up")
        self.particles = Particles()
        self.trans = None
        self.toast_msg, self.toast_t = None, 0.0
        self.shatter, self.flash, self.want_shatter = None, 0.0, False
        self.house_visible, self.house_shatter, self.vanish_wait = True, None, None
        self.last_choice = False
        self.final_k = 0.0
        self.room, self.show, self.offer_sel = None, None, 0
        self.end_t = 0.0
        self.rays = pygame.Surface((W, H))
        self.thoughts = ui.Thoughts()
        self.pause = None
        self.locked = 0.0
        self.grab = None            # (início, ação) — mãos fechando no item
        st = self.state
        if st.get("final"):                      # jogo salvo depois da 5ª escolha
            self.house_visible, self.final_k = False, 1.0
            self.player = self.mkplayer(W / 2, 330, "down")
        elif st["round"] >= st["max_rounds"]:
            self.last_choice, self.vanish_wait = True, 1.0
            self.player = self.mkplayer(W / 2, 330, "down")
        elif arriving and st["round"] == 0:
            self.locked = 9.5
            for k, (txt, d) in enumerate((("Uma casa...?", 2.2),
                                          ("Eu nunca tinha visto essa casa antes.", 2.6),
                                          ("Ela é tão bonita... deve ser de algum vizinho novo.", 2.8),
                                          ("Seria legal ir conhecer!", 2.2))):
                self.thoughts.add(txt, lambda: self.player.head(), d, [0.6, 2.9, 5.6, 8.5][k])

    @property
    def screen(self):
        return self.app.screen

    def mkplayer(self, x, y, facing):
        return Player(x, y, facing, self.app.look(), self.SCALE)

    # ------------------------------------------------------------ util
    def toast(self, msg, secs=3.5):
        self.toast_msg, self.toast_t = msg, secs

    def go(self, fn, dur=0.45):
        self.trans = [0.0, dur, fn, False]

    def history(self):
        return self.state.get("history", [])

    def room_ready(self):
        return self.pending is None and self.state.get("room") is not None

    def final(self):
        return self.state.get("final") if self.pending is None else None

    def poll(self):
        if self.pending is not None and self.pending.done():
            try:
                self.state = self.pending.result()
            except Exception as e:  # noqa: BLE001
                print("[jogo] erro no Arquiteto:", e)
                self.state = self.agent.get_state()
                if self.state["round"] < self.state["max_rounds"] and not self.state["room"]:
                    self.pending = self.agent.ensure()
                    return
            self.pending = None
            self.app.profile["mcp"] = self.state      # salva o progresso (inclui o que a IA aprendeu)
            self.app.save()

    def window_color(self):
        st = self.state.get("room")
        if self.room_ready() and st:
            return art.THEME_STYLE.get(st["theme"], art.THEME_STYLE["cripta"])["accent"]
        k = .5 + .5 * math.sin(self.t * 3)
        return mix((120, 100, 90), (255, 220, 150), k)

    # ------------------------------------------------------------ eventos
    def close_pause(self):
        self.pause = None

    def handle(self, e):
        if self.pause:
            self.pause.handle(e)
            return
        if e.type != pygame.KEYDOWN or self.trans or self.shatter or self.locked > 0 or self.grab:
            return
        k = e.key
        if k == pygame.K_ESCAPE and self.scene in ("outside", "room"):
            self.pause = ui.Pause(self.app, self.close_pause)
            return
        act = k in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER)
        if self.scene == "outside" and act:
            self.interact_outside()
        elif self.scene == "room" and act:
            idx = self.near_pedestal()
            if idx is not None:
                self.open_showcase(idx)
        elif self.scene == "showcase":
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start_grab(self.choose)
            elif k in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_e):
                self.close_showcase()
                self.scene = "room"
        elif self.scene == "offer":
            if k in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d, pygame.K_UP, pygame.K_DOWN):
                self.offer_sel = 1 - self.offer_sel
                self.app.audio.play("blip")
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_e):
                if self.offer_sel == 0:
                    self.start_grab(self.answer_offer)
                else:
                    self.answer_offer()
        elif self.scene == "ending_yes" and k in (pygame.K_ESCAPE, pygame.K_RETURN) and self.end_t > 2:
            self.app.finish_game()

    def start_grab(self, action):
        self.grab = (self.t, action)
        self.app.audio.play("pop")

    def grab_k(self):
        return 0.0 if not self.grab else min(1.0, (self.t - self.grab[0]) / .5)

    def interact_outside(self):
        p = self.player
        if self.house_visible and math.hypot(p.x - DOOR_POS[0], p.y - DOOR_POS[1]) < 55:
            if self.state["round"] >= self.state["max_rounds"] or self.last_choice:
                self.toast("A porta não abre mais.")
            elif self.room_ready():
                self.go(self.enter_room)
            else:
                self.toast("A porta está trancada... algo se mexe lá dentro.")
        elif not self.house_visible and self.final_k > .9 and self.near_final():
            self.app.audio.play("blip")
            self.show = {"t0": self.t}
            self.offer_sel = 0
            self.scene = "offer"

    def near_final(self):
        return math.hypot(self.player.x - FINAL_POS[0], self.player.y - FINAL_POS[1]) < 70

    def near_pedestal(self):
        best = None
        for i, x in enumerate(PED_X):
            d = math.hypot(self.player.x - x, self.player.y - (PED_Y + 10))
            if d < 75 and (best is None or d < best[0]):
                best = (d, i)
        return best[1] if best else None

    # ------------------------------------------------------------ sala
    def enter_room(self):
        self.room = self.state["room"]
        self.scene = "room"
        self.player = self.mkplayer(W / 2, H - 30, "up")
        self.room_t0 = self.t
        self.secs, self.counts = {}, {}
        self.banner_t0 = self.t
        self.toast_t = 0

    def open_showcase(self, idx):
        item = self.room["items"][idx]
        self.counts[item["id"]] = self.counts.get(item["id"], 0) + 1
        self.show = {"idx": idx, "item": item, "t0": self.t}
        self.scene = "showcase"
        self.app.audio.play("blip")

    def close_showcase(self):
        item = self.show["item"]
        self.secs[item["id"]] = self.secs.get(item["id"], 0) + (self.t - self.show["t0"])

    def choose(self):
        self.close_showcase()
        item = self.show["item"]
        self.last_choice = self.state["round"] + 1 >= self.state["max_rounds"]
        self.pending = self.agent.choose(item["id"], self.secs, self.counts, self.t - self.room_t0)
        self.app.audio.play("chime")
        self.want_shatter = True

    def after_snapshot(self, snap):
        """O lugar se desfaz e você volta pro lado de fora da casa."""
        self.shatter = Shatter(snap, tile=20, origin=(W / 2, 230), up=-50, life=1.3)
        self.flash = 1.0
        self.app.audio.play("whoosh")
        self.scene = "outside"
        self.player = self.mkplayer(DOOR_POS[0], DOOR_POS[1] + 34, "down")
        self.room = None
        if self.last_choice:
            self.vanish_wait = 1.2

    # ------------------------------------------------------------ final
    def start_vanish(self):
        surf = art.house_surface(self.window_color(), self.t)
        ox, oy = HOUSE_POS[0] - 10, HOUSE_POS[1] - 6
        self.house_shatter = Shatter(surf, (ox, oy), tile=10, origin=(150, 200), speed=(30, 120),
                                     up=-90, life=1.9, wave=1.0, skip_empty=True)
        self.house_visible = False
        self.app.audio.play("whoosh")
        for _ in range(6):
            self.particles.emit(W / 2 + random.uniform(-120, 120), 170 + random.uniform(-60, 60), 8,
                                random.choice([(255, 150, 190), (255, 255, 255), (255, 220, 120)]),
                                speed=60, life=3.0, kind="petal", gravity=18, up=-40)
        self.toast("A casa se desfez. Alguma coisa brilha num canto do campo.", 5)

    def answer_offer(self):
        if self.offer_sel == 0:
            self.app.audio.play("chime")
            self.go(self.to_yes, .8)
        else:
            self.scene = "ending_no"
            self.end_t = 0.0
            self.cat = {"x": W + 80.0, "mode": "walk", "rang": 0, "sit_t": None, "ring_t": None}
            self.player.facing = "right"

    def to_yes(self):
        self.scene = "ending_yes"
        self.end_t = 0.0

    # ------------------------------------------------------------ update
    def update(self, dt):
        if self.pause:
            return
        self.t += dt
        self.locked = max(0.0, self.locked - dt)
        self.thoughts.update(dt)
        if self.grab and self.t - self.grab[0] >= .55:
            action, self.grab = self.grab[1], None
            action()
        self.poll()
        if self.trans:
            self.trans[0] += dt
            if not self.trans[3] and self.trans[0] >= self.trans[1]:
                self.trans[2]()
                self.trans[3] = True
            if self.trans[0] >= self.trans[1] * 2:
                self.trans = None
        if self.toast_t > 0:
            self.toast_t -= dt
        self.flash = max(0.0, self.flash - dt * 2.5)
        if self.shatter:
            self.shatter.update(dt)
            if self.shatter.done:
                self.shatter = None
        if self.house_shatter:
            self.house_shatter.update(dt)
            if self.house_shatter.done:
                self.house_shatter = None
        self.particles.update(dt)
        keys = pygame.key.get_pressed()
        locked = self.trans is not None or self.shatter is not None or self.locked > 0

        if self.scene == "outside":
            blockers = self.field.blockers + ([HOUSE_BLOCK] if self.house_visible else [])
            if not locked:
                self.player.update(dt, keys, FIELD_BOUNDS, blockers)
            if self.vanish_wait is not None and not self.shatter and self.final():
                self.vanish_wait -= dt
                if self.vanish_wait <= 0:
                    self.vanish_wait = None
                    self.start_vanish()
            if not self.house_visible:
                self.final_k = min(1.0, self.final_k + dt * .6)
                if random.random() < .15:
                    self.particles.emit(FINAL_POS[0], FINAL_POS[1] - 60, 1,
                                        hexc(self.state["final"]["item"]["glow"]), speed=40, life=1.0, size=4)
        elif self.scene == "room":
            blockers = [pygame.Rect(int(x) - 36, PED_Y - 18, 72, 20) for x in PED_X]
            if not locked:
                self.player.update(dt, keys, ROOM_BOUNDS, blockers)
        elif self.scene in ("showcase", "offer"):
            item = self.show_item()
            if random.random() < .5:
                a = random.uniform(0, TAU)
                self.particles.emit(W / 2 + math.cos(a) * 110, 215 + math.sin(a) * 90, 1,
                                    hexc(item["glow"]), speed=25, life=1.2, size=5, up=-15)
        elif self.scene == "ending_yes":
            self.end_t += dt
        elif self.scene == "ending_no":
            self.update_no(dt)

    def update_no(self, dt):
        self.end_t += dt
        c = self.cat
        target = self.player.x + 80
        if c["mode"] == "walk":
            c["x"] -= 120 * dt
            if c["x"] <= target:
                c["x"], c["mode"], c["sit_t"] = target, "sit", self.end_t
        else:
            st = self.end_t - c["sit_t"]
            for k, when in enumerate((1.0, 1.9)):
                if c["rang"] == k and st >= when:
                    c["rang"] += 1
                    self.app.audio.play("bell")
                    c["ring_t"] = self.end_t
            if st > 3.0 + len(NO_LINE) / 22 + 3.4:
                self.app.quit()

    def show_item(self):
        if self.scene == "offer":
            return self.state["final"]["item"]
        return self.show["item"]

    # ------------------------------------------------------------ desenho
    def draw_hud(self):
        if self.scene in ("ending_yes", "ending_no", "offer"):
            return
        r = pygame.Rect(15, 12, 5 * 42 + 12, 51)
        art.panel(self.screen, r, art.DUSK, 190)
        hist = self.history()
        for i in range(5):
            cx, cy = r.left + 27 + i * 42, r.centery
            pygame.draw.rect(self.screen, (150, 110, 120), (pixel.snap(cx - 16), pixel.snap(cy - 15), 33, 33), 3)
            if i < len(hist):
                icon = art.item_surface(hist[i]["chosen"], 30)
                self.screen.blit(icon, icon.get_rect(center=(cx, cy)))

    def draw_toast(self):
        if not self.toast_msg or self.toast_t <= 0:
            return
        a = min(1.0, self.toast_t)
        f = art.font(20, italic=True)
        w = min(W - 80, f.size(self.toast_msg)[0] + 40)
        lines = art.wrap(self.toast_msg, f, w - 40)
        r = pygame.Rect(0, 0, w, 20 + 26 * len(lines))
        r.midbottom = (W // 2, H - 18)
        art.panel(self.screen, r, art.DUSK, int(200 * a), 12)
        for i, ln in enumerate(lines):
            art.text(self.screen, ln, f, mix(art.DUSK, (245, 235, 250), a), (r.centerx, r.top + 10 + i * 26), "midtop")

    def draw_field(self, with_house=True, show_final=True):
        s = self.screen
        s.blit(self.field.ground, (0, 0))
        draws = [(y, (lambda sf=sf, pos=pos: s.blit(sf, pos))) for y, sf, pos in self.field.sprites]
        if with_house and self.house_visible:
            shake = 0
            if self.vanish_wait is not None and self.final():
                shake = math.sin(self.t * 40) * 2
            draws.append((DOOR_POS[1], lambda: art.draw_house(s, HOUSE_POS[0] + shake, HOUSE_POS[1], self.window_color(), self.t)))
        fin = self.state.get("final")
        if show_final and not self.house_visible and fin and self.final_k > 0:
            draws.append((FINAL_POS[1], lambda: self.draw_final_spot(fin["item"])))
        draws.append((self.player.y, lambda: self.player.draw(s)))
        for _, fn in sorted(draws, key=lambda d: d[0]):
            fn()
        if self.house_shatter:
            self.house_shatter.draw(s)

    def draw_final_spot(self, item, alpha_k=None):
        k = self.final_k if alpha_k is None else alpha_k
        x, y = FINAL_POS
        pygame.draw.ellipse(self.screen, mix(GRASS, (176, 168, 174), k), (x - 27, y - 15, 54, 21))
        pygame.draw.ellipse(self.screen, mix(GRASS, (206, 200, 204), k), (x - 24, y - 15, 48, 15))
        art.draw_floating_item(self.screen, item, (x, y - 62), 64, self.t, 1.1 * k, int(255 * k))

    # ------------------------------------------------------------ desenho (mundo → pixeliza → interface)
    def prompts(self):
        p = self.player
        if self.trans or self.shatter:
            return
        if self.scene == "outside":
            if self.house_visible and not self.last_choice and math.hypot(p.x - DOOR_POS[0], p.y - DOOR_POS[1]) < 55:
                art.prompt_bubble(self.screen, p.x, p.y - 96, "E  entrar", self.t)
            elif not self.house_visible and self.final_k > .9 and self.near_final():
                art.prompt_bubble(self.screen, p.x, p.y - 96, "E  pegar", self.t)
        elif self.scene == "room" and self.near_pedestal() is not None:
            art.prompt_bubble(self.screen, p.x, p.y - 96, "E  examinar", self.t)

    def draw_outside(self):
        self.draw_field()

    def draw_room_world(self):
        s, room = self.screen, self.room
        art.draw_room(s, room["theme"], self.t)
        draws = []
        for i, x in enumerate(PED_X):
            item = room["items"][i]

            def ped(x=x, item=item, i=i):
                art.draw_pedestal(s, x, PED_Y, room["theme"])
                # o palpite (meio) brilha um tiquinho mais — quase imperceptível
                strength = 1.0 if i == 1 else .85
                art.draw_floating_item(s, item, (x, PED_Y - 140), 96, self.t + i * 1.7, strength)
            draws.append((PED_Y, ped))
        draws.append((self.player.y, lambda: self.player.draw(s)))
        for _, fn in sorted(draws, key=lambda d: d[0]):
            fn()

    def room_ui(self):
        s, room = self.screen, self.room
        dt_b = self.t - self.banner_t0
        if dt_b < 5 and room.get("intro"):
            a = max(0.0, min(1.0, dt_b, 5 - dt_b))
            f = art.font(22)
            img = f.render(room["intro"], False, art.CREAM)
            r = img.get_rect(midtop=(W // 2, 78))
            art.panel(s, r.inflate(36, 18), art.DUSK, int(200 * a))
            img.set_alpha(int(255 * a))
            s.blit(img, r)

    def showcase_art(self):
        """Mãos (adaptadas da foto de referência) subindo e indo pegar o item."""
        s, item = self.screen, self.show_item()
        c, G = hexc(item["color"]), hexc(item["glow"], (255, 255, 255))
        k = min(1.0, (self.t - self.show["t0"]) / .6)
        ease = 1 - (1 - k) ** 3
        g = self.grab_k()
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((*mix(darker(c, .72), (90, 40, 48), .45), int(215 * ease)))
        s.blit(ov, (0, 0))
        cx, cy = W / 2, 215
        self.rays.fill((0, 0, 0))
        ray_col = art.scale(G, .09 * ease)
        for i in range(10):
            a = self.t * .25 + i * TAU / 10
            pygame.draw.polygon(self.rays, ray_col, [
                (cx, cy), (cx + math.cos(a) * 420, cy + math.sin(a) * 420),
                (cx + math.cos(a + .13) * 420, cy + math.sin(a + .13) * 420)])
        s.blit(self.rays, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        art.blit_glow(s, (cx, cy), 175 + 12 * math.sin(self.t * 3), G, (.75 + .5 * g) * ease)
        bob = math.sin(self.t * 2) * 9 * (1 - g)
        size = 192
        img = art.spin_item(item, size, self.t * 1.7 * (1 - g * .8))
        s.blit(img, img.get_rect(center=(int(cx), int(cy + bob))))
        # mãos: sobem de baixo (alcançar) e fecham no item (pegar)
        curl = .1 + .06 * math.sin(self.t * 2.4) + g * .9
        left, right = pixel.hands(curl)
        hy = 345 + (1 - ease) * 330 - g * 40
        dx = 162 - g * 62
        for img_, x in ((left, cx - dx), (right, cx + dx)):
            r = img_.get_rect(center=(int(x), int(hy)))
            s.blit(img_, (pixel.snap(r.x), pixel.snap(r.y)))
        self.particles.draw(s)
        if g > .6:
            fl = pygame.Surface((W, H))
            fl.fill(art.scale(G, (g - .6) * 1.2))
            s.blit(fl, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    def showcase_ui(self):
        s, item = self.screen, self.show_item()
        c, G = hexc(item["color"]), hexc(item["glow"], (255, 255, 255))
        box = pygame.Rect(W // 2 - 351, 444, 702, 141)
        reveal = (self.t - self.show["t0"] - .5) * 35 / max(1, len(item["phrase"]))
        art.draw_caption(s, box, item, self.t, item["name"], item["phrase"], reveal)
        f = art.font(18)
        if self.scene == "showcase":
            art.text(s, "Enter: pegar este      Esc: devolver", f, lighter(G, .3), (W // 2, H - 36), "midtop")
        else:
            art.text(s, "Aceitar?", art.font(22, bold=True), lighter(G, .3), (W // 2, H - 51), "midtop")
            for i, lab in enumerate(("Sim", "Não")):
                r = pygame.Rect(0, 0, 111, 36)
                r.center = (W // 2 + (i * 2 - 1) * 150, H - 36)
                sel = i == self.offer_sel
                art.panel(s, r, G if sel else darker(c, .6), 240, border=lighter(G, .2))
                art.text(s, lab, art.font(20, bold=True), darker(c, .7) if sel else art.CREAM, r.center, "center")

    def yes_art(self):
        s, fin = self.screen, self.state["final"]
        item = fin["item"]
        c, G = hexc(item["color"]), hexc(item["glow"], (255, 255, 255))
        art._vgrad(s, pygame.Rect(0, 0, W, H), mix(darker(c, .35), (150, 76, 80), .6), (70, 34, 44))
        k = min(1.0, self.end_t / 1.2)
        art.draw_floating_item(s, item, (W / 2, 100), 144, self.t, k)

    def yes_ui(self):
        s, fin = self.screen, self.state["final"]
        item = fin["item"]
        c, G = hexc(item["color"]), hexc(item["glow"], (255, 255, 255))
        art.text(s, "SEU RESULTADO", art.font(18, bold=True), lighter(G, .2), (W / 2, 183), "midtop")
        art.text(s, fin["title"], art.font(38, bold=True), G, (W / 2, 204), "midtop", shadow=darker(c, .7))
        f = art.font(20)
        lines = art.wrap(fin["text"], f, W - 240)
        box = pygame.Rect(99, 267, W - 198, 36 + 27 * len(lines))
        art.panel(s, box, mix(darker(c, .78), (18, 14, 28), .35), 235, border=lighter(c, .4))
        art.FRAME_FUNCS.get(item["frame"], art._fr_estrelas)(s, box, c, G, self.t)
        pixel.pixelate(s, box.inflate(36, 36))
        for i, ln in enumerate(lines):
            art.text(s, ln, f, (240, 234, 246), (W / 2, box.top + 18 + i * 27), "midtop")
        pct = sorted(fin["percentages"].items(), key=lambda kv: -kv[1])
        y0 = box.bottom + 33
        grow = min(1.0, max(0.0, (self.end_t - .8) / 1.5))
        for i, (trait, v) in enumerate(pct):
            col, row = i % 2, i // 2
            x, y = 129 + col * 372, y0 + row * 39
            art.text(s, TRAIT_LABEL[trait], art.font(18), (240, 228, 236), (x, y))
            bar = pygame.Rect(x + 120, y + 3, 180, 15)
            art.notched(s, bar, (90, 60, 76))
            fill = bar.copy()
            fill.width = pixel.snap(bar.width * v / 100 * grow)
            if fill.width >= 6:
                art.notched(s, fill, G)
            art.text(s, f"{int(v * grow)}%", art.font(16), lighter(G, .3), (bar.right + 10, y))
        if REVEAL_AT_END and self.end_t > 3.5:
            a = min(1.0, (self.end_t - 3.5) / 1.5)
            msg = (f"P.S.: o item do meio sempre foi o meu palpite. "
                   f"Acertei {fin['hits']} de {fin['rounds']}. Coincidência, né?")
            img = art.font(18).render(msg, False, lighter(G, .4))
            img.set_alpha(int(255 * a))
            s.blit(img, img.get_rect(midtop=(W / 2, H - 63)))
        art.text(s, "Enter para voltar ao correio", art.font(16), (230, 200, 200), (W / 2, H - 30), "midtop")

    def no_art(self):
        s, c = self.screen, self.cat
        self.draw_field(with_house=False, show_final=False)
        fade = max(0.0, 1 - self.end_t / 1.2)
        if fade > 0:
            self.draw_final_spot(self.state["final"]["item"], fade)
        mode = c["mode"]
        paw = 0.0
        if mode == "sit":
            st = self.end_t - c["sit_t"]
            for when in (1.0, 1.9):
                d = st - (when - .35)
                if 0 <= d < .6:
                    paw = math.sin(d / .6 * math.pi)
        bx, by = art.draw_cat(s, c["x"], self.player.y + 4, self.t, mode, -1, paw)
        if c["ring_t"] is not None:
            dt = self.end_t - c["ring_t"]
            for k in range(3):
                rad = (dt - k * .15) * 90
                if 0 < rad < 80:
                    pygame.draw.circle(s, (255, 236, 150), (int(bx), int(by)), int(rad), 3)
            if dt < .5:
                art.blit_glow(s, (bx, by), 40, (255, 220, 120), 1 - dt * 2)

    def no_ui(self):
        s, c = self.screen, self.cat
        if c["mode"] == "sit":
            st = self.end_t - c["sit_t"]
            if st > 3.0:
                n = int((st - 3.0) * 22)
                box = pygame.Rect(W // 2 - 330, H - 120, 660, 75)
                art.panel(s, box, art.DUSK, 235, border=(150, 110, 130))
                art.text(s, NO_LINE[:n], art.font(26), art.CREAM, box.center, "center")
            end = 3.0 + len(NO_LINE) / 22 + 1.6
            if st > end:
                k = min(1.0, (st - end) / 1.6)
                ov = pygame.Surface((W, H))
                ov.set_alpha(int(255 * k))
                s.blit(ov, (0, 0))

    def draw(self, surf):
        s = self.screen
        sc = self.scene
        if sc in ("outside", "offer"):
            self.draw_field()
            if sc == "outside":
                self.particles.draw(s)
        elif sc in ("room", "showcase"):
            self.draw_room_world()
        elif sc == "ending_yes":
            self.yes_art()
        elif sc == "ending_no":
            self.no_art()
        if sc in ("showcase", "offer"):
            pixel.pixelate(s, grade=True)
            self.showcase_art()
        pixel.pixelate(s, grade=sc not in ("showcase", "offer"))
        if self.want_shatter:  # tira uma 'foto' da cena e quebra ela em pedaços
            self.want_shatter = False
            self.after_snapshot(s.copy())
            self.particles.p.clear()
            self.draw_field()
            pixel.pixelate(s, grade=True)
        if self.shatter:
            self.shatter.draw(s)
        if self.flash > 0:
            ov = pygame.Surface((W, H))
            ov.fill((255, 250, 240))
            ov.set_alpha(int(255 * min(1.0, self.flash)))
            s.blit(ov, (0, 0))
        # ---- interface (nítida, por cima do mundo pixelizado)
        if sc in ("outside", "room"):
            self.prompts()
        if sc == "room":
            self.room_ui()
        elif sc in ("showcase", "offer"):
            self.showcase_ui()
        elif sc == "ending_yes":
            self.yes_ui()
        elif sc == "ending_no":
            self.no_ui()
        self.thoughts.draw(s)
        self.draw_hud()
        self.draw_toast()
        if self.pause:
            self.pause.draw(s, self.t)
        if self.trans:
            t, d, _, switched = self.trans
            a = min(1.0, t / d) if not switched else max(0.0, 1 - (t - d) / d)
            ov = pygame.Surface((W, H))
            ov.fill((60, 30, 36))
            ov.set_alpha(int(255 * a))
            s.blit(ov, (0, 0))
