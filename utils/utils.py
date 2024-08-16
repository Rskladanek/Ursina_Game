from ursina import *

def pause_input(key, player, editor_camera, weapon):
    if key == 'p':
        if not application.paused:
            player.disable()
            editor_camera.enable()
        else:
            player.enable()
            editor_camera.disable()

        application.paused = not application.paused

def exit_game():
    application.quit()
