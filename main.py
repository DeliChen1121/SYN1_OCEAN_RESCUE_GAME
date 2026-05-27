import pygame
import math
import random
import os
import asyncio

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ocean Rescue - Synthesis 1 Project")
clock = pygame.time.Clock()

# ================= Color definitions =================
COLOR_TOXIC = (60, 50, 20)   
COLOR_START = (140, 130, 80) 
COLOR_CLEAN = (60, 150, 200) 

HOOK_GRAY = (180, 180, 180)
WHITE = (255, 255, 255)
WARNING_RED = (200, 0, 0)
SCORE_GREEN = (50, 220, 50) 
SCORE_RED = (255, 50, 50)   
BTN_COLOR = (40, 120, 180)
BTN_HOVER = (60, 150, 220)

# Font setup
font = pygame.font.SysFont("Arial", 24, bold=True)
float_font = pygame.font.SysFont("Arial", 32, bold=True) 
huge_font = pygame.font.SysFont("Arial", 100, bold=True) 
stat_font = pygame.font.SysFont("Arial", 36, bold=True) 
tutorial_font = pygame.font.SysFont("Arial", 30, bold=True)
info_font = pygame.font.SysFont("Arial", 20, bold=False) 
title_font = pygame.font.SysFont("Arial", 70, bold=True) 

# ================= Load audio =================
bgm_path = os.path.join(BASE_DIR, "resources", "bgm.ogg")

def load_sound(filename):
    path = os.path.join(BASE_DIR, "resources", filename)
    return pygame.mixer.Sound(path) if os.path.exists(path) else None

snd_catch = load_sound("click.wav")              
snd_success = load_sound("chime.wav")            
snd_fail = load_sound("error.wav")               
snd_countdown = load_sound("five_sec_countdown.ogg") 
snd_end = load_sound("end.wav")                  

def play_sound(snd):
    if snd: snd.play()

# ================= Item configuration dictionary =================
ITEM_CONFIG = {
    "banana": {
        "category": "trash",
        "score": 20,
        "img": "resources/banana.png",
        "size": 45,
        "color": (255, 255, 0),
    },
    "bag": {
        "category": "trash",
        "score": 30,
        "img": "resources/bag.png",
        "size": 45,
        "color": (150, 150, 150),
    },
    "can": {
        "category": "trash",
        "score": 40,
        "img": "resources/can.png",
        "size": 45,
        "color": (200, 200, 200),
    },
    "waste": {
        "category": "trash",
        "score": 50,
        "img": "resources/waste.png",
        "size": 45,
        "color": (150, 0, 200),
    },
    "starfish": {
        "category": "animal",
        "score": -10,
        "img": "resources/starfish.png",
        "size": 45,
        "color": (255, 165, 0),
    },
    "jellyfish": {
        "category": "animal",
        "score": -20,
        "img": "resources/jellyfish.png",
        "size": 45,
        "color": (255, 150, 200),
    },
    "fish": {
        "category": "animal",
        "score": -30,
        "img": "resources/fish.png",
        "size": 45,
        "color": (50, 200, 80),
    },
    "turtle": {
        "category": "animal",
        "score": -40,
        "img": "resources/turtle.png",
        "size": 45,
        "color": (0, 150, 0),
    },
}

def get_dynamic_bg_color(score):
    max_score = 600   
    min_score = -300  
    if score >= max_score: return COLOR_CLEAN
    elif score <= min_score: return COLOR_TOXIC
    elif score > 0:
        ratio = score / max_score
        return (int(COLOR_START[0] + (COLOR_CLEAN[0] - COLOR_START[0]) * ratio),
                int(COLOR_START[1] + (COLOR_CLEAN[1] - COLOR_START[1]) * ratio),
                int(COLOR_START[2] + (COLOR_CLEAN[2] - COLOR_START[2]) * ratio))
    else: 
        ratio = score / min_score
        return (int(COLOR_START[0] + (COLOR_TOXIC[0] - COLOR_START[0]) * ratio),
                int(COLOR_START[1] + (COLOR_TOXIC[1] - COLOR_START[1]) * ratio),
                int(COLOR_START[2] + (COLOR_TOXIC[2] - COLOR_START[2]) * ratio))

