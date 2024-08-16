from ursina import *
from ursina.prefabs.ursfx import ursfx
from random import uniform

class Weapon(Entity):
    def __init__(self, player, **kwargs):
        super().__init__(**kwargs)
        self.player = player
        self.model = 'cube'  # Keeping the original model for now
        self.parent = camera
        self.position = (.5, -0.25, 0.25)
        self.scale = (0.3, 0.2, 1)
        self.origin_z = -0.5
        self.color = color.red
        self.on_cooldown = False
        self.muzzle_flash = Entity(parent=self, z=1, world_scale=0.5, model='quad', color=color.yellow, enabled=False)
        self.ammo = 30
        self.max_ammo = 30
        self.reload_time = 1.5
        self.reloading = False
        self.damage = 100  # Set damage to be enough to destroy the enemy in one hit

        # Create crosshair
        self.crosshair = Entity(parent=camera.ui, model='quad', color=color.white, scale=0.02, texture='white_cube')
        self.crosshair.texture = None
        self.crosshair.scale = (0.02, 0.002)
        self.crosshair.y = -0.02

        for i in range(4):
            part = Entity(parent=self.crosshair, model='quad', color=color.white, scale=(0.01, 0.002) if i % 2 == 0 else (0.002, 0.01), texture='white_cube')
            part.texture = None
            part.position = (0.015 if i == 0 else -0.015 if i == 1 else 0, 0.015 if i == 2 else -0.015 if i == 3 else 0)

    def shoot(self):
        if self.ammo > 0 and not self.on_cooldown:
            self.on_cooldown = True
            self.muzzle_flash.enabled = True
            ursfx(
                [(0.0, 0.0), (0.1, 0.9), (0.15, 0.75), (0.3, 0.14), (0.6, 0.0)],
                volume=uniform(0.4, 0.6), wave='noise', pitch=uniform(-13, -12),
                pitch_change=-12, speed=3.0
            )
            invoke(self.muzzle_flash.disable, delay=0.05)
            invoke(setattr, self, 'on_cooldown', False, delay=0.15)

            # Apply recoil
            self.animate('position', self.position + Vec3(0, 0, -0.1), duration=0.05, curve=curve.linear)
            self.animate('position', self.position, duration=0.1, delay=0.05, curve=curve.linear)

            # Create the bullet
            bullet = Entity(
                model='sphere', scale=(0.1, 0.1, 0.1), color=color.yellow,
                position=self.world_position + self.forward * 1.5,
                collider='box'
            )
            bullet.velocity = self.player.camera_pivot.forward * 100  # Increased bullet speed
            bullet.gravity = 9.8
            bullet.bounciness = 0.9
            bullet.alive_time = 0

            def bullet_update():
                bullet.velocity.y -= bullet.gravity * time.dt
                bullet.position += bullet.velocity * time.dt
                bullet.alive_time += time.dt

                # Handle bouncing off surfaces
                hit_info = bullet.intersects()
                if hit_info.hit:
                    normal = hit_info.world_normal
                    bullet.velocity = self.reflect(bullet.velocity, normal) * bullet.bounciness

                # Check for collision with enemies
                if hit_info.hit and hasattr(hit_info.entity, 'take_damage'):
                    hit_info.entity.take_damage(self.damage, self.forward)
                    destroy(bullet)

                # Destroy bullet after 5 seconds
                if bullet.alive_time > 5:
                    destroy(bullet)

            bullet.update = bullet_update
            self.ammo -= 1

    def reload(self):
        if self.ammo < self.max_ammo and not self.reloading:
            self.reloading = True
            print_on_screen("Reloading...", position=(0, 0), origin=(0, 0), duration=self.reload_time)
            self.animate('position', self.position + Vec3(0, -0.2, 0), duration=self.reload_time / 2, curve=curve.linear)
            self.animate('position', self.position, duration=self.reload_time / 2, delay=self.reload_time / 2, curve=curve.linear)
            invoke(self.finish_reload, delay=self.reload_time)

    def finish_reload(self):
        self.ammo = self.max_ammo
        self.reloading = False

    def update_ui(self, health_text, ammo_text):
        health_text.text = f'HP: {self.player.hp}'
        ammo_text.text = f'Ammo: {self.ammo}/{self.max_ammo}'

    def reflect(self, vector, normal):
        return vector - 2 * vector.dot(normal) * normal
