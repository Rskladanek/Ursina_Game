from ursina import *
from ursina.prefabs.ursfx import ursfx
from random import uniform
import math

class Weapon(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player

        # Broń jako model podstawowy
        self.parent = camera
        self.position = (0.5, -0.25, 0.25)  # Dostosowane, aby broń była widoczna
        self.scale = (0.2, 0.1, 0.5)
        self.origin_z = -0.5
        self.model = 'cube'
        self.color = color.gray

        # Ustawienia broni
        self.ammo = 30
        self.max_ammo = 30
        self.reload_time = 1.5
        self.damage = 100
        self.bullet_speed = 100  # Prędkość pocisku zwiększona
        self.fire_rate = 0.1
        self.on_cooldown = False
        self.reloading = False

        # Muzzle flash
        self.muzzle_flash = Entity(parent=self, position=(0, 0, 0.25), world_scale=0.1, model='quad', color=color.yellow, enabled=False)

        # Krzyżyk celownika
        self.crosshair = Entity(parent=camera.ui, model='quad', color=color.white, scale=0.02)
        self.crosshair.scale_y = 0.002
        self.crosshair.y = -0.02

        for i in range(4):
            part = Entity(parent=self.crosshair, model='quad', color=color.white, scale=(0.01, 0.002) if i % 2 == 0 else (0.002, 0.01))
            part.position = (0.015 if i == 0 else -0.015 if i == 1 else 0, 0.015 if i == 2 else -0.015 if i == 3 else 0)

        # Dostosuj dodatkowe argumenty
        for key, value in kwargs.items():
            setattr(self, key, value)

    def shoot(self):
        if self.ammo > 0 and not self.on_cooldown and not self.reloading:
            self.on_cooldown = True
            self.muzzle_flash.enabled = True

            # Odtwórz dźwięk strzału
            ursfx(
                [(0, 0.9), (0.05, 0.7), (0.1, 0.5), (0.15, 0.3), (0.2, 0)],
                volume=uniform(0.8, 1.0), wave='square', pitch=uniform(-12, -11),
                pitch_change=-12, speed=3.0
            )

            # Animizacja wystrzału
            self.muzzle_flash.animate_scale(0.2, duration=0.05)
            invoke(self.muzzle_flash.disable, delay=0.05)

            # Efekt odrzutu
            self.animate_position(self.position + Vec3(uniform(-0.02, 0.02), uniform(-0.02, 0.02), -0.1), duration=0.05, curve=curve.in_expo)
            self.animate_position(self.position, duration=0.1, delay=0.05, curve=curve.out_expo)

            # Stworzenie pocisku
            bullet = Entity(
                model='sphere',
                scale=0.05,
                color=color.yellow,
                position=self.world_position + self.forward * 1.5,
                collider='box'
            )
            bullet.velocity = self.forward * self.bullet_speed
            bullet.gravity = 9.8
            bullet.bounciness = 0.9  # Dodany współczynnik odbicia
            bullet.alive_time = 0

            def bullet_update():
                bullet.velocity.y -= bullet.gravity * time.dt
                bullet.position += bullet.velocity * time.dt
                bullet.alive_time += time.dt

                # Detekcja kolizji
                hit_info = bullet.intersects()
                if hit_info.hit:
                    normal = hit_info.world_normal
                    bullet.velocity = self.reflect(bullet.velocity, normal) * bullet.bounciness

                    # Jeśli pocisk trafi w wroga
                    if hasattr(hit_info.entity, 'take_damage'):
                        hit_info.entity.take_damage(self.damage, self.forward)
                        destroy(bullet)

                # Usunięcie pocisku po 5 sekundach
                if bullet.alive_time > 5:
                    destroy(bullet)

            bullet.update = bullet_update

            # Czas na następny strzał
            invoke(setattr, self, 'on_cooldown', False, delay=self.fire_rate)
            self.ammo -= 1

    def reload(self):
        if self.ammo < self.max_ammo and not self.reloading:
            self.reloading = True
            print_on_screen("Reloading...", position=(0, 0), origin=(0, 0), duration=self.reload_time)

            # Animacja przeładowania
            self.animate_position(self.position + Vec3(0, -0.2, 0), duration=self.reload_time / 2, curve=curve.in_out_expo)
            self.animate_position(self.position, duration=self.reload_time / 2, delay=self.reload_time / 2, curve=curve.in_out_expo)
            invoke(self.finish_reload, delay=self.reload_time)

    def finish_reload(self):
        self.ammo = self.max_ammo
        self.reloading = False

    def reflect(self, vector, normal):
        return vector - 2 * vector.dot(normal) * normal

    def update_ui(self, health_text, ammo_text):
        health_text.text = f'HP: {self.player.hp}'
        ammo_text.text = f'Ammo: {self.ammo}/{self.max_ammo}'
