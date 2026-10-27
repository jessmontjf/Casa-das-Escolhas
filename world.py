"""Base das cenas onde o jogador anda: movimento, pontos de interação, balões,
diálogos, quadros de história e sobreposições (guarda-roupa, minijogos)."""
import math

import pygame

import art
import pixel
import ui
from art import W, H

ACT_KEYS = (pygame.K_e, pygame.K_z, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER)


class Scene:
    def __init__(self, app):
        self.app, self.t = app, 0.0

    def enter(self):
        pass

    def handle(self, e):
        pass

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        pass


class Player:
    SPEED = 200

    def __init__(self, x, y, facing="down", look=None, scale=1.0):
        self.x, self.y, self.facing = float(x), float(y), facing
        self.look, self.scale = look, scale
        self.phase, self.moving = 0.0, False

    def update(self, dt, keys, bounds, blockers):
        dx = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(keys[pygame.K_UP] or keys[pygame.K_w])
        self.moving = bool(dx or dy)
        if not self.moving:
            return
        if dx and dy:
            dx, dy = dx * .7071, dy * .7071
        if abs(dx) > abs(dy):
            self.facing = "right" if dx > 0 else "left"
        else:
            self.facing = "down" if dy > 0 else "up"
        self.phase += dt * 11
        sp = self.SPEED * (0.75 + 0.25 * self.scale)
        for mx, my in ((dx, 0), (0, dy)):
            nx, ny = self.x + mx * sp * dt, self.y + my * sp * dt
            foot = pygame.Rect(int(nx) - 9, int(ny) - 6, 18, 8)
            if bounds.contains(foot) and not any(foot.colliderect(b) for b in blockers):
                self.x, self.y = nx, ny

    def head(self, cam_x=0):
        return self.x - cam_x, self.y - 70 * self.scale

    def draw(self, surf, cam_x=0):
        art.draw_character(surf, self.x - cam_x, self.y, self.facing, self.phase, self.moving,
                           self.look, self.scale)


class Hotspot:
    def __init__(self, x, y, label, action, r=60, when=None):
        self.x, self.y, self.label, self.action, self.r, self.when = x, y, label, action, r, when

    def active(self):
        return self.when is None or self.when()


class WorldScene(Scene):
    SCALE = 1.5
    BG_ASSET = None          # nome do PNG de cenário (assets/<nome>.png), se houver

    def __init__(self, app, spawn, facing="down"):
        super().__init__(app)
        self.player = Player(spawn[0], spawn[1], facing, app.look(), self.SCALE)
        self.hotspots, self.blockers = [], []
        self.bounds = pygame.Rect(0, 0, W, H)
        self.cam_x, self.world_w = 0.0, W
        self.dialog = self.cutscene = self.overlay = self.pause = None
        self.thoughts, self.toast = ui.Thoughts(), ui.Toast()
        self.arrows = []
        self.locked = 0.0   # segundos sem poder andar (ex.: enquanto pensa)

    # ---------- ferramentas pras cenas ----------
    def say(self, *lines, then=None):
        self.dialog = ui.Dialog(lines, then)

    def play(self, frames, then=None):
        self.cutscene = ui.Cutscene(frames, then)

    def think(self, text, secs=3.2, delay=0.0):
        self.thoughts.add(text, lambda: self.player.head(self.cam_x), secs, delay)

    def refresh_look(self):
        self.player.look = self.app.look()

    def flags(self):
        return self.app.profile.setdefault("flags", {})

    def busy(self):
        return any((self.dialog, self.cutscene, self.overlay, self.pause))

    # ---------- entrada ----------
    def handle(self, e):
        for layer in (self.pause, self.cutscene, self.overlay, self.dialog):
            if layer:
                layer.handle(e)
                return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.pause = ui.Pause(self.app, self.close_pause)
            elif e.key in ACT_KEYS:
                self.interact()

    def close_pause(self):
        self.pause = None

    def nearest(self):
        best = None
        for h in self.hotspots:
            if not h.active():
                continue
            d = math.hypot(self.player.x - h.x, self.player.y - h.y)
            if d < h.r and (best is None or d < best[0]):
                best = (d, h)
        return best[1] if best else None

    def interact(self):
        h = self.nearest()
        if h and self.locked <= 0:
            self.app.audio.play("blip")
            h.action()

    # ---------- ciclo ----------
    def update(self, dt):
        self.t += dt
        self.locked = max(0.0, self.locked - dt)
        for name in ("cutscene", "overlay", "dialog"):
            layer = getattr(self, name)
            if layer:
                layer.update(dt)
                if layer.done:
                    setattr(self, name, None)
                    if getattr(layer, "then", None):
                        layer.then()
        self.thoughts.update(dt)
        self.toast.update(dt)
        if not self.busy() and self.locked <= 0:
            self.player.update(dt, pygame.key.get_pressed(), self.bounds, self.blockers)
        else:
            self.player.moving = False
        self.cam_x = max(0.0, min(self.world_w - W, self.player.x - W / 2))
        self.tick(dt)

    def tick(self, dt):
        pass

    def draw_bg(self, surf):
        pass

    def actors(self):
        return []

    def draw_fg(self, surf):
        pass

    def draw_hud(self, surf):
        pass

    def draw(self, surf):
        self.draw_bg(surf)
        acts = self.actors() + [(self.player.y, lambda: self.player.draw(surf, self.cam_x))]
        for _, fn in sorted(acts, key=lambda a: a[0]):
            fn()
        self.draw_fg(surf)
        pixel.pixelate(surf)
        for x, y in self.arrows:
            ui.float_button(surf, x - self.cam_x, y, self.t)
        if not self.busy() and self.locked <= 0:
            h = self.nearest()
            if h:
                hx, hy = self.player.head(self.cam_x)
                art.prompt_bubble(surf, hx, hy - 4, f"E  {h.label}", self.t)
        self.thoughts.draw(surf)
        self.draw_hud(surf)
        self.toast.draw(surf)
        for layer in (self.dialog, self.overlay, self.cutscene, self.pause):
            if layer:
                layer.draw(surf, self.t)
