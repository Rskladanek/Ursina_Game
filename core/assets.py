from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from ursina import load_texture

from settings import (
    AUDIO_DIR,
    LEGACY_ASSERTS_DIR,
    MODELS_DIR,
    TEXTURES_DIR,
)

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')
MODEL_EXTENSIONS = ('.obj', '.glb', '.gltf', '.bam', '.egg')
AUDIO_EXTENSIONS = ('.wav', '.mp3', '.ogg')

_TEXTURE_CACHE: dict[str, object] = {}


def _with_extensions(name: str, extensions: Iterable[str]) -> list[str]:
    path = Path(name)
    if path.suffix:
        return [name]
    return [f'{name}{ext}' for ext in extensions]


def first_existing(paths: Iterable[Path]) -> Optional[Path]:
    for path in paths:
        if path.exists():
            return path
    return None


def texture(name: str, fallback_builtin: str | None = None):
    """
    Ładuje teksturę z assets/textures, a dopiero potem próbuje builtin Ursiny.
    Dzięki temu tekstury nie znikają po zmianie katalogu roboczego / poziomu.
    """
    cache_key = f'{name}|{fallback_builtin}'
    if cache_key in _TEXTURE_CACHE:
        return _TEXTURE_CACHE[cache_key]

    candidates = []
    for filename in _with_extensions(name, IMAGE_EXTENSIONS):
        candidates.append(TEXTURES_DIR / filename)

    found = first_existing(candidates)

    tex = None
    if found:
        tex = load_texture(str(found))

    if tex is None:
        # Fallback na tekstury wbudowane w Ursinę, np. brick/grass/white_cube.
        tex = load_texture(fallback_builtin or name)

    _TEXTURE_CACHE[cache_key] = tex
    return tex


def model_path(name: str) -> str:
    """
    Zwraca ścieżkę do modelu z assets/models albo nazwę modelu wbudowanego.
    Użycie: Entity(model=model_path('tree.obj')) albo model_path('cube').
    """
    for filename in _with_extensions(name, MODEL_EXTENSIONS):
        candidate = MODELS_DIR / filename
        if candidate.exists():
            return str(candidate)
    return name


def audio_path(name: str) -> str:
    """
    Najpierw assets/audio, potem stary katalog asserts.
    Dzięki temu nie musisz od razu ręcznie przenosić mp3/wav.
    """
    candidates = []
    for filename in _with_extensions(name, AUDIO_EXTENSIONS):
        candidates.append(AUDIO_DIR / filename)
        candidates.append(LEGACY_ASSERTS_DIR / filename)

    found = first_existing(candidates)
    return str(found) if found else name
