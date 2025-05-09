import pygame
import random

def draw_text(surface, text, pos, font, color=(255, 255, 255)):
    """Helper to draw text on a surface"""
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, pos)

def get_adjacent_coords(x, y):
    """Return coordinates of adjacent tiles"""
    return [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]

def get_resource_durability(resource_type):
    """Return a random durability value for the given resource type based on its rarity"""
    from config import RESOURCE_DISTRIBUTION, RESOURCE_RARITY
    
    if resource_type == 'EMPTY':
        return 0
    
    rarity_type = RESOURCE_DISTRIBUTION.get(resource_type, {}).get('rarity', 'NORMAL')
    durability_range = RESOURCE_RARITY[rarity_type]['durability_range']
    return random.randint(durability_range[0], durability_range[1])

def random_resource():
    """Return a random resource type based on rarity settings"""
    from config import RESOURCE_TYPES, RESOURCE_DISTRIBUTION, RESOURCE_RARITY
    
    # First decide if empty or not (30% chance of empty)
    if random.random() < 0.3:
        return 'EMPTY'
    
    # Create weighted distribution of resources based on rarity
    resource_weights = {}
    for resource, data in RESOURCE_DISTRIBUTION.items():
        if resource != 'EMPTY':
            rarity_type = data['rarity']
            resource_weights[resource] = RESOURCE_RARITY[rarity_type]['multiplier']
    
    # Get weighted random choice
    total_weight = sum(resource_weights.values())
    resources = list(resource_weights.keys())
    weights = [resource_weights[r]/total_weight for r in resources]
    
    return random.choices(resources, weights=weights, k=1)[0]
