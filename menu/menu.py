from ursina import *

class MenuMenu(Entity):
    def __init__(self, start_game_callback, **kwargs):
        super().__init__(parent=camera.ui, ignore_paused=True)

        # Create empty entities that will be parents of our menus content
        self.main_menu = Entity(parent=self, enabled=True, position=(0, 0, 0))
        self.options_menu = Entity(parent=self, enabled=False, position=(0, 0, 0))
        self.help_menu = Entity(parent=self, enabled=False, position=(0, 0, 0))
        self.credits_menu = Entity(parent=self, enabled=False, position=(0, 0, 0))

        # Add a background. You can change 'shore' to a different texture if you'd like.
        self.background = Sprite('shore', parent=self, color=color.dark_gray, z=1, scale=(camera.aspect_ratio, 1))

        # [MAIN MENU] WINDOW START
        # Title of our menu
        Text("MAIN MENU", parent=self.main_menu, y=0.4, origin=(0, 0), scale=2, color=color.azure)

        def switch(menu1, menu2):
            menu1.enabled = True
            menu2.enabled = False

        # Button list
        button_y_positions = [0.1, 0, -0.1, -0.2, -0.3]

        start_button = Button(text='Start', scale=(0.4, 0.1), position=(0, button_y_positions[0]), parent=self.main_menu, color=color.green)
        start_button.on_click = start_game_callback

        options_button = Button(text='Opcje', scale=(0.4, 0.1), position=(0, button_y_positions[1]), parent=self.main_menu, color=color.orange)
        options_button.on_click = lambda: switch(self.options_menu, self.main_menu)

        credits_button = Button(text='Kredyty', scale=(0.4, 0.1), position=(0, button_y_positions[2]), parent=self.main_menu, color=color.yellow)
        credits_button.on_click = lambda: switch(self.credits_menu, self.main_menu)

        help_button = Button(text='Pomoc', scale=(0.4, 0.1), position=(0, button_y_positions[3]), parent=self.main_menu, color=color.cyan)
        help_button.on_click = lambda: switch(self.help_menu, self.main_menu)

        exit_button = Button(text='Wyjście', scale=(0.4, 0.1), position=(0, button_y_positions[4]), parent=self.main_menu, color=color.red)
        exit_button.on_click = application.quit
        # [MAIN MENU] WINDOW END

        # [OPTIONS MENU] WINDOW START
        # Title of our menu
        Text("OPTIONS MENU", parent=self.options_menu, y=0.4, origin=(0, 0), scale=2, color=color.azure)

        # Button
        Button("Back", parent=self.options_menu, y=-0.3, scale=(0.3, 0.1), color=color.orange,
               on_click=lambda: switch(self.main_menu, self.options_menu))
        # [OPTIONS MENU] WINDOW END

        # [HELP MENU] WINDOW START
        # Title of our menu
        Text("HELP MENU", parent=self.help_menu, y=0.4, origin=(0, 0), scale=2, color=color.azure)

        # Button list with more spacing
        help_buttons = [
            ("Gameplay", "You clicked on Gameplay help button!"),
            ("Battle", "You clicked on Battle help button!"),
            ("Control", "You clicked on Control help button!"),
            ("Back", None)
        ]

        for i, (text, msg) in enumerate(help_buttons):
            y_pos = 0.2 - (i * 0.15)
            if msg:
                button = Button(text=text, scale=(0.4, 0.1), position=(0, y_pos), parent=self.help_menu, color=color.azure)
                button.on_click = Func(print_on_screen, msg, position=(0, 0.1), origin=(0, 0))
            else:
                button = Button(text=text, scale=(0.4, 0.1), position=(0, y_pos), parent=self.help_menu, color=color.orange)
                button.on_click = lambda: switch(self.main_menu, self.help_menu)
        # [HELP MENU] WINDOW END

        # [CREDITS MENU] WINDOW START
        Text("CREDITS MENU", parent=self.credits_menu, y=0.4, origin=(0, 0), scale=2, color=color.azure)

        credits_text = """
        Game Design: Remigiusz Squadanek
        Programming: Remigiusz Squadanek
        Art: John Smith
        Music: Jane Smith
        """

        Text(credits_text, parent=self.credits_menu, y=0, origin=(0, 0), color=color.white)

        Button("Back", parent=self.credits_menu, y=-0.3, scale=(0.3, 0.1), color=color.orange,
               on_click=lambda: switch(self.main_menu, self.credits_menu))
        # [CREDITS MENU] WINDOW END

        # Here we can change attributes of this class when call this class
        for key, value in kwargs.items():
            setattr(self, key, value)

    # Input function that checks if a key is pressed on the keyboard
    def input(self, key):
        def switch(menu1, menu2):
            menu1.enabled = True
            menu2.enabled = False

        # If our main menu is enabled and we press [Escape]
        if key == "escape":
            if self.main_menu.enabled:
                application.quit()
            elif self.options_menu.enabled:
                switch(self.main_menu, self.options_menu)
            elif self.help_menu.enabled:
                switch(self.main_menu, self.help_menu)
            elif self.credits_menu.enabled:
                switch(self.main_menu, self.credits_menu)

    # Update function that checks something every frame
    def update(self):
        pass
