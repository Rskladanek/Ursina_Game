import pygame

def play_music(file_path, volume=0.5):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1)  # -1 means the music will loop indefinitely

def stop_music():
    pygame.mixer.music.stop()