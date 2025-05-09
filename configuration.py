import pygame
import sys
from config import *

class ConfigurationScreen:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.confirmed = False
        
        # Fonts
        self.font_large = pygame.font.SysFont('Arial', 28)
        self.font = pygame.font.SysFont('Arial', 18)
        self.font_small = pygame.font.SysFont('Arial', 14)
        
        # Button tracking
        self.settings_buttons = {}
        
        # Import configuration variables
        from config import (
            NUM_AI_PLAYERS, WORLD_SIZE, WORLD_SIZE_SMALL, WORLD_SIZE_MEDIUM, 
            WORLD_SIZE_LARGE, RESOURCE_DISTRIBUTION, AI_DIFFICULTY, AI_DIFFICULTY_LEVELS
        )
        
    def draw_text(self, surface, text, position, font, color=WHITE):
        """Helper function to draw text"""
        text_surface = font.render(text, True, color)
        surface.blit(text_surface, position)
    
    def run(self):
        """Run the configuration screen"""
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            
            self.handle_events()
            self.draw()
            
            if self.confirmed:
                return True
                
        return False  # User quit the game
    
    def handle_events(self):
        """Process events for configuration screen"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.handle_click(event.pos)
    
    def handle_click(self, pos):
        """Handle mouse clicks on configuration screen"""
        import config
        
        for button_id, rect in self.settings_buttons.items():
            if rect.collidepoint(pos):
                if button_id == 'ai_minus':
                    if config.NUM_AI_PLAYERS > 1:
                        config.NUM_AI_PLAYERS -= 1
                    return True
                elif button_id == 'ai_plus':
                    if config.NUM_AI_PLAYERS < 5:  # Maximum of 5 AI players
                        config.NUM_AI_PLAYERS += 1
                    return True
                elif button_id == 'size_small':
                    config.WORLD_SIZE = config.WORLD_SIZE_SMALL
                    return True
                elif button_id == 'size_medium':
                    config.WORLD_SIZE = config.WORLD_SIZE_MEDIUM
                    return True
                elif button_id == 'size_large':
                    config.WORLD_SIZE = config.WORLD_SIZE_LARGE
                    return True
                elif button_id == 'start_game':
                    self.confirmed = True
                    self.running = False
                    return True
                elif button_id.startswith('difficulty_'):
                    # Handle AI difficulty setting
                    difficulty = button_id.split('_')[1]
                    if difficulty in config.AI_DIFFICULTY_LEVELS:
                        config.AI_DIFFICULTY = difficulty
                    return True
                elif button_id.startswith('rarity_'):
                    # Handle resource rarity setting
                    parts = button_id.split('_')
                    if len(parts) >= 3:
                        resource = parts[1]
                        rarity = '_'.join(parts[2:])  # Join back in case rarity has underscores
                        if resource in config.RESOURCE_DISTRIBUTION:
                            config.RESOURCE_DISTRIBUTION[resource]['rarity'] = rarity
                    return True

    def draw(self):
        """Draw the configuration screen"""
        from config import (
            NUM_AI_PLAYERS, WORLD_SIZE, WORLD_SIZE_SMALL, WORLD_SIZE_MEDIUM, 
            WORLD_SIZE_LARGE, RESOURCE_DISTRIBUTION, AI_DIFFICULTY, AI_DIFFICULTY_LEVELS
        )
        
        # Get all resources that need configuration
        resources = list(RESOURCE_DISTRIBUTION.keys())
        rarity_options = ['COMMON', 'NORMAL', 'RARE', 'VERY_RARE']
        
        # Calculate dynamic panel height based on content
        base_height = 240  # Base height for non-resource settings
        resource_height_per_item = 30  # Height per resource row
        total_resource_height = len(resources) * resource_height_per_item
        panel_height = base_height + total_resource_height
        
        # Clear screen
        self.screen.fill(BLACK)
        
        # Title
        title_text = "Factory Management Game - Configuration"
        self.draw_text(
            self.screen, 
            title_text, 
            (SCREEN_WIDTH // 2 - self.font_large.size(title_text)[0] // 2, 20), 
            self.font_large
        )
        
        # Settings panel
        panel_width = 450
        x = (SCREEN_WIDTH - panel_width) // 2
        y = 70
        
        panel_rect = pygame.Rect(x, y, panel_width, panel_height)
        pygame.draw.rect(self.screen, GRAY, panel_rect)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)
        
        # Title
        self.draw_text(self.screen, "Game Settings", (x + 10, y + 10), self.font_large)
        
        current_y = y + 50
        
        # Number of AI Players setting
        self.draw_text(self.screen, "Number of AI Players:", (x + 20, current_y), self.font)
        
        # Draw - button
        minus_rect = pygame.Rect(x + 250, current_y, 30, 25)
        pygame.draw.rect(self.screen, LIGHT_GRAY, minus_rect)
        pygame.draw.rect(self.screen, BLACK, minus_rect, 1)
        self.draw_text(self.screen, "-", (minus_rect.x + 12, minus_rect.y + 2), self.font)
        self.settings_buttons['ai_minus'] = minus_rect
        
        # Draw current value
        value_rect = pygame.Rect(x + 285, current_y, 40, 25)
        pygame.draw.rect(self.screen, WHITE, value_rect)
        pygame.draw.rect(self.screen, BLACK, value_rect, 1)
        self.draw_text(self.screen, str(NUM_AI_PLAYERS), (value_rect.x + 15, value_rect.y + 2), self.font, BLACK)
        
        # Draw + button
        plus_rect = pygame.Rect(x + 330, current_y, 30, 25)
        pygame.draw.rect(self.screen, LIGHT_GRAY, plus_rect)
        pygame.draw.rect(self.screen, BLACK, plus_rect, 1)
        self.draw_text(self.screen, "+", (plus_rect.x + 10, plus_rect.y + 2), self.font)
        self.settings_buttons['ai_plus'] = plus_rect
        
        current_y += 40
        
        # AI Difficulty setting
        self.draw_text(self.screen, "AI Difficulty:", (x + 20, current_y), self.font)
        
        # Draw difficulty buttons
        difficulty_options = list(AI_DIFFICULTY_LEVELS.keys())
        button_width = 80
        spacing = 10
        total_width = button_width * len(difficulty_options) + spacing * (len(difficulty_options) - 1)
        start_x = x + panel_width // 2 - total_width // 2
        
        for i, difficulty in enumerate(difficulty_options):
            diff_x = start_x + (button_width + spacing) * i
            diff_rect = pygame.Rect(diff_x, current_y, button_width, 25)
            color = LIGHT_GRAY if AI_DIFFICULTY == difficulty else WHITE
            pygame.draw.rect(self.screen, color, diff_rect)
            pygame.draw.rect(self.screen, BLACK, diff_rect, 1)
            self.draw_text(self.screen, difficulty.capitalize(), (diff_x + 10, diff_rect.y + 2), self.font_small, BLACK)
            self.settings_buttons[f'difficulty_{difficulty}'] = diff_rect
        
        current_y += 40
        
        # World size setting
        self.draw_text(self.screen, "World Size:", (x + 20, current_y), self.font)
        
        # Small button
        small_rect = pygame.Rect(x + 150, current_y, 70, 25)
        color = LIGHT_GRAY if WORLD_SIZE == WORLD_SIZE_SMALL else WHITE
        pygame.draw.rect(self.screen, color, small_rect)
        pygame.draw.rect(self.screen, BLACK, small_rect, 1)
        self.draw_text(self.screen, "Small", (small_rect.x + 15, small_rect.y + 2), self.font, BLACK)
        self.settings_buttons['size_small'] = small_rect
        
        # Medium button
        medium_rect = pygame.Rect(x + 225, current_y, 70, 25)
        color = LIGHT_GRAY if WORLD_SIZE == WORLD_SIZE_MEDIUM else WHITE
        pygame.draw.rect(self.screen, color, medium_rect)
        pygame.draw.rect(self.screen, BLACK, medium_rect, 1)
        self.draw_text(self.screen, "Medium", (medium_rect.x + 10, medium_rect.y + 2), self.font, BLACK)
        self.settings_buttons['size_medium'] = medium_rect
        
        # Large button
        large_rect = pygame.Rect(x + 300, current_y, 70, 25)
        color = LIGHT_GRAY if WORLD_SIZE == WORLD_SIZE_LARGE else WHITE
        pygame.draw.rect(self.screen, color, large_rect)
        pygame.draw.rect(self.screen, BLACK, large_rect, 1)
        self.draw_text(self.screen, "Large", (large_rect.x + 15, large_rect.y + 2), self.font, BLACK)
        self.settings_buttons['size_large'] = large_rect
        
        current_y += 40
        
        # Resource rarity settings
        self.draw_text(self.screen, "Resource Rarity:", (x + 20, current_y), self.font)
        current_y += 25
        
        # List all resources from config
        for i, resource in enumerate(resources):
            res_y = current_y + i * 30
            self.draw_text(self.screen, f"{resource}:", (x + 40, res_y), self.font_small)
            
            # Draw rarity buttons
            current_rarity = RESOURCE_DISTRIBUTION.get(resource, {}).get('rarity', 'NORMAL')
            
            for j, rarity in enumerate(rarity_options):
                rarity_rect = pygame.Rect(x + 150 + j * 72, res_y, 65, 20)
                color = LIGHT_GRAY if current_rarity == rarity else WHITE
                pygame.draw.rect(self.screen, color, rarity_rect)
                pygame.draw.rect(self.screen, BLACK, rarity_rect, 1)
                self.draw_text(self.screen, rarity[:4], (rarity_rect.x + 10, rarity_rect.y + 2), self.font_small, BLACK)
                self.settings_buttons[f'rarity_{resource}_{rarity}'] = rarity_rect
        
        # Start game button at the bottom
        current_y = y + panel_height + 20
        start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 75, current_y, 150, 40)
        pygame.draw.rect(self.screen, GREEN, start_rect)
        pygame.draw.rect(self.screen, BLACK, start_rect, 1)
        self.draw_text(self.screen, "Start Game", (start_rect.x + 30, start_rect.y + 10), self.font)
        self.settings_buttons['start_game'] = start_rect
        
        # Update display
        pygame.display.flip()
