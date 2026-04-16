# In-game statistics screen showing graphs and summary table.
# Reads from the CSV files in /stats/ and renders using pygame.
# No matplotlib needed — everything drawn with pygame primitives.

import pygame
import csv
import os

GOLD  = (255, 215,   0)
WHITE = (255, 255, 255)
RED   = (220,  60,  60)
GREEN = ( 80, 200, 100)
BLUE  = ( 80, 160, 255)


def _load_csv(name):
    """Load a CSV into a list of dicts. Returns [] if missing."""
    path = os.path.join("stats", f"{name}.csv")
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class StatsScreen:

    def __init__(self):
        self.font_hd = pygame.font.SysFont(None, 38)
        self.font    = pygame.font.SysFont(None, 28)
        self.font_sm = pygame.font.SysFont(None, 22)
        self.tab     = 0   # 0=Table, 1=Graph1, 2=Graph2, 3=Graph3, 4=Graph4
        self.tabs    = ["Summary Table", "Payout Dist.", "Detection Map",
                        "Shop Items", "Money Over Time"]

    # ------------------------------------------------------------------

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "exit"
            if event.key == pygame.K_LEFT:
                self.tab = (self.tab - 1) % len(self.tabs)
            if event.key == pygame.K_RIGHT:
                self.tab = (self.tab + 1) % len(self.tabs)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            for i, tab_rect in enumerate(self._tab_rects):
                if tab_rect.collidepoint(mx, my):
                    self.tab = i
            if self._exit_rect().collidepoint(mx, my):
                return "exit"
        return None

    # ------------------------------------------------------------------

    def draw(self, screen):
        W, H = screen.get_size()
        screen.fill((10, 10, 20))

        # Background stripes
        for i in range(-H, W + H, 36):
            pygame.draw.line(screen, (16, 16, 28), (i, 0), (i + H, H), 14)

        # Title
        t = self.font_hd.render("STATISTICS", True, GOLD)
        screen.blit(t, t.get_rect(center=(W // 2, 28)))

        # Tab buttons
        self._tab_rects = []
        tab_w = (W - 40) // len(self.tabs)
        for i, label in enumerate(self.tabs):
            r = pygame.Rect(20 + i * tab_w, 52, tab_w - 4, 32)
            self._tab_rects.append(r)
            active = (i == self.tab)
            pygame.draw.rect(screen, (40, 40, 80) if active else (20, 20, 35),
                             r, border_radius=4)
            pygame.draw.rect(screen, GOLD if active else (50, 50, 70),
                             r, 1, border_radius=4)
            ls = self.font_sm.render(label, True,
                                     GOLD if active else (150, 150, 150))
            screen.blit(ls, ls.get_rect(center=r.center))

        # Content area
        content_y = 95
        content_h = H - content_y - 50

        if self.tab == 0:
            self._draw_table(screen, W, content_y, content_h)
        elif self.tab == 1:
            self._draw_payout_histogram(screen, W, content_y, content_h)
        elif self.tab == 2:
            self._draw_detection_scatter(screen, W, content_y, content_h)
        elif self.tab == 3:
            self._draw_shop_bar(screen, W, content_y, content_h)
        elif self.tab == 4:
            self._draw_money_line(screen, W, content_y, content_h)

        # Exit button
        er = self._exit_rect()
        pygame.draw.rect(screen, (40, 20, 20), er, border_radius=6)
        pygame.draw.rect(screen, (150, 60, 60), er, 2, border_radius=6)
        el = self.font_sm.render("ESC / Click to close", True, (180, 100, 100))
        screen.blit(el, el.get_rect(center=er.center))

        # Navigation hint
        hint = self.font_sm.render("← → to switch tabs", True, (60, 60, 80))
        screen.blit(hint, hint.get_rect(center=(W // 2, H - 14)))

    def _exit_rect(self):
        return pygame.Rect(600, 560, 180, 30)

    # ------------------------------------------------------------------
    # TAB 0 — Summary Statistics Table
    # ------------------------------------------------------------------

    def _draw_table(self, screen, W, y0, h):
        gambling = _load_csv("gambling")
        detection = _load_csv("detection")
        money    = _load_csv("money")
        shop     = _load_csv("shop")
        days     = _load_csv("day_summary")

        def safe_stats(rows, key):
            vals = []
            for r in rows:
                try: vals.append(float(r[key]))
                except: pass
            if not vals:
                return None
            n   = len(vals)
            avg = sum(vals) / n
            mn  = min(vals)
            mx  = max(vals)
            s   = vals[:]
            s.sort()
            med = s[n // 2] if n % 2 else (s[n//2-1] + s[n//2]) / 2
            variance = sum((v - avg)**2 for v in vals) / n
            std = variance ** 0.5
            return avg, med, std, mn, mx

        headers = ["Feature", "Mean", "Median", "Std Dev", "Min", "Max"]
        col_w   = [200, 90, 90, 90, 90, 90]
        col_x   = [20]
        for w in col_w[:-1]:
            col_x.append(col_x[-1] + w)

        # Header row
        hry = y0 + 10
        pygame.draw.rect(screen, (30, 30, 60),
                         (20, hry, W - 40, 28), border_radius=4)
        for i, h_label in enumerate(headers):
            s = self.font_sm.render(h_label, True, GOLD)
            screen.blit(s, (col_x[i] + 4, hry + 6))

        # Data rows
        features = [
            ("Gambling Payout ($)", gambling, "payout"),
            ("Guard Suspicion",     detection, "suspicion_level"),
            ("Player Money ($)",    money,     "player_money"),
            ("Shop Item Cost ($)",  shop,      "item_cost"),
            ("Days Survived",       days,      "day_number"),
        ]

        for idx, (label, rows, key) in enumerate(features):
            ry = hry + 34 + idx * 36
            bg = (18, 18, 32) if idx % 2 == 0 else (22, 22, 38)
            pygame.draw.rect(screen, bg, (20, ry, W - 40, 32), border_radius=3)

            screen.blit(self.font_sm.render(label, True, WHITE),
                        (col_x[0] + 4, ry + 8))

            stats = safe_stats(rows, key)
            if stats:
                avg, med, std, mn, mx = stats
                for ci, val in enumerate([avg, med, std, mn, mx]):
                    txt = f"{val:.0f}"
                    s   = self.font_sm.render(txt, True, (180, 220, 180))
                    screen.blit(s, (col_x[ci + 1] + 4, ry + 8))
            else:
                screen.blit(self.font_sm.render("No data yet", True, (80, 80, 80)),
                            (col_x[1] + 4, ry + 8))

        # Note
        note = self.font_sm.render(
            "Play more sessions to accumulate data for accurate statistics.",
            True, (70, 70, 90))
        screen.blit(note, note.get_rect(center=(W // 2, y0 + h - 10)))

    # ------------------------------------------------------------------
    # TAB 1 — Payout Histogram (Distribution)
    # ------------------------------------------------------------------

    def _draw_payout_histogram(self, screen, W, y0, h):
        gambling = _load_csv("gambling")
        if not gambling:
            self._no_data(screen, W, y0, h)
            return

        payouts = []
        for r in gambling:
            try: payouts.append(float(r["payout"]))
            except: pass

        if not payouts:
            self._no_data(screen, W, y0, h)
            return

        # Build 10 bins
        payouts_sorted = sorted(payouts)
        mn = min(payouts)

        p95_idx = int(len(payouts_sorted) * 0.95)
        mx = payouts_sorted[min(p95_idx, len(payouts_sorted) - 1)]
        outliers = sum(1 for v in payouts if v > mx)

        if mx == mn:
            self._no_data(screen, W, y0, h, "All payouts are the same value.")
            return

        bins = 10
        bin_size = (mx - mn) / bins
        counts = [0] * bins
        for v in payouts:
            if v <= mx:
                idx = min(int((v - mn) / bin_size), bins - 1)
                counts[idx] += 1

        # Draw axes
        ax_x, ax_y = 80, y0 + h - 40
        ax_w, ax_h = W - 120, h - 60

        pygame.draw.line(screen, WHITE, (ax_x, y0 + 10), (ax_x, ax_y), 2)
        pygame.draw.line(screen, WHITE, (ax_x, ax_y), (ax_x + ax_w, ax_y), 2)

        # Title + axis labels
        screen.blit(self.font.render("Payout Amount Distribution (Histogram)",
                                     True, GOLD),
                    (ax_x, y0 + 6))
        screen.blit(self.font_sm.render("Payout ($)", True, WHITE),
                    (ax_x + ax_w // 2 - 30, ax_y + 14))
        y_label = self.font_sm.render("Frequency", True, WHITE)
        y_label_rot = pygame.transform.rotate(y_label, 90)
        screen.blit(y_label_rot, y_label_rot.get_rect(
            center=(ax_x - 30, y0 + 10 + (ax_h // 2))
        ))

        # Bars
        max_count = max(counts) if max(counts) > 0 else 1
        bar_w     = ax_w // bins - 2
        for i, count in enumerate(counts):
            bx  = ax_x + i * (ax_w // bins) + 2
            bh  = int((count / max_count) * (ax_h - 20))
            by  = ax_y - bh
            pygame.draw.rect(screen, GOLD, (bx, by, bar_w, bh))
            pygame.draw.rect(screen, (180, 140, 0), (bx, by, bar_w, bh), 1)

            # X tick label
            label = f"${int(mn + i * bin_size)}"
            ls    = self.font_sm.render(label, True, (150, 150, 150))
            screen.blit(ls, (bx, ax_y + 4))

            # Count on top of bar
            if count > 0:
                cs = self.font_sm.render(str(count), True, WHITE)
                screen.blit(cs, (bx + bar_w // 2 - cs.get_width() // 2, by - 18))

        if outliers > 0:
            note = self.font_sm.render(
                f"{outliers} outlier(s) above ${int(mx):,} hidden for readability",
                True, (160, 120, 80)
            )
            screen.blit(note, (ax_x, ax_y + 30))
    # ------------------------------------------------------------------
    # TAB 2 — Detection Scatter Plot
    # ------------------------------------------------------------------

    def _draw_detection_scatter(self, screen, W, y0, h):
        detection = _load_csv("detection")
        if not detection:
            self._no_data(screen, W, y0, h)
            return

        ax_x, ax_y = 110, y0 + h - 55
        ax_w = W - 150
        ax_h = h - 90

        # Title — above the plot with enough clearance
        screen.blit(self.font.render("Guard Detection Positions (Danger Map)",
                                     True, GOLD),
                    (ax_x, y0 + 8))

        # Axes
        pygame.draw.line(screen, WHITE, (ax_x, y0 + 34), (ax_x, ax_y), 2)
        pygame.draw.line(screen, WHITE, (ax_x, ax_y), (ax_x + ax_w, ax_y), 2)

        # X axis ticks + label
        for val in [0, 200, 400, 600, 800]:
            sx = ax_x + int(val / 800 * ax_w)
            pygame.draw.line(screen, (80, 80, 80), (sx, ax_y), (sx, ax_y + 4), 1)
            ls = self.font_sm.render(str(val), True, (100, 100, 100))
            screen.blit(ls, ls.get_rect(midtop=(sx, ax_y + 6)))
        screen.blit(self.font_sm.render("Player X (pixels)", True, WHITE),
                    self.font_sm.render("Player X (pixels)", True, WHITE)
                    .get_rect(midtop=(ax_x + ax_w // 2, ax_y + 22)))

        # Y axis ticks + label (rotated)
        for val in [0, 140, 280, 420, 558]:
            sy = y0 + 34 + int(val / 558 * ax_h)
            pygame.draw.line(screen, (80, 80, 80), (ax_x - 4, sy), (ax_x, sy), 1)
            ls = self.font_sm.render(str(val), True, (100, 100, 100))
            screen.blit(ls, ls.get_rect(midright=(ax_x - 8, sy)))
        y_label = self.font_sm.render("Player Y (pixels)", True, WHITE)
        y_label_rot = pygame.transform.rotate(y_label, 90)
        screen.blit(y_label_rot, y_label_rot.get_rect(
            center=(ax_x - 40, y0 + 34 + ax_h // 2)
        ))

        # Scale game coords (800 x 558) to plot area
        for row in detection:
            try:
                px = float(row["player_x"])
                py = float(row["player_y"])
                sl = float(row["suspicion_level"])
            except:
                continue

            # Map to plot coords
            sx = ax_x + int(px / 800 * ax_w)
            sy = y0 + 34 + int(py / 558 * ax_h)

            # Color by suspicion — low=green, high=red
            ratio = min(sl / 60, 1.0)
            color = (int(220 * ratio), int(200 * (1 - ratio)), 60)
            pygame.draw.circle(screen, color, (sx, sy), 4)

        # Legend
        screen.blit(self.font_sm.render("Low suspicion", True, (60, 200, 60)),
                    (ax_x + ax_w - 140, y0 + 20))
        screen.blit(self.font_sm.render("High suspicion", True, (220, 60, 60)),
                    (ax_x + ax_w - 140, y0 + 36))

    # ------------------------------------------------------------------
    # TAB 3 — Shop Bar Chart
    # ------------------------------------------------------------------

    def _draw_shop_bar(self, screen, W, y0, h):
        shop = _load_csv("shop")
        if not shop:
            self._no_data(screen, W, y0, h)
            return

        # Count purchases per item
        counts = {}
        for row in shop:
            name = row.get("item_name", "Unknown")
            counts[name] = counts.get(name, 0) + 1

        if not counts:
            self._no_data(screen, W, y0, h)
            return

        items  = sorted(counts.items(), key=lambda x: -x[1])
        labels = [i[0] for i in items]
        values = [i[1] for i in items]

        ax_x, ax_y = 80, y0 + h - 60
        ax_w = W - 120
        ax_h = h - 80

        pygame.draw.line(screen, WHITE, (ax_x, y0 + 10), (ax_x, ax_y), 2)
        pygame.draw.line(screen, WHITE, (ax_x, ax_y), (ax_x + ax_w, ax_y), 2)

        screen.blit(self.font.render("Shop Item Purchase Frequency (Bar Chart)",
                                     True, GOLD), (ax_x, y0 + 6))

        max_val = max(values) if values else 1
        bar_w   = min(80, (ax_w - 10) // len(labels) - 8)
        colors  = [RED, GOLD, GREEN, BLUE,
                   (220, 130, 60), (180, 80, 220)]

        for i, (label, val) in enumerate(zip(labels, values)):
            bx = ax_x + 10 + i * ((ax_w - 10) // len(labels))
            bh = int((val / max_val) * (ax_h - 20))
            by = ax_y - bh

            pygame.draw.rect(screen, colors[i % len(colors)],
                             (bx, by, bar_w, bh), border_radius=4)

            # Value on top
            vs = self.font_sm.render(str(val), True, WHITE)
            screen.blit(vs, (bx + bar_w // 2 - vs.get_width() // 2, by - 18))

            # Label below axis — wrap long names
            words = label.split()
            for wi, word in enumerate(words[:2]):
                ls = self.font_sm.render(word, True, (150, 150, 150))
                screen.blit(ls, (bx, ax_y + 6 + wi * 16))

    # ------------------------------------------------------------------
    # TAB 4 — Money Over Time Line Graph
    # ------------------------------------------------------------------

    def _draw_money_line(self, screen, W, y0, h):
        money = _load_csv("money")
        if not money:
            self._no_data(screen, W, y0, h)
            return

        # More margin for Y axis labels and title
        ax_x = 110
        ax_y = y0 + h - 55
        ax_w = W - 150
        ax_h = h - 90

        # Title
        screen.blit(self.font.render("Player Balance Over Time (Line Graph)",
                                     True, GOLD), (ax_x, y0 + 8))

        # Group by day
        days = {}
        for row in money:
            d = row.get("day", "1")
            if d not in days:
                days[d] = []
            try:
                days[d].append(float(row["player_money"]))
            except:
                pass

        if not days:
            self._no_data(screen, W, y0, h)
            return

        all_vals = [v for vals in days.values() for v in vals]

        # Cap at 95th percentile to prevent outliers squashing the chart
        all_sorted = sorted(all_vals)
        p95_idx = int(len(all_sorted) * 0.95)
        mx_v = all_sorted[min(p95_idx, len(all_sorted) - 1)]
        mn_v = 0  # always start y-axis at 0
        outliers = sum(1 for v in all_vals if v > mx_v)

        if mx_v == mn_v:
            mx_v = mn_v + 1

        # Axes
        pygame.draw.line(screen, WHITE, (ax_x, y0 + 34), (ax_x, ax_y), 2)
        pygame.draw.line(screen, WHITE, (ax_x, ax_y), (ax_x + ax_w, ax_y), 2)

        # X axis label
        xl = self.font_sm.render("Time elapsed (snapshots every 10s)", True, WHITE)
        screen.blit(xl, xl.get_rect(midtop=(ax_x + ax_w // 2, ax_y + 22)))

        # Y axis ticks + rotated label
        for pct in [0, 25, 50, 75, 100]:
            val = mn_v + (mx_v - mn_v) * pct / 100
            sy = ax_y - int(pct / 100 * ax_h)
            pygame.draw.line(screen, (50, 50, 70), (ax_x, sy), (ax_x + ax_w, sy), 1)
            pygame.draw.line(screen, (80, 80, 80), (ax_x - 4, sy), (ax_x, sy), 1)
            ls = self.font_sm.render(f"${int(val):,}", True, (100, 100, 100))
            screen.blit(ls, ls.get_rect(midright=(ax_x - 8, sy)))

        y_label = self.font_sm.render("Balance ($)", True, WHITE)
        y_label_rot = pygame.transform.rotate(y_label, 90)
        screen.blit(y_label_rot, y_label_rot.get_rect(
            center=(ax_x - 55, y0 + 34 + ax_h // 2)
        ))

        # Lines — one per day, clamp values to mx_v
        line_colors = [GOLD, GREEN, RED, BLUE,
                       (220, 130, 60), (180, 80, 220), WHITE]

        for di, (day_num, vals) in enumerate(sorted(days.items(),
                                                    key=lambda x: int(x[0]))):
            if len(vals) < 2:
                continue
            color = line_colors[di % len(line_colors)]
            points = []
            for vi, v in enumerate(vals):
                v_clamped = min(v, mx_v)
                sx = ax_x + int(vi / (len(vals) - 1) * ax_w)
                sy = ax_y - int((v_clamped - mn_v) / (mx_v - mn_v) * ax_h)
                points.append((sx, sy))

            if len(points) >= 2:
                pygame.draw.lines(screen, color, False, points, 2)

            # Day label — stacked on right side to avoid overlap
            ls = self.font_sm.render(f"Day {day_num}", True, color)
            label_y = y0 + 34 + di * 20  # stack labels top-right
            screen.blit(ls, (ax_x + ax_w + 6, label_y))
            # Small color dot to connect label to line
            pygame.draw.circle(screen, color, (ax_x + ax_w + 3, label_y + 7), 4)

        # Outlier note
        if outliers > 0:
            note = self.font_sm.render(
                f"{outliers} value(s) above ${int(mx_v):,} clamped for readability",
                True, (160, 120, 80)
            )
            screen.blit(note, note.get_rect(midtop=(ax_x + ax_w // 2, ax_y + 38)))

    # ------------------------------------------------------------------

    def _no_data(self, screen, W, y0, h, msg="No data yet — play some sessions first!"):
        s = self.font.render(msg, True, (80, 80, 100))
        screen.blit(s, s.get_rect(center=(W // 2, y0 + h // 2)))