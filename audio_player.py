"""
Audio-Wrapper um pygame.mixer.

Bietet eine einfache API für Musik (Background-Loop) und kurze Sound-Effekte.
Initialisiert pygame erst beim ersten Zugriff ("lazy init"), damit ein fehlendes
oder kaputtes Audio-Device die App nicht zum Absturz bringt — ohne Ton läuft
das Spiel weiter, die Calls werden zu No-Ops.

Verwendung:
    import audio_player as audio
    audio.play_music("Jeopardy intro with host introduction.mp3")
    audio.stop_music()
    audio.play_sound("effect.mp3")

Pfade werden über `resources.resource_path("audio/...")` aufgelöst, damit
sowohl der Dev-Modus als auch der PyInstaller-Bundle (sys._MEIPASS) funktionieren.
"""

import os

# Muss gesetzt sein, BEVOR pygame importiert wird — unterdrückt die
# "Hello from pygame community" Banner-Ausgabe auf stdout.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import resources as r

_pygame = None          # lazy-loaded pygame-Modul
_mixer_ready = False    # True sobald pygame.mixer.init() erfolgreich war
_init_failed = False    # True wenn Init einmal fehlschlug → keine weiteren Versuche


def _ensure_init():
    """Initialisiert pygame.mixer beim ersten Aufruf. Idempotent."""
    global _pygame, _mixer_ready, _init_failed
    if _mixer_ready:
        return True
    if _init_failed:
        return False
    try:
        import pygame
        _pygame = pygame
        pygame.mixer.init()
        _mixer_ready = True
        return True
    except Exception as e:
        print(f"[audio] mixer init failed: {e}")
        _init_failed = True
        return False


def _audio_file(filename):
    """Gibt den vollen Pfad zu einer Audio-Datei im audio/-Verzeichnis zurück."""
    return r.resource_path(os.path.join("audio", filename))


def play_music(filename, loop=False):
    """Startet Hintergrundmusik (ersetzt eventuell laufende Musik).

    Returns True bei Erfolg, False wenn Datei fehlt oder Audio nicht verfügbar.
    """
    if not _ensure_init():
        return False
    path = _audio_file(filename)
    if not os.path.exists(path):
        print(f"[audio] file not found: {path}")
        return False
    try:
        _pygame.mixer.music.load(path)
        _pygame.mixer.music.play(-1 if loop else 0)
        return True
    except Exception as e:
        print(f"[audio] play failed: {e}")
        return False


def stop_music():
    """Stoppt die aktuell laufende Musik. No-Op wenn Mixer nicht bereit."""
    if not _mixer_ready or _pygame is None:
        return
    try:
        _pygame.mixer.music.stop()
    except Exception:
        pass


def is_playing():
    """True wenn gerade Musik läuft."""
    if not _mixer_ready or _pygame is None:
        return False
    try:
        return bool(_pygame.mixer.music.get_busy())
    except Exception:
        return False


def play_sound(filename):
    """Spielt einen kurzen Sound-Effekt parallel zur Musik (eigener Channel)."""
    if not _ensure_init():
        return False
    path = _audio_file(filename)
    if not os.path.exists(path):
        print(f"[audio] file not found: {path}")
        return False
    try:
        sound = _pygame.mixer.Sound(path)
        sound.play()
        return True
    except Exception as e:
        print(f"[audio] sound failed: {e}")
        return False
