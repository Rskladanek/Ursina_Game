from __future__ import annotations

from random import uniform
from ursina import *
from ursina.prefabs.ursfx import ursfx

from core.assets import texture
from data.ui_text import TEXT


class Weapon(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.parent = camera
        self.position = (0.5, -0.25, 0.25)
        self.scale = (0.22, 0.1, 0.55)
        self.origin_z = -0.5
        self.model = 'cube'
        self.texture = texture('metal')
        self.color = color.gray

        self.ammo = 30
        self.max_ammo = 30
        self.reload_time = 1.35
        self.damage = 55
        self.bullet_speed = 120
        self.fire_rate = 0.095
        self.on_cooldown = False
        self.reloading = False

        self.barrel = Entity(parent=self, model='cube', scale=(.45, .35, 1.25), position=(0, 0, .2), texture=texture('metal'), color=color.dark_gray)
        self.handle = Entity(parent=self, model='cube', scale=(.25, .7, .25), position=(.12, -.28, -.25), rotation_x=-12, texture=texture('concrete'), color=color.black)
        self.muzzle_flash = Entity(parent=self, position=(0, 0, 0.9), world_scale=0.1, model='quad', color=color.yellow, enabled=False)

        self.crosshair = Entity(parent=camera.ui, model='quad', color=color.clear, scale=1)
        self.crosshair_parts = []
        for pos, sc in [((.025, 0), (.018, .003)), ((-.025, 0), (.018, .003)), ((0, .025), (.003, .018)), ((0, -.025), (.003, .018))]:
            self.crosshair_parts.append(Entity(parent=self.crosshair, model='quad', color=color.white, scale=sc, position=pos))

        for key, value in kwargs.items():
            setattr(self, key, value)

    def _play_shot_sound(self):
        try:
            # Minimum 5 punktów, bo część wersji Ursiny czyta volume_curve[4].
            ursfx(
                [
                    (0.00, 0.00),
                    (0.01, 0.95),
                    (0.05, 0.65),
                    (0.10, 0.25),
                    (0.16, 0.00),
                ],
                volume=uniform(0.55, 0.85),
                wave='square',
                pitch=uniform(-12, -10),
                pitch_change=-10,
                speed=3.0,
            )
        except Exception as exc:
            # Dźwięk nie może crashować całej gry.
            print(f'[weapon] Pomijam dźwięk strzału: {exc}')

    def shoot(self):
        if self.ammo <= 0:
            if not self.reloading:
                print_on_screen(TEXT['no_ammo'], position=(0, -.22), origin=(0, 0), duration=.8)
            return
        if self.on_cooldown or self.reloading:
            return

        self.on_cooldown = True
        self.ammo -= 1
        self.muzzle_flash.enabled = True
        self.muzzle_flash.scale = .1

        self._play_shot_sound()

        self.muzzle_flash.animate_scale(0.23, duration=0.04)
        invoke(self.muzzle_flash.disable, delay=0.045)

        original_pos = Vec3(self.position)
        self.animate_position(original_pos + Vec3(uniform(-0.015, 0.015), uniform(-0.015, 0.015), -0.08), duration=0.04, curve=curve.in_expo)
        self.animate_position(original_pos, duration=0.09, delay=0.04, curve=curve.out_expo)

        bullet = Entity(model='sphere', scale=0.065, color=color.yellow, position=camera.world_position + camera.forward * 1.3, collider='box')
        bullet.velocity = camera.forward * self.bullet_speed
        bullet.alive_time = 0
        bullet.ignore = (self, self.player)

        def bullet_update():
            bullet.position += bullet.velocity * time.dt
            bullet.alive_time += time.dt

            hit_info = bullet.intersects(ignore=bullet.ignore)
            if hit_info.hit:
                if hasattr(hit_info.entity, 'take_damage'):
                    hit_info.entity.take_damage(self.damage, camera.forward)
                marker = Entity(model='sphere', scale=.12, color=color.orange, position=hit_info.world_point)
                destroy(marker, delay=.12)
                destroy(bullet)
                return

            if bullet.alive_time > 2.4:
                destroy(bullet)

        bullet.update = bullet_update
        invoke(setattr, self, 'on_cooldown', False, delay=self.fire_rate)

    def reload(self):
        if self.ammo >= self.max_ammo or self.reloading:
            return
        self.reloading = True
        print_on_screen(TEXT['reload'], position=(0, -.18), origin=(0, 0), duration=self.reload_time)
        original_pos = Vec3(self.position)
        self.animate_position(original_pos + Vec3(0, -0.22, 0), duration=self.reload_time / 2, curve=curve.in_out_expo)
        self.animate_position(original_pos, duration=self.reload_time / 2, delay=self.reload_time / 2, curve=curve.in_out_expo)
        invoke(self.finish_reload, delay=self.reload_time)

    def finish_reload(self):
        self.ammo = self.max_ammo
        self.reloading = False

    def cleanup(self):
        if self.crosshair:
            destroy(self.crosshair)
        destroy(self)
