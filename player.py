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
        tile.building = building_type
        return True
    
    def survey_tile(self, tile):
        """Survey a tile to reveal resources"""
        if self.can_afford(SURVEY_COST):
            self.money -= SURVEY_COST
            tile.surveyed = True
            return True
        return False
    
    def sell_resources(self, deposit_building, resource_type, amount, price_per_unit):
        """Sell resources from a deposit building"""
        if resource_type in deposit_building.resources and deposit_building.resources[resource_type] >= amount:
            deposit_building.resources[resource_type] -= amount
            self.money += amount * price_per_unit
            return True
        return False
