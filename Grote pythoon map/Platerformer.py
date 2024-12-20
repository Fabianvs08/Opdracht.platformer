import pygame
import random
from os import listdir
from os.path import isfile, join

# Initialize pygame
pygame.init()

# Game settings
pygame.display.set_caption("Platformer")
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
ENEMY_VEL = 3  # Speed of the enemies

# Create the game window
window = pygame.display.set_mode((WIDTH, HEIGHT))


# Function to flip sprite images horizontally
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


# Function to load sprite sheets
def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


# Function to get block image for terrain
def get_block(size):
    path = join("assets", "Terrain", "MosterdGras.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(image)


# Player class with movement, animations, etc.
class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


# Object class for generic game objects (used for fire traps, blocks, etc.)
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


# Block class for terrain (e.g. ground)
class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


# Fire trap class for hazards
class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

# Finish flag class
class Flag(Object):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "finish")
        self.image = pygame.image.load(join("assets", "Finish", "FinishLine.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (width, height))
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, win, offset_x):
        super().draw(win, offset_x)


# Moving enemy class
class MovingEnemy(Object):
    def __init__(self, x, y, width, height, speed):
        super().__init__(x, y, width, height, "enemy")
        self.image = pygame.image.load(join("assets", "Enemies", "VoetenGoomba.png")).convert_alpha()
        self.image = pygame.transform.scale(self.image, (width, height))
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = speed
        self.direction = random.choice([-1, 1])  # Enemy moves left or right randomly

    def move(self):
        self.rect.x += self.direction * self.speed
        if self.rect.x <= 0 or self.rect.x >= WIDTH - self.width:
            self.direction *= -1

    def draw(self, win, offset_x):
        super().draw(win, offset_x)
        self.move()


# Function to get background images
def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


# Function to draw everything in the game (background, objects, player)
def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()


# Collision handling
def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


# Handle player movement based on key presses and collisions
def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()


# Start screen for the game
def start_screen(window):
    window.fill((0, 0, 0))  # Black background
    font = pygame.font.SysFont("comicsans", 100)
    text = font.render("Ninja Frog", True, (255, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
    
    font_small = pygame.font.SysFont("comicsans", 50)
    instructions = font_small.render("Press any key to start", True, (255, 255, 255))
    window.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT // 2))
    
    clock = pygame.time.Clock()
    color_toggle = True
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                return

        color_toggle = not color_toggle
        text = font.render("Ninja Frog", True, (0, 255, 0) if color_toggle else (255, 0, 0))
        window.fill((0, 0, 0))  # Clear screen
        window.blit(text, text_rect)
        window.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT // 2))
        pygame.display.update()
        clock.tick(2)  # Flashing effect

# Game Over screen function
def game_end(window):
    font = pygame.font.SysFont("Arial", 40)
    text = font.render("Game Over! Press any key to restart", True, (255, 0, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    window.fill((0, 0, 0))
    window.blit(text, text_rect)
    pygame.display.update()

    # Wait for user to press any key to restart or quit
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
                return True  # Restart the game

# You Win screen function
def you_win(window):
    font = pygame.font.SysFont("Arial", 40)
    text = font.render("You Win! Press any key to restart", True, (0, 255, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    window.fill((0, 0, 0))
    window.blit(text, text_rect)
    pygame.display.update()

    # Wait for user to press any key to restart or quit
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
                return True  # Restart the game

# Main game loop function
def main(window):
    start_screen(window)  # Show the start screen before starting the game

    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    block_size = 96

    # Create player and objects
    player = Player(100, 100, 50, 50)
    fire_trap1 = Fire(300, HEIGHT - block_size - 64, 16, 32)
    fire_trap1.on()
    fire_hits = 0
    fire_trap2 = Fire(650, HEIGHT - block_size - 64, 16, 32)
    fire_trap2.on()
    fire_hits = 0
    fire_trap3 = Fire(1500, HEIGHT - block_size - 64, 16, 32)
    fire_trap3.on()
    fire_hits = 0
    fire_trap4 = Fire(1950, HEIGHT - block_size - 64, 16, 32)
    fire_trap4.on()
    fire_hits = 0
    
    hole_start_index = 13  # Index where the hole begins
    hole_width = 2  # Width of the hole in blocks

    floor = [
    Block(i * block_size, HEIGHT - block_size, block_size)
    for i in range(-WIDTH // block_size, (WIDTH * 3) // block_size)
    if i < hole_start_index or i >= hole_start_index + hole_width  # Skip blocks for the hole
]

    platforms = [
        Block(block_size * 5, HEIGHT - block_size * 3, block_size),
        Block(block_size * 7, HEIGHT - block_size * 4, block_size),
        Block(block_size * 10, HEIGHT - block_size * 5, block_size),
        Block(block_size * 0, HEIGHT - block_size * 2, block_size),
        Block(block_size * 0, HEIGHT - block_size * 3, block_size),
        Block(block_size * 0, HEIGHT - block_size * 4, block_size),
        Block(block_size * 0, HEIGHT - block_size * 3, block_size),
        Block(block_size * 0, HEIGHT - block_size * 4, block_size),
        Block(block_size * 0, HEIGHT - block_size * 5, block_size),
        Block(block_size * 0, HEIGHT - block_size * 6, block_size),
        Block(block_size * 0, HEIGHT - block_size * 7, block_size),
        Block(block_size * 0, HEIGHT - block_size * 8, block_size),
        Block(block_size * 0, HEIGHT - block_size * 9, block_size),
        Block(block_size * 0, HEIGHT - block_size * 10, block_size),
        Block(block_size * 21, HEIGHT - block_size * 2, block_size),
        Block(block_size * 22, HEIGHT - block_size * 2, block_size),
        Block(block_size * 22, HEIGHT - block_size * 2, block_size),
        Block(block_size * 23, HEIGHT - block_size * 3, block_size),
        Block(block_size * 23, HEIGHT - block_size * 3, block_size),
        Block(block_size * 24, HEIGHT - block_size * 4, block_size),
        Block(block_size * 24, HEIGHT - block_size * 5, block_size),
        Block(block_size * 23, HEIGHT - block_size * 2, block_size),
        Block(block_size * 24, HEIGHT - block_size * 2, block_size),
        Block(block_size * 24, HEIGHT - block_size * 3, block_size),
        Block(block_size * 25, HEIGHT - block_size * 2, block_size),
        Block(block_size * 25, HEIGHT - block_size * 3, block_size),
        Block(block_size * 25, HEIGHT - block_size * 4, block_size),
        Block(block_size * 25, HEIGHT - block_size * 5, block_size),
        Block(block_size * 26, HEIGHT - block_size * 2, block_size),
        Block(block_size * 26, HEIGHT - block_size * 3, block_size),
        Block(block_size * 27, HEIGHT - block_size * 2, block_size),
        Block(block_size * 31, HEIGHT - block_size * 2, block_size),
        Block(block_size * 31, HEIGHT - block_size * 3, block_size),
        Block(block_size * 31, HEIGHT - block_size * 4, block_size),
        Block(block_size * 31, HEIGHT - block_size * 5, block_size),
        Block(block_size * 31, HEIGHT - block_size * 6, block_size),
        Block(block_size * 31, HEIGHT - block_size * 7, block_size),
    ]
    finish_line = Flag(WIDTH - -1900, HEIGHT - block_size - 100, 50, 100)
    
    # Number of enemies to spawn
    num_enemies = 20  # You can change this to any number

    # List to store enemies
    enemies = []

    # Create multiple enemies
    for _ in range(num_enemies):
        x_position = random.randint(500, 800)  # Random x position
        y_position = HEIGHT - block_size - 32  # Position just above the ground
        speed = ENEMY_VEL  # Use the defined enemy velocity
        enemy = MovingEnemy(x_position, y_position, 32, 32, speed)
        enemies.append(enemy)

    objects = [*floor, *platforms, fire_trap1, fire_trap2, fire_trap3, fire_trap4, finish_line, *enemies]  # Add enemies to the objects list


    offset_x = 0 
    scroll_area_width = 200

    run = True
    while run:
        clock.tick(FPS)

        # Check collision with fire trap
        if player.rect.colliderect(fire_trap1.rect):
            fire_hits += 1
            fire_trap1.on()
            if fire_hits >= 2:
                print("you hit the fire!")
                game_end(window)
                run = False

        # Check collision with fire trap
        if player.rect.colliderect(fire_trap2.rect):
            fire_hits += 1
            fire_trap2.on()
            if fire_hits >= 2:
                print("you hit the fire!")
                game_end(window)
                run = False

        # Check collision with fire trap
        if player.rect.colliderect(fire_trap2.rect):
            fire_hits += 1
            fire_trap3.on()
            if fire_hits >= 2:
                print("you hit the fire!")
                game_end(window)
                run = False

        # Check collision with fire trap
        if player.rect.colliderect(fire_trap2.rect):
            fire_hits += 1
            fire_trap4.on()
            if fire_hits >= 2:
                print("you hit the fire!")
                game_end(window)
                run = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        fire_trap1.loop()
        fire_trap2.loop()
        fire_trap3.loop()
        fire_trap4.loop()
        for enemy in enemies:
            enemy.move()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        # Camera scrolling
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

        # Check if player has reached the finish line
        if player.rect.colliderect(finish_line.rect):
            print("You reached the finish line!")
            if you_win(window):  # Trigger You Win screen and restart if the user presses a key
                main(window)
                run = False

        # Check if player hits any enemy
        for enemy in enemies:
            if pygame.sprite.collide_mask(player, enemy):
                print("You were hit by an enemy!")
                run = False
                break

        if not run:
            if game_end(window):
                main(window)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)

