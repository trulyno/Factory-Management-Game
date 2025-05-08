import pygame
from config import *
import utils

class Building:
    def __init__(self, tile, building_type):
        self.tile = tile
        self.type = building_type
        self.resources = {}
        self.processing_time = 0
        self.processing_resource = None
    
    def update(self):
        """Update building state"""
        if self.type == 'COLLECTION':
            self.collect_resources()
        elif self.type == 'PROCESSING':
            self.process_resources()
            
    def collect_resources(self):
        """Collect resources from the tile"""
        if self.tile.resource_type != 'EMPTY':
            # Simulate resource collection
            if self.tile.resource_type not in self.resources:
                self.resources[self.tile.resource_type] = 0
            self.resources[self.tile.resource_type] += 1
    
    def process_resources(self):
        """Process raw resources into refined goods"""
        if self.processing_resource:
            self.processing_time -= 1
            if self.processing_time <= 0:
                output_resource = PROCESSED_RESOURCES[self.processing_resource]['from']
                if output_resource not in self.resources:
                    self.resources[output_resource] = 0
                self.resources[output_resource] += 1
                self.processing_resource = None
        else:
            # Look for raw resources to process
            for processed, details in PROCESSED_RESOURCES.items():
                raw = details['from']
                if raw in self.resources and self.resources[raw] > 0:
                    self.resources[raw] -= 1
                    self.processing_resource = processed
                    self.processing_time = details['time']
                    break

    def transfer_resources(self, target_building):
        """Transfer resources to another building"""
        for resource, amount in list(self.resources.items()):
            if resource not in target_building.resources:
                target_building.resources[resource] = 0
            target_building.resources[resource] += amount
            self.resources[resource] = 0
