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

# World settings
WORLD_SIZE_SMALL = {'width': 30, 'height': 20}
WORLD_SIZE_MEDIUM = {'width': 50, 'height': 30}
WORLD_SIZE_LARGE = {'width': 80, 'height': 50}
WORLD_SIZE = WORLD_SIZE_MEDIUM  # Default world size

# Resource rarity settings
RESOURCE_RARITY = {
    'COMMON': {'multiplier': 1.0, 'durability_range': (50, 80)},
    'NORMAL': {'multiplier': 0.7, 'durability_range': (30, 50)},
    'RARE': {'multiplier': 0.4, 'durability_range': (15, 30)},
    'VERY_RARE': {'multiplier': 0.2, 'durability_range': (5, 15)}
}

# Resource distribution (default rarity is NORMAL)
RESOURCE_DISTRIBUTION = {
    'EMPTY': {'rarity': 'COMMON'},
    'WOOD': {'rarity': 'COMMON'},
    'STONE': {'rarity': 'COMMON'},
    'IRON_ORE': {'rarity': 'NORMAL'},
    'COPPER_ORE': {'rarity': 'NORMAL'},
    'COAL': {'rarity': 'NORMAL'},
    'CLAY': {'rarity': 'NORMAL'},
    'GOLD_ORE': {'rarity': 'RARE'}
}

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
    'BRICK': {'from': 'CLAY', 'value': 25, 'time': 3, 'color': RED},
    'STEEL': {'from': 'IRON_INGOT', 'value': 100, 'time': 12, 'color': (100, 100, 120)},
    'PLANK': {'from': 'WOOD', 'value': 20, 'time': 2, 'color': (139, 69, 19)},
}

# Processing recipes
RECIPES = {
    'IRON_INGOT': {
        'input1': 'IRON_ORE',
        'input2': 'COAL',
        'output': 'IRON_INGOT',
        'duration': 8,
        'output_amount': 1
    },
    'COPPER_INGOT': {
        'input1': 'COPPER_ORE',
        'input2': 'COAL',
        'output': 'COPPER_INGOT',
        'duration': 6,
        'output_amount': 1
    },
    'GOLD_INGOT': {
        'input1': 'GOLD_ORE',
        'input2': None,
        'output': 'GOLD_INGOT',
        'duration': 10,
        'output_amount': 1
    },
    'BRICK': {
        'input1': 'CLAY',
        'input2': None,
        'output': 'BRICK',
        'duration': 4,
        'output_amount': 2
    },
    'STEEL': {
        'input1': 'IRON_INGOT',
        'input2': 'COAL',
        'output': 'STEEL',
        'duration': 12,
        'output_amount': 1
    },
    'PLANK': {
        'input1': 'WOOD',
        'input2': None,
        'output': 'PLANK',
        'duration': 3,
        'output_amount': 2
    }
}

# Building types and costs
BUILDINGS = {
    'CENTRAL': {'base_cost': 0, 'cost': 0, 'color': BLUE},
    'COLLECTION': {'base_cost': 50, 'cost': 50, 'color': GREEN},
    'DEPOSIT': {'base_cost': 100, 'cost': 100, 'color': YELLOW},
    'PROCESSING': {'base_cost': 200, 'cost': 200, 'color': PURPLE},
    'COMMERCE': {'base_cost': 300, 'cost': 300, 'color': RED}
}

# Game settings
INITIAL_MONEY = 1000
INITIAL_TILES = 5
WIN_CONDITION = 10000

# Base pricing settings
SURVEY_BASE_COST = 50
TILE_BASE_COST = 100
TILE_COST_MULTIPLIER = 0.9

# Dynamic pricing configuration
PRICE_UPDATE_INTERVAL = 60  # Seconds between price adjustments (more frequent updates)
PRICE_INCREASE_RATE = 0.02  # Base percentage increase per update (smoother progression)
MAX_PRICE_MULTIPLIER = 5.0  # Maximum price multiplier from base price
MIN_PRICE_MULTIPLIER = 0.8  # Minimum price multiplier (prevents prices getting too low)
ECONOMY_SCALING_FACTOR = 0.00008  # How much total economy affects prices
BUILDINGS_SCALING_FACTOR = 0.015  # How much total buildings affects prices
TILES_SCALING_FACTOR = 0.008  # How much surveyed tiles affects prices
TIME_SCALING_FACTOR = 0.002  # How much game time affects prices
DIFFICULTY_SCALING = {
    'EASY': 0.7,      # 70% of normal price increases
    'NORMAL': 1.0,    # Normal price increases
    'HARD': 1.3       # 130% of normal price increases
}

# Collection and Transport settings
COLLECTION_DURATION = 5  # seconds between resource collection
TRANSPORT_DURATION_PER_UNIT_OF_DISTANCE = 0.5  # seconds per tile distance
DEPOSIT_SIZE = 100  # maximum resources per deposit
MAX_RESOURCE_TYPES_PER_DEPOSIT = 3  # maximum different types of resources in a deposit
AUTOSELL_DURATION = 10  # seconds between auto-selling

# AI settings
NUM_AI_PLAYERS = 3  # Default number of AI players
AI_DIFFICULTY_LEVELS = {
    'EASY': {'decision_speed': 1.5, 'expansion_rate': 0.5, 'survey_probability': 0.2},
    'NORMAL': {'decision_speed': 1.0, 'expansion_rate': 0.7, 'survey_probability': 0.3},
    'HARD': {'decision_speed': 0.7, 'expansion_rate': 0.9, 'survey_probability': 0.4}
}
AI_DIFFICULTY = 'NORMAL'  # Default AI difficulty
AI_DECISION_MIN_TIME = 3.0  # Minimum seconds between AI decisions
AI_DECISION_MAX_TIME = 8.0  # Maximum seconds between AI decisions
AI_SURVEY_PROBABILITY = 0.3  # Probability of choosing to survey instead of build/buy
AI_BUILD_TILE_PROBABILITY = 0.5  # Probability of buying a tile vs. building (when both are possible)
AI_COMMERCE_THRESHOLD = 1500  # Money threshold before considering commerce buildings
AI_PROCESSING_THRESHOLD = 800  # Money threshold before considering processing buildings
AI_EXPANSION_RATE = 0.7  # Higher values make AI more likely to expand territory

# Market settings
MARKET_UPDATE_INTERVAL = 10  # Seconds between market price updates
MARKET_PRICE_ADJUSTMENT_FACTOR = 0.05  # Maximum percentage change in price per update
MARKET_MAX_PRICE_MULTIPLIER = 2.5  # Maximum multiplier from base price
MARKET_MIN_PRICE_MULTIPLIER = 0.4  # Minimum multiplier from base price (lower for more volatility)

# Debug settings
DEBUG_LOGGER = False  # Whether to show the in-game log UI
LOGGER_SHOW_PLAYER = True  # Whether to show player-related logs (PLAYER source)
LOGGER_SHOW_AI = True      # Whether to show AI-related logs (AI-x source)
LOGGER_SHOW_BUILDING = False  # Whether to show building-related logs (DEPOSIT, PROCESSING, COLLECTION, COMMERCE sources)
