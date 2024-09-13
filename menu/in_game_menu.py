from ursina import *

class InGameMenu(Entity):
    def __init__(self, **kwargs):
        super().__init__(parent=camera.ui, enabled=False)

        # Semi-transparent background for the menu
        self.menu_background = Entity(
            parent=self,
            model='quad',
            texture='white_cube',
            color=color.rgba(0, 0, 0, 150),
            scale=(window.aspect_ratio * 2, 2),
            z=0.1
        )

        # Title for the menu
        self.title = Text(
            'PAUZA',
            parent=self,
            y=0.4,
            origin=(0, 0),
            scale=2,
            color=color.gold,
            shadow=(0.5, 0.5),
            background=True
        )

        # Resume button
        self.resume_button = Button(
            text='Wznów grę',
            scale=(0.5, 0.1),
            y=0.1,
            parent=self,
            color=color.azure,
            highlight_color=color.cyan,
            pressed_color=color.lime,
            tooltip=Tooltip('Powrót do gry')
        )
        self.resume_button.on_click = self.resume_game

        # Options button
        self.options_button = Button(
            text='Opcje',
            scale=(0.5, 0.1),
            y=-0.05,
            parent=self,
            color=color.azure,
            highlight_color=color.cyan,
            pressed_color=color.lime,
            tooltip=Tooltip('Ustawienia gry')
        )
        self.options_button.on_click = self.show_options

        # Quit button
        self.quit_button = Button(
            text='Wyjdź',
            scale=(0.5, 0.1),
            y=-0.2,
            parent=self,
            color=color.azure,
            highlight_color=color.cyan,
            pressed_color=color.lime,
            tooltip=Tooltip('Zakończ grę')
        )
        self.quit_button.on_click = application.quit

        # Animacja pojawiania się menu
        self.animate_in = Func(self.animate_menu_in)
        self.animate_out = Func(self.animate_menu_out)

        # Dodatkowe parametry z kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def animate_menu_in(self):
        self.enabled = True
        self.scale = 0.8
        self.animate_scale(1, duration=0.1, curve=curve.out_quint)
        mouse.visible = True
        mouse.locked = False
        application.paused = True

    def animate_menu_out(self):
        def disable_menu():
            self.enabled = False
            application.paused = False
            mouse.locked = True
            mouse.visible = False
        self.animate_scale(0.8, duration=0.1, curve=curve.in_quint)
        invoke(disable_menu, delay=0.1)

    def resume_game(self):
        self.animate_out()

    def show_options(self):
        print("Opcje - funkcjonalność do zaimplementowania.")

    def enable(self):
        self.animate_in()

    def disable(self):
        self.animate_out()

