# VISUALIZATION.md
# Gosino — Data Visualization Documentation

This file documents all data visualizations in the Gosino statistics system.
All visualizations are drawn in real time inside the game using Pygame primitives.
Data is collected automatically during gameplay and stored in CSV files inside the `stats/` folder.

---

## Overview

The statistics screen contains **5 components** across 5 tabs:
1. Summary Table
2. Payout Distribution (Histogram)
3. Guard Detection Map (Scatter Plot)
4. Shop Item Purchase Frequency (Bar Chart)
5. Player Balance Over Time (Line Graph)

---

## 1. Summary Table

![Summary Table](Summary_Table.png)

The Summary Table provides a statistical overview of five key gameplay features collected across all sessions. Each row shows the Mean, Median, Standard Deviation, Min, and Max for one feature. Looking at this data, the Gambling Payout row shows a mean of \$107,375 but a median of only $20, which reveals that most gambling rounds result in small or zero payouts while a small number of rare jackpot wins create an extreme right skew — this is exactly the expected behavior of a casino game. The Guard Suspicion row (scale 0–100) shows a mean of 99 and median of 60, indicating that most logged detection events happen when guards are already highly suspicious of the player, meaning the player tends to stay in risky zones too long before escaping. The Days Survived row shows a median of 2 days, giving a useful benchmark for average run length across all sessions.

---

## 2. Payout Distribution — Histogram

![Payout Distribution](Payout_Distribution_Graph.png)

This histogram shows how frequently different payout amounts occur across all gambling events recorded in `gambling.csv`. The x-axis represents payout amount in dollars and the y-axis represents how many times that payout range occurred. The chart is capped at the 95th percentile (\$12,145) to prevent rare jackpot outliers from squashing the visible data — 9 outliers above this threshold are noted at the bottom. The dominant bar at $0 with a count of 153 clearly shows that the majority of gambling rounds result in no payout (losses), while smaller bars spread across the range represent winning rounds of varying sizes. This right-skewed distribution confirms that the game is balanced toward frequent small losses with occasional large wins, which is consistent with real casino game design and creates the intended risk-reward tension.

---

## 3. Guard Detection Map — Scatter Plot

![Guard Detection Map](Guard_Detection_Graph.png)

This scatter plot maps every player position where a guard detection event was logged, using the player's X and Y pixel coordinates on the casino floor (800×558 pixels). Each dot is color-coded by suspicion level — green dots represent low suspicion (guard starting to notice the player) and red dots represent high suspicion (guard about to chase). The cluster of dots is concentrated in the center of the map roughly between X=200–600 and Y=200–420, which corresponds to the main gambling floor area where all five mini-game zones are located. This makes sense because the player spends most of their time in this area gambling, increasing the chance of guard encounters. The spread of red dots throughout the center indicates that players frequently get caught mid-floor rather than near the exit, suggesting that guards are most dangerous when the player is between machines.

---

## 4. Shop Item Purchase Frequency — Bar Chart

![Shop Items](Shop_items_purchase_frequency_graph.png)

This bar chart shows how many times each shop item was purchased across all sessions recorded in `shop.csv`, sorted from most to least purchased. Card Counter leads with 40 purchases, followed by Whale Status with 31. These two are both permanent upgrades, which suggests players strongly prefer permanent effects over consumables when they have enough money. Insurance and Loaded Dice are tied at 14 purchases each, while Lucky Charm and Hot Streak trail at 11 and 10 respectively. The preference for permanent upgrades over consumables makes strategic sense — permanent effects compound over multiple days while consumables are single-use. This data could be used to balance item costs or adjust drop rates to encourage more diverse purchasing behavior.

---

## 5. Player Balance Over Time — Line Graph

![Player Balance Over Time](Player_Balance_Over_Time_Graph.png)

This line graph shows the player's money balance at 10-second snapshots throughout each day of gameplay, with each day represented as a separate colored line recorded in `money.csv`. The y-axis is capped at the 95th percentile value ($594,049) to keep the chart readable — 36 extreme values above this threshold are clamped. Most lines cluster near \$0 at the bottom of the chart, representing typical sessions where the player maintains a modest balance. The white and blue lines show dramatically steeper growth curves, indicating sessions where the player achieved a long winning streak — likely through effective use of shop items like Whale Status or Hot Streak combined with high-multiplier gambling. The sharp rises followed by drops visible on some lines reflect the volatility of the gambling system, where a player can quickly gain or lose large amounts in a short window of time.

---

## Data Collection Summary

| CSV File | Records | Key Columns |
|---|---|---|
| `gambling.csv` | Every gambling event | game_type, bet, payout, outcome |
| `detection.csv` | Guard detection events | suspicion_level, player_x, player_y |
| `money.csv` | Balance snapshot every 10s | player_money, debt, day |
| `shop.csv` | Every shop purchase | item_name, item_type, item_cost |
| `day_summary.csv` | End-of-day summary | time_used, wins, losses, debt_paid |
