import random
from config import *
import utils

class AIFactory:
    def __init__(self, factory_id, world):
        self.id = factory_id
        self.world = world
        self.money = INITIAL_MONEY
        self.owned_tiles = []
        self.buildings = []
        self.update_owned_tiles()
        
    def update_owned_tiles(self):
        """Update the list of owned tiles"""
        self.owned_tiles = []
        for pos, tile in self.world.tiles.items():
            if tile.owner == f'ai_{self.id}':
                self.owned_tiles.append(tile)
    
    def update(self):
        """Update AI factory state"""
        # Basic decision making
        self.try_buy_tile()
        self.try_build()
        
    def try_buy_tile(self):
        """Try to buy an adjacent tile"""
        if self.money < TILE_BASE_COST:
            return
            
        # Find adjacent tiles that can be bought
        potential_tiles = []
        for tile in self.owned_tiles:
            for adj_x, adj_y in utils.get_adjacent_coords(tile.x, tile.y):
                if (adj_x, adj_y) in self.world.tiles:
                    adj_tile = self.world.tiles[(adj_x, adj_y)]
                    if adj_tile.owner is None:
                        potential_tiles.append(adj_tile)
        
        if potential_tiles:
            tile = random.choice(potential_tiles)
            cost = tile.get_tile_cost()
            if self.money >= cost:
                self.money -= cost
                tile.owner = f'ai_{self.id}'
                self.owned_tiles.append(tile)
    
    def try_build(self):
        """Try to build a structure"""
        if self.money < min(b['cost'] for b in BUILDINGS.values() if b['cost'] > 0):
            return
            
        # Simple building logic: build collection on resources, deposit near collections
        for tile in self.owned_tiles:
            if tile.building is None:
                if tile.resource_type != 'EMPTY':
                    if self.money >= BUILDINGS['COLLECTION']['cost']:
                        tile.building = 'COLLECTION'
                        self.money -= BUILDINGS['COLLECTION']['cost']
                        return
                elif self.has_nearby_building('COLLECTION', tile):
                    if self.money >= BUILDINGS['DEPOSIT']['cost']:
                        tile.building = 'DEPOSIT'
                        self.money -= BUILDINGS['DEPOSIT']['cost']
                        return
                elif self.has_nearby_building('DEPOSIT', tile):
                    if self.money >= BUILDINGS['PROCESSING']['cost']:
                        tile.building = 'PROCESSING'
                        self.money -= BUILDINGS['PROCESSING']['cost']
                        return
    
    def has_nearby_building(self, building_type, tile):
        """Check if there's a specific building type near this tile"""
        for adj_x, adj_y in utils.get_adjacent_coords(tile.x, tile.y):
            if (adj_x, adj_y) in self.world.tiles:
                adj_tile = self.world.tiles[(adj_x, adj_y)]
                if adj_tile.owner == f'ai_{self.id}' and adj_tile.building == building_type:
                    return True
        return False
