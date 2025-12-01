import pygame
import random
import sys
import math
import os

# ----- Settings -----
WIDTH, HEIGHT = 800, 450
FPS = 60

GRAVITY = 0.6
JUMP_VELOCITY = -15
GROUND_HEIGHT = 32
PLAYER_SPEED = 4

CUBE_W = 72
CUBE_H = 72
COIN_W = 36
COIN_H = 36

# Score / health
SCORE_CORRECT = 10
SCORE_WRONG = -5
SCORE_COIN = 5
MAX_LIVES = 3
LEVEL_TIME = 30  # seconds per level

# Combo
COMBO_RESET_TIME = 3.0  # seconds without correct hit to reset combo

# Colors
BG = (30, 30, 40)
PLAYER_COLOR = (240, 230, 140)
CUBE_COLOR = (80, 150, 220)
COIN_COLOR = (250, 220, 50)
TEXT_COLOR = (230, 230, 230)
NAME_COLOR = (255, 255, 0)
HIGHLIGHT_COLOR = (255, 215, 0)
CORRECT_COLOR = (80, 220, 100)
WRONG_COLOR = (220, 80, 80)
PUFF_COLOR = (200, 200, 200)

pygame.init()
pygame.font.init()

# fonts
FONT_BIG = pygame.font.SysFont(None, 64)
FONT_MED = pygame.font.SysFont(None, 36)
FONT_SMALL = pygame.font.SysFont(None, 24)

pygame.mixer.init()

pygame.mixer.music.load("bg_music.mp3")  
pygame.mixer.music.set_volume(0.3)  
pygame.mixer.music.play(-1)  

jump_sfx = pygame.mixer.Sound("jump.mp3")
walk_sfx = pygame.mixer.Sound("walk.mp3")
score_sfx = pygame.mixer.Sound("coin.mp3")
game_over_sfx = pygame.mixer.Sound("gameover.mp3")

jump_sfx.set_volume(0.4)
walk_sfx.set_volume(0.9)
score_sfx.set_volume(0.7)
game_over_sfx.set_volume(0.6)



BASE_DIR = os.path.dirname(__file__)

SKY_BG = pygame.image.load("sky.png")
FAR_GROUND = pygame.image.load("far-grounds.png")
GROUND_TILE = pygame.image.load("platform1.png")
CLOUD = pygame.image.load("clouds.png")


print("All images loaded successfully!")




# ----- Animation Helper -----
class Animation:
    def __init__(self, image_paths=None, sprite_sheet=None, frame_width=16, frame_height=16,
                 frame_count=1, frame_time=0.15, scale=1.0, row=0):
        self.frames = []
        self.frame_time = frame_time
        self.current_time = 0.0
        self.current_frame = 0
        self.scale = scale

        if image_paths:
            for path in image_paths:
                frame = pygame.image.load(path).convert_alpha()
                if scale != 1.0:
                    frame = pygame.transform.scale(
                        frame,
                        (int(frame.get_width() * scale), int(frame.get_height() * scale))
                    )
                self.frames.append(frame)
        elif sprite_sheet:
            sheet = pygame.image.load(sprite_sheet).convert_alpha()
            for i in range(frame_count):
                frame_rect = pygame.Rect(
                    i * frame_width,
                    row * frame_height,
                    frame_width,
                    frame_height
                )
                frame = sheet.subsurface(frame_rect)
                if scale != 1.0:
                    frame = pygame.transform.scale(
                        frame,
                        (int(frame_width * scale), int(frame_height * scale))
                    )
                self.frames.append(frame)

    def update(self, dt):
        self.current_time += dt
        if self.current_time >= self.frame_time:
            self.current_time = 0.0
            self.current_frame = (self.current_frame + 1) % len(self.frames)

    def get_frame(self):
        return self.frames[self.current_frame]

