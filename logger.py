import pygame
from config import DEBUG_LOGGER, LOGGER_SHOW_PLAYER, LOGGER_SHOW_AI, LOGGER_SHOW_BUILDING

def draw_text(surface, text, pos, font, color=(255, 255, 255)):
    """Helper to draw text on a surface"""
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, pos)

class GameLogger:
    def __init__(self):
        self.messages = []
        self.max_messages = 10
        # Building log sources - these are considered building logs
        self.building_sources = ['DEPOSIT', 'PROCESSING', 'COLLECTION', 'COMMERCE', 'CENTRAL', 'COLLECTOR']    
        # For session saving
        self.session_saver = None
        
    def set_session_saver(self, saver):
        """Set the session saver reference"""
        self.session_saver = saver
        
    def log(self, source, action_type, description):
        """Add a log message"""
        message = f"[{source}] [{action_type}] {description}"
        # Add source category to the message for filtering when drawing
        category = self.get_log_category(source)
        
        if (category == 'player' and LOGGER_SHOW_PLAYER) or \
            (category == 'ai' and LOGGER_SHOW_AI) or \
            (category == 'building' and LOGGER_SHOW_BUILDING):
            print(message)  # Console output
        
        # Store log in session saver if available
        if self.session_saver:
            self.session_saver.capture_log(source, action_type, description, category)
        
        log_entry = {'message': message, 'source': source, 'category': category}
        self.messages.append(log_entry)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
    
    def get_log_category(self, source):
        """Determine the category of a log based on its source"""
        if source == 'PLAYER':
            return 'player'
        elif source.startswith('AI-'):
            return 'ai'
        elif source in self.building_sources:
            return 'building'
        else:
            return 'other'  # Other logs will always be shown

    def draw(self, surface, x, y, font):
        """Draw log messages on screen if DEBUG_LOGGER is True"""
        if not DEBUG_LOGGER:
            return
        
        y_offset = 0
        for log_entry in self.messages:
            # Filter logs based on category
            category = log_entry['category']
            should_draw = True
            
            if category == 'player' and not LOGGER_SHOW_PLAYER:
                should_draw = False
            elif category == 'ai' and not LOGGER_SHOW_AI:
                should_draw = False
            elif category == 'building' and not LOGGER_SHOW_BUILDING:
                should_draw = False
                
            if should_draw:
                draw_text(surface, log_entry['message'], (x, y + y_offset), font, (200, 200, 200))
                y_offset += 20