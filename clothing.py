class Clothing:

    def __init__(self, name, cost, suspicion_reduction, durability):
        self.name = name
        self.cost = cost
        self.suspicion_reduction = suspicion_reduction
        self.durability = durability

    def use_day(self):
        self.durability -= 1

    def is_broken(self):
        return self.durability <= 0