# ----- Player Class -----
class Player:
    def __init__(self, x, ground_y, w=32, h=32):
        self.scale_x = 1   # width scale
        self.scale_y = 2.5   # height scale

        self.frame_w = w
        self.frame_h = h
        self.display_w = int(self.frame_w * self.scale_x)
        self.display_h = int(self.frame_h * self.scale_y)
        self.collision_h = int(self.display_h * 0.5)

        self.rect = pygame.Rect(x, ground_y - self.collision_h, self.display_w, self.collision_h)
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_right = True
        self.ground_y = ground_y

        # Jump control
        self.holding_jump = False
        self.max_jump_time = 0.25
        self.jump_time = 0.0

        # Animations
        self.animations = {
            "idle": Animation(image_paths=["tile000.png","tile001.png","tile002.png","tile003.png"],
                              frame_time=0.2, scale=self.scale_y),
            "jump": Animation(image_paths=["tile000.png"],
                              frame_time=0.15, scale=self.scale_y)
        }
        self.current_anim = self.animations["idle"]

    def update(self, keys, dt, speed_mult=1.0):
        # Horizontal movement
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= int(PLAYER_SPEED * speed_mult)
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += int(PLAYER_SPEED * speed_mult)
            self.facing_right = True
        
        if abs(self.vel_y) > 0 and self.on_ground:
            if not pygame.mixer.Channel(1).get_busy():  
                pygame.mixer.Channel(1).play(walk_sfx)

        # Variable jump height
        if self.holding_jump and self.jump_time < self.max_jump_time:
            self.vel_y += GRAVITY * -0.5
            self.jump_time += dt

        # Apply gravity
        self.vel_y += GRAVITY
        self.rect.y += int(self.vel_y)

        # Ground collision
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            self.vel_y = 0
            self.on_ground = True
            self.holding_jump = False
            self.jump_time = 0.0
        else:
            self.on_ground = False

        # Clamp horizontal
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))

        # Animation
        if not self.on_ground:
            self.current_anim = self.animations["jump"]
        else:
            self.current_anim = self.animations["idle"]
        self.current_anim.update(dt)

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_VELOCITY
            self.on_ground = False
            self.holding_jump = True
            self.jump_time = 0.0
            return True
        return False

    def release_jump(self):
        self.holding_jump = False

    def draw(self, surf):
        frame = self.current_anim.get_frame()
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        draw_y = self.rect.bottom - frame.get_height() + 8  # adjust +5 downwards
        surf.blit(frame, (self.rect.x, draw_y))

# ----- Puff, AnswerCube, Coin, FloatingText classes remain the same -----
# (Copy them from your previous code; nothing changes for these)
class Puff:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 6
        self.alpha = 220
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(-1.2, -0.6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.radius += 0.6
        self.alpha -= 6
        return self.alpha > 0

    def draw(self, surf):
        if self.alpha <= 0:
            return
        s = pygame.Surface((int(self.radius*2), int(self.radius*2)), pygame.SRCALPHA)
        color = (PUFF_COLOR[0], PUFF_COLOR[1], PUFF_COLOR[2], max(0,int(self.alpha)))
        pygame.draw.circle(s, color, (int(self.radius), int(self.radius)), int(self.radius))
        surf.blit(s, (self.x - self.radius, self.y - self.radius))


class AnswerCube:
    def __init__(self, x, base_y, value, correct=False, float_amp=20, float_speed=1.2, phase=0.0):
        self.w = CUBE_W
        self.h = CUBE_H
        self.base_x = x
        self.base_y = base_y
        self.rect = pygame.Rect(x, base_y - self.h, self.w, self.h)
        self.value = value
        self.correct = correct
        self.float_amp = float_amp
        self.float_speed = float_speed
        self.phase = phase
        self.flash_alpha = 0

    def update(self, t):
        offset = math.sin(t * self.float_speed + self.phase) * self.float_amp
        self.rect.y = self.base_y + int(offset) - self.h
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 12)

    def flash(self):
        self.flash_alpha = 200

    def draw(self, surf, font):
        cube_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.rect(cube_surf, CUBE_COLOR, (0,0,self.w,self.h), border_radius=6)
        if self.flash_alpha > 0:
            overlay = pygame.Surface((self.w,self.h), pygame.SRCALPHA)
            overlay.fill((255,255,255,int(self.flash_alpha)))
            cube_surf.blit(overlay, (0,0))
        surf.blit(cube_surf, (self.rect.x, self.rect.y))
        txt = font.render(str(self.value), True, TEXT_COLOR)
        txt_rect = txt.get_rect(center=(self.rect.centerx, self.rect.top - 20))
        surf.blit(txt, txt_rect)


