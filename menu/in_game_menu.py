from __future__ import annotations

from ursina import *
from data.ui_text import TEXT


class InGameMenu(Entity):
    """Menu pauzy. Esc obsługuje GameManager, żeby nie było podwójnych eventów."""

    def __init__(self, resume_callback=None, restart_callback=None, main_menu_callback=None, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True, enabled=False)
        self.resume_callback = resume_callback
        self.restart_callback = restart_callback
        self.main_menu_callback = main_menu_callback

        self.menu_background = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 185), scale=(window.aspect_ratio * 2.1, 2.1), z=0.12)
        self.card = Entity(parent=self, model='quad', color=color.rgba(22, 25, 32, 230), scale=(.72, .82), z=.11)
        Text(TEXT['pause'], parent=self, y=.31, origin=(0, 0), scale=2.0, color=color.gold)
        Text('Esc wraca do gry. R robi restart poziomu.', parent=self, y=.22, origin=(0, 0), scale=.62, color=color.light_gray)

        self._button(TEXT['resume'], .09, self._resume, color.lime)
        self._button(TEXT['restart_level'], -.03, self._restart, color.azure)
        self._button('Sterowanie', -.15, self._controls, color.cyan)
        self._button(TEXT['main_menu'], -.27, self._main_menu, color.orange)
        self._button(TEXT['quit'], -.39, application.quit, color.red)

        self.controls_text = Text('', parent=self, y=-.51, origin=(0, 0), scale=.55, color=color.rgba(255, 255, 255, 180))

        for key, value in kwargs.items():
            setattr(self, key, value)

    def _button(self, text, y, on_click, color_value):
        return Button(text=text, parent=self, y=y, scale=(.45, .075), color=color_value, highlight_color=color.cyan, pressed_color=color.lime, on_click=on_click)

    def show(self):
        self.enabled = True
        self.scale = .92
        self.animate_scale(1, duration=.08, curve=curve.out_quad)
        mouse.visible = True
        mouse.locked = False
        application.paused = True

    def force_hide(self):
        self.enabled = False
        self.controls_text.text = ''

    def _resume(self):
        self.force_hide()
        if self.resume_callback:
            self.resume_callback()
        else:
            application.paused = False
            mouse.locked = True
            mouse.visible = False

    def _restart(self):
        self.force_hide()
        if self.restart_callback:
            self.restart_callback()

    def _main_menu(self):
        self.force_hide()
        if self.main_menu_callback:
            self.main_menu_callback()

    def _controls(self):
        self.controls_text.text = TEXT['controls_line']

    # kompatybilność ze starym main.py
    def resume_game(self):
        self._resume()

    def enable(self):
        self.show()

    def disable(self):
        self.force_hide()
