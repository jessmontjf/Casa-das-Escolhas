"""Carregador de sprites. Se existir um PNG em assets/, ele é usado no lugar do
desenho procedural. Sem arquivos, o jogo continua 100% desenhado por código.

Convenção (detalhes no README):
  assets/<nome>.png                  imagem única (cenários, quadros)
  assets/<nome>.png  + manifest.json  folha de animação horizontal
  manifest.json: {"player_walk_down": {"frames": 4, "fps": 8}}
Sem manifest, uma folha é cortada em quadros quadrados (largura = altura).
"""
import json
import os

import pygame

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_cache, _frames, _manifest = {}, {}, None


def _man():
    global _manifest
    if _manifest is None:
        try:
            with open(os.path.join(DIR, "manifest.json"), encoding="utf-8") as f:
                _manifest = json.load(f)
        except Exception:  # noqa: BLE001
            _manifest = {}
    return _manifest


def image(name):
    if name not in _cache:
        path = os.path.join(DIR, name + ".png")
        surf = None
        if os.path.exists(path):
            try:
                surf = pygame.image.load(path).convert_alpha()
            except Exception as e:  # noqa: BLE001
                print(f"[assets] erro em {path}: {e}")
        _cache[name] = surf
    return _cache[name]


def frames(name):
    if name not in _frames:
        img = image(name)
        if img is None:
            _frames[name] = None
        else:
            n = _man().get(name, {}).get("frames") or max(1, img.get_width() // max(1, img.get_height()))
            fw = img.get_width() // n
            _frames[name] = [img.subsurface((i * fw, 0, fw, img.get_height())) for i in range(n)]
    return _frames[name]


def fps(name, default=8):
    return _man().get(name, {}).get("fps", default)


def blit_bg(surf, name, cam_x=0):
    """Desenha um cenário em PNG, se houver. Devolve True se desenhou."""
    img = image(name)
    if img is None:
        return False
    surf.blit(img, (-int(cam_x), 0))
    return True
