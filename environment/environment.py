from ursina import *

def setup_environment():
    # Ground
    ground = Entity(model='plane', collider='box', scale=256, texture='grass', texture_scale=(8, 8))

    # Add buildings
    for i in range(8):
        Entity(
            model='cube',
            origin_y=-.5,
            scale=2,
            texture='brick',
            texture_scale=(1, 2),
            x=random.uniform(-64, 64),
            z=random.uniform(-64, 64),
            collider='box',
            scale_y=random.uniform(2, 3),
            color=color.hsv(0, 0, random.uniform(.9, 1))
        )

    # Add obstacles
    for i in range(5):
        Entity(
            model='cube',
            origin_y=-.5,
            scale=(2, random.uniform(2, 4), 2),
            texture='brick',
            collider='box',
            position=(random.uniform(-64, 64), 0, random.uniform(-64, 64)),
        )

    # Add light
    DirectionalLight(y=10, color=color.white)

    # Remove Sky
    # Sky()  # Comment out or remove this line
