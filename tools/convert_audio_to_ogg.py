from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO_DIR = ROOT / 'assets' / 'audio'


def main() -> None:
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        print('Brak ffmpeg. Zainstaluj: sudo apt install ffmpeg')
        return

    mp3_files = sorted(AUDIO_DIR.glob('*.mp3'))
    if not mp3_files:
        print('Nie znaleziono MP3 w assets/audio.')
        return

    for src in mp3_files:
        dst = src.with_suffix('.ogg')
        print(f'Konwertuję: {src.name} -> {dst.name}')
        subprocess.run([
            ffmpeg,
            '-y',
            '-i', str(src),
            '-vn',
            '-acodec', 'libvorbis',
            '-q:a', '4',
            str(dst),
        ], check=False)

    print('Gotowe. W config/levels.py używaj nazw bez rozszerzenia, np. music="level1".')


if __name__ == '__main__':
    main()
