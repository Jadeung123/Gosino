import random
import time

class Roulette:

    def __init__(self):

        self.red_numbers = [
            1,3,5,7,9,12,14,16,18,
            19,21,23,25,27,30,32,34,36
        ]


    def get_color(self, number):

        if number == 0:
            return "green"

        if number in self.red_numbers:
            return "red"

        return "black"


    def play(self, player):

        bet = 10

        if player.money < bet:
            print("Not enough money!")
            return

        print("Roulette Bets:")
        print("1 - Red")
        print("2 - Black")
        print("3 - Number")

        choice = input("Choose bet: ")

        chosen_number = None

        # ask number BEFORE spinning
        if choice == "3":
            chosen_number = int(input("Choose number (0-36): "))

        player.money -= bet

        print("Spinning the wheel...")
        time.sleep(2)

        result_number = random.randint(0,36)
        result_color = self.get_color(result_number)

        print("Result:", result_number, result_color)

        # RED
        if choice == "1":

            if result_color == "red":
                player.money += bet * 2
                print("You won!", bet * 2)

            else:
                print("You lost!")

        # BLACK
        elif choice == "2":

            if result_color == "black":
                player.money += bet * 2
                print("You won!", bet * 2)

            else:
                print("You lost!")

        # NUMBER
        elif choice == "3":

            if chosen_number == result_number:
                player.money += bet * 35
                print("JACKPOT! You won", bet * 35)

            else:
                print("You lost!")