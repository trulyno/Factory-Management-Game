import pygame
import random

def draw_text(surface, text, pos, font, color=(255, 255, 255)):
    """Helper to draw text on a surface"""
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, pos)

def get_adjacent_coords(x, y):
    """Return coordinates of adjacent tiles"""
    return [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]

def random_resource():
    """Return a random resource type"""
    from config import RESOURCE_TYPES
    resources = list(RESOURCE_TYPES.keys())
    resources.remove('EMPTY')
    # 30% chance of empty tile
    if random.random() < 0.3:
        return 'EMPTY'
    return random.choice(resources)
