import random

class SlotMachine:

    def play(self, player, score_system, messages):
        bet = 10

        if player.money < bet:
            messages.add("not enough money", player.x, player.y)
            return

        player.money -= bet

        spin = random.randint(1,10)

        if spin >= 8:
            win = bet * 3
            player.money += win
            score_system.add_money_score(win)
            messages.add(f"JACKPOT!! +{win}", player.x, player.y)

        elif spin >= 5:
            win = bet * 2
            player.money += win
            score_system.add_money_score(win)
            messages.add(f"+{win}", player.x, player.y)

        else:
            print("You lost the bet")