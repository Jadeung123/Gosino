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

        self._chase_sound_played = False

    def move(self, walls=None):
        old_x, old_y = self.x, self.y

        if self.state == "patrol":
            self.move_timer += 1

            if self.move_timer > 180:
                # Pick a new angle that's roughly forward-ish — not completely random
                # This prevents the guard from immediately turning back into a wall
                bias = random.uniform(-90, 90)
                self.target_angle = (self.angle + bias) % 360
                self.move_timer = 0

            # Smooth angle interpolation — always takes the shortest arc
            # This eliminates the shaky cone problem
            diff = (self.target_angle - self.angle + 180) % 360 - 180
            if abs(diff) > 1:
                self.angle += max(-self.turn_speed, min(self.turn_speed, diff))
            self.angle = self.angle % 360

            rad = math.radians(self.angle)
            self.x += math.cos(rad) * self.speed
            self.y += math.sin(rad) * self.speed

        elif self.state == "alert":
            # Smooth turn toward last known direction
            diff = (self.target_angle - self.angle + 180) % 360 - 180
            if abs(diff) > 1:
                self.angle += max(-self.turn_speed, min(self.turn_speed, diff))
            self.angle = self.angle % 360

            rad = math.radians(self.angle)
            self.x += math.cos(rad) * (self.speed * 0.6)
            self.y += math.sin(rad) * (self.speed * 0.6)

            self.alert_timer -= 1
            if self.alert_timer <= 0:
                self.state = "patrol"


        elif self.state == "search":
            if self.last_seen_x is None:
                self.state = "patrol"
                return

            dx = self.last_seen_x - self.x
            dy = self.last_seen_y - self.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 5:
                # Smooth turn toward target
                target_angle = math.degrees(math.atan2(dy, dx))
                diff = (target_angle - self.angle + 180) % 360 - 180
                if abs(diff) > 1:
                    self.angle += max(-3, min(3, diff))
                self.angle = self.angle % 360
                rad = math.radians(self.angle)
                self.x = old_x + math.cos(rad) * self.speed
                self.y = old_y + math.sin(rad) * self.speed
            else:
                # Arrived — spin slowly while looking around
                self.angle = (self.angle + 1.5) % 360
                self.search_timer -= 1
                if self.search_timer <= 0:
                    self.state = "patrol"

        # --- Screen boundary clamp ---
        from constants import PLAY_HEIGHT
        self.x = max(10, min(790 - 32, self.x))
        self.y = max(10, min(PLAY_HEIGHT - 32, self.y))

        # --- Wall collision with smart bounce ---
        if walls:
            guard_rect = pygame.Rect(self.x, self.y, 32, 32)
            for wall in walls:
                if guard_rect.colliderect(wall):
                    hit_x = False
                    hit_y = False

                    test_x = pygame.Rect(self.x, old_y, 32, 32)
                    if test_x.colliderect(wall):
                        self.x = old_x
                        hit_x = True

                    test_y = pygame.Rect(old_x, self.y, 32, 32)
                    if test_y.colliderect(wall):
                        self.y = old_y
                        hit_y = True

                    # Smart bounce — reflect angle off the wall axis
                    # instead of picking a random direction
                    if self.state == "patrol":
                        if hit_x and hit_y:
                            # Corner hit — reverse completely
                            self.target_angle = (self.angle + 180) % 360
                        elif hit_x:
                            # Hit a vertical wall — reflect horizontally
                            self.target_angle = (180 - self.angle) % 360
                        elif hit_y:
                            # Hit a horizontal wall — reflect vertically
                            self.target_angle = (360 - self.angle) % 360

                        # Add small random offset so guards don't
                        # bounce perfectly back and forth forever
                        self.target_angle = (self.target_angle + random.uniform(-25, 25)) % 360
                        self.move_timer = 0

    def draw(self, screen):
        """
        Security guard — human shaped with uniform, hat, and facing direction.
        Body rotates to show which way the guard is looking.
        """
        import math

        cx = int(self.x + 16)
        cy = int(self.y + 16)

        rad = math.radians(self.angle)
        dx = math.cos(rad)
        dy = math.sin(rad)

        # Perpendicular axis — used to offset body parts left/right
        px = -dy
        py = dx

        # Uniform colors per guard type
        uniform_colors = {
            "normal": (40, 70, 160),
            "fast": (180, 45, 45),
            "watcher": (40, 130, 70),
            "lazy": (110, 90, 50),
            "elite": (90, 20, 110),
        }
        uniform = uniform_colors.get(self.type, (40, 70, 160))
        dark_uni = tuple(max(0, c - 50) for c in uniform)
        light_uni = tuple(min(255, c + 40) for c in uniform)

        # State ring — drawn first so it appears behind the body
        ring_color = {
            "alert": (255, 220, 0),
            "chase": (255, 50, 50),
            "search": (180, 180, 180),
        }.get(self.state, None)
        if ring_color:
            pygame.draw.circle(screen, ring_color, (cx, cy), 16, 3)

        # Shadow
        pygame.draw.ellipse(screen, (20, 80, 20),
                            (cx - 9, cy + 10, 18, 5))

        # Legs — two small rects pointing away from facing direction
        l1x = int(cx - dx * 2 + px * 4)
        l1y = int(cy - dy * 2 + py * 4)
        l2x = int(cx - dx * 2 - px * 4)
        l2y = int(cy - dy * 2 - py * 4)
        pygame.draw.circle(screen, (30, 30, 30), (l1x, l1y), 4)
        pygame.draw.circle(screen, (30, 30, 30), (l2x, l2y), 4)

        # Body — uniform colored, centered
        pygame.draw.circle(screen, uniform, (cx, cy), 11)

        # Shoulder pads — two lighter circles on the sides
        sp1x = int(cx + px * 9)
        sp1y = int(cy + py * 9)
        sp2x = int(cx - px * 9)
        sp2y = int(cy - py * 9)
        pygame.draw.circle(screen, light_uni, (sp1x, sp1y), 5)
        pygame.draw.circle(screen, light_uni, (sp2x, sp2y), 5)

        # Badge — gold dot on the chest (slightly to the left)
        bx = int(cx + dx * 3 + px * 3)
        by = int(cy + dy * 3 + py * 3)
        pygame.draw.circle(screen, (255, 215, 0), (bx, by), 2)

        # Belt line — dark stripe across the body perpendicular to facing
        b1x = int(cx + px * 10 - dx * 1)
        b1y = int(cy + py * 10 - dy * 1)
        b2x = int(cx - px * 10 - dx * 1)
        b2y = int(cy - py * 10 - dy * 1)
        pygame.draw.line(screen, dark_uni, (b1x, b1y), (b2x, b2y), 3)

        # Body outline
        pygame.draw.circle(screen, dark_uni, (cx, cy), 11, 2)

        # Neck — small circle between body and head
        nx = int(cx + dx * 10)
        ny = int(cy + dy * 10)
        pygame.draw.circle(screen, (190, 150, 110), (nx, ny), 4)

        # Head — skin colored, faces the movement direction
        hx = int(cx + dx * 15)
        hy = int(cy + dy * 15)
        pygame.draw.circle(screen, (210, 170, 120), (hx, hy), 7)

        # Hat — dark circle slightly further in facing direction
        hatx = int(hx + dx * 4)
        haty = int(hy + dy * 4)
        pygame.draw.circle(screen, (20, 20, 20), (hatx, haty), 5)
        # Hat brim — slightly wider flat line
        brim1x = int(hatx + px * 6)
        brim1y = int(haty + py * 6)
        brim2x = int(hatx - px * 6)
        brim2y = int(haty - py * 6)
        pygame.draw.line(screen, (15, 15, 15),
                         (brim1x, brim1y), (brim2x, brim2y), 3)

        # Eyes — two tiny white dots on the head facing forward
        e1x = int(hx + dx * 2 + px * 2)
        e1y = int(hy + dy * 2 + py * 2)
        e2x = int(hx + dx * 2 - px * 2)
        e2y = int(hy + dy * 2 - py * 2)
        pygame.draw.circle(screen, (240, 240, 240), (e1x, e1y), 2)
        pygame.draw.circle(screen, (240, 240, 240), (e2x, e2y), 2)
        pygame.draw.circle(screen, (10, 10, 10), (e1x, e1y), 1)
        pygame.draw.circle(screen, (10, 10, 10), (e2x, e2y), 1)

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
        self._chase_sound_played = False

    def update_speed(self, difficulty):
        self.speed += difficulty * 0.2
        self.chase_speed += difficulty * 0.2