# Collects and saves gameplay statistics to CSV files.
# One CSV per feature — all stored in the /stats/ folder.
# Each row has a timestamp so data from multiple sessions
# can be distinguished during analysis.

import csv
import os
from datetime import datetime


class StatsLogger:

    STATS_DIR = "stats"

    # Column headers for each CSV file
    HEADERS = {
        "gambling": [
            "timestamp", "day", "game_type", "bet_amount",
            "payout", "outcome", "shop_effect_used",
            "player_money_before", "player_money_after"
        ],
        "detection": [
            "timestamp", "day", "guard_id", "guard_type",
            "guard_state", "suspicion_level",
            "player_x", "player_y", "guard_x", "guard_y"
        ],
        "money": [
            "timestamp", "day", "time_remaining_s",
            "player_money", "debt", "net_balance"
        ],
        "shop": [
            "timestamp", "day", "item_name", "item_type",
            "item_cost", "player_money_after"
        ],
        "day_summary": [
            "timestamp", "day_number", "time_limit_s",
            "time_used_s", "starting_money", "ending_money",
            "debt_paid", "total_bets", "total_wins",
            "total_losses", "guards_triggered", "items_purchased"
        ],
    }

    def __init__(self):
        # Create stats folder if it doesn't exist
        os.makedirs(self.STATS_DIR, exist_ok=True)

        # Open one file writer per feature — append mode so
        # data from multiple sessions accumulates in the same file
        self._writers  = {}
        self._files    = {}

        for name, headers in self.HEADERS.items():
            path       = os.path.join(self.STATS_DIR, f"{name}.csv")
            file_exists = os.path.exists(path)
            f          = open(path, "a", newline="", encoding="utf-8")
            writer     = csv.writer(f)

            # Only write headers if the file is brand new
            if not file_exists or os.path.getsize(path) == 0:
                writer.writerow(headers)

            self._files[name]   = f
            self._writers[name] = writer

        # Session-level counters — reset each day
        self.session_bets       = 0
        self.session_wins       = 0
        self.session_losses     = 0
        self.session_detections = 0
        self.session_purchases  = 0
        self.day_start_money    = 0

        # Money snapshot timer — logs every 10 real seconds
        self._snapshot_timer    = 0
        self._snapshot_interval = 600   # 60 FPS x 10 seconds

    # ------------------------------------------------------------------
    # Feature 1 — Gambling Event
    # ------------------------------------------------------------------

    def log_gamble(self, day, game_type, bet, payout,
                   outcome, shop_effect, money_before, money_after):
        """
        Call this inside every _resolve() method after an outcome is decided.
        outcome should be 'win', 'loss', or 'jackpot'.
        """
        self._writers["gambling"].writerow([
            self._ts(), day, game_type, bet,
            payout, outcome, shop_effect,
            money_before, money_after
        ])
        self._files["gambling"].flush()

        self.session_bets += 1
        if outcome in ("win", "jackpot"):
            self.session_wins += 1
        else:
            self.session_losses += 1

    # ------------------------------------------------------------------
    # Feature 2 — Guard Detection Event
    # ------------------------------------------------------------------

    def log_detection(self, day, guard_id, guard_type, guard_state,
                      suspicion, player_x, player_y, guard_x, guard_y):
        """
        Call this inside Guard.see_player() when suspicion crosses
        a meaningful threshold (e.g. every 20 points).
        """
        self._writers["detection"].writerow([
            self._ts(), day, guard_id, guard_type,
            guard_state, round(suspicion, 1),
            round(player_x), round(player_y),
            round(guard_x),  round(guard_y)
        ])
        self._files["detection"].flush()
        self.session_detections += 1

    # ------------------------------------------------------------------
    # Feature 3 — Player Money Snapshot
    # ------------------------------------------------------------------

    def update(self, day, time_remaining_s, player_money, debt):
        """
        Call every frame from _update_systems() in main.py.
        Automatically logs a snapshot every 10 real seconds.
        """
        self._snapshot_timer += 1
        if self._snapshot_timer >= self._snapshot_interval:
            self._snapshot_timer = 0
            net = player_money - debt
            self._writers["money"].writerow([
                self._ts(), day, time_remaining_s,
                player_money, debt, net
            ])
            self._files["money"].flush()

    # ------------------------------------------------------------------
    # Feature 4 — Shop Purchase Event
    # ------------------------------------------------------------------

    def log_purchase(self, day, item_name, item_type,
                     item_cost, player_money_after):
        """Call this inside Shop._buy() on every successful purchase."""
        self._writers["shop"].writerow([
            self._ts(), day, item_name, item_type,
            item_cost, player_money_after
        ])
        self._files["shop"].flush()
        self.session_purchases += 1

    # ------------------------------------------------------------------
    # Feature 5 — Day Completion Summary
    # ------------------------------------------------------------------

    def log_day_summary(self, day, time_limit_s, time_used_s,
                        starting_money, ending_money, debt_paid):
        """Call this inside Game._handle_exit() when a day ends."""
        self._writers["day_summary"].writerow([
            self._ts(), day, time_limit_s, time_used_s,
            starting_money, ending_money,
            1 if debt_paid else 0,
            self.session_bets, self.session_wins, self.session_losses,
            self.session_detections, self.session_purchases
        ])
        self._files["day_summary"].flush()

        # Reset session counters for next day
        self.session_bets       = 0
        self.session_wins       = 0
        self.session_losses     = 0
        self.session_detections = 0
        self.session_purchases  = 0

    def set_day_start_money(self, money):
        """Call at the start of each day to track starting balance."""
        self.day_start_money = money

    # ------------------------------------------------------------------

    def close(self):
        """Call when the game exits to flush and close all CSV files."""
        for f in self._files.values():
            f.close()

    def _ts(self):
        """Returns current datetime as a string timestamp."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")