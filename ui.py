import pygame
from config import *

class UI:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.ui_panel_rect = pygame.Rect(
            screen_width - UI_PANEL_WIDTH, 0, 
            UI_PANEL_WIDTH, screen_height
        )
        self.font_large = pygame.font.SysFont('Arial', 24)
        self.font = pygame.font.SysFont('Arial', 18)
        self.font_small = pygame.font.SysFont('Arial', 14)
        
        # UI states
        self.selected_tile = None
        self.selected_building_type = None
        self.hovered_tile = None
        
        # Button areas
        self.build_buttons = {}
        self.action_buttons = {}
        
    def draw(self, surface, player, market):
        """Draw the UI panel"""
        # Draw panel background
        pygame.draw.rect(surface, GRAY, self.ui_panel_rect)
        pygame.draw.rect(surface, BLACK, self.ui_panel_rect, 2)
        
        # Display money
        money_text = f"Money: ${player.money:,}"
        self.draw_text(surface, money_text, 
                       (self.ui_panel_rect.x + 10, 10), 
                       self.font_large)
        
        # Draw win condition
        progress = min(1.0, player.money / WIN_CONDITION)
        win_text = f"Goal: ${WIN_CONDITION:,} ({progress*100:.1f}%)"
        self.draw_text(surface, win_text, 
                       (self.ui_panel_rect.x + 10, 40), 
                       self.font)
        
        # Draw progress bar
        progress_rect = pygame.Rect(
            self.ui_panel_rect.x + 10, 65,
            UI_PANEL_WIDTH - 20, 20
        )
        pygame.draw.rect(surface, BLACK, progress_rect, 1)
        fill_rect = pygame.Rect(
            progress_rect.x + 1, progress_rect.y + 1,
            int((progress_rect.width - 2) * progress), progress_rect.height - 2
        )
        pygame.draw.rect(surface, GREEN, fill_rect)
        
        # Draw building options
        self.draw_text(surface, "Build:", 
                       (self.ui_panel_rect.x + 10, 100), 
                       self.font)
        
        y = 125
        self.build_buttons.clear()
        for building_type, details in BUILDINGS.items():
            if building_type == 'CENTRAL':  # Can't build central buildings
                continue
                
            button_rect = pygame.Rect(
                self.ui_panel_rect.x + 10, y,
                UI_PANEL_WIDTH - 20, 30
            )
            self.build_buttons[building_type] = button_rect
            
            # Highlight selected building type
            if self.selected_building_type == building_type:
                pygame.draw.rect(surface, LIGHT_GRAY, button_rect)
            
            pygame.draw.rect(surface, details['color'], 
                            (button_rect.x + 5, button_rect.y + 5, 20, 20))
            
            cost_text = f"{building_type} (${details['cost']})"
            self.draw_text(surface, cost_text, 
                        (button_rect.x + 30, button_rect.y + 5), 
                        self.font)
            
            # Show affordability
            if not player.can_afford(details['cost']):
                pygame.draw.rect(surface, (255, 0, 0, 128), button_rect, 2)
            
            pygame.draw.rect(surface, BLACK, button_rect, 1)
            y += 35
        
        # Selected tile info
        y += 20
        self.draw_text(surface, "Selected Tile:", 
                       (self.ui_panel_rect.x + 10, y), 
                       self.font)
        y += 25
        
        if self.selected_tile:
            tile = self.selected_tile
            # Tile coordinates
            self.draw_text(surface, f"Position: ({tile.x}, {tile.y})", 
                        (self.ui_panel_rect.x + 10, y), 
                        self.font_small)
            y += 20
            
            # Ownership
            owner = tile.owner if tile.owner else "None"
            self.draw_text(surface, f"Owner: {owner}", 
                        (self.ui_panel_rect.x + 10, y), 
                        self.font_small)
            y += 20
            
            # Resource info
            resource = "Unknown" if not tile.surveyed else tile.resource_type
            self.draw_text(surface, f"Resource: {resource}", 
                        (self.ui_panel_rect.x + 10, y), 
                        self.font_small)
            y += 20
            
            # Building info
            building = tile.building if tile.building else "None"
            self.draw_text(surface, f"Building: {building}", 
                        (self.ui_panel_rect.x + 10, y), 
                        self.font_small)
            y += 30
            
            # Action buttons
            self.action_buttons.clear()
            
            # Buy tile button
            if tile.owner is None and player.can_afford(tile.get_tile_cost()):
                buy_rect = pygame.Rect(
                    self.ui_panel_rect.x + 10, y,
                    UI_PANEL_WIDTH - 20, 30
                )
                self.action_buttons['buy_tile'] = buy_rect
                pygame.draw.rect(surface, LIGHT_GRAY, buy_rect)
                pygame.draw.rect(surface, BLACK, buy_rect, 1)
                self.draw_text(surface, f"Buy Tile (${tile.get_tile_cost()})", 
                            (buy_rect.x + 10, buy_rect.y + 5), 
                            self.font_small)
                y += 35
            
            # Survey tile button
            if not tile.surveyed and tile.owner is None and player.can_afford(SURVEY_COST):
                survey_rect = pygame.Rect(
                    self.ui_panel_rect.x + 10, y,
                    UI_PANEL_WIDTH - 20, 30
                )
                self.action_buttons['survey'] = survey_rect
                pygame.draw.rect(surface, LIGHT_GRAY, survey_rect)
                pygame.draw.rect(surface, BLACK, survey_rect, 1)
                self.draw_text(surface, f"Survey Tile (${SURVEY_COST})", 
                            (survey_rect.x + 10, survey_rect.y + 5), 
                            self.font_small)
                y += 35
        
        # Market prices
        y = self.height - 200
        self.draw_text(surface, "Market Prices:", 
                       (self.ui_panel_rect.x + 10, y), 
                       self.font)
        y += 25
        
        # Show some key resources
        for resource in ['WOOD', 'STONE', 'IRON_ORE', 'IRON_INGOT']:
            if resource in market.prices:
                price = market.prices[resource]
                self.draw_text(surface, f"{resource}: ${price:.2f}", 
                           (self.ui_panel_rect.x + 10, y), 
                           self.font_small)
                y += 20
    
    def draw_text(self, surface, text, position, font, color=WHITE):
        """Helper to draw text on the UI"""
        text_surface = font.render(str(text), True, color)
        surface.blit(text_surface, position)
    
    def handle_click(self, pos, player, world):
        """Handle mouse click on UI elements"""
        # Check if click was on UI panel
        if self.ui_panel_rect.collidepoint(pos):
            # Check building buttons
            for building_type, rect in self.build_buttons.items():
                if rect.collidepoint(pos):
                    self.selected_building_type = building_type
                    return True
            
            # Check action buttons
            for action, rect in self.action_buttons.items():
                if rect.collidepoint(pos):
                    if action == 'buy_tile' and self.selected_tile:
                        if world.can_buy_tile(self.selected_tile.x, self.selected_tile.y, 'player'):
                            player.buy_tile(self.selected_tile)
                    elif action == 'survey' and self.selected_tile:
                        player.survey_tile(self.selected_tile)
                    return True
            
            return True  # Click was on UI but not on a button
        
        return False  # Click was not on UI
