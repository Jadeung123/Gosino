import pygame
from player import Player
from map import CasinoMap
from time_system import TimeSystem
from slot_machine import SlotMachine
from shop import Shop
from suspicion_system import SuspicionSystem
from guard import Guard

pygame.init()

WIDTH = 800
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gorilla Gambler")

clock = pygame.time.Clock()

player = Player(400, 300)
casino_map = CasinoMap()
time_system = TimeSystem()
slot_machine = SlotMachine()
shop = Shop()
suspicion = SuspicionSystem()

guards = [
    Guard(300,200),
    Guard(500,400),
    Guard(700,250)
]

running = True

while running:

    clock.tick(60)

    for guard in guards:
        if guard.see_player(player):
            suspicion.increase(1)

    # EVENTS
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_e:
                interaction = casino_map.check_interaction(player.get_rect())

                if interaction == "slots":
                    slot_machine.play(player)
                    suspicion.increase(5)

                elif interaction == "dice":
                    print("Playing dice game")

                elif interaction == "roulette":
                    print("Playing roulette")

                elif interaction == "shop":
                    shop.open_shop(player)

    # MOVEMENT
    for guard in guards:
        guard.move()

    keys = pygame.key.get_pressed()
    moved = player.move(keys)

    if suspicion.is_caught():
        print("Security caught the gorilla!")
        running = False

    if moved:
        time_system.add_time(1)

    # DRAW
    screen.fill((30, 120, 30))  # casino floor color

    casino_map.draw(screen)
    player.draw(screen)

    time_system.draw(screen, player)
    suspicion.draw(screen)
    for guard in guards:
        guard.draw_vision(screen)
    for guard in guards:
        guard.draw(screen)

    pygame.display.update()

pygame.quit()