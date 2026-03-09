from clothing import Clothing

class Shop:

    def __init__(self):

        self.items = [
            Clothing("Sunglasses",50,5,3),
            Clothing("Hat",80,10,4),
            Clothing("Suit",200,20,5)
        ]

    def open_shop(self, player):

        print("Welcome to the disguise shop")

        for i,item in enumerate(self.items):
            print(i, item.name, "Cost:", item.cost)

        choice = input("Choose item number: ")

        if not choice.isdigit():
            return

        choice = int(choice)

        if choice >= len(self.items):
            return

        item = self.items[choice]

        if player.money >= item.cost:

            player.money -= item.cost
            player.add_clothing(item)

            print("You bought", item.name)

        else:
            print("Not enough money")