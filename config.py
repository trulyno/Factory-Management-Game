# Game configuration and constants

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
BROWN = (165, 42, 42)

# Game dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
TILE_SIZE = 50
GRID_WIDTH = 30
GRID_HEIGHT = 20
UI_PANEL_WIDTH = 300

# Resource types
RESOURCE_TYPES = {
    'EMPTY': {'color': LIGHT_GRAY, 'value': 0},
    'WOOD': {'color': BROWN, 'value': 10},
    'STONE': {'color': GRAY, 'value': 15},
    'IRON_ORE': {'color': (139, 69, 19), 'value': 25},
    'COPPER_ORE': {'color': (184, 115, 51), 'value': 30},
    'GOLD_ORE': {'color': YELLOW, 'value': 50},
    'COAL': {'color': BLACK, 'value': 20},
    'CLAY': {'color': (210, 105, 30), 'value': 10}
}

# Processed resources
PROCESSED_RESOURCES = {
    'IRON_INGOT': {'from': 'IRON_ORE', 'value': 50, 'time': 5, 'color': (200, 200, 200)},
    'COPPER_INGOT': {'from': 'COPPER_ORE', 'value': 60, 'time': 5, 'color': (184, 115, 51)},
    'GOLD_INGOT': {'from': 'GOLD_ORE', 'value': 100, 'time': 10, 'color': YELLOW},
    'BRICK': {'from': 'CLAY', 'value': 25, 'time': 3, 'color': RED}
}

# Building types and costs
BUILDINGS = {
    'CENTRAL': {'cost': 0, 'color': BLUE},
    'COLLECTION': {'cost': 50, 'color': GREEN},
    'DEPOSIT': {'cost': 100, 'color': YELLOW},
    'PROCESSING': {'cost': 200, 'color': PURPLE},
    'COMMERCE': {'cost': 300, 'color': RED}
}

# Game settings
INITIAL_MONEY = 1000
INITIAL_TILES = 5
WIN_CONDITION = 1000000
SURVEY_COST = 50
TILE_BASE_COST = 100