class Coin:
    def __init__(self, x, y, float_amp=15, float_speed=2.0, phase=0.0):
        self.w = COIN_W
        self.h = COIN_H
        self.base_x = x
        self.base_y = y
        self.rect = pygame.Rect(x, y - self.h, self.w, self.h)
        self.float_amp = float_amp
        self.float_speed = float_speed
        self.phase = phase

    def update(self, t):
        offset = math.sin(t * self.float_speed + self.phase) * self.float_amp
        self.rect.y = self.base_y + int(offset) - self.h

    def draw(self, surf):
        pygame.draw.ellipse(surf, COIN_COLOR, self.rect)


class FloatingText:
    def __init__(self, x, y, text, color, lifetime=1.0):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = lifetime
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        self.y -= 30 * dt
        return self.age < self.lifetime

    def draw(self, surf, font):
        alpha = int(255 * max(0, (1 - self.age/self.lifetime)))
        txt_surf = font.render(self.text, True, self.color)
        txt_surf.set_alpha(alpha)
        surf.blit(txt_surf, (self.x, self.y))

# ----- Helpers -----
def draw_text(surf, text, font, x, y, center=False, color=TEXT_COLOR, alpha=255):
    txt_surf = font.render(text, True, color)
    if alpha < 255:
        txt_surf = txt_surf.convert_alpha()
        txt_surf.set_alpha(alpha)
    r = txt_surf.get_rect()
    if center:
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    surf.blit(txt_surf, r)
    return r

# ----- Level definitions -----
def generate_levels():
    return [
        ("3 + 5 = ?", 8, [6, 9, 10]),
        ("7 * 2 = ?", 14, [12, 15, 13]),
        ("10 - 4 = ?", 6, [5, 7, 8]),
    ]

# ----- Level Setup -----
def setup_level(levels, idx):
    eq_text, correct, wrongs = levels[idx]
    answers = [correct] + wrongs[:]
    random.shuffle(answers)

    # Lower cubes near the ground
    cube_y = HEIGHT - GROUND_HEIGHT - CUBE_H - 50
    spacing = WIDTH // (len(answers) + 1)
    cubes = []
    for i, a in enumerate(answers):
        x = spacing * (i + 1) - CUBE_W // 2
        phase = random.uniform(0, math.pi*2)
        cubes.append(AnswerCube(x, cube_y, a, correct=(a==correct),
                                float_amp=18, float_speed=1.6, phase=phase))

    # Coins floating just above the ground
    coins = []
    coin_base_y = HEIGHT - GROUND_HEIGHT - 20
    for i in range(3):
        cx = random.randint(50, WIDTH-50)
        phase = random.uniform(0, math.pi*2)
        coins.append(Coin(cx, coin_base_y, float_amp=15, float_speed=2.0, phase=phase))

    return eq_text, cubes, correct, coins

