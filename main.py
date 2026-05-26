from __future__ import annotations

import math
import random
import time as pytime
from typing import Optional

from panda3d.core import loadPrcFileData

from game_settings import (
    ENABLE_ADVANCED_SHADER,
    GAME_TITLE,
    MOUSE_LOCK_DELAY,
    SHOW_FPS,
    WINDOW_HEIGHT,
    WINDOW_POS_X,
    WINDOW_POS_Y,
    WINDOW_WIDTH,
)

# ---------------------------------------------------------------------
# Panda3D config MUSI być przed Ursina()
# ---------------------------------------------------------------------

WIN_W = int(WINDOW_WIDTH)
WIN_H = int(WINDOW_HEIGHT)
WIN_X = int(WINDOW_POS_X)
WIN_Y = int(WINDOW_POS_Y)

loadPrcFileData('', f'win-size {WIN_W} {WIN_H}')
loadPrcFileData('', f'window-title {GAME_TITLE}')
loadPrcFileData('', 'sync-video false')
loadPrcFileData('', 'show-frame-rate-meter false')
loadPrcFileData('', 'textures-power-2 none')
loadPrcFileData('', 'notify-level warning')

from ursina import *  # noqa: E402

from config.levels import LEVELS  # noqa: E402
from core.assets import audio_path  # noqa: E402
from data.ui_text import TEXT  # noqa: E402
from enemy.enemy import Enemy, distance_xz  # noqa: E402
from environment.environment import setup_environment  # noqa: E402
from menu.in_game_menu import InGameMenu  # noqa: E402
from menu.menu import MenuMenu  # noqa: E402
from player.player import Player  # noqa: E402


# ---------------------------------------------------------------------
# Pomocnicze funkcje
# ---------------------------------------------------------------------

def safe_destroy(entity):
    if entity is None:
        return

    try:
        destroy(entity)
    except Exception as exc:
        print(f'[cleanup] Nie udało się usunąć {entity}: {exc}')


def safe_enabled(entity, value: bool):
    if entity is None:
        return

    try:
        entity.enabled = value
    except Exception:
        pass


def safe_mouse_lock(enabled: bool):
    """
    Na Linux/X11 Ursina czasem pluje:
    Failed to grab pointer!
    Nie zabija gry, ale łapiemy to łagodniej.
    """
    try:
        mouse.visible = not enabled
    except Exception:
        pass

    def apply():
        try:
            mouse.locked = enabled
        except Exception as exc:
            print(f'[mouse] Nie udało się ustawić mouse.locked={enabled}: {exc}')

    try:
        invoke(apply, delay=float(MOUSE_LOCK_DELAY), unscaled=True)
    except TypeError:
        invoke(apply, delay=float(MOUSE_LOCK_DELAY))
    except Exception:
        apply()


def clamp_level_index(index: int) -> int:
    return max(0, min(int(index), len(LEVELS) - 1))


def get_text(key: str, fallback: str) -> str:
    return TEXT.get(key, fallback)


# ---------------------------------------------------------------------
# Ekran wyniku / przegranej
# ---------------------------------------------------------------------

