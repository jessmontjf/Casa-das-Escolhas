"""A Casa das Escolhas — ponto de entrada.

Fluxo: caixa de correio (menu) → nome → acordar → quarto → corredor → térreo
(café da manhã) → bairro → a casa no campo (as 5 escolhas) → final.
"""
import copy
import json
import os
import threading
import time

import pygame

import art
from art import W, H, hexc
from audio import Audio
from content import BOTTOMS, SHOES, TOPS

HERE = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(HERE, "saves")
SETTINGS_FILE = os.path.join(HERE, "settings.json")
DEFAULT_SETTINGS = {"music": 0.6, "sfx": 0.8, "fullscreen": False, "crt": True}


class App:
    def __init__(self):
        pygame.init()
        pygame.key.stop_text_input()
        self.settings = dict(DEFAULT_SETTINGS)
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                self.settings.update(json.load(f))
        except Exception:  # noqa: BLE001
            pass
        flags = pygame.SCALED | (pygame.FULLSCREEN if self.settings["fullscreen"] else 0)
        self.screen = pygame.display.set_mode((W, H), flags)
        pygame.display.set_caption("A Casa das Escolhas")
        self.screen.fill(art.DUSK)
        art.text(self.screen, "abrindo a caixa de correio...", art.font(24, italic=True), art.CREAM,
                 (W // 2, H // 2), "center")
        pygame.display.flip()
        self.clock = pygame.time.Clock()
        self.audio = Audio(self.settings)
        import pixel
        self.crt = pixel.CRT()
        pixel._palette()
        self._agent, self._agent_err = None, None
        threading.Thread(target=self._start_agent, daemon=True).start()

        self.profile, self.slot = None, None
        self.running = True
        self.fade, self.fade_dir, self.next_scene = 0.0, 0, None
        from scene_menu import MenuScene
        self.scene = MenuScene(self)

    # ---------- IA (Claude + MCP) inicia em segundo plano ----------
    def _start_agent(self):
        try:
            from llm_agent import GameAgent
            self._agent = GameAgent()
        except Exception as e:  # noqa: BLE001
            self._agent_err = e
            print("[IA] não iniciou:", e)

    def agent(self):
        while self._agent is None and self._agent_err is None:
            time.sleep(.05)
        if self._agent_err:
            raise RuntimeError(f"A IA não iniciou: {self._agent_err}")
        return self._agent

    # ---------- aparência do protagonista ----------
    def look(self, outfit=None):
        L = copy.deepcopy(art.DEFAULT_LOOK)
        L["sprite"] = "player"
        p = self.profile or {}
        f = p.get("flags", {})
        o = outfit if outfit is not None else (p.get("outfit") if f.get("dressed") else None)
        if o:
            for key, opts, i in (("top", TOPS, o[0]), ("bottom", BOTTOMS, o[1]), ("shoes", SHOES, o[2])):
                L[key] = {"color": hexc(opts[i]["color"]), "style": opts[i]["style"]}
        elif f.get("showered"):
            L["top"] = {"color": (255, 238, 224), "style": "robe"}
            L["bottom"] = {"color": (255, 238, 224), "style": "pants"}
        return L

    # ---------- cenas ----------
    def set_scene(self, scene):
        self.next_scene, self.fade_dir = scene, 1

    def back_to_menu(self, save=True):
        if save:
            self.save()
        from scene_menu import MenuScene
        self.set_scene(MenuScene(self))

    def finish_game(self):
        self.profile["stage"] = "done"
        self.back_to_menu()

    def quit(self):
        self.running = False

    def scene_for_stage(self):
        from scene_choices import ChoicesScene
        from scene_home import BedroomScene, GroundScene, HallScene, IntroScene
        from scene_name import NameScene
        from scene_street import StreetScene
        table = {"name": NameScene, "intro": IntroScene, "bedroom": BedroomScene, "hall": HallScene,
                 "ground": GroundScene, "street": StreetScene, "choices": ChoicesScene}
        return table.get(self.profile.get("stage"), NameScene)(self)

    # ---------- saves (3 cartas) ----------
    def slot_path(self, i):
        return os.path.join(SAVE_DIR, f"carta{i + 1}.json")

    def read_slot(self, i):
        try:
            with open(self.slot_path(i), encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            return None

    def delete_slot(self, i):
        try:
            os.remove(self.slot_path(i))
        except OSError:
            pass

    def save(self):
        if self.slot is None or not self.profile:
            return
        os.makedirs(SAVE_DIR, exist_ok=True)
        self.profile["saved_at"] = time.strftime("%d/%m %H:%M")
        with open(self.slot_path(self.slot), "w", encoding="utf-8") as f:
            json.dump(self.profile, f, ensure_ascii=False, indent=1)

    def new_game(self, i):
        self.slot = i
        self.profile = {"name": "", "stage": "name", "flags": {}, "outfit": None, "mcp": None}
        self.save()
        self.set_scene(self.scene_for_stage())

    def continue_game(self, i):
        self.slot = i
        self.profile = self.read_slot(i) or {"stage": "name", "flags": {}}
        self.set_scene(self.scene_for_stage())

    # ---------- opções ----------
    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f)
        except OSError:
            pass

    def set_volume(self, key, v):
        self.settings[key] = round(max(0.0, min(1.0, v)), 2)
        self.audio.apply()
        self.save_settings()

    def toggle_crt(self):
        self.settings["crt"] = not self.settings.get("crt")
        self.save_settings()

    def toggle_fullscreen(self):
        self.settings["fullscreen"] = not self.settings["fullscreen"]
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error as e:
            print("[tela]", e)
        self.save_settings()

    # ---------- loop ----------
    def run(self):
        while self.running:
            dt = min(self.clock.tick(60) / 1000, 1 / 20)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    self.toggle_fullscreen()
                elif self.fade_dir == 0:
                    self.scene.handle(e)
            if self.fade_dir:
                self.fade += self.fade_dir * dt * 3.2
                if self.fade_dir > 0 and self.fade >= 1:
                    self.fade, self.fade_dir = 1.0, -1
                    self.scene = self.next_scene
                    self.scene.enter()
                elif self.fade_dir < 0 and self.fade <= 0:
                    self.fade, self.fade_dir = 0.0, 0
            self.scene.update(dt)
            self.scene.draw(self.screen)
            if self.fade > 0:
                ov = pygame.Surface((W, H))
                ov.fill((60, 30, 36))
                ov.set_alpha(int(255 * self.fade))
                self.screen.blit(ov, (0, 0))
            if self.settings.get("crt"):
                self.crt.apply(self.screen)
            pygame.display.flip()
        self.save()
        if self._agent:
            self._agent.close()
        pygame.quit()


if __name__ == "__main__":
    App().run()
