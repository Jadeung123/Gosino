import random


class UpgradeManager:

    def __init__(self):

        self.reroll_cost = 300

        # Upgrades the player already owns (tracks name -> level)
        self.owned = []

        # Full upgrade pool — names must match the effect logic below
        self.pool = [
            {"name": "Lucky Dice",        "cost": 400, "desc": "+5% dice win chance per level"},
            {"name": "Fast Feet",         "cost": 350, "desc": "+0.5 movement speed per level", "max_level": 4},
            {"name": "High Roller",       "cost": 500, "desc": "+500 max displayable bet"},
            {"name": "Dice Instinct",     "cost": 300, "desc": "Dice animation 10 frames shorter"},
            {"name": "Blind Spot",        "cost": 450, "desc": "Guard vision -10 per level", "max_level": 3},
            {"name": "Late Shift",        "cost": 500, "desc": "+20 seconds added next day"},
            {"name": "Starting Capital",  "cost": 400, "desc": "+$200 bonus at start of each day"},
            {"name": "Cooldown Master",   "cost": 350, "desc": "Machine cooldowns 20% shorter"},
            {"name": "Adrenaline",        "cost": 450, "desc": "+1 speed when casino is closing", "max_level": 3},
            {"name": "Debt Negotiator",   "cost": 600, "desc": "Debt grows $20 slower each day", "max_level": 3},
        ]

        self.current_choices = []
        self.levels = {}

    # ------------------------------------------------------------------

    def roll_upgrades(self):
        """Pick 3 random upgrades, excluding any that are already maxed out."""

        # Build a filtered pool — only upgrades the player can still level up
        available = [
            upgrade for upgrade in self.pool
            if self.levels.get(upgrade["name"], 0) < upgrade.get("max_level", 99)
        ]

        if len(available) >= 3:
            self.current_choices = random.sample(available, 3)
        else:
            self.current_choices = available.copy()  # show whatever is left

        # Reset bought flag for this round
        for upgrade in self.current_choices:
            upgrade["bought"] = False

    def reroll(self, player):
        """Spend money to get 3 new upgrade choices."""
        if player.money >= self.reroll_cost:
            player.money -= self.reroll_cost
            self.roll_upgrades()
            return True
        return False

    # ------------------------------------------------------------------

    def buy_upgrade(self, index, player, day_system=None):
        """
        Purchase the upgrade at position `index` in current_choices.
        Applies the effect immediately to the player (or day_system).
        `day_system` is optional — only needed for time-based upgrades.
        """
        if index >= len(self.current_choices):
            return

        upgrade = self.current_choices[index]

        if upgrade.get("bought", False):
            return

        # Check max level cap
        name = upgrade["name"]
        max_level = upgrade.get("max_level", 99)  # 99 = effectively uncapped
        current = self.levels.get(name, 0)
        if current >= max_level:
            return

        if player.money < upgrade["cost"]:
            return

        # Deduct cost and mark as purchased
        player.money -= upgrade["cost"]
        upgrade["bought"] = True

        # Track level for display purposes
        name = upgrade["name"]
        self.levels[name] = self.levels.get(name, 0) + 1
        level = self.levels[name]

        # ── Apply the actual effect ────────────────────────────────────

        if name == "Fast Feet":
            # Each level gives +0.5 movement speed
            player.speed += 0.5

        elif name == "Lucky Dice":
            # Each level gives +5 to player.luck
            # DiceGame reads player.luck as a bonus win-chance percentage
            player.luck += 5

        elif name == "Blind Spot":
            # Each level gives +1 stealth
            # Guard.see_player() subtracts player.stealth from its vision_distance
            player.stealth += 1

        elif name == "High Roller":
            # Raises the soft cap shown in dice/slots betting UI
            player.max_bet = getattr(player, "max_bet", 1000) + 500

        elif name == "Dice Instinct":
            # Shortens the dice roll animation by 10 frames per level
            # DiceGame reads player.dice_speed_bonus as a frame reduction
            player.dice_speed_bonus = getattr(player, "dice_speed_bonus", 0) + 10

        elif name == "Late Shift":
            # Adds 20 extra seconds to the NEXT day's time limit
            # day_system is passed in from main.py when calling this method
            if day_system:
                day_system.time_limit += 20 * 60   # 20 seconds in frames

        elif name == "Starting Capital":
            # Grants a daily money bonus at the start of each new day
            # main.py checks player.daily_bonus in _handle_exit / next_day
            player.daily_bonus = getattr(player, "daily_bonus", 0) + 200

        elif name == "Cooldown Master":
            # Reduces all machine cooldown values by 20% per level
            # main.py multiplies cooldowns by (1 - player.cooldown_reduction)
            player.cooldown_reduction = getattr(player, "cooldown_reduction", 0.0) + 0.20

        elif name == "Adrenaline":
            # When casino is closing, player gets +1 speed bonus
            # main.py applies this in _update_explore when day_system.closing
            player.adrenaline_bonus = getattr(player, "adrenaline_bonus", 0) + 1

        elif name == "Debt Negotiator":
            # Reduces the per-day debt increase by $20 per level
            # main.py passes player.debt_reduction into day_system.next_day()
            player.debt_reduction = getattr(player, "debt_reduction", 0) + 20