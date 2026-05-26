from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

GAME_TITLE = 'Ursina Shooter - modular edition'
WINDOW_WIDTH = 1536
WINDOW_HEIGHT = 864
WINDOW_POS_X = 192
WINDOW_POS_Y = 108
SHOW_FPS = True

ASSETS_DIR = PROJECT_ROOT / 'assets'
TEXTURES_DIR = ASSETS_DIR / 'textures'
MODELS_DIR = ASSETS_DIR / 'models'
AUDIO_DIR = ASSETS_DIR / 'audio'
TEXTS_DIR = ASSETS_DIR / 'texts'

# Stary folder z pierwotnego projektu. Zostaje jako fallback.
LEGACY_ASSERTS_DIR = PROJECT_ROOT / 'asserts'

MOUSE_LOCK_DELAY = 0.12
DEFAULT_VOLUME = 0.35

# Na razie OFF. lit_with_shadows_shader potrafił przepalać/wybielać tekstury.
ENABLE_ADVANCED_SHADER = False
