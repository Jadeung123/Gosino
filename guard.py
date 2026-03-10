import pygame, random, math

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

    def move(self):
        if self.state == "patrol":
            self.move_timer += 1

            if self.move_timer > 120:
                self.target_angle = random.uniform(0, 360)
                self.move_timer = 0

            if abs(self.angle - self.target_angle) > 1:
                if (self.target_angle - self.angle) % 360 > 180:
                    self.angle -= self.turn_speed
                else:
                    self.angle += self.turn_speed

            rad = math.radians(self.angle)
            self.x += math.cos(rad) * self.speed
            self.y += math.sin(rad) * self.speed

        elif self.state == "alert":
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
                self.x += dx / distance * self.speed
                self.y += dy / distance * self.speed
                self.angle = math.degrees(math.atan2(dy, dx))
            else:
                self.angle += 2
                self.search_timer -= 1
                if self.search_timer <= 0:
                    self.state = "patrol"

    def draw(self, screen):
        rotated = pygame.transform.rotate(self.sprite, -self.angle)
        screen.blit(rotated, (self.x, self.y))

    def see_player(self, player, guards, messages):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance > self.vision_distance:
            self.suspicion = max(0, self.suspicion - 1)
            return False

        angle_to_player = math.degrees(math.atan2(dy, dx))
        diff = (angle_to_player - self.angle + 180) % 360 - 180

        if abs(diff) < 40:
            self.suspicion += 2
        elif abs(diff) < 60:
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

    def draw_vision(self, screen):
        left = math.radians(self.angle - 35)
        right = math.radians(self.angle + 35)

        p1 = (self.x + 16, self.y + 16)
        p2 = (self.x + 16 + math.cos(left) * self.vision_distance,
              self.y + 16 + math.sin(left) * self.vision_distance)
        p3 = (self.x + 16 + math.cos(right) * self.vision_distance,
              self.y + 16 + math.sin(right) * self.vision_distance)

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

    def update_speed(self, difficulty, messages, player):
        messages.add("Guard speed increased", player.x, player.y)
        self.speed += difficulty * 0.2
        self.chase_speed += difficulty * 0.2