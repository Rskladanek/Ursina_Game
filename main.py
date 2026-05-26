from __future__ import annotations

import math
import random

from panda3d.core import loadPrcFileData

from settings import GAME_TITLE, MOUSE_LOCK_DELAY, SHOW_FPS, WINDOW_HEIGHT, WINDOW_WIDTH

# Musi być przed stworzeniem Ursina(), inaczej Panda3D potrafi pluć warningami 1536.0 / 864.0.
loadPrcFileData('', f'win-size {int(WINDOW_WIDTH)} {int(WINDOW_HEIGHT)}')
loadPrcFileData('', f'window-title {GAME_TITLE}')

from ursina import *  # noqa: E402
from ursina.shaders import lit_with_shadows_shader  # noqa: E402

from config.levels import LEVELS  # noqa: E402
from core.assets import audio_path  # noqa: E402
from data.ui_text import TEXT  # noqa: E402
from enemy.enemy import Enemy, distance_xz  # noqa: E402
from environment.environment import setup_environment  # noqa: E402
from menu.in_game_menu import InGameMenu  # noqa: E402
from menu.menu import MenuMenu  # noqa: E402
from player.player import Player  # noqa: E402


class ResultScreen(Entity):
    def __init__(self, restart_callback, next_callback, menu_callback, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True, enabled=False)
        self.restart_callback = restart_callback
        self.next_callback = next_callback
        self.menu_callback = menu_callback
        self.allow_next = True

        self.background = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 210), scale=(window.aspect_ratio * 2.2, 2.2), z=0.2)
        self.title = Text('', parent=self, y=0.28, origin=(0, 0), scale=2.1, color=color.white)
        self.subtitle = Text('', parent=self, y=0.14, origin=(0, 0), scale=1.0, color=color.light_gray)
        self.stats = Text('', parent=self, y=0.02, origin=(0, 0), scale=0.9, color=color.azure)

        self.next_button = Button(text='Następny poziom', parent=self, y=-0.15, scale=(0.45, 0.075), color=color.lime, highlight_color=color.green, on_click=self._next)
        self.restart_button = Button(text='Restart poziomu', parent=self, y=-0.26, scale=(0.45, 0.075), color=color.azure, highlight_color=color.cyan, on_click=self._restart)
        self.menu_button = Button(text='Menu główne', parent=self, y=-0.37, scale=(0.45, 0.075), color=color.orange, highlight_color=color.gold, on_click=self._menu)

        for key, value in kwargs.items():
            setattr(self, key, value)

    def show(self, title: str, subtitle: str, stats: str = '', allow_next: bool = True):
        self.title.text = title
        self.subtitle.text = subtitle
        self.stats.text = stats
        self.allow_next = allow_next
        self.next_button.enabled = allow_next
        self.enabled = True
        mouse.locked = False
        mouse.visible = True
        application.paused = True

    def hide(self):
        self.enabled = False
        application.paused = False
        mouse.locked = True
        mouse.visible = False

    def _restart(self):
        self.hide()
        self.restart_callback()

    def _next(self):
        if not self.allow_next:
            return
        self.hide()
        self.next_callback()

    def _menu(self):
        self.hide()
        self.menu_callback()


