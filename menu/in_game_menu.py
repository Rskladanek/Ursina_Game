from __future__ import annotations

from ursina import *
from data.ui_text import TEXT


def txt(key: str, fallback: str) -> str:
    return TEXT.get(key, fallback)


class InGameMenu(Entity):
    """
    Stabilne menu pauzy:
    - bez Buttonów,
    - bez Unicode,
    - bez białych paneli,
    - działa ESC/P/R/Enter/W/S/klik myszą,
    - samo obsługuje input nawet gdy application.paused=True.
    """

    def __init__(
        self,
        resume_callback=None,
        restart_callback=None,
        main_menu_callback=None,
        quit_callback=None,
        **kwargs
    ):
        super().__init__(
            parent=camera.ui,
            enabled=False,
            ignore_paused=True,
        )

        self.resume_callback = resume_callback
        self.restart_callback = restart_callback
        self.main_menu_callback = main_menu_callback
        self.quit_callback = quit_callback or application.quit

        self.selected_index = 0
        self.controls_visible = False

        self.entries = []
        self.entry_labels = []

        self._build()

        for key, value in kwargs.items():
            setattr(self, key, value)

    def _build(self):
        # Overlay z tyłu.
        self.overlay = Entity(
            parent=self,
            model='quad',
            scale=(3.5, 2.2),
            position=(0, 0, 0.5),
            color=color.rgba(0, 0, 0, 235),
            collider=None,
            ignore_paused=True,
        )

        # Teksty z przodu.
        self.title = Text(
            text='PAUZA',
            parent=self,
            origin=(0, 0),
            position=(0, 0.34, -1),
            scale=2.3,
            color=color.yellow,
            ignore_paused=True,
        )

        self.subtitle = Text(
            text='Gra zatrzymana',
            parent=self,
            origin=(0, 0),
            position=(0, 0.245, -1),
            scale=0.9,
            color=color.light_gray,
            ignore_paused=True,
        )

        self.hint = Text(
            text='W/S - wybor     Enter - zatwierdz     Esc/P - powrot',
            parent=self,
            origin=(0, 0),
            position=(0, 0.175, -1),
            scale=0.58,
            color=color.gray,
            ignore_paused=True,
        )

        self.line_top = Text(
            text='------------------------------',
            parent=self,
            origin=(0, 0),
            position=(0, 0.115, -1),
            scale=0.65,
            color=color.dark_gray,
            ignore_paused=True,
        )

        self.entries = [
            {
                'label': txt('resume', 'Wroc do gry'),
                'callback': self._resume,
                'base_color': color.lime,
            },
            {
                'label': txt('restart_level', 'Restart poziomu'),
                'callback': self._restart,
                'base_color': color.azure,
            },
            {
                'label': 'Sterowanie',
                'callback': self._toggle_controls,
                'base_color': color.cyan,
            },
            {
                'label': txt('main_menu', 'Menu glowne'),
                'callback': self._main_menu,
                'base_color': color.orange,
            },
            {
                'label': txt('quit', 'Wyjdz'),
                'callback': self._quit,
                'base_color': color.red,
            },
        ]

        start_y = 0.035
        step = 0.085

        for i, entry in enumerate(self.entries):
            label = Text(
                text='',
                parent=self,
                origin=(0, 0),
                position=(0, start_y - i * step, -1),
                scale=0.9,
                color=entry['base_color'],
                ignore_paused=True,
            )

            self.entry_labels.append(label)

        self.line_bottom = Text(
            text='------------------------------',
            parent=self,
            origin=(0, 0),
            position=(0, -0.405, -1),
            scale=0.65,
            color=color.dark_gray,
            ignore_paused=True,
        )

        self.controls_text = Text(
            text='',
            parent=self,
            origin=(0, 0),
            position=(0, -0.47, -1),
            scale=0.55,
            color=color.white,
            enabled=False,
            ignore_paused=True,
        )

        self._refresh()

    def _refresh(self):
        for i, entry in enumerate(self.entries):
            selected = i == self.selected_index
            number = i + 1

            if selected:
                self.entry_labels[i].text = f'>  {number}. {entry["label"]}  <'
                self.entry_labels[i].color = color.yellow
                self.entry_labels[i].scale = 1.05
            else:
                self.entry_labels[i].text = f'   {number}. {entry["label"]}'
                self.entry_labels[i].color = entry['base_color']
                self.entry_labels[i].scale = 0.9

    def update(self):
        if not self.enabled:
            return

        hovered = self._get_hovered_index()

        if hovered is not None and hovered != self.selected_index:
            self.selected_index = hovered
            self._refresh()

    def input(self, key):
        """
        Najważniejsza poprawka.
        To działa nawet podczas application.paused=True, bo menu ma ignore_paused=True.
        """
        if not self.enabled:
            return

        self.handle_key(key)

    def _get_hovered_index(self):
        mx = mouse.x
        my = mouse.y

        if not (-0.45 <= mx <= 0.45):
            return None

        for i, label in enumerate(self.entry_labels):
            y = label.y

            if y - 0.04 <= my <= y + 0.04:
                return i

        return None

    def _activate_selected(self):
        if not self.entries:
            return

        callback = self.entries[self.selected_index]['callback']

        if callback:
            callback()

    def handle_key(self, key: str) -> bool:
        if not self.enabled:
            return False

        if key in ('escape', 'p'):
            self._resume()
            return True

        if key == 'r':
            self._restart()
            return True

        if key in ('w', 'up arrow'):
            self.selected_index = (self.selected_index - 1) % len(self.entries)
            self._refresh()
            return True

        if key in ('s', 'down arrow'):
            self.selected_index = (self.selected_index + 1) % len(self.entries)
            self._refresh()
            return True

        if key in ('enter', 'space'):
            self._activate_selected()
            return True

        if key == 'left mouse down':
            hovered = self._get_hovered_index()

            if hovered is not None:
                self.selected_index = hovered
                self._refresh()
                self._activate_selected()

            return True

        if key in ('1', '2', '3', '4', '5'):
            index = int(key) - 1

            if 0 <= index < len(self.entries):
                self.selected_index = index
                self._refresh()
                self._activate_selected()

            return True

        return False

    def show(self):
        self.enabled = True

        self.selected_index = 0
        self.controls_visible = False
        self.controls_text.enabled = False
        self.controls_text.text = ''

        self._refresh()

        mouse.visible = True
        mouse.locked = False
        application.paused = True

    def hide(self):
        self.enabled = False

        self.controls_visible = False
        self.controls_text.enabled = False
        self.controls_text.text = ''

    def force_hide(self):
        self.hide()

    def _resume(self):
        self.hide()

        if self.resume_callback:
            self.resume_callback()
        else:
            application.paused = False
            mouse.visible = False
            mouse.locked = True

    def _restart(self):
        self.hide()

        if self.restart_callback:
            self.restart_callback()

    def _main_menu(self):
        self.hide()

        if self.main_menu_callback:
            self.main_menu_callback()

    def _quit(self):
        self.quit_callback()

    def _toggle_controls(self):
        self.controls_visible = not self.controls_visible
        self.controls_text.enabled = self.controls_visible

        if self.controls_visible:
            self.controls_text.text = (
                'WASD ruch | Mysz celowanie | LPM strzal\n'
                'Shift sprint | R przeladuj | Esc/P pauza'
            )
        else:
            self.controls_text.text = ''

    def resume_game(self):
        self._resume()

    def enable(self):
        self.show()

    def disable(self):
        self.hide()


PauseMenu = InGameMenu
IngameMenu = InGameMenu
PauseOverlay = InGameMenu