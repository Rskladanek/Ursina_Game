from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from ursina import load_texture

from game_settings import (
    AUDIO_DIR,
    LEGACY_ASSERTS_DIR,
    MODELS_DIR,
    PROJECT_ROOT,
    TEXTURES_DIR,
)

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp')
MODEL_EXTENSIONS = ('.obj', '.glb', '.gltf', '.bam', '.egg')

# Ursina na Twoim Linuxie pokazała jasno: obsługuje .ogg i .wav, a nie .mp3.
AUDIO_EXTENSIONS = ('.ogg', '.wav')

_TEXTURE_CACHE: dict[str, object] = {}
_WARNED_MISSING: set[str] = set()
_WARNED_MP3: set[str] = set()


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


def _asset_name(path: Path, *, keep_extension: bool = False) -> str:
    """
    Ursina najstabilniej ładuje assety jako ścieżki relatywne względem asset_folder,
    np. 'assets/textures/grass', a nie absolutne '/home/.../grass.png'.
    """
    try:
        rel = path.resolve().relative_to(PROJECT_ROOT.resolve())
        if not keep_extension:
            rel = rel.with_suffix('')
        return rel.as_posix()
    except ValueError:
        return str(path)


def texture(name: str, fallback_builtin: str | None = 'white_cube'):
    """
    Ładowanie tekstur odporne na katalog roboczy, restart poziomu i Linuxowe ścieżki.
    Najpierw assets/textures, potem fallback do wbudowanych tekstur Ursiny.
    """
    cache_key = f'{name}|{fallback_builtin}'
    if cache_key in _TEXTURE_CACHE:
        return _TEXTURE_CACHE[cache_key]

    candidates: list[Path] = []
    for filename in _with_extensions(name, IMAGE_EXTENSIONS):
        p = Path(filename)
        candidates.append(p if p.is_absolute() else TEXTURES_DIR / filename)

    found = first_existing(candidates)

    if found:
        # Kolejność ma znaczenie. Relatywna bez rozszerzenia zwykle działa najlepiej.
        attempts = [
            _asset_name(found, keep_extension=False),
            _asset_name(found, keep_extension=True),
            str(found),
        ]
        for item in attempts:
            tex = load_texture(item)
            if tex:
                _TEXTURE_CACHE[cache_key] = tex
                return tex

    tex = load_texture(fallback_builtin or name)
    _TEXTURE_CACHE[cache_key] = tex
    return tex


def model_path(name: str) -> str:
    for filename in _with_extensions(name, MODEL_EXTENSIONS):
        p = Path(filename)
        candidate = p if p.is_absolute() else MODELS_DIR / filename
        if candidate.exists():
            return _asset_name(candidate, keep_extension=True)
    return name


def audio_path(name: str) -> str | None:
    """
    Zwraca nazwę assetu audio dla Ursiny albo None.

    WAŻNE:
    - w tej konfiguracji Ursina ładuje .ogg/.wav,
    - .mp3 siedzi w folderze, ale Audio() go nie bierze, więc nie pchamy go na siłę,
      bo tylko spamuje logami.
    """
    raw = Path(name)
    base = raw.with_suffix('').as_posix()

    candidates: list[Path] = []
    for filename in _with_extensions(base, AUDIO_EXTENSIONS):
        candidates.append(AUDIO_DIR / filename)
        candidates.append(LEGACY_ASSERTS_DIR / filename)

    found = first_existing(candidates)
    if found:
        return _asset_name(found, keep_extension=False)

    # Czy istnieje mp3? Jeśli tak, daj konkretną informację zamiast debilnego warninga Ursiny.
    mp3_candidates = [AUDIO_DIR / f'{base}.mp3', LEGACY_ASSERTS_DIR / f'{base}.mp3']
    mp3_found = first_existing(mp3_candidates)
    if mp3_found and base not in _WARNED_MP3:
        print(f'[audio] {base}: znaleziono MP3, ale Ursina w tym setupie go nie ładuje. Przekonwertuj na .ogg albo .wav.')
        _WARNED_MP3.add(base)
        return None

    if base not in _WARNED_MISSING:
        print(f'[audio] Brak audio: {base}. Szukano .ogg/.wav w assets/audio i asserts.')
        _WARNED_MISSING.add(base)

    return None
