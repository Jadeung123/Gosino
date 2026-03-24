import pygame, random, math
from constants import PLAY_HEIGHT

class Guard:
    def __init__(self, x, y, guard_type="normal"):
        self.x = x
        self.y = y
        self.type = guard_type
        self.speed = 1.2
        self.chase_speed = 1.8
        self.angle = random.uniform(0, 360)
        self.target_angle = self.angle
        self.turn_speed = 2
        self.move_timer = 0
        self.state = "patrol"
        self.alert_timer = 0
        self.search_timer = 0
        self.last_seen_x = None
        self.last_seen_y = None
        self.vision_distance = 110
        self.chase_distance = 160
        self.suspicion = 0
        self.chase_timer = 0

        if self.type == "fast":
            self.chase_speed = 2.6
            self.vision_distance = 90

        if self.type == "watcher":
            self.chase_speed = 1.5
            self.vision_distance = 150

        if self.type == "lazy":
            self.speed = 0.8
            self.vision_distance = 80

        if self.type == "elite":
            self.speed = 1.6
            self.chase_speed = 2.4
            self.vision_distance = 160

        self.sprite = pygame.image.load("sprites/guard.png")
        self.sprite = pygame.transform.scale(self.sprite, (32, 32))

    def move(self, walls=None):
        old_x, old_y = self.x, self.y

        if self.state == "patrol":
            self.move_timer += 1

            if self.move_timer > 120:
                self.target_angle = random.uniform(0, 360)
                self.move_timer   = 0

            if abs(self.angle - self.target_angle) > 1:
                if (self.target_angle - self.angle) % 360 > 180:
                    self.angle -= self.turn_speed
                else:
                    self.angle += self.turn_speed

            rad     = math.radians(self.angle)
            self.x += math.cos(rad) * self.speed
            self.y += math.sin(rad) * self.speed

        elif self.state == "alert":
            rad     = math.radians(self.angle)
            self.x += math.cos(rad) * (self.speed * 0.6)
            self.y += math.sin(rad) * (self.speed * 0.6)

            self.alert_timer -= 1
            if self.alert_timer <= 0:
                self.state = "patrol"

        elif self.state == "search":
            if self.last_seen_x is None:
                self.state = "patrol"
                return

            dx       = self.last_seen_x - self.x
            dy       = self.last_seen_y - self.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 5:
                self.x += dx / distance * self.speed
                self.y += dy / distance * self.speed
                self.angle = math.degrees(math.atan2(dy, dx))
            else:
                self.angle       += 2
                self.search_timer -= 1
                if self.search_timer <= 0:
                    self.state = "patrol"

        # --- Screen boundary clamp ---
        self.x = max(10, min(790 - 32, self.x))
        self.y = max(10, min(PLAY_HEIGHT - 32, self.y))

        # --- Wall collision (pillars) ---
        if walls:
            guard_rect = pygame.Rect(self.x, self.y, 32, 32)
            for wall in walls:
                if guard_rect.colliderect(wall):
                    # Test each axis separately so guard slides along walls
                    test_x = pygame.Rect(self.x, old_y, 32, 32)
                    if test_x.colliderect(wall):
                        self.x = old_x
                        # Nudge patrol angle away from the wall
                        if self.state == "patrol":
                            self.target_angle = random.uniform(0, 360)

                    test_y = pygame.Rect(old_x, self.y, 32, 32)
                    if test_y.colliderect(wall):
                        self.y = old_y
                        if self.state == "patrol":
                            self.target_angle = random.uniform(0, 360)

    def draw(self, screen):
        rotated = pygame.transform.rotate(self.sprite, -self.angle)
        screen.blit(rotated, (self.x, self.y))

    def draw_detection(self, screen):
        if self.suspicion <= 0:
            return

        bar_width = 40
        bar_height = 6
        ratio = min(self.suspicion / 60, 1)
        x = self.x - 4
        y = self.y - 10

        # background
        pygame.draw.rect(screen, (60,60,60), (x, y, bar_width, bar_height))

        # fill
        pygame.draw.rect(screen, (255,60,60), (x, y, bar_width * ratio, bar_height))

    def draw_state_indicator(self, screen):
        """
        Draws a ! or ? above the guard depending on their current state.
        This gives the player a clear visual warning before being caught.
        """
        if self.state == "patrol":
            return  # nothing to show when guard is calm

        # Position the indicator centered above the guard sprite
        cx = int(self.x + 16)
        cy = int(self.y - 18)

        if self.state == "alert":
            text = "?"
            color = (255, 220, 50)  # yellow — suspicious but not sure
        elif self.state == "chase":
            text = "!"
            color = (255, 50, 50)  # red — actively chasing
        elif self.state == "search":
            text = "?"
            color = (180, 180, 180)  # grey — lost you, still looking
        else:
            return

        font = pygame.font.SysFont(None, 36)

        # Dark circle background for readability
        pygame.draw.circle(screen, (0, 0, 0), (cx, cy), 12)
        pygame.draw.circle(screen, color, (cx, cy), 12, 2)

        surf = font.render(text, True, color)
        screen.blit(surf, surf.get_rect(center=(cx, cy)))

    def _effective_vision(self, player):
        """
        Returns (distance, half_angle) reduced by the player's stealth level.
        Both see_player() and draw_vision() call this so visuals always match
        actual detection — no desync between what you see and what triggers.
        """
        stealth = getattr(player, "stealth", 0)
        distance = max(30, self.vision_distance - stealth * 10)
        half_angle = max(15, 35 - stealth * 3)
        return distance, half_angle

    def see_player(self, player, guards, messages):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx * dx + dy * dy)

        eff_distance, half_angle = self._effective_vision(player)
        if distance > eff_distance:
            self.suspicion = max(0, self.suspicion - 1)
            return False

        angle_to_player = math.degrees(math.atan2(dy, dx))
        diff = (angle_to_player - self.angle + 180) % 360 - 180

        if abs(diff) < half_angle:
            self.suspicion += 2
        elif abs(diff) < half_angle + 20:
            self.suspicion += 1
        else:
            self.suspicion = max(0, self.suspicion - 1)

        if self.suspicion > 60:
            if self.state != "chase":
                messages.add("SPOTTED!", player.x, player.y)

                for guard in guards:
                    if guard != self:
                        d = math.sqrt((guard.x - self.x) ** 2 + (guard.y - self.y) ** 2)
                        if d < 200:
                            guard.state = "alert"
                            guard.alert_timer = 120

            self.state = "chase"
            self.last_seen_x = player.x
            self.last_seen_y = player.y
            return True

        elif self.suspicion > 20 and self.state == "patrol":
            self.state = "alert"
            self.alert_timer = 120
            self.angle = angle_to_player

        return False

    def draw_vision(self, screen, player=None):
        if player is not None:
            eff_distance, half_angle = self._effective_vision(player)
        else:
            eff_distance = self.vision_distance
            half_angle = 35  # fallback if called without player

        left = math.radians(self.angle - 35)
        right = math.radians(self.angle + 35)

        p1 = (self.x + 16, self.y + 16)
        p2 = (self.x + 16 + math.cos(left) * eff_distance,
              self.y + 16 + math.sin(left) * eff_distance)
        p3 = (self.x + 16 + math.cos(right) * eff_distance,
              self.y + 16 + math.sin(right) * eff_distance)

        pygame.draw.polygon(screen, (255, 255, 0), [p1, p2, p3])

    def chase_player(self, player):
        if self.state != "chase":
            return

        self.chase_timer += 1

        if self.chase_timer > 300:
            self.chase_speed = max(1.2, self.chase_speed - 0.01)

        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance > self.chase_distance:
            self.state = "search"
            self.search_timer = 180
            self.chase_timer = 0
            return

        if distance != 0:
            self.x += dx / distance * self.chase_speed
            self.y += dy / distance * self.chase_speed

        self.angle = math.degrees(math.atan2(dy, dx))
        self.last_seen_x = player.x
        self.last_seen_y = player.y

    def start_closing_chase(self, player):
        """
        Called when the casino closes.
        Forces the guard to home in on the player from anywhere
        on the map — no vision check needed.
        """
        self.state = "chase"
        self.last_seen_x = player.x
        self.last_seen_y = player.y
        # Override chase distance — guards never give up during closing
        self.chase_distance = 9999

    def reset(self):
        """
        Called at the start of every new day.
        Puts the guard back into patrol mode with normal stats.
        """
        self.state = "patrol"
        self.suspicion = 0
        self.chase_timer = 0
        self.last_seen_x = None
        self.last_seen_y = None
        self.alert_timer = 0
        self.search_timer = 0

        # Restore chase distance based on guard type
        chase_distances = {
            "elite": 200,
            "watcher": 180,
            "fast": 140,
            "lazy": 120,
            "normal": 160,
        }
        self.chase_distance = chase_distances.get(self.type, 160)

    def update_speed(self, difficulty):
        self.speed += difficulty * 0.2
        self.chase_speed += difficulty * 0.2