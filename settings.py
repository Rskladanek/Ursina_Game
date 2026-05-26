from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

GAME_TITLE = 'Ursina Shooter - modular edition'
WINDOW_WIDTH = 1536
WINDOW_HEIGHT = 864
SHOW_FPS = True

# Docelowy, normalny katalog assetów.
ASSETS_DIR = PROJECT_ROOT / 'assets'
TEXTURES_DIR = ASSETS_DIR / 'textures'
MODELS_DIR = ASSETS_DIR / 'models'
AUDIO_DIR = ASSETS_DIR / 'audio'
TEXTS_DIR = ASSETS_DIR / 'texts'

# Stary katalog z projektu. Zostaje jako fallback, żeby nie rozwalić muzyki po patchu.
LEGACY_ASSERTS_DIR = PROJECT_ROOT / 'asserts'

MOUSE_LOCK_DELAY = 0.08
DEFAULT_VOLUME = 0.35