class ResultScreen(Entity):
    """
    Prosty ekran końca poziomu bez Buttonów.
    Buttony u Ciebie robiły białe plamy, więc result screen też jest tekstowy.
    Sterowanie:
    Enter - następny poziom
    R - restart
    Esc/P - menu
    """

    def __init__(self, restart_callback, next_callback, menu_callback, **kwargs):
        super().__init__(
            parent=camera.ui,
            ignore_paused=True,
            enabled=False,
        )

        self.restart_callback = restart_callback
        self.next_callback = next_callback
        self.menu_callback = menu_callback
        self.allow_next = True

        self.background = Entity(
            parent=self,
            model='quad',
            color=color.rgba(0, 0, 0, 235),
            scale=(3.5, 2.2),
            collider=None,
            ignore_paused=True,
        )

        self.title = Text(
            '',
            parent=self,
            origin=(0, 0),
            position=(0, 0.28),
            scale=2.0,
            color=color.yellow,
            ignore_paused=True,
        )

        self.subtitle = Text(
            '',
            parent=self,
            origin=(0, 0),
            position=(0, 0.16),
            scale=0.85,
            color=color.light_gray,
            ignore_paused=True,
        )

        self.stats = Text(
            '',
            parent=self,
            origin=(0, 0),
            position=(0, 0.05),
            scale=0.72,
            color=color.azure,
            ignore_paused=True,
        )

        self.controls = Text(
            '',
            parent=self,
            origin=(0, 0),
            position=(0, -0.13),
            scale=0.62,
            color=color.white,
            ignore_paused=True,
        )

        self.tip = Text(
            'Nie ma tu białych paneli. Same teksty, żeby UI się nie srało.',
            parent=self,
            origin=(0, 0),
            position=(0, -0.27),
            scale=0.48,
            color=color.gray,
            ignore_paused=True,
        )

        for key, value in kwargs.items():
            setattr(self, key, value)

    def show(self, title: str, subtitle: str, stats: str = '', allow_next: bool = True):
        self.title.text = title
        self.subtitle.text = subtitle
        self.stats.text = stats
        self.allow_next = allow_next

        if allow_next:
            self.controls.text = 'Enter - następny poziom    |    R - restart    |    Esc/P - menu'
        else:
            self.controls.text = 'R - restart    |    Esc/P - menu'

        self.enabled = True

        mouse.locked = False
        mouse.visible = True
        application.paused = True

    def hide(self, unpause: bool = True):
        self.enabled = False

        if unpause:
            application.paused = False
            safe_mouse_lock(True)

    def handle_key(self, key: str) -> bool:
        if not self.enabled:
            return False

        if key in ('escape', 'p'):
            self.hide(unpause=False)
            self.menu_callback()
            return True

        if key == 'r':
            self.hide(unpause=False)
            self.restart_callback()
            return True

        if key == 'enter' and self.allow_next:
            self.hide(unpause=False)
            self.next_callback()
            return True

        return True


# ---------------------------------------------------------------------
# Game Manager
# ---------------------------------------------------------------------

