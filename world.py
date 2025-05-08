import random
from config import *
import utils
import pygame

class Tile:
    def __init__(self, x, y, resource_type='EMPTY', owner=None):
        self.x = x
        self.y = y
        self.resource_type = resource_type
        self.owner = owner
        self.building = None
        self.surveyed = False
        
    def can_build(self, building_type):
        """Check if a building can be placed on this tile"""
        if self.building:
            return False
        if building_type == 'COLLECTION' and self.resource_type == 'EMPTY':
            return False
        if building_type == 'CENTRAL' and self.resource_type != 'EMPTY':
            return False
        return True

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
            else:
                border_color = RED
            pygame.draw.rect(surface, WHITE, rect)
            pygame.draw.rect(surface, border_color, rect, 2)
            
        # Draw resource if surveyed
        if (self.surveyed or (self.owner is not None)) and self.resource_type != 'EMPTY':
            resource_color = RESOURCE_TYPES[self.resource_type]['color']
            resource_rect = rect.inflate(-20, -20)
            pygame.draw.rect(surface, resource_color, resource_rect)
        
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
        """Calculate the cost to buy this tile"""
        return TILE_BASE_COST

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = {}
        self.generate_world()
        
    def generate_world(self):
        """Generate the world with resources"""
        for x in range(self.width):
            for y in range(self.height):
                resource = utils.random_resource()
                self.tiles[(x, y)] = Tile(x, y, resource)
    
    def setup_player_start(self, player):
        """Set up the player's starting area"""
        # Find a suitable location with at least one resource
        center_x, center_y = self.width // 2, self.height // 2
        
        # Set the central tile
        self.tiles[(center_x, center_y)].owner = 'player'
        self.tiles[(center_x, center_y)].building = 'CENTRAL'
        self.tiles[(center_x, center_y)].surveyed = True
        
        # Make sure at least one adjacent tile has a resource
        adjacents = utils.get_adjacent_coords(center_x, center_y)
        resource_placed = False
        
        for x, y in adjacents:
            if (x, y) in self.tiles:
                self.tiles[(x, y)].owner = 'player'
                self.tiles[(x, y)].surveyed = True
                if not resource_placed:
                    self.tiles[(x, y)].resource_type = random.choice(['WOOD', 'STONE', 'IRON_ORE'])
                    resource_placed = True
        
        # Set up the 5th tile
        for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
            pos = (center_x + dx, center_y + dy)
            if pos in self.tiles:
                self.tiles[pos].owner = 'player'
                self.tiles[pos].surveyed = True
                break
    
    def setup_ai_factories(self, num_factories=2):
        """Set up AI factories in the world"""
        for i in range(num_factories):
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
            
            # Add surrounding tiles
            for adj_x, adj_y in utils.get_adjacent_coords(x, y):
                if (adj_x, adj_y) in self.tiles:
                    self.tiles[(adj_x, adj_y)].owner = f'ai_{i}'
    
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
    
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the world on the surface"""
        for tile in self.tiles.values():
            tile.draw(surface, camera_offset)
