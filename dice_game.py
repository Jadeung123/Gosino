import random
import time

class DiceGame:

    def play(self, player, score_system):
        bet = 10

        if player.money < bet:
            print("Not enough money!")
            return

        player.money -= bet

        print("Rolling dice...")
        time.sleep(1)

        dice1 = random.randint(1,6)
        dice2 = random.randint(1,6)
        total = dice1 + dice2
        print("Dice:", dice1, "+", dice2, "=", total)

        # WIN
        if total == 7 or total == 11:
            win = bet * 2
            player.money += win
            score_system.add_money_score(win)

            print("You win!", win)

        # LOSE
        elif total in [2,3,12]:
            print("Craps! You lose!")

        # ROLL AGAIN
        else:
            print("Roll again to beat", total)
            point = total

            while True:
                input("Press Enter to roll again...")

                dice1 = random.randint(1,6)
                dice2 = random.randint(1,6)

                total = dice1 + dice2

                print("Dice:", dice1, "+", dice2, "=", total)

                if total == point:
                    win = bet * 2
                    player.money += win
                    score_system.add_money_score(win)

                    print("You hit your number! You win", win)
                    break

                elif total == 7:
                    print("Rolled a 7! You lose!")
                    break