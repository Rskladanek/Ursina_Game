from ursina import *

class HUD(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(parent=camera.ui)

        self.health_text = Text(
            text=f'HP: {player.hp}',
            position=(-0.7, 0.4),  # Lower left corner
            origin=(0, 0),
            scale=2,
            background=True,
            color=color.white,
            background_color=color.rgba(0, 0, 0, 150),
            font='VeraMono.ttf'
        )
        self.ammo_text = Text(
            text=f'Ammo: {player.weapon.ammo}/{player.weapon.max_ammo}',
            position=(0.67, -0.4),  # Upper right corner
            origin=(0, 0),
            scale=2,
            background=True,
            color=color.white,
            background_color=color.rgba(0, 0, 0, 150),
            font='VeraMono.ttf'
        )

        self.player = player

    def update(self):
        self.health_text.text = f'HP: {self.player.hp}'
        self.ammo_text.text = f'Ammo: {self.player.weapon.ammo}/{self.player.weapon.max_ammo}'
