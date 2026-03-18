# message_system.py
# Two-channel message system:
#   "ui"    — fixed position on screen, visible in every state
#   "world" — floats up from world coordinates, explore only

import pygame

# Fixed screen anchor for UI messages (top-centre)
UI_X = 400
UI_Y = 30


class MessageSystem:

    def __init__(self):
        self.messages    = []   # active messages being displayed
        self.queue       = []   # waiting to be spawned

        self.spawn_delay = 20   # frames between spawning queued messages
        self.spawn_timer = 0

        self.font    = pygame.font.SysFont(None, 30)
        self.font_ui = pygame.font.SysFont(None, 34)

    # ------------------------------------------------------------------

    def add(self, text, x=None, y=None, kind="world"):
        """
        Add a message to the queue.

        kind="world"  — floats up from (x, y) in world space.
                        Only visible during STATE_EXPLORE.
        kind="ui"     — appears at the top-centre of the screen.
                        Visible in every game state.
        """
        self.queue.append({
            "text":  text,
            "x":     x if x is not None else UI_X,
            "y":     y if y is not None else UI_Y,
            "kind":  kind,
            "timer": 0,   # filled on spawn
        })

    def add_ui(self, text):
        """Shorthand for a UI-type message (no coordinates needed)."""
        self.add(text, kind="ui")

    # ------------------------------------------------------------------

    def update(self):
        self.spawn_timer += 1

        if self.queue and self.spawn_timer >= self.spawn_delay:
            msg = self.queue.pop(0).copy()

            if msg["kind"] == "ui":
                msg["timer"] = 160          # stays longer
            else:
                msg["timer"] = 120

            self.messages.append(msg)
            self.spawn_timer = 0

        # Tick all active messages
        for m in self.messages:
            m["timer"] -= 1
            if m["kind"] == "world":
                m["y"] -= 0.4              # float upward in world space

        # Remove expired
        self.messages = [m for m in self.messages if m["timer"] > 0]

    # ------------------------------------------------------------------

    def draw_world(self, screen):
        """Call this only during STATE_EXPLORE to draw floating world messages."""
        for m in self.messages:
            if m["kind"] != "world":
                continue

            alpha = min(255, m["timer"] * 3)
            surf  = self.font.render(m["text"], True, (255, 255, 0))
            surf.set_alpha(alpha)
            screen.blit(surf, (m["x"], m["y"]))

    def draw_ui(self, screen):
        """
        Call this on EVERY screen to draw UI messages.
        Messages stack downward from the top-centre anchor.
        """
        ui_msgs = [m for m in self.messages if m["kind"] == "ui"]

        for i, m in enumerate(ui_msgs):
            alpha = min(255, m["timer"] * 2)

            # Pick colour by content
            if any(w in m["text"] for w in ("WIN", "Paid", "Started", "ready")):
                color = (100, 255, 120)
            elif any(w in m["text"] for w in ("CLOSING", "caught", "Lost", "failed", "empty")):
                color = (255, 100, 100)
            else:
                color = (255, 220, 80)

            surf = self.font_ui.render(m["text"], True, color)
            surf.set_alpha(alpha)

            # Centre horizontally, stack vertically
            rect = surf.get_rect(center=(UI_X, UI_Y + i * 38))

            # Dark pill background for readability on any screen
            bg = pygame.Surface((surf.get_width() + 20, surf.get_height() + 8),
                                 pygame.SRCALPHA)
            bg.fill((0, 0, 0, 120))
            screen.blit(bg, (rect.x - 10, rect.y - 4))
            screen.blit(surf, rect)