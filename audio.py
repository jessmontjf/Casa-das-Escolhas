"""Som do jogo: efeitos e música sintetizados (sem arquivos).
Se existir assets/music/tema.ogg (ou .mp3/.wav), ele toca no lugar da música gerada."""
import math
import os
import random
import threading
from array import array

import pygame

MUSIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "music")


def _midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


class Audio:
    def __init__(self, settings):
        self.settings = settings
        self.sounds, self.music_sound, self.music_ch, self.file_music = {}, None, None, False
        self.ok = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            freq, size, ch = pygame.mixer.get_init()
            if size != -16:
                return
            self.freq, self.ch = freq, ch
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(1)
            self.music_ch = pygame.mixer.Channel(0)
            self.ok = True
        except Exception as e:  # noqa: BLE001
            print("[som] sem áudio:", e)
            return
        self.sounds["bell"] = self._make(self._bell, 2.2, .55)
        self.sounds["chime"] = self._make(self._chime, 1.2, .35)
        self.sounds["blip"] = self._make(self._blip, .22, .25)
        self.sounds["pop"] = self._make(self._pop, .15, .3)
        self.sounds["whoosh"] = self._make(self._whoosh(), 1.4, .35)
        self.sounds["paper"] = self._make(self._paper(), .35, .3)
        self.sounds["fail"] = self._make(self._fail, .35, .25)
        threading.Thread(target=self._start_music, daemon=True).start()

    # ---------- música ----------
    def _start_music(self):
        for ext in ("ogg", "mp3", "wav"):
            path = os.path.join(MUSIC_DIR, f"tema.{ext}")
            if os.path.exists(path):
                try:
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.play(-1)
                    self.file_music = True
                    self.apply()
                    return
                except Exception as e:  # noqa: BLE001
                    print("[som] música:", e)
        self.music_sound = self._lullaby()
        self.apply()
        self.music_ch.play(self.music_sound, loops=-1)

    def _lullaby(self):
        """Loop acolhedor: Fmaj7 – Em7 – Dm7 – Cmaj7, arpejo + baixo + pad."""
        beat = 0.6
        n = int(self.freq * beat * 16)
        buf = [0.0] * n
        sr = self.freq

        def note(start, dur, f, amp, kind):
            i0, i1 = int(start * sr), min(n, int((start + dur) * sr))
            w = math.tau * f / sr
            for i in range(i0, i1):
                tt = (i - i0) / sr
                if kind == "pluck":
                    env = math.exp(-3.2 * tt) * min(1.0, tt * 80)
                    v = math.sin(w * (i - i0)) + .25 * math.sin(2 * w * (i - i0))
                else:
                    env = min(1.0, tt / .6, (dur - tt) / .6)
                    v = math.sin(w * (i - i0)) + .15 * math.sin(3 * w * (i - i0))
                buf[i] += v * env * amp

        chords = [(65, [69, 72, 76, 72], [53, 57, 60, 64]),
                  (64, [67, 71, 74, 71], [52, 55, 59, 62]),
                  (62, [65, 69, 72, 69], [50, 53, 57, 60]),
                  (60, [64, 67, 72, 67], [48, 52, 55, 59])]
        for b, (root, arp, pad) in enumerate(chords):
            t0 = b * 4 * beat
            for k, m in enumerate(arp):
                note(t0 + k * beat, beat * 1.6, _midi(m), .22, "pluck")
            note(t0, 4 * beat, _midi(root - 24), .22, "pad")
            for m in pad:
                note(t0, 4 * beat, _midi(m), .05, "pad")
        a = array("h")
        for v in buf:
            s = int(max(-1.0, min(1.0, v)) * 0.6 * 32767)
            a.append(s)
            if self.ch == 2:
                a.append(s)
        return pygame.mixer.Sound(buffer=a.tobytes())

    def apply(self):
        if not self.ok:
            return
        vol = self.settings.get("music", .6)
        if self.file_music:
            pygame.mixer.music.set_volume(vol)
        elif self.music_ch:
            self.music_ch.set_volume(vol)

    # ---------- efeitos ----------
    def _make(self, fn, dur, vol):
        n = int(self.freq * dur)
        a = array("h")
        for i in range(n):
            v = int(max(-1.0, min(1.0, fn(i / self.freq, dur))) * vol * 32767)
            a.append(v)
            if self.ch == 2:
                a.append(v)
        return pygame.mixer.Sound(buffer=a.tobytes())

    @staticmethod
    def _bell(t, dur):
        def strike(tt, amp):
            if tt < 0:
                return 0.0
            f = 1568.0
            env = math.exp(-2.6 * tt) * min(1.0, tt * 300)
            return amp * env * (math.sin(math.tau * f * tt)
                                + .55 * math.sin(math.tau * f * 2.76 * tt) * math.exp(-4 * tt)
                                + .3 * math.sin(math.tau * f * 5.4 * tt) * math.exp(-7 * tt))
        jingle = .75 + .25 * math.sin(math.tau * 21 * t)
        return (strike(t, 1.0) + strike(t - .3, .7)) * jingle / 2.4

    @staticmethod
    def _chime(t, dur):
        v = 0.0
        for k, f in enumerate((1046.5, 1318.5, 1568.0, 2093.0)):
            tt = t - k * .08
            if tt > 0:
                v += math.sin(math.tau * f * tt) * math.exp(-4 * tt) * min(1.0, tt * 200)
        return v / 2.2

    @staticmethod
    def _blip(t, dur):
        return math.sin(math.tau * (520 + 900 * t) * t) * math.exp(-12 * t)

    @staticmethod
    def _pop(t, dur):
        return math.sin(math.tau * (300 + 1400 * math.exp(-30 * t)) * t) * math.exp(-25 * t)

    @staticmethod
    def _fail(t, dur):
        return math.sin(math.tau * (330 - 200 * t) * t) * math.exp(-6 * t)

    @staticmethod
    def _whoosh():
        state = [0.0]

        def fn(t, dur):
            cut = .02 + .25 * math.sin(math.pi * t / dur)
            state[0] += (random.uniform(-1, 1) - state[0]) * cut
            return state[0] * 2.2 * math.sin(math.pi * t / dur)
        return fn

    @staticmethod
    def _paper():
        state = [0.0]

        def fn(t, dur):
            state[0] += (random.uniform(-1, 1) - state[0]) * .5
            return state[0] * math.sin(math.pi * t / dur) * (.6 + .4 * math.sin(t * 90))
        return fn

    def play(self, name):
        s = self.sounds.get(name)
        if s:
            s.set_volume(self.settings.get("sfx", .8))
            s.play()
