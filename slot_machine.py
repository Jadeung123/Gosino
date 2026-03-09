import random

class SlotMachine:

    def play(self, player):

        bet = 10

        if player.money < bet:
            print("Not enough money!")
            return

        player.money -= bet

        spin = random.randint(1,10)

        if spin >= 8:
            win = bet * 3
            player.money += win
            print("JACKPOT! You won", win)

        elif spin >= 5:
            win = bet * 2
            player.money += win
            print("You won", win)

        else:
            print("You lost the bet")