class GameManager(Entity):
    """
    Centralny manager gry.
    Tutaj jest tylko flow:
    menu -> poziom -> pauza -> wynik/przegrana -> kolejny poziom/menu.
    """

    def __init__(self):
        super().__init__(ignore_paused=True)

        self.current_level_index = 0
        self.state = 'menu'

        self.environment: Optional[Entity] = None
        self.shootables_parent: Optional[Entity] = None
        self.player: Optional[Entity] = None
        self.editor_camera: Optional[Entity] = None
        self.music: Optional[Audio] = None
        self.sky: Optional[Entity] = None

        self.level_started_at = 0.0
        self.kills_at_level_start = 0
        self.end_screen_shown = False
        self.loading_level = False

        self.main_menu = MenuMenu(
            start_game_callback=self.start_level,
            level_count=len(LEVELS),
            get_level_name=lambda index: LEVELS[index].name,
            get_level_subtitle=lambda index: LEVELS[index].subtitle,
        )

        self.pause_menu = InGameMenu(
            resume_callback=self.resume_game,
            restart_callback=self.restart_level,
            main_menu_callback=self.return_to_menu,
        )

        self.result_screen = ResultScreen(
            restart_callback=self.restart_level,
            next_callback=self.next_level,
            menu_callback=self.return_to_menu,
        )

        self._setup_initial_state()

    def _setup_initial_state(self):
        self.state = 'menu'
        application.paused = False
        mouse.locked = False
        mouse.visible = True

        if self.main_menu:
            self.main_menu.enabled = True

        if self.pause_menu:
            self.pause_menu.force_hide()

        if self.result_screen:
            self.result_screen.enabled = False

    # -----------------------------------------------------------------
    # Mysz / UI gry
    # -----------------------------------------------------------------

    def capture_mouse(self, enabled: bool):
        safe_mouse_lock(enabled)

    def _set_gameplay_ui_visible(self, visible: bool):
        """
        Pauza ma schować HUD i crosshair.
        Inaczej teksty gry mieszają się z menu.
        """
        if not self.player:
            return

        hud = getattr(self.player, 'hud', None)
        safe_enabled(hud, visible)

        weapon = getattr(self.player, 'weapon', None)

        if weapon:
            crosshair = getattr(weapon, 'crosshair', None)
            safe_enabled(crosshair, visible)

    def _set_player_visible(self, visible: bool):
        """
        Nie wyłączamy całego playera na pauzie, bo application.paused już stopuje update.
        Chowamy tylko broń/celownik/HUD, żeby menu wyglądało czysto.
        """
        if not self.player:
            return

        weapon = getattr(self.player, 'weapon', None)

        if weapon:
            safe_enabled(weapon, visible)

    # -----------------------------------------------------------------
    # Poziomy
    # -----------------------------------------------------------------

    def start_level(self, level_index: int = 0):
        if self.loading_level:
            return

        self.loading_level = True

        try:
            self.cleanup_level()

            self.current_level_index = clamp_level_index(level_index)
            level = LEVELS[self.current_level_index]

            random.seed(1000 + self.current_level_index)
            Enemy.all_enemies.clear()

            self.state = 'loading'
            self.end_screen_shown = False
            application.paused = False

            if self.main_menu:
                self.main_menu.enabled = False

            if self.pause_menu:
                self.pause_menu.force_hide()

            if self.result_screen:
                self.result_screen.enabled = False

            self.environment = setup_environment(level)
            self.shootables_parent = Entity(name='Shootables')

            enemy_positions = self.generate_enemy_positions(level)

            self.player = Player(
                shootables_parent=self.shootables_parent,
                initial_enemy_positions=enemy_positions,
                spawn_position=level.spawn,
                game_manager=self,
            )

            self.player.score = getattr(self.player, 'score', 0)

            if hasattr(self.player, 'hud') and self.player.hud:
                self.player.hud.set_level(level.name, level.goal_text)
                self.player.hud.set_manager(self)
                self.player.hud.enabled = True

            for pos in enemy_positions:
                Enemy(
                    shootables_parent=self.shootables_parent,
                    player=self.player,
                    initial_position=pos,
                    max_hp=level.enemy_hp,
                    speed=level.enemy_speed,
                    detect_radius=level.detect_radius,
                    kill_score=100 + self.current_level_index * 50,
                    group='level_wave',
                )

            # EditorCamera zostaje disabled, żeby nie mieszała sterowania.
            self.editor_camera = EditorCamera(
                enabled=False,
                ignore_paused=True,
            )

            self.play_music(level.music)

            self.level_started_at = pytime.time()
            self.kills_at_level_start = getattr(self.player, 'kills', 0)

            self.state = 'playing'
            self.end_screen_shown = False

            self._set_gameplay_ui_visible(True)
            self._set_player_visible(True)
            self.capture_mouse(True)

        finally:
            self.loading_level = False

    def generate_enemy_positions(self, level):
        positions = []
        margin = 8
        attempts = 0

        while len(positions) < level.enemy_count and attempts < 700:
            attempts += 1

            x = random.uniform(-level.bounds + margin, level.bounds - margin)
            z = random.uniform(-level.bounds + margin, level.bounds - margin)

            candidate = Vec3(x, 0, z)

            if distance_xz(candidate, level.spawn) < 18:
                continue

            if any(distance_xz(candidate, other) < 7 for other in positions):
                continue

            positions.append(candidate)

        # Fallback, gdy random nie znajdzie pozycji.
        while len(positions) < level.enemy_count:
            angle = len(positions) / max(level.enemy_count, 1) * 360
            radius = level.bounds * 0.55

            positions.append(
                Vec3(
                    math.cos(math.radians(angle)) * radius,
                    0,
                    math.sin(math.radians(angle)) * radius,
                )
            )

        return positions

    def restart_level(self):
        self.start_level(self.current_level_index)

    def next_level(self):
        if self.current_level_index + 1 < len(LEVELS):
            self.start_level(self.current_level_index + 1)
        else:
            self.return_to_menu()

    # -----------------------------------------------------------------
    # Audio
    # -----------------------------------------------------------------

    def play_music(self, music_file: str):
        if self.music:
            safe_destroy(self.music)
            self.music = None

        if not music_file:
            return

        path = audio_path(music_file)

        if not path:
            print(f'[audio] Brak muzyki dla poziomu: {music_file}')
            return

        try:
            self.music = Audio(
                path,
                autoplay=True,
                loop=True,
                volume=0.32,
            )
        except Exception as exc:
            print(f'[audio] Nie udało się odtworzyć muzyki {music_file}: {exc}')
            self.music = None

    # -----------------------------------------------------------------
    # Czyszczenie
    # -----------------------------------------------------------------

    def cleanup_level(self):
        application.paused = False

        if self.pause_menu:
            self.pause_menu.force_hide()

        if self.result_screen:
            self.result_screen.enabled = False

        if self.music:
            safe_destroy(self.music)
            self.music = None

        if self.player:
            try:
                if hasattr(self.player, 'cleanup'):
                    self.player.cleanup()
            except Exception as exc:
                print(f'[cleanup] Player cleanup problem: {exc}')

            safe_destroy(self.player)
            self.player = None

        if self.editor_camera:
            safe_destroy(self.editor_camera)
            self.editor_camera = None

        if self.shootables_parent:
            safe_destroy(self.shootables_parent)
            self.shootables_parent = None

        if self.environment:
            safe_destroy(self.environment)
            self.environment = None

        Enemy.all_enemies.clear()

    def return_to_menu(self):
        self.cleanup_level()

        self.state = 'menu'
        self.end_screen_shown = False
        application.paused = False

        mouse.locked = False
        mouse.visible = True

        if self.pause_menu:
            self.pause_menu.force_hide()

        if self.result_screen:
            self.result_screen.enabled = False

        if self.main_menu:
            self.main_menu.enabled = True

            if hasattr(self.main_menu, 'show_main'):
                self.main_menu.show_main()

    # -----------------------------------------------------------------
    # Pauza
    # -----------------------------------------------------------------

    def pause_game(self):
        if self.state != 'playing':
            return

        if self.result_screen.enabled:
            return

        self._set_gameplay_ui_visible(False)
        self._set_player_visible(False)

        mouse.locked = False
        mouse.visible = True

        if self.pause_menu:
            self.pause_menu.show()

        application.paused = True

    def resume_game(self):
        if self.state != 'playing':
            return

        if self.pause_menu:
            self.pause_menu.force_hide()

        application.paused = False

        self._set_gameplay_ui_visible(True)
        self._set_player_visible(True)

        self.capture_mouse(True)

    def toggle_pause(self):
        if self.state != 'playing':
            return

        if self.result_screen.enabled:
            return

        if self.pause_menu.enabled or application.paused:
            self.resume_game()
        else:
            self.pause_game()

    # -----------------------------------------------------------------
    # Statystyki
    # -----------------------------------------------------------------

    def remaining_enemies(self) -> int:
        return sum(1 for enemy in Enemy.all_enemies if getattr(enemy, 'alive', False))

    def elapsed_time(self) -> int:
        if not self.level_started_at:
            return 0

        return int(pytime.time() - self.level_started_at)

    def level_stats_text(self) -> str:
        if not self.player:
            return ''

        killed_this_level = getattr(self.player, 'kills', 0) - self.kills_at_level_start
        score = getattr(self.player, 'score', 0)

        return f'Czas: {self.elapsed_time()} s   Zabici: {killed_this_level}   Punkty: {score}'

    # -----------------------------------------------------------------
    # Update gry
    # -----------------------------------------------------------------

    def update(self):
        if self.state != 'playing':
            return

        if not self.player:
            return

        if self.end_screen_shown:
            return

        if self.pause_menu.enabled:
            return

        player_dead = getattr(self.player, 'is_dead', False) or getattr(self.player, 'hp', 1) <= 0

        if player_dead:
            self.end_screen_shown = True
            self.state = 'game_over'

            self._set_gameplay_ui_visible(False)
            self._set_player_visible(False)

            self.result_screen.show(
                title='GAME OVER',
                subtitle='Zginąłeś. Trzeba jeszcze raz.',
                stats=self.level_stats_text(),
                allow_next=False,
            )

            return

        if self.remaining_enemies() <= 0:
            self.end_screen_shown = True
            self.state = 'level_complete'

            self._set_gameplay_ui_visible(False)
            self._set_player_visible(False)

            last_level = self.current_level_index == len(LEVELS) - 1

            self.result_screen.show(
                title='POZIOM WYCZYSZCZONY' if not last_level else 'KONIEC GRY',
                subtitle='Lecimy dalej.' if not last_level else 'Wyczyściłeś wszystkie fale.',
                stats=self.level_stats_text(),
                allow_next=not last_level,
            )

            return

    # -----------------------------------------------------------------
    # Input
    # -----------------------------------------------------------------

    def handle_key(self, key):
        # Result screen ma najwyższy priorytet.
        if self.result_screen and self.result_screen.enabled:
            if self.result_screen.handle_key(key):
                return

        # Pauza przejmuje input, jeśli jest aktywna.
        if self.pause_menu and self.pause_menu.enabled:
            if hasattr(self.pause_menu, 'handle_key'):
                if self.pause_menu.handle_key(key):
                    return

            if key in ('escape', 'p'):
                self.resume_game()
                return

            if key == 'r':
                self.restart_level()
                return

        # Globalne sterowanie.
        if key in ('escape', 'p'):
            if self.state == 'playing':
                self.toggle_pause()
            elif self.state in ('game_over', 'level_complete'):
                self.return_to_menu()
            elif self.state == 'menu':
                if hasattr(self.main_menu, 'go_back_or_quit'):
                    self.main_menu.go_back_or_quit()
                else:
                    application.quit()
            return

        # R w trakcie gry zostawiamy graczowi jako reload.
        # Restart działa tylko w pauzie/result screenie.
        if key == 'r':
            if self.state in ('game_over', 'level_complete'):
                self.restart_level()
            return

        if key == 'enter':
            if self.result_screen.enabled and self.result_screen.allow_next:
                self.next_level()
            return

        if key == 'f1':
            controls = get_text(
                'controls_line',
                'WASD ruch | Mysz celowanie | LPM strzał | Shift sprint | R przeładuj | Esc/P pauza',
            )
            print_on_screen(
                controls,
                position=(0, -0.35),
                origin=(0, 0),
                duration=4,
                scale=0.8,
            )
            return


# ---------------------------------------------------------------------
# App bootstrap
# ---------------------------------------------------------------------

app = Ursina()

window.title = GAME_TITLE
window.borderless = False
window.fps_counter.enabled = SHOW_FPS
window.exit_button.visible = False

# Inty, nie floaty.
window.size = (WIN_W, WIN_H)
window.position = (WIN_X, WIN_Y)

if ENABLE_ADVANCED_SHADER:
    try:
        from ursina.shaders import lit_with_shadows_shader
        Entity.default_shader = lit_with_shadows_shader
    except Exception as exc:
        print(f'[shader] Nie udało się włączyć shadera: {exc}')

sky = Sky()

manager = GameManager()


def input(key):
    manager.handle_key(key)


app.run()