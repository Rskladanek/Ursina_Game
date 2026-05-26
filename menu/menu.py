from __future__ import annotations

from ursina import *
from data.ui_text import TEXT


class MenuMenu(Entity):
    """Menu główne. Nie obsługuje samo Esc — input idzie centralnie przez GameManager."""

    def __init__(self, start_game_callback, level_count=3, get_level_name=None, get_level_subtitle=None, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True, enabled=True)
        self.start_game_callback = start_game_callback
        self.level_count = level_count
        self.get_level_name = get_level_name or (lambda index: f'Poziom {index + 1}')
        self.get_level_subtitle = get_level_subtitle or (lambda index: '')
        self.selected_level = 0

        self.background = Entity(parent=self, model='quad', color=color.rgb(12, 14, 18), scale=(window.aspect_ratio * 2.1, 2.1), z=.15)
        self.accent = Entity(parent=self, model='quad', color=color.rgba(40, 120, 220, 80), scale=(1.45, .02), y=.275, z=.14)

        self.main_menu = Entity(parent=self, enabled=True)
        self.level_menu = Entity(parent=self, enabled=False)
        self.options_menu = Entity(parent=self, enabled=False)
        self.help_menu = Entity(parent=self, enabled=False)
        self.credits_menu = Entity(parent=self, enabled=False)

        self._build_main()
        self._build_levels()
        self._build_options()
        self._build_help()
        self._build_credits()

        for key, value in kwargs.items():
            setattr(self, key, value)

    def _title(self, parent, text):
        Text(text, parent=parent, y=.36, origin=(0, 0), scale=2.0, color=color.azure)

    def _button(self, parent, text, y, on_click, color_value=color.azure, scale=(.46, .078)):
        return Button(
            text=text,
            parent=parent,
            y=y,
            scale=scale,
            color=color_value,
            highlight_color=color.cyan,
            pressed_color=color.lime,
            on_click=on_click,
        )

    def _build_main(self):
        self._title(self.main_menu, TEXT['game_title'])
        Text(TEXT['game_subtitle'], parent=self.main_menu, y=.26, origin=(0, 0), scale=.75, color=color.light_gray)
        self.selected_text = Text('', parent=self.main_menu, y=.17, origin=(0, 0), scale=.78, color=color.gold)
        self._button(self.main_menu, TEXT['start_game'], .06, lambda: self.start_game_callback(self.selected_level), color.green)
        self._button(self.main_menu, TEXT['level_select'], -.05, lambda: self.switch_to(self.level_menu), color.azure)
        self._button(self.main_menu, TEXT['options'], -.16, lambda: self.switch_to(self.options_menu), color.orange)
        self._button(self.main_menu, TEXT['help'], -.27, lambda: self.switch_to(self.help_menu), color.cyan)
        self._button(self.main_menu, TEXT['credits'], -.38, lambda: self.switch_to(self.credits_menu), color.yellow)
        self._button(self.main_menu, TEXT['quit'], -.49, application.quit, color.red)
        self.refresh_selected_text()

    def _build_levels(self):
        self._title(self.level_menu, 'WYBÓR POZIOMU')
        Text('Kliknij poziom i od razu startuj. Esc wraca do menu.', parent=self.level_menu, y=.26, origin=(0, 0), scale=.75, color=color.light_gray)
        start_y = .11
        for index in range(self.level_count):
            y = start_y - index * .15
            label = self.get_level_name(index)
            subtitle = self.get_level_subtitle(index)
            self._button(self.level_menu, label, y, Func(self.choose_level, index), color.azure, scale=(.56, .075))
            if subtitle:
                Text(subtitle, parent=self.level_menu, y=y - .055, origin=(0, 0), scale=.55, color=color.rgba(220, 220, 220, 185))
        self._button(self.level_menu, TEXT['back'], -.43, self.show_main, color.orange, scale=(.36, .07))

    def _build_options(self):
        self._title(self.options_menu, 'OPCJE')
        Text('Projekt jest przygotowany pod rozbudowę: config, core, data i assets.', parent=self.options_menu, y=.24, origin=(0, 0), scale=.7, color=color.light_gray)
        Text('• Teksty: data/ui_text.py albo assets/texts\n• Tekstury: assets/textures\n• Modele: assets/models\n• Audio: assets/audio\n• Poziomy: config/levels.py', parent=self.options_menu, y=.03, origin=(0, 0), scale=.78, color=color.white)
        self._button(self.options_menu, TEXT['back'], -.36, self.show_main, color.orange, scale=(.36, .07))

    def _build_help(self):
        self._title(self.help_menu, 'STEROWANIE')
        Text(TEXT['controls_block'], parent=self.help_menu, y=.05, origin=(0, 0), scale=.85, color=color.white)
        self._button(self.help_menu, TEXT['back'], -.38, self.show_main, color.orange, scale=(.36, .07))

    def _build_credits(self):
        self._title(self.credits_menu, 'AUTORZY')
        Text('Game Design / Programming:\nRemigiusz Składanek & Dawid Hajkowski\n\nArt / Audio / Assets:\nwrzucaj do folderu assets i podmieniaj bez grzebania w logice gry', parent=self.credits_menu, y=.04, origin=(0, 0), scale=.82, color=color.white)
        self._button(self.credits_menu, TEXT['back'], -.36, self.show_main, color.orange, scale=(.36, .07))

    def refresh_selected_text(self):
        self.selected_text.text = f'Wybrany: {self.get_level_name(self.selected_level)}'

    def choose_level(self, index):
        self.selected_level = index
        self.refresh_selected_text()
        self.start_game_callback(index)

    def switch_to(self, target):
        for menu in (self.main_menu, self.level_menu, self.options_menu, self.help_menu, self.credits_menu):
            menu.enabled = False
        target.enabled = True

    def show_main(self):
        self.switch_to(self.main_menu)
        self.refresh_selected_text()

    def go_back_or_quit(self):
        if self.main_menu.enabled:
            application.quit()
        else:
            self.show_main()