class GameManager(Entity):
    def __init__(self):
        super().__init__(ignore_paused=True)
        self.current_level_index = 0
        self.state = 'menu'
        self.environment = None
        self.shootables_parent = None
        self.player = None
        self.editor_camera = None
        self.music = None
        self.level_started_at = 0
        self.kills_at_level_start = 0
        self.end_screen_shown = False

        self.main_menu = MenuMenu(
            start_game_callback=self.start_level,
            level_count=len(LEVELS),
            get_level_name=lambda index: LEVELS[index].name,
            get_level_subtitle=lambda index: LEVELS[index].subtitle,
        )
        self.pause_menu = InGameMenu(resume_callback=self.resume_game, restart_callback=self.restart_level, main_menu_callback=self.return_to_menu)
        self.result_screen = ResultScreen(restart_callback=self.restart_level, next_callback=self.next_level, menu_callback=self.return_to_menu)

    def capture_mouse(self, enabled: bool):
        """
        Linux/X11 czasem wypluwa Failed to grab pointer, gdy łapiesz myszkę za wcześnie.
        Mały delay po starcie/restartcie poziomu mocno ogranicza ten syf.
        """
        mouse.visible = not enabled

        def apply_lock():
            mouse.locked = enabled

        invoke(apply_lock, delay=MOUSE_LOCK_DELAY)

    def start_level(self, level_index: int = 0):
        self.cleanup_level()
        self.current_level_index = int(clamp(int(level_index), 0, len(LEVELS) - 1))
        level = LEVELS[self.current_level_index]

        random.seed(1000 + self.current_level_index)
        Enemy.all_enemies.clear()

        self.main_menu.enabled = False
        self.pause_menu.force_hide()
        self.result_screen.enabled = False
        application.paused = False
        self.capture_mouse(True)

        self.environment = setup_environment(level)
        self.shootables_parent = Entity(name='Shootables')

        enemy_positions = self.generate_enemy_positions(level)
        self.player = Player(shootables_parent=self.shootables_parent, initial_enemy_positions=enemy_positions, spawn_position=level.spawn, game_manager=self)
        self.player.score = getattr(self.player, 'score', 0)
        self.player.hud.set_level(level.name, level.goal_text)
        self.player.hud.set_manager(self)

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

        self.editor_camera = EditorCamera(enabled=False, ignore_paused=True)
        self.play_music(level.music)
        self.level_started_at = time.time()
        self.kills_at_level_start = self.player.kills
        self.state = 'playing'
        self.end_screen_shown = False
        print_on_screen(f'{level.name}\n{level.goal_text}', position=(0, .25), origin=(0, 0), duration=3, scale=1.3)

    def generate_enemy_positions(self, level):
        positions = []
        margin = 8
        attempts = 0
        while len(positions) < level.enemy_count and attempts < 500:
            attempts += 1
            x = random.uniform(-level.bounds + margin, level.bounds - margin)
            z = random.uniform(-level.bounds + margin, level.bounds - margin)
            candidate = Vec3(x, 0, z)
            if distance_xz(candidate, level.spawn) < 18:
                continue
            if any(distance_xz(candidate, other) < 7 for other in positions):
                continue
            positions.append(candidate)
        while len(positions) < level.enemy_count:
            angle = len(positions) / max(level.enemy_count, 1) * 360
            positions.append(Vec3(math.cos(math.radians(angle)) * level.bounds * .55, 0, math.sin(math.radians(angle)) * level.bounds * .55))
        return positions

    def play_music(self, music_file: str):
        if self.music:
            destroy(self.music)
            self.music = None
        try:
            self.music = Audio(audio_path(music_file), autoplay=True, loop=True, volume=.35)
        except Exception as exc:
            print(f'Nie udało się odtworzyć muzyki {music_file}: {exc}')

    def cleanup_level(self):
        if self.music:
            destroy(self.music)
            self.music = None
        if self.player:
            if hasattr(self.player, 'cleanup'):
                self.player.cleanup()
            destroy(self.player)
            self.player = None
        if self.editor_camera:
            destroy(self.editor_camera)
            self.editor_camera = None
        if self.shootables_parent:
            destroy(self.shootables_parent)
            self.shootables_parent = None
        if self.environment:
            destroy(self.environment)
            self.environment = None
        Enemy.all_enemies.clear()

    def restart_level(self):
        self.start_level(self.current_level_index)

    def next_level(self):
        if self.current_level_index + 1 < len(LEVELS):
            self.start_level(self.current_level_index + 1)
        else:
            self.return_to_menu()

    def return_to_menu(self):
        self.cleanup_level()
        self.state = 'menu'
        self.end_screen_shown = False
        application.paused = False
        mouse.locked = False
        mouse.visible = True
        self.pause_menu.force_hide()
        self.result_screen.enabled = False
        self.main_menu.enabled = True
        self.main_menu.show_main()

    def pause_game(self):
        if self.state != 'playing' or self.result_screen.enabled:
            return
        application.paused = True
        mouse.locked = False
        mouse.visible = True
        self.pause_menu.show()

    def resume_game(self):
        application.paused = False
        self.pause_menu.force_hide()
        self.capture_mouse(True)

    def toggle_pause(self):
        if self.state != 'playing' or self.result_screen.enabled:
            return
        if application.paused or self.pause_menu.enabled:
            self.resume_game()
        else:
            self.pause_game()

    def remaining_enemies(self) -> int:
        return sum(1 for enemy in Enemy.all_enemies if enemy.alive)

    def elapsed_time(self) -> int:
        if not self.level_started_at:
            return 0
        return int(time.time() - self.level_started_at)

    def level_stats_text(self) -> str:
        if not self.player:
            return ''
        killed_this_level = self.player.kills - self.kills_at_level_start
        return f'Czas: {self.elapsed_time()} s   Zabici: {killed_this_level}   Punkty: {self.player.score}'

    def update(self):
        if self.state != 'playing' or not self.player or self.end_screen_shown:
            return

        if self.player.is_dead or self.player.hp <= 0:
            self.end_screen_shown = True
            self.state = 'game_over'
            self.result_screen.show('GAME OVER', 'R = restart, Esc = menu.', self.level_stats_text(), allow_next=False)
            return

        if self.remaining_enemies() <= 0:
            self.end_screen_shown = True
            self.state = 'level_complete'
            last_level = self.current_level_index == len(LEVELS) - 1
            self.result_screen.show(
                'POZIOM WYCZYSZCZONY' if not last_level else 'KONIEC GRY — WYGRAŁEŚ',
                'Enter = dalej, R = restart, Esc = menu.' if not last_level else 'Wyczyściłeś wszystkie fale. Esc = menu, R = restart.',
                self.level_stats_text(),
                allow_next=not last_level,
            )

    def handle_key(self, key):
        if key == 'escape':
            if self.pause_menu.enabled or (self.state == 'playing' and application.paused):
                self.resume_game()
            elif self.result_screen.enabled or self.state in ('game_over', 'level_complete'):
                self.return_to_menu()
            elif self.state == 'playing':
                self.pause_game()
            elif self.state == 'menu':
                self.main_menu.go_back_or_quit()
            return

        if key == 'r':
            if self.pause_menu.enabled or self.result_screen.enabled or self.state in ('game_over', 'level_complete'):
                self.restart_level()
            return

        if key == 'enter' and self.result_screen.enabled and self.result_screen.allow_next:
            self.next_level()
            return

        if key == 'f1':
            print_on_screen(TEXT['controls_line'], position=(0, -.35), origin=(0, 0), duration=4)


# ---------- App bootstrap ----------
app = Ursina()
window.title = GAME_TITLE
window.borderless = False
window.fps_counter.enabled = SHOW_FPS
window.exit_button.visible = False
window.size = (int(WINDOW_WIDTH), int(WINDOW_HEIGHT))
window.position = (192, 108)

Entity.default_shader = lit_with_shadows_shader
Sky()
manager = GameManager()


def input(key):
    manager.handle_key(key)


app.run()
