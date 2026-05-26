from __future__ import annotations

from math import sin, pi
from random import uniform

from ursina import *
from ursina.prefabs.ursfx import ursfx


class ImpactEffect(Entity):
    def __init__(self, position, normal=None, **kwargs):
        super().__init__(
            model='sphere',
            position=position,
            scale=0.08,
            color=color.rgba(255, 170, 30, 220),
            collider=None,
            **kwargs
        )

        self.lifetime = 0.12
        self.timer = self.lifetime

        self.normal = Vec3(normal) if normal is not None else Vec3(0, 1, 0)

    def update(self):
        self.timer -= time.dt

        progress = max(self.timer / self.lifetime, 0)

        self.scale = Vec3(1, 1, 1) * (0.08 + (1 - progress) * 0.22)
        self.color = color.rgba(255, 170, 30, int(220 * progress))

        if self.timer <= 0:
            destroy(self)


class BulletTracer(Entity):
    """
    Krótka smuga strzału.
    To NIE jest fizyczny pocisk, tylko efekt wizualny po raycaście.
    Dzięki temu nie ma żółtych kulek stojących w miejscu.
    """

    def __init__(self, start, end, **kwargs):
        self.start = Vec3(start)
        self.end = Vec3(end)

        direction = self.end - self.start
        distance = max(direction.length(), 0.01)

        super().__init__(
            model='cube',
            position=self.start + direction * 0.5,
            scale=(0.025, 0.025, distance),
            color=color.rgba(255, 235, 80, 190),
            collider=None,
            **kwargs
        )

        self.look_at(self.end)

        self.lifetime = 0.055
        self.timer = self.lifetime

    def update(self):
        self.timer -= time.dt

        progress = max(self.timer / self.lifetime, 0)

        self.color = color.rgba(255, 235, 80, int(190 * progress))

        # smuga szybko się skraca, żeby nie zostawał syf na mapie
        self.scale = Vec3(
            max(0.005, 0.025 * progress),
            max(0.005, 0.025 * progress),
            max(0.01, self.scale_z * 0.86),
        )

        if self.timer <= 0:
            destroy(self)


