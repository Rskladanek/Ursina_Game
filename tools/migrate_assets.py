from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / 'asserts'
AUDIO = ROOT / 'assets' / 'audio'
TEXTURES = ROOT / 'assets' / 'textures'
MODELS = ROOT / 'assets' / 'models'
TEXTS = ROOT / 'assets' / 'texts'

AUDIO_EXT = {'.mp3', '.wav', '.ogg'}


def main():
    for folder in (AUDIO, TEXTURES, MODELS, TEXTS):
        folder.mkdir(parents=True, exist_ok=True)

    copied = 0
    if LEGACY.exists():
        for file in LEGACY.iterdir():
            if file.is_file() and file.suffix.lower() in AUDIO_EXT:
                target = AUDIO / file.name
                if not target.exists():
                    shutil.copy2(file, target)
                    copied += 1

    print(f'Audio skopiowane z asserts -> assets/audio: {copied}')
    print('Foldery assetów gotowe:')
    print(f'  tekstury: {TEXTURES}')
    print(f'  modele:   {MODELS}')
    print(f'  audio:    {AUDIO}')
    print(f'  teksty:   {TEXTS}')


if __name__ == '__main__':
    main()
