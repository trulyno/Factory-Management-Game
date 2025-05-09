import random
from config import *
import utils
import pygame
from entities import Building

class Tile:
    def __init__(self, x, y, resource_type='EMPTY', owner=None):
        self.x = x
        self.y = y
        self.resource_type = resource_type
        self.owner = owner
        self.building = None
        self.building_instance = None
        self.surveyed = False
        self.world = None  # Set by World class
        self.durability = 0  # Resource durability (how many times resources can be collected)
        self.price = TILE_BASE_COST  # Default price, will be updated based on resource
    
    def update(self, dt):
        """Update tile state"""
        if self.building_instance:
            self.building_instance.update(dt)
        
    def can_build(self, building_type):
        """Check if a building can be placed on this tile"""
        if self.building:
            return False
        if building_type == 'COLLECTION' and self.resource_type == 'EMPTY':
            return False
        if self.resource_type != 'EMPTY' and building_type != 'COLLECTION':
            return False
        if building_type == 'CENTRAL' and self.resource_type != 'EMPTY':
            return False
        return True

    def set_building(self, building_type):
        """Set the building type and create its instance"""
        self.building = building_type
        if building_type:
            self.building_instance = Building(self, building_type)
            
            # Enable autosell by default for AI deposit buildings
            if building_type == 'DEPOSIT' and self.owner and self.owner.startswith('ai_'):
                from config import RESOURCE_TYPES
                # Enable autosell for all resource types
                for resource in RESOURCE_TYPES:
                    if resource != 'EMPTY':
                        self.building_instance.autosell[resource] = True
        else:
            self.building_instance = None

    def get_total_resources(self):
        """Get total resources stored in building"""
        if self.building_instance:
            return self.building_instance.get_total_resources()
        return 0

    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the tile on the surface"""
        rect = pygame.Rect(
            self.x * TILE_SIZE - camera_offset[0],
            self.y * TILE_SIZE - camera_offset[1],
            TILE_SIZE,
            TILE_SIZE
        )
        
        # Draw base tile
        if self.owner is None:
            # Unowned tile
            pygame.draw.rect(surface, LIGHT_GRAY, rect)
        else:
            # Owned tile
            if self.owner == 'player':
                border_color = BLUE
            elif self.owner and self.owner.startswith('ai_'):
                # Get the AI instance from game and use its color
                from game import Game
                if Game.instance and hasattr(Game.instance, 'ai_factories'):
                    ai_id = int(self.owner.split('_')[1])
                    if 0 <= ai_id < len(Game.instance.ai_factories):
                        border_color = Game.instance.ai_factories[ai_id].color
                    else:
                        border_color = RED  # Fallback color if AI not found
                else:
                    border_color = RED  # Fallback color if Game instance not available
            else:
                border_color = RED
            pygame.draw.rect(surface, WHITE, rect)
            pygame.draw.rect(surface, border_color, rect, 2)
            
        # Draw resource if surveyed
        if (self.surveyed or (self.owner is not None)) and self.resource_type != 'EMPTY':
            resource_color = RESOURCE_TYPES[self.resource_type]['color']
            resource_rect = rect.inflate(-20, -20)
            pygame.draw.rect(surface, resource_color, resource_rect)
            
            # # Draw durability indicator if resource is not empty
            # if self.durability > 0:
            #     # Create a font for showing durability
            #     font = pygame.font.SysFont(None, 20)
            #     text = font.render(str(self.durability), True, WHITE)
            #     text_rect = text.get_rect(center=(
            #         rect.centerx - camera_offset[0],
            #         rect.centery - camera_offset[1]
            #     ))
            #     surface.blit(text, text_rect)
        
        # Draw building if present
        if self.building:
            building_color = BUILDINGS[self.building]['color']
            building_rect = pygame.Rect(
                rect.centerx - TILE_SIZE//4,
                rect.centery - TILE_SIZE//4,
                TILE_SIZE//2,
                TILE_SIZE//2
            )
            pygame.draw.rect(surface, building_color, building_rect)
    def get_tile_cost(self):
        """Calculate the cost to buy this tile using dynamic pricing"""
        # Get current multiplier from PriceManager
        from economy import PriceManager
        
        multiplier = 1.0
        if PriceManager.instance:
            multiplier = PriceManager.instance.get_tile_cost_multiplier()
        
        # If the tile has been surveyed, provide a discount
        if self.surveyed:
            return int(self.price * 0.7 * multiplier)  # 30% discount for surveyed tiles
        
        return int(self.price * multiplier)

class World:
    def __init__(self):
        # Use the configured world size from config
        from config import WORLD_SIZE
        self.width = WORLD_SIZE['width']
        self.height = WORLD_SIZE['height']
        self.tiles = {}
        self.generate_world()
        
    def generate_world(self):
        """Generate the world with resources"""
        # First pass: create tiles with resources
        for x in range(self.width):
            for y in range(self.height):
                resource = utils.random_resource()
                tile = Tile(x, y, resource)
                tile.world = self  # Set reference to world
                
                # Set durability based on resource rarity
                tile.durability = utils.get_resource_durability(resource)
                
                self.tiles[(x, y)] = tile
        
        # Second pass: set initial prices based on resource rarity
        self.initialize_tile_prices()
        
        # Third pass: propagate prices to neighboring tiles
        self.propagate_tile_prices()
    
    def initialize_tile_prices(self):
        """Set initial tile prices based on resource rarity"""
        from config import RESOURCE_DISTRIBUTION, RESOURCE_RARITY, TILE_BASE_COST, TILE_COST_MULTIPLIER
        
        for coords, tile in self.tiles.items():
            resource_type = tile.resource_type
            rarity = RESOURCE_DISTRIBUTION.get(resource_type, {}).get('rarity', 'NORMAL')
            multiplier = RESOURCE_RARITY.get(rarity, {}).get('multiplier', 1.0)
            
            # Calculate base price based on rarity
            base_price = TILE_BASE_COST / (multiplier or 0.1)  # Avoid division by zero
            tile.price = int(base_price)
            
            # Set durability based on rarity
            durability_range = RESOURCE_RARITY.get(rarity, {}).get('durability_range', (10, 20))
            tile.durability = random.randint(durability_range[0], durability_range[1])
            resource = tile.resource_type
            
            # Base price starts at TILE_BASE_COST
            base_price = TILE_BASE_COST
            
            # Adjust price based on resource rarity
            if resource != 'EMPTY':
                rarity = RESOURCE_DISTRIBUTION.get(resource, {}).get('rarity', 'NORMAL')
                
                # Price multipliers based on rarity
                rarity_multipliers = {
                    'COMMON': 1.5,  # 50% higher than base
                    'NORMAL': 2.0,  # 100% higher than base
                    'RARE': 3.0,    # 200% higher than base
                    'VERY_RARE': 4.0 # 300% higher than base
                }
                
                # Apply rarity multiplier
                rarity_multiplier = rarity_multipliers.get(rarity, 1.0)
                
                # Add some randomness (±20% variation)
                random_factor = 0.8 + (random.random() * 0.4)  # 0.8 to 1.2
                
                # Calculate final price
                tile.price = int(base_price * rarity_multiplier * random_factor * TILE_COST_MULTIPLIER)
            else:
                # Empty tiles are cheaper
                tile.price = int(base_price * TILE_COST_MULTIPLIER)
    
    def propagate_tile_prices(self):
        """Propagate resource tile prices to neighboring tiles within 3 tiles distance"""
        # Make a copy of current prices to avoid affecting the propagation during iteration
        price_influences = {coords: 0 for coords in self.tiles.keys()}
        
        for (x, y), tile in self.tiles.items():
            if tile.resource_type != 'EMPTY':
                base_influence = tile.price - TILE_BASE_COST
                if base_influence <= 0:
                    continue
                
                # Propagate price influence to neighbors up to 3 tiles away
                for distance in range(1, 4):  # 1, 2, 3 tiles distance
                    influence_factor = 0.7 ** distance  # Decrease by distance (0.7, 0.49, 0.343)
                    
                    # Get all tiles at this distance
                    for dx in range(-distance, distance + 1):
                        for dy in range(-distance, distance + 1):
                            # Only consider tiles exactly at 'distance' away (Manhattan distance)
                            if abs(dx) + abs(dy) == distance:
                                nx, ny = x + dx, y + dy
                                if (nx, ny) in self.tiles:
                                    # Apply influence with some randomness
                                    random_factor = 0.7 + (random.random() * 0.6)  # 0.7 to 1.3
                                    influence = int(base_influence * influence_factor * random_factor)
                                    price_influences[(nx, ny)] += influence
        
        # Apply the calculated influences to all tiles
        for coords, influence in price_influences.items():
            tile = self.tiles[coords]
            if influence > 0:
                tile.price += influence
    
    def setup_player_start(self, player):
        """Set up the player's starting area"""
        # Find a suitable location with at least one resource
        center_x, center_y = self.width // 2, self.height // 2
        
        # Set the central tile
        self.tiles[(center_x, center_y)].owner = 'player'
        self.tiles[(center_x, center_y)].building = 'CENTRAL'
        self.tiles[(center_x, center_y)].resource_type = 'EMPTY'
        self.tiles[(center_x, center_y)].surveyed = True
        
        # Count initial tiles
        tile_count = 1
        # Make sure at least one adjacent tile has a resource
        adjacents = utils.get_adjacent_coords(center_x, center_y)
        resource_placed = False
        
        for x, y in adjacents:
            if (x, y) in self.tiles:
                self.tiles[(x, y)].owner = 'player'
                self.tiles[(x, y)].surveyed = True
                tile_count += 1
                if not resource_placed:
                    resource_type = random.choice(['WOOD', 'STONE', 'IRON_ORE'])
                    self.tiles[(x, y)].resource_type = resource_type
                    self.tiles[(x, y)].durability = utils.get_resource_durability(resource_type)
                    resource_placed = True
        
        # Set up the 5th tile
        for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
            pos = (center_x + dx, center_y + dy)
            if pos in self.tiles:
                self.tiles[pos].owner = 'player'
                self.tiles[pos].surveyed = True
                tile_count += 1
                break
        
        # Update initial stats
        from game import Game
        if Game.instance and hasattr(Game.instance, 'stats'):
            Game.instance.stats.tiles_owned = tile_count
            Game.instance.stats.num_buildings = 1  # Starting with central building
    
    def setup_ai_factories(self):
        """Set up AI factories in the world using the configured number of AI players"""
        from config import NUM_AI_PLAYERS
        
        for i in range(NUM_AI_PLAYERS):
            # Find a location away from the player
            while True:
                x = random.randint(0, self.width - 1)
                y = random.randint(0, self.height - 1)
                # Ensure it's far enough from player start
                if abs(x - self.width//2) + abs(y - self.height//2) > 10:
                    break
            
            # Set up AI territory
            self.tiles[(x, y)].owner = f'ai_{i}'
            self.tiles[(x, y)].building = 'CENTRAL'
            self.tiles[(x, y)].resource_type = 'EMPTY'
            self.tiles[(x, y)].surveyed = True
            
            # Add surrounding tiles
            # Ensure at least one resource for AI to start with
            adjacents = utils.get_adjacent_coords(x, y)
            resource_placed = False
            
            for adj_x, adj_y in adjacents:
                if (adj_x, adj_y) in self.tiles:
                    self.tiles[(adj_x, adj_y)].owner = f'ai_{i}'
                    self.tiles[(adj_x, adj_y)].surveyed = True
                    
                    # Ensure AI has at least one resource to start with
                    if not resource_placed:
                        resource_type = random.choice(['WOOD', 'STONE', 'IRON_ORE'])
                        self.tiles[(adj_x, adj_y)].resource_type = resource_type
                        self.tiles[(adj_x, adj_y)].durability = utils.get_resource_durability(resource_type)
                        resource_placed = True
    
    def can_buy_tile(self, x, y, owner):
        """Check if a tile can be bought by the owner"""
        if (x, y) not in self.tiles:
            return False
            
        tile = self.tiles[(x, y)]
        if tile.owner is not None:
            return False
            
        # Check if adjacent to any owned tiles
        for adj_x, adj_y in utils.get_adjacent_coords(x, y):
            if (adj_x, adj_y) in self.tiles and self.tiles[(adj_x, adj_y)].owner == owner:
                return True
                
        return False
    
    def update(self, dt):
        """Update all tiles"""
        for tile in self.tiles.values():
            tile.update(dt)
    
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the world on the surface"""
        for tile in self.tiles.values():
            tile.draw(surface, camera_offset)