class Weapon(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)

        self.player = player
        self.parent = camera

        self.base_position = Vec3(0.5, -0.25, 0.25)
        self.position = self.base_position

        self.scale = (0.22, 0.1, 0.55)
        self.origin_z = -0.5
        self.model = 'cube'
        self.color = color.gray
        self.collider = None

        self.ammo = 30
        self.max_ammo = 30

        self.damage = 55
        self.range = 130

        self.fire_rate = 0.095
        self.cooldown_timer = 0

        self.reload_time = 1.35
        self.reload_timer = 0
        self.reloading = False

        self.recoil_timer = 0
        self.recoil_duration = 0.09
        self.recoil_offset = Vec3(0, 0, 0)

        self.muzzle_timer = 0

        self.barrel = Entity(
            parent=self,
            model='cube',
            scale=(0.45, 0.35, 1.25),
            position=(0, 0, 0.2),
            color=color.dark_gray,
            collider=None,
        )

        self.handle = Entity(
            parent=self,
            model='cube',
            scale=(0.25, 0.7, 0.25),
            position=(0.12, -0.28, -0.25),
            rotation_x=-12,
            color=color.black,
            collider=None,
        )

        self.muzzle_flash = Entity(
            parent=self,
            position=(0, 0, 0.95),
            model='quad',
            scale=0.001,
            color=color.rgba(255, 220, 40, 0),
            collider=None,
        )

        self.crosshair = Entity(
            parent=camera.ui,
            model='quad',
            color=color.clear,
            scale=1,
            collider=None,
        )

        self.crosshair_parts = []

        for pos, sc in [
            ((0.025, 0), (0.018, 0.003)),
            ((-0.025, 0), (0.018, 0.003)),
            ((0, 0.025), (0.003, 0.018)),
            ((0, -0.025), (0.003, 0.018)),
        ]:
            self.crosshair_parts.append(
                Entity(
                    parent=self.crosshair,
                    model='quad',
                    color=color.white,
                    scale=sc,
                    position=pos,
                    collider=None,
                )
            )

        for key, value in kwargs.items():
            setattr(self, key, value)

    def update(self):
        self._update_cooldown()
        self._update_reload()
        self._update_recoil()
        self._update_muzzle_flash()

    def _update_cooldown(self):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= time.dt

        if self.cooldown_timer < 0:
            self.cooldown_timer = 0

    def _update_reload(self):
        if not self.reloading:
            return

        self.reload_timer -= time.dt

        progress = 1 - max(self.reload_timer / self.reload_time, 0)
        reload_drop = -0.22 * sin(progress * pi)

        target_position = self.base_position + Vec3(0, reload_drop, 0)
        self.position = self.position + (target_position - self.position) * min(time.dt * 16, 1)

        if self.reload_timer <= 0:
            self.finish_reload()

    def _update_recoil(self):
        if self.reloading:
            return

        if self.recoil_timer > 0:
            self.recoil_timer -= time.dt
            progress = max(self.recoil_timer / self.recoil_duration, 0)

            target_position = self.base_position + self.recoil_offset * progress
            self.position = self.position + (target_position - self.position) * min(time.dt * 24, 1)
        else:
            self.position = self.position + (self.base_position - self.position) * min(time.dt * 18, 1)

    def _update_muzzle_flash(self):
        if self.muzzle_timer > 0:
            self.muzzle_timer -= time.dt

            progress = max(self.muzzle_timer / 0.045, 0)
            self.muzzle_flash.scale = 0.12 + 0.16 * progress
            self.muzzle_flash.color = color.rgba(255, 220, 40, int(240 * progress))
        else:
            self.muzzle_flash.scale = 0.001
            self.muzzle_flash.color = color.rgba(255, 220, 40, 0)

    def _play_shot_sound(self):
        try:
            ursfx(
                [
                    (0.00, 0.00),
                    (0.01, 0.95),
                    (0.05, 0.65),
                    (0.10, 0.25),
                    (0.16, 0.00),
                ],
                volume=uniform(0.42, 0.68),
                wave='square',
                pitch=uniform(-12, -10),
                pitch_change=-10,
                speed=3.0,
            )
        except Exception as exc:
            print(f'[weapon] Pomijam dźwięk strzału: {exc}')

    def _get_ignore_list(self):
        ignore = [
            self,
            self.player,
            self.barrel,
            self.handle,
            self.muzzle_flash,
        ]

        # Jak player ma jakieś dzieci/collidery, ignorujemy też je.
        try:
            ignore.extend(self.player.children)
        except Exception:
            pass

        return ignore

    def _apply_damage(self, entity, direction):
        target = entity

        # Czasem trafiasz w dziecko obiektu, więc idziemy po parentach.
        for _ in range(8):
            if target is None:
                return False

            if hasattr(target, 'take_damage'):
                try:
                    target.take_damage(self.damage, direction)
                except TypeError:
                    target.take_damage(self.damage)

                return True

            target = getattr(target, 'parent', None)

        return False

    def shoot(self):
        if self.reloading:
            return

        if self.cooldown_timer > 0:
            return

        if self.ammo <= 0:
            print_on_screen(
                'Brak ammo — R żeby przeładować',
                position=(0, -0.22),
                origin=(0, 0),
                duration=0.8,
            )
            return

        self.cooldown_timer = self.fire_rate
        self.ammo -= 1

        self._play_shot_sound()

        self.muzzle_timer = 0.045

        self.recoil_timer = self.recoil_duration
        self.recoil_offset = Vec3(
            uniform(-0.012, 0.012),
            uniform(-0.010, 0.010),
            -0.09,
        )

        start = camera.world_position + camera.forward * 1.15
        direction = camera.forward.normalized()

        hit = raycast(
            start,
            direction,
            distance=self.range,
            ignore=self._get_ignore_list(),
            debug=False,
        )

        if hit.hit:
            end = hit.world_point

            if hit.entity is not None:
                self._apply_damage(hit.entity, direction)

            ImpactEffect(end, getattr(hit, 'world_normal', None))
        else:
            end = start + direction * self.range

        # Profesjonalniejszy FPS-owy efekt: krótka smuga, nie żółta piłka.
        BulletTracer(start, end)

    def reload(self):
        if self.reloading:
            return

        if self.ammo >= self.max_ammo:
            return

        self.reloading = True
        self.reload_timer = self.reload_time

        print_on_screen(
            'Przeładowanie...',
            position=(0, -0.18),
            origin=(0, 0),
            duration=self.reload_time,
        )

    def finish_reload(self):
        self.ammo = self.max_ammo
        self.reloading = False
        self.reload_timer = 0
        self.position = self.base_position

    def cleanup(self):
        if self.crosshair:
            destroy(self.crosshair)

        destroy(self)