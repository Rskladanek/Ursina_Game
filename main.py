from ursina import *
from ursina.shaders import lit_with_shadows_shader
from player.player import Player
from enemy.enemy import Enemy
from environment.environment import setup_environment
from utils.utils import pause_input
from menu.menu import MenuMenu
from menu.in_game_menu import InGameMenu
from random import uniform

app = Ursina()

# Global settings
random.seed(0)
Entity.default_shader = lit_with_shadows_shader

# Global variables
player = None
shootables_parent = None
enemies = []
editor_camera = None
pause_handler = None
in_game_menu = None

# Create the main menu
main_menu = MenuMenu(start_game_callback=lambda: start_game())

def start_game():
    global player, shootables_parent, enemies, editor_camera, pause_handler, in_game_menu

    # Hide the menu
    main_menu.disable()

    # Create the game environment
    setup_environment()

    # Create the player
    player = Player()

    # Create a parent for shootable objects
    shootables_parent = Entity()

    # Pass shootables_parent to player
    player.shootables_parent = shootables_parent

    # Create initial enemy positions
    initial_enemy_positions = [Vec3(x * 10, 0, uniform(-8, 8)) for x in range(10)]
    player.initial_enemy_positions = initial_enemy_positions  # Store initial enemy positions in player

    # Create enemies and pass shootables_parent and player
    for pos in initial_enemy_positions:
        Enemy(shootables_parent=shootables_parent, player=player, initial_position=pos)

    # Create the editor camera
    editor_camera = EditorCamera(enabled=False, ignore_paused=True)

    # Handle pause functionality
    pause_handler = Entity(ignore_paused=True, input=lambda key: pause_input(key, player, editor_camera, player.weapon))

    # Create in-game menu
    in_game_menu = InGameMenu()

    # Light and sky
    sun = DirectionalLight()
    sun.look_at(Vec3(1, -1, -1))
    Sky()

def update():
    global enemies, shootables_parent

    if shootables_parent:
        enemies = [enemy for enemy in shootables_parent.children if isinstance(enemy, Enemy) and enemy.alive]
        for enemy in enemies:
            enemy.update()

    if player:
        player.update()

def input(key):
    if key == 'escape':
        if application.paused:
            in_game_menu.resume_game()
        else:
            in_game_menu.enable()
            application.paused = True
    if player:
        player.input(key)

app.run()
