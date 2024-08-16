from ursina import *

class InGameMenu(Entity):
    def __init__(self, **kwargs):
        super().__init__(parent=camera.ui, enabled=False)

        # Background for the menu
        self.menu_background = Entity(parent=self, model='quad', texture='white_cube', color=color.rgba(0, 0, 0, 150), scale=(1.5, 1, 1))

        # Title for the menu
        self.title = Text('Game Menu', parent=self, y=0.35, origin=(0, 0), scale=2, color=color.gold)

        # Resume button
        self.resume_button = Button(text='Resume', scale=(0.4, 0.1), y=0.1, parent=self, color=color.azure)
        self.resume_button.on_click = self.resume_game
        self.resume_button.on_mouse_enter = Func(self.button_hover, self.resume_button)
        self.resume_button.on_mouse_exit = Func(self.button_normal, self.resume_button)

        # Options button
        self.options_button = Button(text='Options', scale=(0.4, 0.1), y=-0.1, parent=self, color=color.azure)
        self.options_button.on_click = self.show_options
        self.options_button.on_mouse_enter = Func(self.button_hover, self.options_button)
        self.options_button.on_mouse_exit = Func(self.button_normal, self.options_button)

        # Quit button
        self.quit_button = Button(text='Quit', scale=(0.4, 0.1), y=-0.3, parent=self, color=color.azure)
        self.quit_button.on_click = application.quit
        self.quit_button.on_mouse_enter = Func(self.button_hover, self.quit_button)
        self.quit_button.on_mouse_exit = Func(self.button_normal, self.quit_button)

    def button_hover(self, button):
        button.color = color.yellow

    def button_normal(self, button):
        button.color = color.azure

    def resume_game(self):
        self.disable()
        application.paused = False
        mouse.locked = True  # Lock the mouse cursor when resuming the game

    def show_options(self):
        print("Options button clicked")  # Placeholder for options functionality

    def enable(self):
        super().enable()
        mouse.visible = True  # Make the mouse cursor visible when the menu is enabled
        mouse.locked = False  # Unlock the mouse cursor when the menu is enabled