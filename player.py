import pygame
from config import *

class Player:
    def __init__(self):
        self.money = INITIAL_MONEY
        self.owned_tiles = []
        self.buildings = []
        
    def can_afford(self, cost):
        """Check if player can afford a cost"""
        return self.money >= cost
        
    def buy_tile(self, tile):
        """Buy a tile and deduct money"""
        cost = tile.get_tile_cost()
        if self.can_afford(cost):
            self.money -= cost
            tile.owner = 'player'
            self.owned_tiles.append(tile)
            # Update stats
            from game import Game
            Game.instance.stats.total_money_spent += cost
            Game.instance.stats.tiles_owned += 1
            return True
        return False
    
    def build(self, tile, building_type):
        """Build a structure on a tile"""
        if tile.owner != 'player':
            return False
            
        if not tile.can_build(building_type):
            return False
            
        cost = BUILDINGS[building_type]['cost']
        if not self.can_afford(cost):
            return False
            
        self.money -= cost
        tile.set_building(building_type)  # Using new set_building method
        from game import Game
        Game.instance.stats.total_money_spent += cost
        Game.instance.stats.num_buildings += 1
        Game.instance.logger.log('PLAYER', 'BUILD', f'Built {building_type} at ({tile.x}, {tile.y})')
        return True
    
    def survey_tile(self, tile):
        """Survey a tile to reveal resources"""
        if self.can_afford(SURVEY_COST):
            self.money -= SURVEY_COST
            tile.surveyed = True
            from game import Game
            Game.instance.stats.total_money_spent += SURVEY_COST
            Game.instance.logger.log('PLAYER', 'SURVEY', f'Surveyed tile at ({tile.x}, {tile.y})')
            return True
        return False
    
    def sell_resources(self, deposit_building, resource_type, amount, price_per_unit):
        """Sell resources from a deposit building"""
        resources = None
        
        # Check if deposit_building is a Building or a Tile with building_instance
        if hasattr(deposit_building, 'resources'):
            # It's already a Building object
            resources = deposit_building.resources
        elif hasattr(deposit_building, 'building_instance') and deposit_building.building_instance:
            # It's a Tile with a building_instance
            resources = deposit_building.building_instance.resources
        else:
            # Neither a Building nor a Tile with building_instance
            return False
            
        if resource_type in resources and resources[resource_type] >= amount:
            resources[resource_type] -= amount
            revenue = amount * price_per_unit
            self.money += revenue
            # Update stats
            from game import Game
            Game.instance.stats.total_money_generated += revenue
            return True
        return False
