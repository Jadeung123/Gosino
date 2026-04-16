# constants.py
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
FPS           = 60
TITLE         = "Gosino"

BLACK      = (0,   0,   0)
WHITE      = (255, 255, 255)
GOLD       = (255, 215, 0)
RED        = (200, 50,  50)
GREEN      = (30,  120, 30)
DARK_UI    = (0,   0,   0)

STATE_EXPLORE   = "explore"
STATE_DICE      = "dice"
STATE_SLOTS     = "slots"
STATE_ROULETTE  = "roulette"
STATE_CASE      = "case"
STATE_BLACKJACK = "blackjack"
STATE_SHOP      = "shop"
STATE_UPGRADE   = "upgrade"
STATE_MENU      = "menu"
STATE_GAME_OVER = "game_over"
STATE_TITLE     = "title"
STATE_SETTINGS  = "settings"
STATE_STATS     = "stats"

DEFAULT_FPS        = 60
DEFAULT_FULLSCREEN = False
DEFAULT_SHOW_FPS   = False

DIFFICULTY_INTERVAL = 1800
GUARD_TYPES = ["normal", "fast", "watcher", "lazy"]

PLAY_HEIGHT = 558
HUD_HEIGHT  = 42