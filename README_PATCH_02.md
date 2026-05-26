# Patch 02 — modularny porządek + assety + Esc

To nie jest cała gra od zera. To jest paczka modułów do nadpisania w Twoim obecnym projekcie.

## Co poprawia

- naprawia `Esc` przez centralny router inputu w `main.py`,
- usuwa chaos z assetami: tekstury/modele/audio mają swoje foldery,
- dodaje prawdziwe pliki tekstur PNG, więc level nie jedzie tylko na magicznych builtinach Ursiny,
- poprawia warning `win-size: 864.0 / 1536.0`, bo rozmiar okna idzie przez Panda3D jako int przed `Ursina()`,
- zostawia fallback na stary folder `asserts`, więc muzyka nie powinna się wywalić,
- dodaje `settings.py`, `config/levels.py`, `core/assets.py`, `data/ui_text.py`.

## Jak wgrać

Zrób backup, potem z katalogu projektu:

```bash
cp -r /ścieżka/do/Ursina_Game_patch_02/* .
python tools/migrate_assets.py
python main.py
```

Jeśli rozpakujesz patch w `~/Pobrane/Ursina_Game_patch_02`, to np.:

```bash
cd ~/Dokumenty/gra/Ursina_Game
cp -r ~/Pobrane/Ursina_Game_patch_02/* .
python tools/migrate_assets.py
python main.py
```

## Docelowy układ projektu

```text
Ursina_Game/
├── main.py                  # bootstrap gry + centralny input
├── settings.py              # rozdzielczość, ścieżki, globalne ustawienia
├── config/
│   └── levels.py            # poziomy, liczba przeciwników, muzyka, spawn
├── core/
│   └── assets.py            # loader tekstur/modeli/audio
├── data/
│   └── ui_text.py           # teksty menu/HUD/komunikatów
├── assets/
│   ├── textures/            # PNG/JPG/WEBP
│   ├── models/              # OBJ/GLB/GLTF/BAM/EGG
│   ├── audio/               # MP3/WAV/OGG
│   └── texts/               # JSON/TXT pod tłumaczenia/dialogi
├── environment/
│   └── environment.py       # budowanie mapy
├── player/
│   ├── player.py
│   └── weapon.py
├── enemy/
│   └── enemy.py
├── menu/
│   ├── menu.py
│   └── in_game_menu.py
└── ui/
    └── hud.py
```

## Gdzie co edytować

- Teksty menu: `data/ui_text.py`
- Poziomy: `config/levels.py`
- Tekstury: `assets/textures/`
- Modele: `assets/models/`
- Muzyka i dźwięki: `assets/audio/`
- Generowanie mapy: `environment/environment.py`
- Sterowanie pauzą/Esc/restartem: `main.py`, metoda `handle_key()`

## Ważne

Stary folder `asserts` był literówką/nieszczęściem. Patch nie usuwa go, bo masz tam mp3/wav. Skrypt `tools/migrate_assets.py` kopiuje audio do `assets/audio`.
