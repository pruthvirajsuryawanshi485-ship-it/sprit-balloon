import math
import random
import time
import tkinter as tk


WIDTH = 480
HEIGHT = 720
BALLOON_X = WIDTH // 2
BALLOON_Y = HEIGHT - 155
BALLOON_RADIUS = 26
SHIELD_RADIUS = 34
OBSTACLE_MIN_SIZE = 18
OBSTACLE_MAX_SIZE = 42
LEVELS = [
    {
        "name": "Quiet Sky",
        "score": 0,
        "bg": "#101820",
        "stripe_a": "#13232e",
        "stripe_b": "#111e27",
        "spawn_delay": 1.15,
        "min_delay": 0.58,
        "speed_bonus": 0.0,
    },
    {
        "name": "Night Wind",
        "score": 350,
        "bg": "#111529",
        "stripe_a": "#171d35",
        "stripe_b": "#13182d",
        "spawn_delay": 0.92,
        "min_delay": 0.45,
        "speed_bonus": 0.35,
    },
    {
        "name": "Storm Path",
        "score": 800,
        "bg": "#1a1722",
        "stripe_a": "#251f31",
        "stripe_b": "#1d1a27",
        "spawn_delay": 0.76,
        "min_delay": 0.34,
        "speed_bonus": 0.75,
    },
    {
        "name": "Final Ascent",
        "score": 1400,
        "bg": "#1e1b14",
        "stripe_a": "#2b261a",
        "stripe_b": "#242015",
        "spawn_delay": 0.62,
        "min_delay": 0.26,
        "speed_bonus": 1.1,
    },
]


class Obstacle:
    def __init__(self, canvas, score, level):
        self.canvas = canvas
        level_data = LEVELS[level]
        self.size = random.randint(OBSTACLE_MIN_SIZE, OBSTACLE_MAX_SIZE + level * 3)
        self.radius = self.size / 2
        self.x = random.randint(self.size, WIDTH - self.size)
        self.y = -random.randint(30, 220)
        self.vx = random.uniform(-0.75, 0.75) + random.uniform(-0.25, 0.25) * level
        self.vy = random.uniform(1.05, 1.85) + level_data["speed_bonus"] + min(score / 1200, 1.2)
        self.shape = random.choice(["circle", "box"])
        self.color = random.choice(["#ff6b6b", "#ffd166", "#35a7ff", "#7bd88f"])

        if self.shape == "circle":
            self.id = canvas.create_oval(
                self.x - self.radius,
                self.y - self.radius,
                self.x + self.radius,
                self.y + self.radius,
                fill=self.color,
                outline="",
            )
        else:
            self.id = canvas.create_rectangle(
                self.x - self.radius,
                self.y - self.radius,
                self.x + self.radius,
                self.y + self.radius,
                fill=self.color,
                outline="",
            )

    def move(self, shield_x, shield_y):
        dx = self.x - shield_x
        dy = self.y - shield_y
        dist = math.hypot(dx, dy)
        push_range = self.radius + SHIELD_RADIUS

        if 0 < dist < push_range:
            force = (push_range - dist) / push_range
            nx = dx / dist
            ny = dy / dist
            self.vx += nx * force * 2.1
            self.vy += ny * force * 1.8

        self.vx *= 0.992
        self.vy += 0.006
        self.x += self.vx
        self.y += self.vy

        if self.x < self.radius:
            self.x = self.radius
            self.vx = abs(self.vx) * 0.75
        elif self.x > WIDTH - self.radius:
            self.x = WIDTH - self.radius
            self.vx = -abs(self.vx) * 0.75

        self.canvas.coords(
            self.id,
            self.x - self.radius,
            self.y - self.radius,
            self.x + self.radius,
            self.y + self.radius,
        )

    def hits_balloon(self):
        distance = math.hypot(self.x - BALLOON_X, self.y - BALLOON_Y)
        return distance < self.radius + BALLOON_RADIUS - 4

    def is_gone(self):
        return self.y - self.radius > HEIGHT + 20

    def delete(self):
        self.canvas.delete(self.id)


class SpiritBalloonGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Spirit Balloon")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#101820", highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_click)
        self.root.bind("<space>", self.on_space)
        self.root.bind("p", self.on_pause_key)
        self.root.bind("P", self.on_pause_key)

        self.shield_x = WIDTH // 2
        self.shield_y = HEIGHT - 255
        self.obstacles = []
        self.score = 0
        self.best = 0
        self.current_level = 0
        self.running = False
        self.paused = False
        self.showing_menu = True
        self.showing_controls = False
        self.showing_story = False
        self.story_scene = 0
        self.story_frame = 0
        self.story_complete = False
        self.menu_buttons = []
        self.pause_button_bounds = (430, 48, 466, 84)
        self.last_spawn = time.time()

        self.draw_scene()
        self.show_menu()
        self.loop()

    def draw_scene(self):
        self.canvas.delete("all")
        self.draw_game_background()

        self.score_text = self.canvas.create_text(
            18,
            18,
            text="0",
            fill="#f6f7fb",
            font=("Arial", 22, "bold"),
            anchor="nw",
        )
        self.best_text = self.canvas.create_text(
            WIDTH - 18,
            20,
            text="Best 0",
            fill="#9fb2bf",
            font=("Arial", 12, "bold"),
            anchor="ne",
        )
        self.level_text = self.canvas.create_text(
            WIDTH // 2,
            22,
            text=LEVELS[self.current_level]["name"],
            fill="#7ef9ff",
            font=("Arial", 12, "bold"),
        )

        self.canvas.create_line(
            BALLOON_X,
            BALLOON_Y + BALLOON_RADIUS,
            BALLOON_X,
            BALLOON_Y + BALLOON_RADIUS + 45,
            fill="#f7d6bd",
            width=2,
        )
        self.canvas.create_oval(
            BALLOON_X - BALLOON_RADIUS,
            BALLOON_Y - BALLOON_RADIUS,
            BALLOON_X + BALLOON_RADIUS,
            BALLOON_Y + BALLOON_RADIUS,
            fill="#f8f1ff",
            outline="#ffffff",
            width=3,
        )
        self.canvas.create_oval(
            BALLOON_X - 10,
            BALLOON_Y - 16,
            BALLOON_X + 2,
            BALLOON_Y - 4,
            fill="#ffffff",
            outline="",
        )

        self.shield = self.canvas.create_oval(
            self.shield_x - SHIELD_RADIUS,
            self.shield_y - SHIELD_RADIUS,
            self.shield_x + SHIELD_RADIUS,
            self.shield_y + SHIELD_RADIUS,
            fill="#7ef9ff",
            outline="#dcfbff",
            width=3,
        )
        self.draw_pause_button()

    def draw_game_background(self):
        level = LEVELS[self.current_level]
        self.canvas.delete("background")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=level["bg"], outline="", tags="background")

        for y in range(0, HEIGHT, 42):
            shade = level["stripe_a"] if (y // 42) % 2 == 0 else level["stripe_b"]
            self.canvas.create_rectangle(0, y, WIDTH, y + 42, fill=shade, outline="", tags="background")

        if self.current_level >= 1:
            for x, y, size in [(56, 86, 2), (132, 146, 3), (340, 92, 2), (412, 180, 3)]:
                self.canvas.create_oval(x, y, x + size, y + size, fill="#d7e3ea", outline="", tags="background")
        if self.current_level >= 2:
            for x in range(34, WIDTH, 92):
                self.canvas.create_line(x, 0, x + 72, HEIGHT, fill="#2b3546", width=2, tags="background")
        if self.current_level >= 3:
            self.canvas.create_oval(318, 74, 456, 212, fill="#4b351c", outline="", tags="background")
            self.canvas.create_oval(344, 96, 438, 190, fill=level["bg"], outline="", tags="background")

        self.canvas.tag_lower("background")

    def show_menu(self):
        self.running = False
        self.showing_menu = True
        self.showing_controls = False
        self.showing_story = False
        self.menu_buttons = []
        self.canvas.delete("menu", "controls", "story", "game_over")

        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#07131d", outline="", tags="menu")
        for y in range(0, HEIGHT, 42):
            color = "#0b1f2c" if (y // 42) % 2 == 0 else "#091923"
            self.canvas.create_rectangle(0, y, WIDTH, y + 42, fill=color, outline="", tags="menu")

        self.draw_balloon(WIDTH // 2, 156, "#f8f1ff", glow=True, tags="menu")
        self.canvas.create_text(
            WIDTH // 2,
            258,
            text="Spirit Balloon",
            fill="#ffffff",
            font=("Arial", 34, "bold"),
            tags="menu",
        )
        self.canvas.create_text(
            WIDTH // 2,
            298,
            text="Protect the spirit. Keep the promise.",
            fill="#7ef9ff",
            font=("Arial", 14, "bold"),
            tags="menu",
        )

        self.add_menu_button("Start Game", 246, "start")
        self.add_menu_button("Story", 316, "story")
        self.add_menu_button("Controls", 386, "controls")
        self.add_menu_button("Quit", 456, "quit")

    def add_menu_button(self, label, y, action):
        x1 = WIDTH // 2 - 118
        y1 = y
        x2 = WIDTH // 2 + 118
        y2 = y + 46
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#123241", outline="#7ef9ff", width=2, tags="menu")
        self.canvas.create_text(
            WIDTH // 2,
            y + 23,
            text=label,
            fill="#ffffff",
            font=("Arial", 15, "bold"),
            tags="menu",
        )
        self.menu_buttons.append((x1, y1, x2, y2, action))

    def show_controls(self):
        self.showing_controls = True
        self.showing_menu = False
        self.canvas.delete("menu", "controls")
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#07131d", outline="", tags="controls")
        self.canvas.create_text(
            WIDTH // 2,
            120,
            text="Controls",
            fill="#ffffff",
            font=("Arial", 32, "bold"),
            tags="controls",
        )
        controls = (
            "Move your mouse to control the glowing shield.\n\n"
            "Push falling obstacles away from the spirit balloon.\n\n"
            "If an obstacle touches the balloon, the game ends.\n\n"
            "Use the pause button or press P to pause the game.\n\n"
            "After game over, click or press Space to restart."
        )
        self.canvas.create_text(
            WIDTH // 2,
            300,
            text=controls,
            fill="#d7e3ea",
            font=("Arial", 15),
            justify="center",
            width=390,
            tags="controls",
        )
        self.canvas.create_text(
            WIDTH // 2,
            548,
            text="Click or press Space to return",
            fill="#7ef9ff",
            font=("Arial", 15, "bold"),
            tags="controls",
        )

    def show_story(self):
        self.showing_menu = False
        self.showing_controls = False
        self.showing_story = True
        self.story_scene = 0
        self.story_frame = 0
        self.story_complete = False
        self.animate_story()

    def animate_story(self):
        if not self.showing_story:
            return

        scenes = [
            (
                "Every time her brother returned from military drill,\n"
                "he brought her a balloon and filled their home with joy."
            ),
            (
                "On his way back, a warning arrived:\n"
                "his enemies had found his family's home."
            ),
            (
                "He ran through the night, but reached home too late.\n"
                "The house was silent, and his family was gone."
            ),
            (
                "As he held his little sister, her spirit rose softly\n"
                "from his arms as a glowing balloon."
            ),
            (
                "He made one final promise.\n"
                "He became the shield, and now he asks you to guide him."
            ),
        ]

        self.canvas.delete("story")
        self.draw_story_background()
        self.draw_story_title()

        caption = scenes[self.story_scene]
        visible_letters = min(len(caption), self.story_frame * 2)
        self.canvas.create_text(
            WIDTH // 2,
            584,
            text=caption[:visible_letters],
            fill="#d7e3ea",
            font=("Arial", 14),
            justify="center",
            width=405,
            tags="story",
        )

        if self.story_scene == 0:
            self.draw_family_scene()
        elif self.story_scene == 1:
            self.draw_warning_scene()
        elif self.story_scene == 2:
            self.draw_return_scene()
        elif self.story_scene == 3:
            self.draw_spirit_scene()
        else:
            self.draw_shield_scene()

        if self.story_complete:
            self.canvas.create_text(
                WIDTH // 2,
                660,
                text="Click or press Space to begin",
                fill="#ffffff",
                font=("Arial", 15, "bold"),
                tags="story",
            )
            return

        self.canvas.create_text(
            WIDTH // 2,
            660,
            text="Click or press Space to skip",
            fill="#8fb7c7",
            font=("Arial", 12),
            tags="story",
        )

        self.story_frame += 1
        if self.story_frame > max(70, len(caption) // 2 + 22):
            self.story_frame = 0
            self.story_scene += 1
            if self.story_scene >= len(scenes):
                self.story_scene = len(scenes) - 1
                self.story_complete = True

        self.root.after(70, self.animate_story)

    def draw_story_background(self):
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#07131d", outline="", tags="story")
        for y in range(0, HEIGHT, 36):
            color = "#0b1f2c" if (y // 36) % 2 == 0 else "#091923"
            self.canvas.create_rectangle(0, y, WIDTH, y + 36, fill=color, outline="", tags="story")
        for x, y, size in [(54, 82, 2), (118, 154, 3), (394, 94, 2), (326, 172, 2), (430, 240, 3)]:
            self.canvas.create_oval(x, y, x + size, y + size, fill="#d7e3ea", outline="", tags="story")

    def draw_story_title(self):
        self.canvas.create_text(
            WIDTH // 2,
            58,
            text="Spirit Balloon",
            fill="#ffffff",
            font=("Arial", 30, "bold"),
            tags="story",
        )
        self.canvas.create_text(
            WIDTH // 2,
            98,
            text="A brother's final promise",
            fill="#7ef9ff",
            font=("Arial", 14, "bold"),
            tags="story",
        )

    def draw_person(self, x, y, shirt, scale=1.0, tags="story"):
        head = 12 * scale
        body = 32 * scale
        self.canvas.create_oval(x - head, y - body - head * 2, x + head, y - body, fill="#f7d6bd", outline="", tags=tags)
        self.canvas.create_rectangle(x - 12 * scale, y - body, x + 12 * scale, y, fill=shirt, outline="", tags=tags)
        self.canvas.create_line(x - 7 * scale, y, x - 14 * scale, y + 26 * scale, fill="#d7e3ea", width=max(1, int(3 * scale)), tags=tags)
        self.canvas.create_line(x + 7 * scale, y, x + 14 * scale, y + 26 * scale, fill="#d7e3ea", width=max(1, int(3 * scale)), tags=tags)
        self.canvas.create_line(x - 12 * scale, y - 22 * scale, x - 28 * scale, y - 8 * scale, fill="#f7d6bd", width=max(1, int(3 * scale)), tags=tags)
        self.canvas.create_line(x + 12 * scale, y - 22 * scale, x + 28 * scale, y - 8 * scale, fill="#f7d6bd", width=max(1, int(3 * scale)), tags=tags)

    def draw_house(self, damaged=False):
        wall = "#27384a" if damaged else "#31495f"
        roof = "#39232d" if damaged else "#8b3d48"
        self.canvas.create_rectangle(94, 292, 386, 448, fill=wall, outline="", tags="story")
        self.canvas.create_polygon(74, 292, 240, 182, 406, 292, fill=roof, outline="", tags="story")
        self.canvas.create_rectangle(212, 360, 268, 448, fill="#17242e", outline="", tags="story")
        self.canvas.create_rectangle(126, 328, 176, 376, fill="#f6d58b" if not damaged else "#111820", outline="", tags="story")
        self.canvas.create_rectangle(304, 328, 354, 376, fill="#f6d58b" if not damaged else "#111820", outline="", tags="story")
        if damaged:
            self.canvas.create_line(118, 306, 184, 362, 152, 410, fill="#111820", width=5, tags="story")
            self.canvas.create_line(332, 300, 292, 352, 350, 420, fill="#111820", width=5, tags="story")

    def draw_balloon(self, x, y, color="#f8f1ff", glow=False, tags="story"):
        if glow:
            self.canvas.create_oval(x - 42, y - 42, x + 42, y + 42, fill="#234f63", outline="", tags=tags)
        self.canvas.create_line(x, y + 22, x, y + 78, fill="#f7d6bd", width=2, tags=tags)
        self.canvas.create_oval(x - 24, y - 30, x + 24, y + 24, fill=color, outline="#ffffff", width=3, tags=tags)
        self.canvas.create_oval(x - 9, y - 16, x + 2, y - 5, fill="#ffffff", outline="", tags=tags)

    def draw_family_scene(self):
        self.draw_house()
        self.draw_person(170, 464, "#7bd88f", 0.86)
        self.draw_person(245, 464, "#5a7d9a", 1.0)
        self.draw_person(315, 464, "#e98d9a", 0.78)
        bob = math.sin(self.story_frame / 6) * 8
        self.draw_balloon(338, 248 + bob, "#ff9ac2")

    def draw_warning_scene(self):
        self.draw_person(134 + self.story_frame * 2 % 180, 456, "#4f6f54", 1.0)
        self.canvas.create_rectangle(214, 236, 366, 330, fill="#182a36", outline="#7ef9ff", width=2, tags="story")
        self.canvas.create_text(290, 268, text="WARNING", fill="#ffd166", font=("Arial", 19, "bold"), tags="story")
        self.canvas.create_text(290, 304, text="Family in danger", fill="#ffffff", font=("Arial", 12, "bold"), tags="story")
        self.canvas.create_line(144, 384, 320, 320, fill="#7ef9ff", width=2, dash=(4, 4), tags="story")

    def draw_return_scene(self):
        self.draw_house(damaged=True)
        self.draw_person(240, 470, "#4f6f54", 1.05)
        self.canvas.create_text(240, 235, text="Too late...", fill="#c7d3dc", font=("Arial", 18, "bold"), tags="story")
        for offset in range(0, 90, 30):
            y = 198 + ((self.story_frame * 3 + offset) % 100)
            self.canvas.create_oval(120 + offset * 2, y, 130 + offset * 2, y + 10, fill="#27384a", outline="", tags="story")

    def draw_spirit_scene(self):
        self.draw_person(242, 492, "#4f6f54", 1.05)
        rise = min(150, self.story_frame * 3)
        self.draw_balloon(242, 390 - rise, "#f8f1ff", glow=True)
        self.canvas.create_text(242, 360, text="Her spirit rises", fill="#ffffff", font=("Arial", 17, "bold"), tags="story")

    def draw_shield_scene(self):
        self.draw_balloon(WIDTH // 2, 230, "#f8f1ff", glow=True)
        pulse = 6 + math.sin(self.story_frame / 5) * 4
        self.canvas.create_oval(
            WIDTH // 2 - 46 - pulse,
            390 - 46 - pulse,
            WIDTH // 2 + 46 + pulse,
            390 + 46 + pulse,
            fill="#163b48",
            outline="",
            tags="story",
        )
        self.canvas.create_oval(
            WIDTH // 2 - 44,
            390 - 44,
            WIDTH // 2 + 44,
            390 + 44,
            fill="#7ef9ff",
            outline="#dcfbff",
            width=4,
            tags="story",
        )
        self.canvas.create_text(WIDTH // 2, 474, text="Protect her.", fill="#ffffff", font=("Arial", 20, "bold"), tags="story")

    def on_mouse_move(self, event):
        self.shield_x = max(SHIELD_RADIUS, min(WIDTH - SHIELD_RADIUS, event.x))
        self.shield_y = max(SHIELD_RADIUS, min(HEIGHT - SHIELD_RADIUS, event.y))

    def on_click(self, _event):
        if self.showing_menu:
            self.handle_menu_click(_event.x, _event.y)
        elif self.showing_controls:
            self.show_menu()
        elif self.showing_story:
            self.start_game()
        elif self.running and self.is_pause_button_click(_event.x, _event.y):
            self.toggle_pause()
        elif not self.running:
            self.restart()

    def on_space(self, _event):
        if self.showing_menu:
            self.start_game()
        elif self.showing_controls:
            self.show_menu()
        elif self.showing_story:
            self.start_game()
        elif not self.running:
            self.restart()

    def on_pause_key(self, _event):
        if self.running and not self.showing_menu and not self.showing_controls and not self.showing_story:
            self.toggle_pause()

    def handle_menu_click(self, x, y):
        for x1, y1, x2, y2, action in self.menu_buttons:
            if x1 <= x <= x2 and y1 <= y <= y2:
                if action == "start":
                    self.start_game()
                elif action == "story":
                    self.show_story()
                elif action == "controls":
                    self.show_controls()
                elif action == "quit":
                    self.root.destroy()
                return

    def start_game(self):
        self.canvas.delete("menu", "controls", "story")
        self.showing_menu = False
        self.showing_controls = False
        self.showing_story = False
        self.running = True
        self.paused = False
        self.canvas.delete("pause_overlay")
        self.draw_pause_button()
        self.last_spawn = time.time()

    def restart(self):
        for obstacle in self.obstacles:
            obstacle.delete()
        self.obstacles.clear()
        self.score = 0
        self.current_level = 0
        self.draw_game_background()
        self.running = True
        self.paused = False
        self.last_spawn = time.time()
        self.canvas.delete("game_over", "level_notice", "pause_overlay")
        self.canvas.itemconfig(self.score_text, text="0")
        self.canvas.itemconfig(self.level_text, text=LEVELS[self.current_level]["name"])
        self.draw_pause_button()

    def is_pause_button_click(self, x, y):
        x1, y1, x2, y2 = self.pause_button_bounds
        return x1 <= x <= x2 and y1 <= y <= y2

    def draw_pause_button(self):
        self.canvas.delete("pause_button")
        x1, y1, x2, y2 = self.pause_button_bounds
        label = ">" if self.paused else "II"
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="#123241", outline="#7ef9ff", width=2, tags="pause_button")
        self.canvas.create_text(
            (x1 + x2) // 2,
            (y1 + y2) // 2,
            text=label,
            fill="#ffffff",
            font=("Arial", 14, "bold"),
            tags="pause_button",
        )

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", stipple="gray50", outline="", tags="pause_overlay")
            self.canvas.create_text(
                WIDTH // 2,
                HEIGHT // 2 - 18,
                text="Paused",
                fill="#ffffff",
                font=("Arial", 30, "bold"),
                tags="pause_overlay",
            )
            self.canvas.create_text(
                WIDTH // 2,
                HEIGHT // 2 + 28,
                text="Click the pause button or press P to continue",
                fill="#d7e3ea",
                font=("Arial", 13),
                tags="pause_overlay",
            )
        else:
            self.canvas.delete("pause_overlay")
            self.last_spawn = time.time()

        self.draw_pause_button()

    def spawn_obstacles(self):
        level = LEVELS[self.current_level]
        spawn_delay = max(level["min_delay"], level["spawn_delay"] - self.score / 1600)
        if time.time() - self.last_spawn < spawn_delay:
            return

        count = 1
        if self.current_level >= 1 and random.random() < 0.35:
            count += 1
        if self.current_level >= 2 and random.random() < 0.45:
            count += 1
        if self.current_level >= 3 and random.random() < 0.25:
            count += 1

        for _ in range(count):
            self.obstacles.append(Obstacle(self.canvas, self.score, self.current_level))
        self.last_spawn = time.time()

    def update_score(self):
        self.score += 1
        self.update_level()
        self.best = max(self.best, self.score)
        self.canvas.itemconfig(self.score_text, text=str(self.score))
        self.canvas.itemconfig(self.best_text, text=f"Best {self.best}")

    def update_level(self):
        new_level = self.current_level
        for index, level in enumerate(LEVELS):
            if self.score >= level["score"]:
                new_level = index

        if new_level == self.current_level:
            return

        self.current_level = new_level
        self.draw_game_background()
        self.canvas.itemconfig(self.level_text, text=LEVELS[self.current_level]["name"])
        self.show_level_notice()

    def show_level_notice(self):
        self.canvas.delete("level_notice")
        self.canvas.create_rectangle(
            WIDTH // 2 - 118,
            86,
            WIDTH // 2 + 118,
            136,
            fill="#07131d",
            outline="#7ef9ff",
            width=2,
            tags="level_notice",
        )
        self.canvas.create_text(
            WIDTH // 2,
            111,
            text=LEVELS[self.current_level]["name"],
            fill="#ffffff",
            font=("Arial", 17, "bold"),
            tags="level_notice",
        )
        self.root.after(1400, lambda: self.canvas.delete("level_notice"))

    def end_game(self):
        self.running = False
        self.paused = False
        self.canvas.delete("pause_overlay")
        self.draw_pause_button()
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000000", stipple="gray50", outline="", tags="game_over")
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 - 42,
            text="The spirit was struck!",
            fill="#ffffff",
            font=("Arial", 27, "bold"),
            tags="game_over",
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 + 2,
            text=f"Score {self.score}   Best {self.best}",
            fill="#d7e3ea",
            font=("Arial", 16, "bold"),
            tags="game_over",
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT // 2 + 42,
            text="Click or press Space to protect her again",
            fill="#9fb2bf",
            font=("Arial", 13),
            tags="game_over",
        )

    def loop(self):
        self.canvas.coords(
            self.shield,
            self.shield_x - SHIELD_RADIUS,
            self.shield_y - SHIELD_RADIUS,
            self.shield_x + SHIELD_RADIUS,
            self.shield_y + SHIELD_RADIUS,
        )

        if self.running and not self.paused:
            self.spawn_obstacles()
            for obstacle in list(self.obstacles):
                obstacle.move(self.shield_x, self.shield_y)
                if obstacle.hits_balloon():
                    self.end_game()
                    break
                if obstacle.is_gone():
                    obstacle.delete()
                    self.obstacles.remove(obstacle)
            self.update_score()

        self.root.after(16, self.loop)


if __name__ == "__main__":
    window = tk.Tk()
    SpiritBalloonGame(window)
    window.mainloop()
