import pygame
from config import DEBUG_LOGGER

def draw_text(surface, text, pos, font, color=(255, 255, 255)):
    """Helper to draw text on a surface"""
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, pos)

class GameLogger:
    def __init__(self):
        self.messages = []
        self.max_messages = 10

    def log(self, source, action_type, description):
        """Add a log message"""
        message = f"[{source}] [{action_type}] {description}"
        print(message)  # Console output
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def draw(self, surface, x, y, font):
        """Draw log messages on screen if DEBUG_LOGGER is True"""
        if not DEBUG_LOGGER:
            return
            
        for i, message in enumerate(self.messages):
            draw_text(surface, message, (x, y + i * 20), font, (200, 200, 200))