class Bubble:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(HEIGHT, HEIGHT + 200)
        self.speed = random.uniform(1, 3)
        self.radius = random.randint(2, 6)
        self.wobble_speed = random.uniform(0.02, 0.05)
        self.wobble_offset = random.uniform(0, math.pi * 2)

    def update(self):
        self.y -= self.speed
        self.x += math.sin(
            self.y * self.wobble_speed + self.wobble_offset
        ) * 1.5
        if self.y < -10:
            self.y = random.randint(HEIGHT, HEIGHT + 50)
            self.x = random.randint(0, WIDTH)

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            WHITE,
            (int(self.x), int(self.y)),
            self.radius,
            1,
        )

class FloatingText:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.alpha = 255
        self.surface = float_font.render(self.text, True, self.color)

    def update(self):
        self.y -= 2
        self.alpha -= 5

    def draw(self, surface):
        if self.alpha > 0:
            text_surface = self.surface.copy()
            text_surface.set_alpha(max(0, self.alpha))
            surface.blit(
                text_surface,
                text_surface.get_rect(center=(self.x, self.y)),
            )

class Hook:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = 50
        self.angle = 0
        self.angle_speed = 1
        self.length = 40
        self.state = "swinging"
        self.speed = 6
        self.caught_item = None

    def update(self):
        if self.state == "swinging":
            self.angle += self.angle_speed
            if self.angle >= 70 or self.angle <= -70:
                self.angle_speed *= -1
        elif self.state == "shooting":
            self.length += self.speed
            hx, hy = self.get_end_pos()
            if hx < 0 or hx > WIDTH or hy > HEIGHT:
                self.state = "retracting"
        elif self.state == "retracting":
            if self.caught_item and self.caught_item.category == "animal":
                current_speed = 2
            else:
                current_speed = self.speed
            self.length -= current_speed
            if self.length <= 40:
                self.length = 40
                self.state = "swinging"
                return self.caught_item
        return None
    def get_end_pos(self):
        rad = math.radians(self.angle)
        return (
            self.x + self.length * math.sin(rad),
            self.y + self.length * math.cos(rad),
        )

    def draw(self, surface):
        ex, ey = self.get_end_pos()
        pygame.draw.line(
            surface,
            HOOK_GRAY,
            (self.x, self.y),
            (ex, ey),
            3,
        )
        pygame.draw.circle(
            surface,
            HOOK_GRAY,
            (int(ex), int(ey)),
            10,
        )

class Item:
    def __init__(self, item_name, x, y):
        self.name = item_name
        self.config = ITEM_CONFIG[item_name]
        self.category = self.config["category"]
        self.score_value = self.config["score"]
        self.size = self.config["size"]
        self.fallback_color = self.config["color"]
        self.x = x
        self.y = y
        self.image = None
        full_img_path = os.path.join(BASE_DIR, self.config["img"])
        if os.path.exists(full_img_path):
            image = pygame.image.load(full_img_path).convert_alpha()
            self.image = pygame.transform.scale(image, (self.size, self.size))

    def draw(self, surface):
        if self.image:
            surface.blit(
                self.image,
                self.image.get_rect(center=(self.x, self.y)),
            )
        else:
            if self.category == "trash":
                pygame.draw.rect(
                    surface,
                    self.fallback_color,
                    (
                        self.x - self.size // 2,
                        self.y - self.size // 2,
                        self.size,
                        self.size,
                    ),
                )
            else:
                pygame.draw.circle(
                    surface,
                    self.fallback_color,
                    (int(self.x), int(self.y)),
                    self.size // 2,
                )