# ----- Game Loop -----
def game_loop(screen, clock):
    ground_y = HEIGHT - GROUND_HEIGHT
    levels = generate_levels()
    current_level = 0
    score = 0
    lives = MAX_LIVES
    timer = LEVEL_TIME
    combo = 0
    combo_timer = 0.0

    player = Player(120, ground_y)
    puffs = []
    floating_texts = []

    equation_text, cubes, correct_answer, coins = setup_level(levels, current_level)

    show_level_intro = True
    level_intro_timer = 0.0

    t0 = pygame.time.get_ticks() / 1000.0
    game_over = False
    win = False

    cloud_offset = 0
    far_ground_offset = 0

    sky_scroll = 0
    cloud_scroll = 0
    far_ground_scroll = 0

    sky_speed = 0.2
    cloud_speed = 0.4
    far_ground_speed = 0.8

    while True:
        dt_ms = clock.tick(FPS)
        dt = dt_ms / 1000.0
        t = pygame.time.get_ticks() / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "exit"
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    if player.jump():
                        jump_sfx.play()
                        for _ in range(3):
                            puffs.append(Puff(player.rect.centerx + random.randint(-8,8),
                                              player.rect.bottom - 6))
                if event.key == pygame.K_r and (game_over or win):
                    return "restart"
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    player.release_jump()

        keys = pygame.key.get_pressed()
        if not game_over and not win:
            player.update(keys, dt)

        # Update puffs
        puffs = [p for p in puffs if p.update()]
        # Update cubes
        for c in cubes:
            c.update(t)
        # Update coins
        for c in coins:
            c.update(t)
        # Update floating texts
        floating_texts = [f for f in floating_texts if f.update(dt)]

        # Countdown timer
        if not show_level_intro and not game_over and not win:
            timer -= dt
            if timer <= 0:
                lives -= 1
                if lives <= 0:
                    game_over = True
                else:
                    player = Player(120, ground_y)
                    equation_text, cubes, correct_answer, coins = setup_level(levels, current_level)
                    timer = LEVEL_TIME
                    combo = 0
                    combo_timer = 0.0

        # Combo timer decay
        if combo > 0:
            combo_timer += dt
            if combo_timer >= COMBO_RESET_TIME:
                combo = 0
                combo_timer = 0.0

        # Collision detection - cubes
        if not game_over and not win and not show_level_intro:
            for c in cubes:
                if player.rect.colliderect(c.rect):
                    if c.correct:
                        c.flash()
                        combo += 1
                        combo_timer = 0.0
                        gained = SCORE_CORRECT * combo
                        score += gained
                        score_sfx.play()
                        floating_texts.append(FloatingText(player.rect.centerx,
                                                           player.rect.top,
                                                           f"+{gained} x{combo}",
                                                           CORRECT_COLOR))
                        current_level += 1
                        if current_level >= len(levels):
                            win = True
                        else:
                            player = Player(120, ground_y)
                            equation_text, cubes, correct_answer, coins = setup_level(levels, current_level)
                            timer = LEVEL_TIME
                            show_level_intro = True
                            level_intro_timer = 0.0
                    else:
                        lives -= 1
                        score += SCORE_WRONG
                        floating_texts.append(FloatingText(player.rect.centerx,
                                                           player.rect.top,
                                                           f"{SCORE_WRONG}",
                                                           WRONG_COLOR))
                        combo = 0
                        combo_timer = 0.0
                        if lives <= 0:
                            game_over = True
                        else:
                            player = Player(120, ground_y)
                            equation_text, cubes, correct_answer, coins = setup_level(levels, current_level)
                            timer = LEVEL_TIME
                    break

        # Collision detection - coins
        for coin in coins[:]:
            if player.rect.colliderect(coin.rect):
                score_sfx.play()
                score += SCORE_COIN
                floating_texts.append(FloatingText(player.rect.centerx,
                                                   player.rect.top,
                                                   f"+{SCORE_COIN}",
                                                   HIGHLIGHT_COLOR))
                coins.remove(coin)

        # Level intro
        if show_level_intro:
            level_intro_timer += dt
            if level_intro_timer > 1.0:
                show_level_intro = False

        # --- Draw everything ---
        # --- Parallax Background ---
        # Update scrolling offsets
        sky_scroll = (sky_scroll - sky_speed) % WIDTH
        cloud_scroll = (cloud_scroll - cloud_speed) % WIDTH
        far_ground_scroll = (far_ground_scroll - far_ground_speed) % WIDTH

        # --- Scale backgrounds to fit screen width ---
        sky_height = 750  # pixels tall — try smaller or larger
        sky_scaled = pygame.transform.scale(SKY_BG, (WIDTH, sky_height))
        cloud_scaled = pygame.transform.scale(CLOUD, (WIDTH, CLOUD.get_height()))
        far_ground_scaled = pygame.transform.scale(FAR_GROUND, (WIDTH, FAR_GROUND.get_height()))

        # --- Draw Sky ---
        screen.blit(sky_scaled, (-sky_scroll, 0))
        screen.blit(sky_scaled, (WIDTH - sky_scroll, 0))

        # --- Draw Clouds ---
        cloud_y = 70
        screen.blit(cloud_scaled, (-cloud_scroll, cloud_y))
        screen.blit(cloud_scaled, (WIDTH - cloud_scroll, cloud_y))

        # --- Draw Far Ground ---
        far_ground_y = HEIGHT - GROUND_HEIGHT - far_ground_scaled.get_height()
        screen.blit(far_ground_scaled, (-far_ground_scroll, far_ground_y))
        screen.blit(far_ground_scaled, (WIDTH - far_ground_scroll, far_ground_y))

        # --- Draw tiled platform ground ---
        tile_w, tile_h = GROUND_TILE.get_size()
        overlap = 1
        tile_w, tile_h = GROUND_TILE.get_size()
        overlap = 8  # Try 1 or 2 pixels
        for x in range(0, WIDTH, tile_w - overlap):
            screen.blit(GROUND_TILE, (x, HEIGHT - tile_h))



        # Puffs
        for puff in puffs:
            puff.draw(screen)
        # Coins
        for coin in coins:
            coin.draw(screen)
        # Player
        player.draw(screen)
        # Cubes
        for c in cubes:
            c.draw(screen, FONT_SMALL)
        # Floating texts
        for ft in floating_texts:
            ft.draw(screen, FONT_SMALL)

        # HUD
        draw_text(screen, f"Score: {score}", FONT_MED, 12, 8)
        draw_text(screen, f"Lives: {lives}", FONT_MED, WIDTH - 120, 8)
        draw_text(screen, f"Time: {int(timer)}s", FONT_MED, WIDTH // 2 - 40, 8)
        draw_text(screen, f"Combo x{combo}" if combo>0 else "", FONT_MED, WIDTH//2 + 60, 40, color=HIGHLIGHT_COLOR)
        draw_text(screen, equation_text, FONT_BIG, WIDTH // 2, 60, center=True, color=HIGHLIGHT_COLOR)

        # Level intro overlay
        if show_level_intro:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,140))
            screen.blit(overlay, (0,0))
            draw_text(screen, f"Level {current_level+1}", FONT_BIG, WIDTH//2, HEIGHT//2, center=True, color=HIGHLIGHT_COLOR)

        # Game over / win overlays
        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,180))
            screen.blit(overlay, (0,0))
            game_over_sfx.play()
            
            draw_text(screen, "GAME OVER", FONT_BIG, WIDTH//2, HEIGHT//3, center=True, color=WRONG_COLOR)
            draw_text(screen, f"Final Score: {score}", FONT_MED, WIDTH//2, HEIGHT//2, center=True)
            draw_text(screen, "Press R to restart or ESC to quit", FONT_SMALL, WIDTH//2, HEIGHT//2 + 50, center=True)
        elif win:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,140))
            screen.blit(overlay, (0,0))
            game_over_sfx.play()
            draw_text(screen, "YOU WIN!", FONT_BIG, WIDTH//2, HEIGHT//3, center=True, color=CORRECT_COLOR)
            draw_text(screen, f"Final Score: {score}", FONT_MED, WIDTH//2, HEIGHT//2, center=True)
            draw_text(screen, "Press R to play again or ESC to quit", FONT_SMALL, WIDTH//2, HEIGHT//2 + 50, center=True)

        pygame.display.flip()

# ----- Menu -----
def menu(screen, clock):
    selected = 0
    options = ["Start","Exit"]
    while True:
        screen.fill(BG)
        draw_text(screen, "MATH RUNNER - v0.1", FONT_BIG, WIDTH//2, HEIGHT//4, center=True)
        draw_text(screen, "© Taki Tech Games - 2025", FONT_SMALL, 400, 400, center=True, color=NAME_COLOR)
        for i, option in enumerate(options):
            color = HIGHLIGHT_COLOR if i==selected else TEXT_COLOR
            draw_text(screen, option, FONT_MED, WIDTH//2, HEIGHT//2 + i*60, center=True, color=color)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected-1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected+1) % len(options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if options[selected]=="Start":
                        return "start"
                    elif options[selected]=="Exit":
                        pygame.quit()
                        sys.exit()
        clock.tick(FPS)

# ----- Main -----
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Math Runner - v0.1 | Taki Tech Games")
    clock = pygame.time.Clock()
    while True:
        choice = menu(screen, clock)
        if choice=="start":
            result = game_loop(screen, clock)
            if result=="exit":
                break
        else:
            break
    pygame.quit()
    sys.exit()

if __name__=="__main__":
    main()
