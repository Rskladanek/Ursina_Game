# Patch 03 — porządek assetów, tekstur, audio i pauzy

## Co poprawia

- `settings.py` zmienione na `game_settings.py`, bo Ursina próbuje czytać `settings.py` jako swój config i wywalała warning:
  `from __future__ imports must occur at the beginning of the file`.
- Loader tekstur działa po ścieżkach relatywnych `assets/textures/...`, nie po absolutnych `/home/...`, które potrafią się wysypać.
- Audio nie próbuje już ładować MP3, bo Twoja Ursina pokazuje, że obsługuje `.ogg` i `.wav`.
- `Esc` i dodatkowo `P` obsługują pauzę przez GameManager oraz Player.
- Budynki nie wiszą już w powietrzu.
- Wyłączony globalny `lit_with_shadows_shader`, bo przepalał/wybielał tekstury.

## Jak wgrać

Z katalogu projektu:

```bash
cp -r ~/Pobrane/Ursina_Game_patch_03/* .
rm -f settings.py
rm -rf __pycache__ */__pycache__
```

Potem audio:

```bash
python tools/convert_audio_to_ogg.py
```

I start:

```bash
python main.py
```

## Gdzie co teraz trzymać

```text
assets/textures/     # PNG/JPG/WEBP tekstury
assets/models/       # OBJ/GLB/GLTF modele
assets/audio/        # OGG/WAV audio
assets/texts/        # JSON/TXT teksty
config/levels.py     # poziomy
core/assets.py       # loader assetów
data/ui_text.py      # napisy UI
main.py              # flow gry, menu, pauza, restart
```
