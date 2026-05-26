from __future__ import annotations

from ursina import *


class HUD(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(parent=camera.ui)
        self.player = player
        self.manager = None
        self.level_name = 'Poziom'
        self.goal_text = 'Wyczyść mapę'

        self.panel = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 145), scale=(.74, .18), position=(-.53, .42), z=.05)
        self.level_text = Text(text='', parent=self, position=(-.86, .475), origin=(-.5, 0), scale=.85, color=color.azure)
        self.goal_label = Text(text='', parent=self, position=(-.86, .425), origin=(-.5, 0), scale=.68, color=color.light_gray)
        self.health_text = Text(text='', parent=self, position=(-.86, .365), origin=(-.5, 0), scale=.8, color=color.white)

        self.right_panel = Entity(parent=self, model='quad', color=color.rgba(0, 0, 0, 145), scale=(.60, .17), position=(.59, -.41), z=.05)
        self.ammo_text = Text(text='', parent=self, position=(.36, -.358), origin=(-.5, 0), scale=.9, color=color.white)
        self.enemy_text = Text(text='', parent=self, position=(.36, -.418), origin=(-.5, 0), scale=.75, color=color.orange)
        self.score_text = Text(text='', parent=self, position=(.36, -.475), origin=(-.5, 0), scale=.7, color=color.lime)

        self.help_text = Text(text='F1 sterowanie | Esc pauza', parent=self, position=(0, .47), origin=(0, 0), scale=.65, color=color.rgba(255, 255, 255, 170))

        for key, value in kwargs.items():
            setattr(self, key, value)

    def set_manager(self, manager):
        self.manager = manager

    def set_level(self, level_name: str, goal_text: str):
        self.level_name = level_name
        self.goal_text = goal_text
        self.update()

    def update(self):
        hp = max(0, int(self.player.hp))
        remaining = self.manager.remaining_enemies() if self.manager else 0
        elapsed = self.manager.elapsed_time() if self.manager else 0
        self.level_text.text = self.level_name
        self.goal_label.text = self.goal_text
        self.health_text.text = f'HP: {hp}/{self.player.max_health}   Sprint: {int(self.player.sprint_timer)}s'
        self.ammo_text.text = f'Ammo: {self.player.weapon.ammo}/{self.player.weapon.max_ammo}'
        self.enemy_text.text = f'Wrogowie: {remaining}   Czas: {elapsed}s'
        self.score_text.text = f'Zabici: {self.player.kills}   Punkty: {self.player.score}'

    def cleanup(self):
        destroy(self)