def spawn_item(existing_items, category):
    trash_types = ["banana", "bag", "can", "waste"]
    trash_weights = [45, 30, 15, 10]
    animal_types = ["starfish", "jellyfish", "fish", "turtle"]
    animal_weights = [45, 30, 15, 10]
    if category == "trash":
        chosen_name = random.choices(
            trash_types,
            weights=trash_weights,
            k=1,
        )[0]
    else:
        chosen_name = random.choices(
            animal_types,
            weights=animal_weights,
            k=1,
        )[0]
    size = ITEM_CONFIG[chosen_name]["size"]
    for _ in range(50):
        rand_x = random.randint(size, WIDTH - size)
        rand_y = random.randint(200 + size, HEIGHT - size - 50)
        if not any(
            math.hypot(rand_x - item.x, rand_y - item.y)
            < (size / 2 + item.size / 2 + 15)
            for item in existing_items
        ):
            return Item(chosen_name, rand_x, rand_y)
    return Item(
        chosen_name,
        random.randint(50, WIDTH - 50),
        random.randint(250, HEIGHT - 100),
    )

# ================= Tutorial icon rendering helper =================
def draw_tutorial_icon(surface, item_name, center):
    cfg = ITEM_CONFIG[item_name]
    size = cfg["size"]
    img_path = os.path.join(BASE_DIR, cfg["img"])
    if os.path.exists(img_path):
        img = pygame.transform.scale(
            pygame.image.load(img_path).convert_alpha(),
            (size, size),
        )
        surface.blit(img, img.get_rect(center=center))
    else:
        if cfg["category"] == "trash":
            pygame.draw.rect(
                surface,
                cfg["color"],
                (
                    center[0] - size // 2,
                    center[1] - size // 2,
                    size,
                    size,
                ),
            )
        else:
            pygame.draw.circle(surface, cfg["color"], center, size // 2)

# ================= Main loop =================
async def main():
    hook = Hook()
    items = []
    floating_texts = []
    bubbles = [Bubble() for _ in range(25)] 
    
    decorations = []
    seagrass_path = os.path.join(BASE_DIR, "resources", "seagrass.png")
    coral_path = os.path.join(BASE_DIR, "resources", "coralreef.png")

    if os.path.exists(seagrass_path):
        seagrass_img = pygame.transform.scale(
            pygame.image.load(seagrass_path).convert_alpha(),
            (60, 60),
        )
    else:
        seagrass_img = None

    if os.path.exists(coral_path):
        coral_img = pygame.transform.scale(
            pygame.image.load(coral_path).convert_alpha(),
            (60, 60),
        )
    else:
        coral_img = None

    if seagrass_img: seagrass_img.set_alpha(150)
    if coral_img: coral_img.set_alpha(150)

    existing_dec_xs = []
    
    def get_non_overlapping_x(min_dist):
        for _ in range(50): 
            x = random.randint(40, WIDTH - 40)
            overlap = False
            for ex in existing_dec_xs:
                if abs(x - ex) < min_dist: 
                    overlap = True
                    break
            if not overlap:
                return x
        return random.randint(40, WIDTH - 40) 

    for _ in range(3): 
        new_x = get_non_overlapping_x(70) 
        existing_dec_xs.append(new_x)
        decorations.append({"type": "coral", "img": coral_img, "x": new_x})
        
    for _ in range(5):
        new_x = get_non_overlapping_x(60)
        existing_dec_xs.append(new_x)
        decorations.append(
            {
                "type": "seagrass",
                "img": seagrass_img,
                "x": new_x,
            }
        )

    for _ in range(7):
        items.append(spawn_item(items, "trash"))
    for _ in range(5):
        items.append(spawn_item(items, "animal"))

    score = 0
    trash_caught_count = 0
    animal_caught_count = 0
    
    time_limit = 60
    warning_frames = 0
    
    game_state = "START_MENU" 
    countdown_start_ticks = 0
    start_ticks = 0
    
    # Button collision rect definitions
    start_button_rect = pygame.Rect(WIDTH//2 - 120, HEIGHT//2 + 70, 240, 60)
    replay_button_rect = pygame.Rect(WIDTH//2 - 100, 480, 200, 50)
    
    countdown_sound_played = False
    bgm_started = False
    end_sound_played = False
    
    running = True

    while running:
        current_ticks = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            # Keyboard controls
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if game_state == "START_MENU":
                    game_state = "COUNTDOWN"
                    countdown_start_ticks = pygame.time.get_ticks()
                elif game_state == "PLAYING" and hook.state == "swinging":
                    hook.state = "shooting"
                elif game_state == "GAMEOVER":
                    # Space key triggers replay logic
                    score = 0
                    trash_caught_count = 0
                    animal_caught_count = 0
                    warning_frames = 0
                    game_state = "COUNTDOWN"
                    countdown_start_ticks = pygame.time.get_ticks()
                    countdown_sound_played = False
                    bgm_started = False
                    end_sound_played = False
                    pygame.mixer.stop()
                    hook = Hook()
                    items = []
                    floating_texts = []
                    for _ in range(7):
                        items.append(spawn_item(items, "trash"))
                    for _ in range(5):
                        items.append(spawn_item(items, "animal"))
                    
            # Mouse click controls
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if (
                    game_state == "START_MENU"
                    and start_button_rect.collidepoint(event.pos)
                ):
                    game_state = "COUNTDOWN"
                    countdown_start_ticks = pygame.time.get_ticks()
                elif (
                    game_state == "GAMEOVER"
                    and replay_button_rect.collidepoint(event.pos)
                ):
                    # Mouse click triggers replay logic
                    score = 0
                    trash_caught_count = 0
                    animal_caught_count = 0
                    warning_frames = 0
                    game_state = "COUNTDOWN"
                    countdown_start_ticks = pygame.time.get_ticks()
                    countdown_sound_played = False
                    bgm_started = False
                    end_sound_played = False
                    pygame.mixer.stop()
                    hook = Hook()
                    items = []
                    floating_texts = []
                    for _ in range(7):
                        items.append(spawn_item(items, "trash"))
                    for _ in range(5):
                        items.append(spawn_item(items, "animal"))

        # ============== Logic updates ==============
        if game_state == "START_MENU":
            for b in bubbles: b.update()
            
        elif game_state == "COUNTDOWN":
            if not countdown_sound_played:
                play_sound(snd_countdown)
                countdown_sound_played = True
            for b in bubbles: b.update() 

        elif game_state == "PLAYING":
            if not bgm_started:
                if os.path.exists(bgm_path):
                    pygame.mixer.music.load(bgm_path)
                    pygame.mixer.music.set_volume(0.3)
                    pygame.mixer.music.play(-1)
                bgm_started = True

            returned_item = hook.update()

            if returned_item:
                score += returned_item.score_value
                if returned_item.score_value > 0:
                    play_sound(snd_success)
                    trash_caught_count += 1
                    text_str = f"+{returned_item.score_value}"
                    text_color = SCORE_GREEN
                else:
                    play_sound(snd_fail)
                    animal_caught_count += 1
                    text_str = f"{returned_item.score_value}"
                    text_color = SCORE_RED
                    warning_frames = 15

                floating_texts.append(
                    FloatingText(
                        hook.x,
                        hook.y + 30,
                        text_str,
                        text_color,
                    )
                )
                items.remove(returned_item)
                hook.caught_item = None
                items.append(
                    spawn_item(
                        items,
                        random.choice(["trash", "animal"]),
                    )
                )
            if hook.state == "shooting":
                hx, hy = hook.get_end_pos()
                for item in items:
                    if (
                        math.hypot(hx - item.x, hy - item.y)
                        < (item.size // 2 + 10)
                    ):
                        hook.state = "retracting"
                        hook.caught_item = item
                        play_sound(snd_catch)
                        break

            if hook.caught_item:
                hx, hy = hook.get_end_pos()
                hook.caught_item.x = hx
                hook.caught_item.y = hy

            for b in bubbles: b.update()
            for f in floating_texts[:]:
                f.update()
                if f.alpha <= 0: floating_texts.remove(f)
                
            if current_ticks - start_ticks >= time_limit * 1000:
                game_state = "GAMEOVER"

        # ============== Rendering ==============
        
        current_bg_color = (
            get_dynamic_bg_color(score)
            if game_state != "START_MENU"
            else COLOR_START
        )
        screen.fill(current_bg_color)
        
        if warning_frames > 0:
            flash_surface = pygame.Surface((WIDTH, HEIGHT))
            flash_surface.set_alpha(100)
            flash_surface.fill(WARNING_RED)
            screen.blit(flash_surface, (0, 0))
            warning_frames -= 1

        for dec in decorations:
            if dec["img"]:
                screen.blit(
                    dec["img"],
                    dec["img"].get_rect(midbottom=(dec["x"], HEIGHT)),
                )
            else:
                if dec["type"] == "coral":
                    pygame.draw.circle(
                        screen,
                        (100, 50, 50),
                        (dec["x"], HEIGHT),
                        30,
                    )
                else:
                    pygame.draw.polygon(
                        screen,
                        (0, 150, 50),
                        [
                            (dec["x"], HEIGHT - 60),
                            (dec["x"] - 15, HEIGHT),
                            (dec["x"] + 15, HEIGHT),
                        ],
                    )
        
        for b in bubbles: b.draw(screen)
        
        if game_state in ["PLAYING", "GAMEOVER"]:
            for item in items: item.draw(screen)
            hook.draw(screen)
            for f in floating_texts: f.draw(screen)
            
            time_left = (
                max(0, time_limit - (current_ticks - start_ticks) // 1000)
                if game_state == "PLAYING"
                else 0
            )
            screen.blit(
                font.render(f"Score: {score}", True, WHITE),
                (20, 20),
            )
            screen.blit(
                font.render(f"Time: {time_left}s", True, WHITE),
                (WIDTH - 120, 20),
            )

        # ============== UI overlay rendering ==============
        
        # 0. Start menu state layer
        if game_state == "START_MENU":
            # Moved the title up slightly to make room for the tutorial
            title_surf = title_font.render(
                "OCEAN RESCUE",
                True,
                WHITE,
            )
            screen.blit(
                title_surf,
                title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 160)),
            )
            
            # --- TUTORIAL SECTION (Updated to use available resources) ---
            tut_heading = tutorial_font.render(
                "HOW TO PLAY",
                True,
                (220, 220, 220),
            )
            screen.blit(
                tut_heading,
                tut_heading.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 90)),
            )

            draw_tutorial_icon(
                screen,
                "bag",
                (WIDTH // 2 - 260, HEIGHT // 2 - 20),
            )
            trash_text = info_font.render(
                "Catch trash to clean the ocean",
                True,
                SCORE_GREEN,
            )
            screen.blit(trash_text, (WIDTH // 2 - 220, HEIGHT // 2 - 40))
            score_text = info_font.render(
                "+ Points for trash items",
                True,
                SCORE_GREEN,
            )
            screen.blit(score_text, (WIDTH // 2 - 220, HEIGHT // 2 - 15))

            draw_tutorial_icon(
                screen,
                "fish",
                (WIDTH // 2 + 50, HEIGHT // 2 - 20),
            )
            animal_text = info_font.render(
                "Avoid animals to stay safe",
                True,
                SCORE_RED,
            )
            screen.blit(animal_text, (WIDTH // 2 + 80, HEIGHT // 2 - 40))
            penalty_text = info_font.render(
                "- Points for animals",
                True,
                SCORE_RED,
            )
            screen.blit(penalty_text, (WIDTH // 2 + 80, HEIGHT // 2 - 15))

            hint_text = info_font.render(
                "Use SPACE or click START when ready",
                True,
                WHITE,
            )
            screen.blit(
                hint_text,
                hint_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)),
            )
            # ----------------------------------------------------------

            # Start Button
            color = (
                BTN_HOVER
                if start_button_rect.collidepoint(mouse_pos)
                else BTN_COLOR
            )
            pygame.draw.rect(
                screen,
                color,
                start_button_rect,
                border_radius=10,
            )
            btn_text = float_font.render(
                "START GAME",
                True,
                WHITE,
            )
            screen.blit(
                btn_text,
                btn_text.get_rect(center=start_button_rect.center),
            )
            
            # Hint Text
            hint_text = info_font.render(
                "Or press SPACE to begin",
                True,
                WHITE,
            )
            screen.blit(
                hint_text,
                hint_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150)),
            )
            
            # Move custom signature to the top-right corner
            sig_text = info_font.render("Made by Deli Chen", True, WHITE)
            screen.blit(sig_text, (WIDTH - sig_text.get_width() - 20, 20))

        # 1. Countdown state layer
        elif game_state == "COUNTDOWN":
            elapsed_sec = (current_ticks - countdown_start_ticks) / 1000.0
            
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            if elapsed_sec < 5:
                countdown_num = str(5 - int(elapsed_sec)) 
                text_surf = huge_font.render(
                    countdown_num,
                    True,
                    WHITE,
                )
                screen.blit(
                    text_surf,
                    text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)),
                )
            else:
                game_state = "PLAYING"
                start_ticks = pygame.time.get_ticks() 

        # 2. Game over state layer
        elif game_state == "GAMEOVER":
            if not end_sound_played:
                pygame.mixer.music.stop() 
                play_sound(snd_end)       
                end_sound_played = True
            
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(220) 
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            center_x = WIDTH // 2
            
            title_surf = title_font.render("TIME'S UP!", True, WHITE)
            trash_surf = stat_font.render(
                f"Trash Cleaned: {trash_caught_count}",
                True,
                SCORE_GREEN,
            )
            animal_surf = stat_font.render(
                f"Animals Harmed: {animal_caught_count}",
                True,
                SCORE_RED,
            )
            score_surf = float_font.render(
                f"Final Score: {score}",
                True,
                WHITE,
            )
            
            # Adjusted Y-axis coordinates to make room for replay button
            screen.blit(
                title_surf,
                title_surf.get_rect(center=(center_x, 80)),
            )
            screen.blit(
                trash_surf,
                trash_surf.get_rect(center=(center_x, 160)),
            )
            screen.blit(
                animal_surf,
                animal_surf.get_rect(center=(center_x, 210)),
            )
            screen.blit(
                score_surf,
                score_surf.get_rect(center=(center_x, 280)),
            )

            msg1 = info_font.render(
                (
                    "Our oceans are drowning in plastic while marine life "
                    "is relentlessly exploited."
                ),
                True,
                (200, 200, 200),
            )
            msg2 = info_font.render(
                (
                    "Every choice has a consequence. Clean the water, "
                    "protect the life."
                ),
                True,
                (200, 200, 200),
            )
            screen.blit(
                msg1,
                msg1.get_rect(center=(center_x, 360)),
            )
            screen.blit(
                msg2,
                msg2.get_rect(center=(center_x, 390)),
            )

            insp_text = info_font.render(
                "Inspiration: Classic 'Gold Miner'",
                True,
                (150, 150, 150),
            )
            screen.blit(
                insp_text,
                insp_text.get_rect(center=(center_x, 430)),
            )

            # New: replay button rendering
            replay_color = (
                BTN_HOVER
                if replay_button_rect.collidepoint(mouse_pos)
                else BTN_COLOR
            )
            pygame.draw.rect(
                screen,
                replay_color,
                replay_button_rect,
                border_radius=10,
            )
            replay_text = float_font.render(
                "REPLAY",
                True,
                WHITE,
            )
            screen.blit(
                replay_text,
                replay_text.get_rect(center=replay_button_rect.center),
            )

            replay_hint = info_font.render(
                "Or press SPACE to replay",
                True,
                (150, 150, 150),
            )
            screen.blit(
                replay_hint,
                replay_hint.get_rect(center=(center_x, 550)),
            )

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())