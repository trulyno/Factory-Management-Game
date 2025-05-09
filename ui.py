import pygame
from config import *
from economy import PriceManager

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
        
        # Settings UI
        self.show_settings = False
        self.settings_buttons = {}
        
        # Restart button
        self.restart_button = None
        
        # Restart button
        self.restart_button = None
        
        # Building menu elements
        self.building_menu_rect = None
        self.menu_buttons = {}
        self.selected_deposit = None
        self.selected_resource = None
        self.sell_amount_input = ""
        self.input_active = False
        self.input_target = None
        
        # Commerce UI states
        self.commerce_dropdown_open = False
        self.commerce_selected_resource = None
        self.commerce_amount_input = ""
        self.commerce_price_input = ""
        self.commerce_buy_amount = ""
        self.commerce_resource_index = 0  # Index for resource selection with arrows
        
        # Recipe list index for cycling through recipes
        self.current_recipe_index = 0
        
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
        
        # Add settings button
        settings_rect = pygame.Rect(self.ui_panel_rect.x + UI_PANEL_WIDTH - 40, 10, 30, 30)
        pygame.draw.rect(surface, LIGHT_GRAY, settings_rect)
        pygame.draw.rect(surface, BLACK, settings_rect, 1)
        self.draw_text(surface, "⚙", (settings_rect.x + 8, settings_rect.y + 5), self.font_large)
        self.action_buttons['settings'] = settings_rect
        
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
            
            # Resource durability info (only show if it's a resource tile and it's surveyed or owned)
            if tile.surveyed or tile.owner:
                if tile.resource_type != 'EMPTY' and hasattr(tile, 'durability'):
                    self.draw_text(surface, f"Durability: {tile.durability}", 
                                (self.ui_panel_rect.x + 10, y), 
                                self.font_small)
                    y += 20
            
            # Tile price info (display different price if surveyed)
            if tile.owner is None:  # Only show price for tiles that can be bought
                base_price = tile.price
                if tile.surveyed:
                    current_price = tile.get_tile_cost()
                    self.draw_text(surface, f"Price: ${current_price} (Surveyed: -30%)", 
                                (self.ui_panel_rect.x + 10, y), 
                                self.font_small, GREEN if tile.surveyed else WHITE)
                else:
                    self.draw_text(surface, f"Price: ${base_price}", 
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
            if not tile.surveyed and tile.owner is None and player.can_afford(PriceManager.instance.get_survey_cost()):
                survey_rect = pygame.Rect(
                    self.ui_panel_rect.x + 10, y,
                    UI_PANEL_WIDTH - 20, 30
                )
                self.action_buttons['survey'] = survey_rect
                pygame.draw.rect(surface, LIGHT_GRAY, survey_rect)
                pygame.draw.rect(surface, BLACK, survey_rect, 1)
                self.draw_text(surface, f"Survey Tile (${PriceManager.instance.get_survey_cost()}) - 30% discount on buy", 
                            (survey_rect.x + 10, survey_rect.y + 5), 
                            self.font_small)
                y += 35
        
        # Price multipliers section
        if PriceManager.instance:
            self.draw_text(surface, "Economy Status:", 
                       (self.ui_panel_rect.x + 10, y), 
                       self.font)
            y += 25
            
            # Show current price multipliers
            survey_mult = PriceManager.instance.survey_cost_multiplier
            tile_mult = PriceManager.instance.tile_cost_multiplier
            building_mult = PriceManager.instance.building_cost_multiplier
            
            # Color-code based on multiplier level
            def get_multiplier_color(mult):
                if mult < 1.5:
                    return GREEN  # Good
                elif mult < 3.0:
                    return YELLOW  # Warning
                else:
                    return RED  # Danger
            
            self.draw_text(surface, f"Survey costs: {survey_mult:.2f}x", 
                       (self.ui_panel_rect.x + 10, y), 
                       self.font_small, get_multiplier_color(survey_mult))
            y += 20
            
            self.draw_text(surface, f"Tile costs: {tile_mult:.2f}x", 
                       (self.ui_panel_rect.x + 10, y), 
                       self.font_small, get_multiplier_color(tile_mult))
            y += 20
            
            self.draw_text(surface, f"Building costs: {building_mult:.2f}x", 
                       (self.ui_panel_rect.x + 10, y), 
                       self.font_small, get_multiplier_color(building_mult))
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
        
        # Draw building-specific menus
        if self.selected_tile and self.selected_tile.building:
            if self.selected_tile.building == 'COLLECTION':
                self.draw_collection_menu(surface, self.selected_tile)
            elif self.selected_tile.building == 'DEPOSIT':
                self.draw_deposit_menu(surface, self.selected_tile, market)
            elif self.selected_tile.building == 'PROCESSING':
                self.draw_processing_menu(surface, self.selected_tile)
            elif self.selected_tile.building == 'COMMERCE':
                self.draw_commerce_menu(surface, self.selected_tile, market)
    
        # Draw settings menu if visible
        if self.show_settings:
            self.draw_settings(surface)
    
    def draw_collection_menu(self, surface, tile):
        """Draw menu for collection stations"""
        from game import Game  # Import inside method to avoid circular import
        x = self.ui_panel_rect.x + 10
        y = self.height - 300
        width = UI_PANEL_WIDTH - 20
        height = 200
        
        self.building_menu_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, GRAY, self.building_menu_rect)
        pygame.draw.rect(surface, BLACK, self.building_menu_rect, 2)
        
        # Title
        self.draw_text(surface, "Collection Station", (x + 10, y + 10), self.font_large)
        
        # Resource info
        y += 40
        self.draw_text(surface, f"Collecting: {tile.resource_type}", (x + 10, y), self.font)
        
        # Check if this is a player-owned tile
        if tile.owner != 'player':
            # For AI-owned buildings, just show info but no interaction
            y += 25
            self.draw_text(surface, f"Owner: {tile.owner}", (x + 10, y), self.font)
            y += 25
            self.draw_text(surface, "Cannot interact with AI buildings", (x + 10, y), self.font_small)
            return
        
        # Target deposit info
        y += 30
        # Fix: Handle the case when target_deposit is already a Tile object
        target = None
        if hasattr(tile, 'building_instance') and tile.building_instance and hasattr(tile.building_instance, 'target_deposit'):
            target_deposit = tile.building_instance.target_deposit
            if target_deposit:
                # Check if target_deposit is a Building or a Tile
                if hasattr(target_deposit, 'tile'):
                    # It's a Building, get the tile
                    target = target_deposit.tile
                else:
                    # It's already a Tile
                    target = target_deposit
            else:
                target = "None"
        else:
            target = "None"
            
        self.draw_text(surface, "Sending to:", (x + 10, y), self.font)
        y += 20
        
        # List available deposits
        self.menu_buttons.clear()
        for pos, tile_obj in Game.instance.world.tiles.items():
            if (tile_obj.owner == self.selected_tile.owner and 
                tile_obj.building == 'DEPOSIT'):
                rect = pygame.Rect(x + 20, y, width - 40, 25)
                pygame.draw.rect(surface, LIGHT_GRAY if tile_obj == target else WHITE, rect)
                pygame.draw.rect(surface, BLACK, rect, 1)
                self.draw_text(surface, f"Deposit at ({tile_obj.x}, {tile_obj.y})", 
                             (rect.x + 5, rect.y + 3), self.font_small)
                self.menu_buttons[f'deposit_{tile_obj.x}_{tile_obj.y}'] = (rect, tile_obj)
                y += 30
    
    def draw_deposit_menu(self, surface, tile, market):
        """Draw menu for deposit buildings"""
        from game import Game  # Import inside method to avoid circular import
        x = self.ui_panel_rect.x + 10
        y = self.height - 300
        width = UI_PANEL_WIDTH - 20
        height = 250  # Increased height to accommodate two-line display for each resource
        
        self.building_menu_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, GRAY, self.building_menu_rect)
        pygame.draw.rect(surface, BLACK, self.building_menu_rect, 2)
        
        # Title
        self.draw_text(surface, "Deposit Building", (x + 10, y + 10), self.font_large)
        y += 40
        
        # Resource list
        self.menu_buttons.clear()
        
        # Check if this is a player-owned tile
        if tile.owner != 'player':
            # For AI-owned buildings, just show info but no interaction
            self.draw_text(surface, f"Owner: {tile.owner}", (x + 10, y), self.font)
            y += 25
            self.draw_text(surface, "Cannot interact with AI buildings", (x + 10, y), self.font_small)
            return
        
        # Fix: Access resources through the Building object using building_instance
        resources = {}
        if hasattr(tile, 'building_instance') and tile.building_instance and hasattr(tile.building_instance, 'resources'):
            resources = tile.building_instance.resources
            
        for resource, amount in resources.items():
            # Get current market price for this resource
            price = market.prices.get(resource, 0)
            
            # LINE 1: Resource name and potential earnings
            resource_display = f"{resource}: {amount}"
            self.draw_text(surface, resource_display, (x + 10, y), self.font)
            
            # Calculate earnings based on sell amount input or total amount
            calculated_amount = amount
            if self.input_active and self.selected_deposit == tile and self.selected_resource == resource and self.sell_amount_input:
                try:
                    input_amount = int(self.sell_amount_input)
                    if 0 < input_amount <= amount:
                        calculated_amount = input_amount
                except ValueError:
                    pass
                    
            earnings = calculated_amount * price
            earnings_text = f"Value: ${earnings:.2f}"
            self.draw_text(surface, earnings_text, (x + width - 120, y), self.font_small, GREEN)
            
            y += 25  # Move to line 2 for this resource
            
            # LINE 2: Interactive controls
            
            # Autosell checkbox
            check_rect = pygame.Rect(x + 10, y, 20, 20)
            pygame.draw.rect(surface, WHITE, check_rect)
            pygame.draw.rect(surface, BLACK, check_rect, 1)
            
            # Fix: Access autosell through the Building object using building_instance
            autosell_enabled = False
            if hasattr(tile, 'building_instance') and tile.building_instance and hasattr(tile.building_instance, 'autosell'):
                autosell_enabled = tile.building_instance.autosell.get(resource, False)
                
            if autosell_enabled:
                pygame.draw.line(surface, BLACK, (check_rect.x + 3, check_rect.y + 10),
                               (check_rect.x + 8, check_rect.y + 15), 2)
                pygame.draw.line(surface, BLACK, (check_rect.x + 8, check_rect.y + 15),
                               (check_rect.x + 17, check_rect.y + 3), 2)
            self.menu_buttons[f'autosell_{resource}'] = (check_rect, resource)
            
            # Auto-sell label
            self.draw_text(surface, "Auto", (check_rect.x + 25, check_rect.y + 2), self.font_small)
            
            # Sell all button
            sell_all_rect = pygame.Rect(x + 70, y, 60, 20)
            pygame.draw.rect(surface, WHITE, sell_all_rect)
            pygame.draw.rect(surface, BLACK, sell_all_rect, 1)
            self.draw_text(surface, "Sell All", (sell_all_rect.x + 5, sell_all_rect.y + 2), self.font_small, BLACK)
            self.menu_buttons[f'sell_all_{resource}'] = (sell_all_rect, resource)
            
            # Amount input
            input_rect = pygame.Rect(x + 140, y, 40, 20)
            pygame.draw.rect(surface, WHITE, input_rect)
            pygame.draw.rect(surface, BLACK, input_rect, 1)
            if self.input_active and self.selected_deposit == tile and self.selected_resource == resource:
                self.draw_text(surface, self.sell_amount_input, (input_rect.x + 5, input_rect.y + 2), self.font_small, BLACK)
            self.menu_buttons[f'input_{resource}'] = (input_rect, resource)
            
            # Sell amount button
            sell_amt_rect = pygame.Rect(x + 190, y, 40, 20)
            pygame.draw.rect(surface, WHITE, sell_amt_rect)
            pygame.draw.rect(surface, BLACK, sell_amt_rect, 1)
            self.draw_text(surface, "Sell", (sell_amt_rect.x + 5, sell_amt_rect.y + 2), self.font_small, BLACK)
            self.menu_buttons[f'sell_amt_{resource}'] = (sell_amt_rect, resource)
            
            y += 30  # Extra spacing between resources

    def draw_processing_menu(self, surface, tile):
        """Draw menu for processing buildings"""
        from game import Game  # Import inside method to avoid circular import
        from config import RECIPES
        
        x = self.ui_panel_rect.x + 10
        y = self.height - 300
        width = UI_PANEL_WIDTH - 20
        height = 200
        
        self.building_menu_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, GRAY, self.building_menu_rect)
        pygame.draw.rect(surface, BLACK, self.building_menu_rect, 2)
        
        # Title
        self.draw_text(surface, "Processing Building", (x + 10, y + 10), self.font_large)
        y += 40
        
        # Check if this is a player-owned tile
        if tile.owner != 'player':
            # For AI-owned buildings, just show info but no interaction
            self.draw_text(surface, f"Owner: {tile.owner}", (x + 10, y), self.font)
            y += 25
            self.draw_text(surface, "Cannot interact with AI buildings", (x + 10, y), self.font_small)
            return
        
        # Current recipe info
        
        # Access the building instance
        building_instance = None
        recipes = list(RECIPES.items())
        
        if hasattr(tile, 'building_instance') and tile.building_instance:
            building_instance = tile.building_instance
            
            # Active/Inactive checkbox
            is_active = not hasattr(building_instance, 'is_inactive') or not building_instance.is_inactive
            active_text = "Active" if is_active else "Inactive"
            self.draw_text(surface, active_text + ":", (x + 10, y), self.font)
            
            check_rect = pygame.Rect(x + 80, y, 20, 20)
            pygame.draw.rect(surface, WHITE, check_rect)
            pygame.draw.rect(surface, BLACK, check_rect, 1)
            
            if is_active:
                pygame.draw.line(surface, BLACK, (check_rect.x + 3, check_rect.y + 10),
                               (check_rect.x + 8, check_rect.y + 15), 2)
                pygame.draw.line(surface, BLACK, (check_rect.x + 8, check_rect.y + 15),
                               (check_rect.x + 17, check_rect.y + 3), 2)
            self.menu_buttons['toggle_active'] = (check_rect, None)
            
            y += 30
            
            # Initialize current recipe index if needed
            if building_instance.selected_recipe:
                for i, (recipe_name, _) in enumerate(recipes):
                    if recipe_name == building_instance.selected_recipe:
                        self.current_recipe_index = i
                        break
            
            # Recipe selection with arrows
            recipe_y = y
            self.draw_text(surface, "Recipe:", (x + 10, y), self.font)
            y += 30
            
            # Draw left/right arrows for recipe selection
            left_arrow_rect = pygame.Rect(x + 10, y, 30, 30)
            pygame.draw.rect(surface, LIGHT_GRAY, left_arrow_rect)
            pygame.draw.rect(surface, BLACK, left_arrow_rect, 1)
            # Draw left triangle
            pygame.draw.polygon(surface, BLACK, [
                (left_arrow_rect.x + 20, left_arrow_rect.y + 5),
                (left_arrow_rect.x + 20, left_arrow_rect.y + 25),
                (left_arrow_rect.x + 5, left_arrow_rect.y + 15)
            ])
            self.menu_buttons['recipe_prev'] = (left_arrow_rect, None)
            
            right_arrow_rect = pygame.Rect(x + width - 40, y, 30, 30)
            pygame.draw.rect(surface, LIGHT_GRAY, right_arrow_rect)
            pygame.draw.rect(surface, BLACK, right_arrow_rect, 1)
            # Draw right triangle
            pygame.draw.polygon(surface, BLACK, [
                (right_arrow_rect.x + 10, right_arrow_rect.y + 5),
                (right_arrow_rect.x + 10, right_arrow_rect.y + 25),
                (right_arrow_rect.x + 25, right_arrow_rect.y + 15)
            ])
            self.menu_buttons['recipe_next'] = (right_arrow_rect, None)
            
            # Draw current recipe in box
            recipe_rect = pygame.Rect(x + 45, y, width - 90, 30)
            pygame.draw.rect(surface, WHITE, recipe_rect)
            pygame.draw.rect(surface, BLACK, recipe_rect, 1)
            
            if len(recipes) > 0:
                recipe_name, details = recipes[self.current_recipe_index]
                recipe_text = f"{recipe_name}"
                if details['input2']:
                    recipe_text += f" ({details['input1']}, {details['input2']} -> {details['output']})"
                else:
                    recipe_text += f" ({details['input1']} -> {details['output']})"
                
                self.draw_text(surface, recipe_text, (recipe_rect.x + 5, recipe_rect.y + 7), self.font_small, BLACK)
                self.menu_buttons['select_recipe'] = (recipe_rect, recipe_name)
            else:
                self.draw_text(surface, "No recipes available", (recipe_rect.x + 5, recipe_rect.y + 7), self.font_small, BLACK)
            
            y += 40
            
            # If a recipe is selected, show more info
            if building_instance.selected_recipe and building_instance.selected_recipe in RECIPES:
                selected_recipe = RECIPES[building_instance.selected_recipe]
                
                # Show materials needed
                if selected_recipe['input2']:
                    materials = f"Materials: {selected_recipe['input1']}, {selected_recipe['input2']}"
                else:
                    materials = f"Materials: {selected_recipe['input1']}"
                self.draw_text(surface, materials, (x + 10, y), self.font_small)
                y += 20
                
                # Show output and duration
                output_info = f"Output: {selected_recipe['output']} (x{selected_recipe.get('output_amount', 1)})"
                self.draw_text(surface, output_info, (x + 10, y), self.font_small)
                y += 20
                
                time_info = f"Processing time: {selected_recipe['duration']}s"
                self.draw_text(surface, time_info, (x + 10, y), self.font_small)
                y += 25
            
            # Show current state and progress if processing
            state = building_instance.processing_state
            self.draw_text(surface, f"Status: {state}", (x + 10, y), self.font)
            y += 25
            
            if state == "processing" and building_instance.selected_recipe:
                recipe = RECIPES[building_instance.selected_recipe]
                progress_pct = min(100, int((building_instance.processing_progress / recipe['duration']) * 100))
                self.draw_text(surface, f"Progress: {progress_pct}%", (x + 10, y), self.font)
                
                # Draw progress bar
                y += 20
                progress_rect = pygame.Rect(x + 10, y, width - 20, 15)
                pygame.draw.rect(surface, BLACK, progress_rect, 1)
                fill_rect = pygame.Rect(
                    progress_rect.x + 1, progress_rect.y + 1,
                    int((progress_rect.width - 2) * (progress_pct / 100)), progress_rect.height - 2
                )
                pygame.draw.rect(surface, GREEN, fill_rect)
                y += 25
    
    def draw_commerce_menu(self, surface, tile, market):
        """Draw menu for commerce buildings"""
        from game import Game  # Import inside method to avoid circular import
        x = self.ui_panel_rect.x + 10
        y = self.height - 300
        width = UI_PANEL_WIDTH - 20
        height = 200
        
        self.building_menu_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, GRAY, self.building_menu_rect)
        pygame.draw.rect(surface, BLACK, self.building_menu_rect, 2)
        
        # Title
        self.draw_text(surface, "Commerce Station", (x + 10, y + 10), self.font_large)
        y += 40
        
        # Access the building instance
        building_instance = None
        if hasattr(tile, 'building_instance') and tile.building_instance:
            building_instance = tile.building_instance
            
            # Player-owned commerce station
            if tile.owner == 'player':
                # Current trade info
                if building_instance.commerce_resource:
                    self.draw_text(surface, "Currently trading:", (x + 10, y), self.font)
                    y += 25
                    
                    # Resource being sold
                    resource_text = f"{building_instance.commerce_resource} ({building_instance.commerce_amount} units at ${building_instance.commerce_price} each)"
                    self.draw_text(surface, resource_text, (x + 20, y), self.font)
                    y += 25
                    
                    # Total value
                    total_value = building_instance.commerce_amount * building_instance.commerce_price
                    self.draw_text(surface, f"Total value: ${total_value}", (x + 20, y), self.font)
                    y += 25
                    
                    # Market comparison
                    market_price = market.prices.get(building_instance.commerce_resource, 0)
                    if market_price > 0:
                        price_diff = ((building_instance.commerce_price / market_price) - 1.0) * 100
                        price_text = f"Your price is {abs(price_diff):.1f}% {'higher' if price_diff > 0 else 'lower'} than market"
                        self.draw_text(surface, price_text, (x + 20, y), self.font_small)
                        y += 25
                        
                    # Reset button
                    reset_rect = pygame.Rect(x + 10, y, width - 20, 30)
                    pygame.draw.rect(surface, LIGHT_GRAY, reset_rect)
                    pygame.draw.rect(surface, BLACK, reset_rect, 1)
                    self.draw_text(surface, "Reset Trade", (reset_rect.x + 10, reset_rect.y + 5), self.font)
                    self.menu_buttons['reset_trade'] = (reset_rect, None)
                    y += 40
                else:
                    # No commerce set up yet - show options to set up
                    self.draw_text(surface, "Set up new trade:", (x + 10, y), self.font)
                    y += 25
                    
                    # Choose resource with arrows
                    self.draw_text(surface, "Resource:", (x + 10, y), self.font_small)
                    
                    # Get available resources from deposits
                    available_resources = []
                    for world_tile in Game.instance.player.owned_tiles:
                        if (world_tile.building == 'DEPOSIT' and 
                            hasattr(world_tile, 'building_instance') and 
                            world_tile.building_instance):
                            
                            deposit = world_tile.building_instance
                            for res, amt in deposit.resources.items():
                                if amt > 0:
                                    available_resources.append(res)
                    
                    # Draw left/right arrows for resource selection
                    left_arrow_rect = pygame.Rect(x + 80, y - 5, 30, 30)
                    pygame.draw.rect(surface, LIGHT_GRAY, left_arrow_rect)
                    pygame.draw.rect(surface, BLACK, left_arrow_rect, 1)
                    # Draw left triangle
                    pygame.draw.polygon(surface, BLACK, [
                        (left_arrow_rect.x + 20, left_arrow_rect.y + 5),
                        (left_arrow_rect.x + 20, left_arrow_rect.y + 25),
                        (left_arrow_rect.x + 5, left_arrow_rect.y + 15)
                    ])
                    self.menu_buttons['resource_prev'] = (left_arrow_rect, None)
                    
                    right_arrow_rect = pygame.Rect(x + 150, y - 5, 30, 30)
                    pygame.draw.rect(surface, LIGHT_GRAY, right_arrow_rect)
                    pygame.draw.rect(surface, BLACK, right_arrow_rect, 1)
                    # Draw right triangle
                    pygame.draw.polygon(surface, BLACK, [
                        (right_arrow_rect.x + 10, right_arrow_rect.y + 5),
                        (right_arrow_rect.x + 10, right_arrow_rect.y + 25),
                        (right_arrow_rect.x + 25, right_arrow_rect.y + 15)
                    ])
                    self.menu_buttons['resource_next'] = (right_arrow_rect, None)
                    
                    # Display current selection or prompt
                    if available_resources:
                        resource = available_resources[self.commerce_resource_index % len(available_resources)]
                        self.draw_text(surface, resource, (x + 115, y), self.font_small, BLACK)
                        self.commerce_selected_resource = resource
                    else:
                        self.draw_text(surface, "No resources", (x + 115, y), self.font_small, (150, 150, 150))
                    
                    y += 30
                    
                    # Amount input
                    self.draw_text(surface, "Amount:", (x + 10, y), self.font_small)
                    amount_rect = pygame.Rect(x + 80, y - 5, 80, 25)
                    pygame.draw.rect(surface, WHITE, amount_rect)
                    pygame.draw.rect(surface, BLACK, amount_rect, 1)
                    
                    if hasattr(self, 'commerce_amount_input'):
                        self.draw_text(surface, self.commerce_amount_input, 
                                     (amount_rect.x + 5, amount_rect.y + 5), self.font_small, BLACK)
                    
                    self.menu_buttons['commerce_amount'] = (amount_rect, None)
                    y += 30
                    
                    # Price input
                    self.draw_text(surface, "Price:", (x + 10, y), self.font_small)
                    price_rect = pygame.Rect(x + 80, y - 5, 80, 25)
                    pygame.draw.rect(surface, WHITE, price_rect)
                    pygame.draw.rect(surface, BLACK, price_rect, 1)
                    
                    if hasattr(self, 'commerce_price_input'):
                        self.draw_text(surface, self.commerce_price_input, 
                                     (price_rect.x + 5, price_rect.y + 5), self.font_small, BLACK)
                        
                        # Show market price comparison if resource is selected
                        if hasattr(self, 'commerce_selected_resource') and self.commerce_selected_resource:
                            market_price = market.prices.get(self.commerce_selected_resource, 0)
                            if market_price > 0:
                                try:
                                    user_price = float(self.commerce_price_input)
                                    price_diff = ((user_price / market_price) - 1.0) * 100
                                    color = GREEN if price_diff < 0 else RED if price_diff > 0 else WHITE
                                    price_text = f"{abs(price_diff):.1f}% {'below' if price_diff < 0 else 'above'} market"
                                    self.draw_text(surface, price_text, 
                                                (price_rect.x + 90, price_rect.y + 5), self.font_small, color)
                                except ValueError:
                                    pass
                    
                    self.menu_buttons['commerce_price'] = (price_rect, None)
                    y += 40
                    
                    # Set up trade button
                    setup_rect = pygame.Rect(x + 10, y, width - 20, 30)
                    pygame.draw.rect(surface, LIGHT_GRAY, setup_rect)
                    pygame.draw.rect(surface, BLACK, setup_rect, 1)
                    self.draw_text(surface, "Set up Trade", (setup_rect.x + 10, setup_rect.y + 5), self.font)
                    self.menu_buttons['setup_trade'] = (setup_rect, None)
            
            # AI-owned commerce station
            else:
                # Current trade info
                if building_instance.commerce_resource:
                    self.draw_text(surface, "Available for purchase:", (x + 10, y), self.font)
                    y += 25
                    
                    # Resource being sold
                    resource_text = f"{building_instance.commerce_resource} ({building_instance.commerce_amount} units at ${building_instance.commerce_price} each)"
                    self.draw_text(surface, resource_text, (x + 20, y), self.font)
                    y += 25
                    
                    # Total value
                    total_value = building_instance.commerce_amount * building_instance.commerce_price
                    self.draw_text(surface, f"Total value: ${total_value}", (x + 20, y), self.font)
                    y += 25
                    
                    # Market comparison
                    market_price = market.prices.get(building_instance.commerce_resource, 0)
                    if market_price > 0:
                        price_diff = ((building_instance.commerce_price / market_price) - 1.0) * 100
                        price_text = f"Price is {abs(price_diff):.1f}% {'higher' if price_diff > 0 else 'lower'} than market"
                        color = RED if price_diff > 0 else GREEN
                        self.draw_text(surface, price_text, (x + 20, y), self.font_small, color)
                        y += 25
                    
                    # Purchase controls
                    # Amount input
                    self.draw_text(surface, "Amount to buy:", (x + 10, y), self.font_small)
                    buy_amount_rect = pygame.Rect(x + 120, y - 5, 60, 25)
                    pygame.draw.rect(surface, WHITE, buy_amount_rect)
                    pygame.draw.rect(surface, BLACK, buy_amount_rect, 1)
                    
                    if hasattr(self, 'commerce_buy_amount'):
                        self.draw_text(surface, self.commerce_buy_amount, 
                                     (buy_amount_rect.x + 5, buy_amount_rect.y + 5), self.font_small, BLACK)
                    
                    self.menu_buttons['buy_amount'] = (buy_amount_rect, None)
                    y += 35
                    
                    # Buy button
                    buy_rect = pygame.Rect(x + 10, y, 100, 30)
                    pygame.draw.rect(surface, LIGHT_GRAY, buy_rect)
                    pygame.draw.rect(surface, BLACK, buy_rect, 1)
                    self.draw_text(surface, "Buy", (buy_rect.x + 10, buy_rect.y + 5), self.font)
                    self.menu_buttons['buy_trade'] = (buy_rect, None)
                    
                    # Buy all button
                    buy_all_rect = pygame.Rect(x + 120, y, 100, 30)
                    pygame.draw.rect(surface, LIGHT_GRAY, buy_all_rect)
                    pygame.draw.rect(surface, BLACK, buy_all_rect, 1)
                    self.draw_text(surface, "Buy All", (buy_all_rect.x + 10, buy_all_rect.y + 5), self.font)
                    self.menu_buttons['buy_all_trade'] = (buy_all_rect, None)
                else:
                    # No commerce set up yet
                    ai_id = tile.owner.split('_')[1] if tile.owner and tile.owner.startswith('ai_') else "?"
                    self.draw_text(surface, f"AI-{ai_id} has not set up any trade", (x + 10, y), self.font)
        else:
            self.draw_text(surface, "Error: Building data not available", (x + 10, y), self.font)

    def draw_text(self, surface, text, position, font, color=WHITE):
        """Helper to draw text on the UI"""
        text_surface = font.render(str(text), True, color)
        surface.blit(text_surface, position)
    
    def handle_click(self, pos, player, world):
        """Handle mouse click on UI elements"""
        from game import Game  # Import inside method to avoid circular import
        from config import RECIPES
        
        # Check for restart button clicks
        if hasattr(self, 'restart_button') and self.restart_button and self.restart_button.collidepoint(pos):
            Game.instance.restart_game = True
            return True
            
        # Handle settings panel clicks if it's visible
        if self.show_settings:
            for button_id, rect in self.settings_buttons.items():
                if rect.collidepoint(pos):
                    import config
                    
                    if button_id == 'close':
                        self.show_settings = False
                        return True
                    elif button_id == 'ai_minus':
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
                    elif button_id == 'apply':
                        # Apply settings and restart the game
                        Game.instance.restart_game = True
                        self.show_settings = False
                        return True
                    elif button_id.startswith('rarity_'):
                        # Handle resource rarity setting
                        # Format: rarity_RESOURCE_RARITY_LEVEL
                        parts = button_id.split('_')
                        if len(parts) >= 3:
                            resource = parts[1]
                            rarity = '_'.join(parts[2:])  # Join back in case rarity has underscores
                            if resource in config.RESOURCE_DISTRIBUTION:
                                config.RESOURCE_DISTRIBUTION[resource]['rarity'] = rarity
                        return True
                    elif button_id.startswith('difficulty_'):
                        # Handle AI difficulty setting
                        difficulty = button_id.split('_')[1]
                        if difficulty in config.AI_DIFFICULTY_LEVELS:
                            config.AI_DIFFICULTY = difficulty
                        return True
            
            # If clicked somewhere else in the overlay but not on a button, keep the panel open
            return True
        
        if self.building_menu_rect and self.building_menu_rect.collidepoint(pos):
            for button_id, (rect, data) in self.menu_buttons.items():
                if rect.collidepoint(pos):
                    if button_id.startswith('deposit_'):                        
                        # Set collection station target
                        if hasattr(self.selected_tile, 'building_instance') and self.selected_tile.building_instance:
                            self.selected_tile.building_instance.target_deposit = data
                    elif button_id.startswith('sell_all_'):
                        # Sell all of a resource and completely remove it from deposit
                        resource = data
                        amount = 0
                        # Get resources from building object
                        if hasattr(self.selected_tile, 'building_instance') and self.selected_tile.building_instance:
                            amount = self.selected_tile.building_instance.resources.get(resource, 0)
                        
                        if amount > 0:
                            price = Game.instance.market.prices[resource]
                            if player.sell_resources(self.selected_tile.building_instance, resource, amount, price):
                                # Completely remove the resource from the dictionary to free up slot
                                if hasattr(self.selected_tile, 'building_instance') and self.selected_tile.building_instance:
                                    if resource in self.selected_tile.building_instance.resources:
                                        del self.selected_tile.building_instance.resources[resource]
                                Game.instance.logger.log('PLAYER', 'SELL', 
                                    f'Sold all {amount} {resource} for ${amount * price} and removed from deposit')
                    elif button_id.startswith('input_'):
                        # Activate input for sell amount
                        self.input_active = True
                        self.input_target = None  # Set to None to indicate deposit sell amount
                        self.selected_deposit = self.selected_tile
                        self.selected_resource = data
                        self.sell_amount_input = ""
                    elif button_id.startswith('sell_amt_'):
                        # Sell specified amount
                        try:
                            amount = int(self.sell_amount_input)
                            resource = data
                            if amount > 0:
                                price = Game.instance.market.prices[resource]
                                if player.sell_resources(self.selected_tile.building_instance, resource, amount, price):
                                    Game.instance.logger.log('PLAYER', 'SELL', 
                                        f'Sold {amount} {resource} for ${amount * price}')
                        except ValueError:
                            pass
                    elif button_id.startswith('autosell_'):
                        # Toggle autosell for resource
                        resource = data
                        # Set autosell on building object
                        if hasattr(self.selected_tile, 'building_instance') and self.selected_tile.building_instance and hasattr(self.selected_tile.building_instance, 'autosell'):
                            current_value = self.selected_tile.building_instance.autosell.get(resource, False)
                            self.selected_tile.building_instance.autosell[resource] = not current_value
                    elif button_id == 'toggle_active':
                        # Toggle processing building active state
                        if hasattr(self.selected_tile, 'building_instance') and self.selected_tile.building_instance:
                            if not hasattr(self.selected_tile.building_instance, 'is_inactive'):
                                self.selected_tile.building_instance.is_inactive = False
                            self.selected_tile.building_instance.is_inactive = not self.selected_tile.building_instance.is_inactive
                            active_state = "inactive" if self.selected_tile.building_instance.is_inactive else "active"
                            Game.instance.logger.log('PROCESSING', 'TOGGLE', 
                                f'Set processing building to {active_state} at ({self.selected_tile.x}, {self.selected_tile.y})')
                    elif button_id == 'recipe_prev':
                        # Select previous recipe
                        recipes = list(RECIPES.items())
                        if len(recipes) > 0:
                            self.current_recipe_index = (self.current_recipe_index - 1) % len(recipes)
                    elif button_id == 'recipe_next':
                        # Select next recipe
                        recipes = list(RECIPES.items())
                        if len(recipes) > 0:
                            self.current_recipe_index = (self.current_recipe_index + 1) % len(recipes)
                    elif button_id == 'select_recipe':
                        # Select the currently displayed recipe
                        if hasattr(self.selected_tile, 'building_instance') and self.selected_tile.building_instance:
                            building_instance = self.selected_tile.building_instance
                            # Can change recipe if either:
                            # 1. The building is in idle state
                            # 2. The building is inactive (regardless of state)
                            if building_instance.selected_recipe is not None and hasattr(self.selected_tile.building_instance, 'is_inactive') and self.selected_tile.building_instance.is_inactive:
                                building_instance.selected_recipe = None
                            elif building_instance.processing_state == "idle" or building_instance.is_inactive:
                                recipe_name = data
                                building_instance.selected_recipe = recipe_name
                                Game.instance.logger.log('PROCESSING', 'SELECT', 
                                    f'Selected recipe {recipe_name} at ({self.selected_tile.x}, {self.selected_tile.y})')
                            else:
                                Game.instance.logger.log('PROCESSING', 'ERROR', 
                                    f'Cannot change recipe while active and processing. Set to inactive first at ({self.selected_tile.x}, {self.selected_tile.y})')
                    # Commerce station buttons
                    elif button_id == 'resource_prev':
                        # Select previous resource for commerce
                        self.commerce_resource_index = (self.commerce_resource_index - 1) % len(Game.instance.player.owned_tiles)
                        # Debug log
                        Game.instance.logger.log('UI', 'DEBUG', f'Selected previous resource: {self.commerce_resource_index}')
                    elif button_id == 'resource_next':
                        # Select next resource for commerce
                        self.commerce_resource_index = (self.commerce_resource_index + 1) % len(Game.instance.player.owned_tiles)
                        # Debug log
                        Game.instance.logger.log('UI', 'DEBUG', f'Selected next resource: {self.commerce_resource_index}')
                    elif button_id == 'commerce_amount':
                        # Activate input for commerce amount
                        self.input_active = True
                        self.input_target = 'commerce_amount'
                        self.commerce_amount_input = ""
                    elif button_id == 'commerce_price':
                        # Activate input for commerce price
                        self.input_active = True
                        self.input_target = 'commerce_price'
                        self.commerce_price_input = ""
                    elif button_id == 'setup_trade':
                        # Set up commerce trade
                        if self.commerce_selected_resource and self.commerce_amount_input and self.commerce_price_input:
                            try:
                                amount = int(self.commerce_amount_input)
                                price = float(self.commerce_price_input)
                                if amount > 0 and price > 0:
                                    if hasattr(self.selected_tile, 'building_instance') and self.selected_tile.building_instance:
                                        if self.selected_tile.building_instance.setup_commerce_trade(
                                            self.commerce_selected_resource, amount, price):
                                            # Reset inputs
                                            self.commerce_selected_resource = None
                                            self.commerce_amount_input = ""
                                            self.commerce_price_input = ""
                                            self.commerce_dropdown_open = False
                            except (ValueError, TypeError):
                                Game.instance.logger.log('COMMERCE', 'ERROR', 
                                    f'Invalid amount or price values')
                    elif button_id == 'reset_trade':
                        # Reset commerce trade setup
                        if hasattr(self.selected_tile, 'building_instance') and self.selected_tile.building_instance:
                            self.selected_tile.building_instance.commerce_resource = None
                            self.selected_tile.building_instance.commerce_amount = 0
                            self.selected_tile.building_instance.commerce_price = 0
                            Game.instance.logger.log('COMMERCE', 'RESET', 
                                f'Reset commerce station at ({self.selected_tile.x}, {self.selected_tile.y})')
                    elif button_id == 'buy_amount':
                        # Activate input for buying from commerce
                        self.input_active = True
                        self.input_target = 'commerce_buy_amount'
                        self.commerce_buy_amount = ""
                    elif button_id == 'buy_trade':
                        # Buy from AI commerce station
                        if hasattr(self.selected_tile, 'building_instance') and self.selected_tile.building_instance:
                            try:
                                amount = int(self.commerce_buy_amount) if self.commerce_buy_amount else 1
                                self.selected_tile.building_instance.buy_from_commerce('player', amount)
                                # Reset input
                                self.commerce_buy_amount = ""
                            except (ValueError, TypeError):
                                Game.instance.logger.log('COMMERCE', 'ERROR', 
                                    f'Invalid amount to buy')
                    elif button_id == 'buy_all_trade':
                        # Buy all from AI commerce station
                        if hasattr(self.selected_tile, 'building_instance') and self.selected_tile.building_instance:
                            self.selected_tile.building_instance.buy_from_commerce('player')
                            # Reset input
                            self.commerce_buy_amount = ""
                    return True
            return True
            
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
                    elif action == 'settings':
                        # Show settings panel
                        self.show_settings = True
                    return True
            
            return True  # Click was on UI but not on a button
        
        return False  # Click was not on UI

    def handle_key_event(self, event):
        """Handle keyboard input for text fields"""
        if not self.input_active:
            return False
            
        # Handle backspace
        if event.key == pygame.K_BACKSPACE:
            if hasattr(self, 'input_target') and self.input_target:
                # Handle different input targets
                if self.input_target == 'commerce_amount':
                    if hasattr(self, 'commerce_amount_input'):
                        self.commerce_amount_input = self.commerce_amount_input[:-1]
                        return True
                elif self.input_target == 'commerce_price':
                    if hasattr(self, 'commerce_price_input'):
                        self.commerce_price_input = self.commerce_price_input[:-1]
                        return True
                elif self.input_target == 'commerce_buy_amount':
                    if hasattr(self, 'commerce_buy_amount'):
                        self.commerce_buy_amount = self.commerce_buy_amount[:-1]
                        return True
            else:  # Default to sell_amount_input (deposit)
                self.sell_amount_input = self.sell_amount_input[:-1]
                return True
                
        # Handle return/enter - deactivate input
        elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            self.input_active = False
            self.input_target = None
            return True
            
        # Handle escape - cancel input
        elif event.key == pygame.K_ESCAPE:
            self.input_active = False
            self.input_target = None
            if hasattr(self, 'input_target') and self.input_target:
                if self.input_target == 'commerce_amount':
                    self.commerce_amount_input = ""
                elif self.input_target == 'commerce_price':
                    self.commerce_price_input = ""
                elif self.input_target == 'commerce_buy_amount':
                    self.commerce_buy_amount = ""
            else:
                self.sell_amount_input = ""
            return True
            
        # Handle regular input
        elif event.unicode.isdigit() or (event.unicode == '.' and self.input_target == 'commerce_price'):
            if hasattr(self, 'input_target') and self.input_target:
                # Handle different input targets
                if self.input_target == 'commerce_amount':
                    if not hasattr(self, 'commerce_amount_input'):
                        self.commerce_amount_input = ""
                    self.commerce_amount_input += event.unicode
                    return True
                elif self.input_target == 'commerce_price':
                    if not hasattr(self, 'commerce_price_input'):
                        self.commerce_price_input = ""
                    # Only allow one decimal point
                    if event.unicode == '.' and '.' in self.commerce_price_input:
                        return True
                    self.commerce_price_input += event.unicode
                    return True
                elif self.input_target == 'commerce_buy_amount':
                    if not hasattr(self, 'commerce_buy_amount'):
                        self.commerce_buy_amount = ""
                    self.commerce_buy_amount += event.unicode
                    return True
            else:  # Default to sell_amount_input (deposit)
                if event.unicode.isdigit():  # Only allow digits for amount
                    self.sell_amount_input += event.unicode
                    return True
            
        return False

    def draw_settings(self, surface):
        """Draw the settings menu"""
        from config import (NUM_AI_PLAYERS, WORLD_SIZE, WORLD_SIZE_SMALL,
                            WORLD_SIZE_MEDIUM, WORLD_SIZE_LARGE, RESOURCE_DISTRIBUTION,
                            AI_DIFFICULTY, AI_DIFFICULTY_LEVELS)
        
        # Get all resources that need configuration
        resources = list(RESOURCE_DISTRIBUTION.keys())
        rarity_options = ['COMMON', 'NORMAL', 'RARE', 'VERY_RARE']
        
        # Calculate dynamic panel height based on content
        base_height = 240  # Base height for non-resource settings
        resource_height_per_item = 30  # Height per resource row
        total_resource_height = len(resources) * resource_height_per_item
        panel_height = base_height + total_resource_height
        
        # Settings panel over the game
        panel_width = 450  # Increased width too
        x = (self.width - panel_width) // 2
        y = (self.height - panel_height) // 2
        
        # Draw panel background with semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        surface.blit(overlay, (0, 0))
        
        panel_rect = pygame.Rect(x, y, panel_width, panel_height)
        pygame.draw.rect(surface, GRAY, panel_rect)
        pygame.draw.rect(surface, BLACK, panel_rect, 2)
        
        # Title
        self.draw_text(surface, "Game Settings", (x + 10, y + 10), self.font_large)
        
        # Close button
        close_rect = pygame.Rect(x + panel_width - 30, y + 5, 25, 25)
        pygame.draw.rect(surface, LIGHT_GRAY, close_rect)
        pygame.draw.rect(surface, BLACK, close_rect, 1)
        self.draw_text(surface, "X", (close_rect.x + 8, close_rect.y + 2), self.font)
        self.settings_buttons['close'] = close_rect
        
        current_y = y + 50
        
        # Number of AI Players setting
        self.draw_text(surface, "Number of AI Players:", (x + 20, current_y), self.font)
        
        # Draw - button
        minus_rect = pygame.Rect(x + 250, current_y, 30, 25)
        pygame.draw.rect(surface, LIGHT_GRAY, minus_rect)
        pygame.draw.rect(surface, BLACK, minus_rect, 1)
        self.draw_text(surface, "-", (minus_rect.x + 12, minus_rect.y + 2), self.font)
        self.settings_buttons['ai_minus'] = minus_rect
        
        # Draw current value
        value_rect = pygame.Rect(x + 285, current_y, 40, 25)
        pygame.draw.rect(surface, WHITE, value_rect)
        pygame.draw.rect(surface, BLACK, value_rect, 1)
        self.draw_text(surface, str(NUM_AI_PLAYERS), (value_rect.x + 15, value_rect.y + 2), self.font, BLACK)
        
        # Draw + button
        plus_rect = pygame.Rect(x + 330, current_y, 30, 25)
        pygame.draw.rect(surface, LIGHT_GRAY, plus_rect)
        pygame.draw.rect(surface, BLACK, plus_rect, 1)
        self.draw_text(surface, "+", (plus_rect.x + 10, plus_rect.y + 2), self.font)
        self.settings_buttons['ai_plus'] = plus_rect
        
        current_y += 40
        
        # AI Difficulty setting
        self.draw_text(surface, "AI Difficulty:", (x + 20, current_y), self.font)
        
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
            pygame.draw.rect(surface, color, diff_rect)
            pygame.draw.rect(surface, BLACK, diff_rect, 1)
            self.draw_text(surface, difficulty.capitalize(), (diff_x + 10, diff_rect.y + 2), self.font_small, BLACK)
            self.settings_buttons[f'difficulty_{difficulty}'] = diff_rect
        
        current_y += 40
        
        # World size setting
        self.draw_text(surface, "World Size:", (x + 20, current_y), self.font)
        
        # Small button
        small_rect = pygame.Rect(x + 150, current_y, 70, 25)
        color = LIGHT_GRAY if WORLD_SIZE == WORLD_SIZE_SMALL else WHITE
        pygame.draw.rect(surface, color, small_rect)
        pygame.draw.rect(surface, BLACK, small_rect, 1)
        self.draw_text(surface, "Small", (small_rect.x + 15, small_rect.y + 2), self.font, BLACK)
        self.settings_buttons['size_small'] = small_rect
        
        # Medium button
        medium_rect = pygame.Rect(x + 225, current_y, 70, 25)
        color = LIGHT_GRAY if WORLD_SIZE == WORLD_SIZE_MEDIUM else WHITE
        pygame.draw.rect(surface, color, medium_rect)
        pygame.draw.rect(surface, BLACK, medium_rect, 1)
        self.draw_text(surface, "Medium", (medium_rect.x + 10, medium_rect.y + 2), self.font, BLACK)
        self.settings_buttons['size_medium'] = medium_rect
        
        # Large button
        large_rect = pygame.Rect(x + 300, current_y, 70, 25)
        color = LIGHT_GRAY if WORLD_SIZE == WORLD_SIZE_LARGE else WHITE
        pygame.draw.rect(surface, color, large_rect)
        pygame.draw.rect(surface, BLACK, large_rect, 1)
        self.draw_text(surface, "Large", (large_rect.x + 15, large_rect.y + 2), self.font, BLACK)
        self.settings_buttons['size_large'] = large_rect
        
        current_y += 40
        
        # Resource rarity settings
        self.draw_text(surface, "Resource Rarity:", (x + 20, current_y), self.font)
        current_y += 25
        
        # List all resources from config
        for i, resource in enumerate(resources):
            res_y = current_y + i * 30
            self.draw_text(surface, f"{resource}:", (x + 40, res_y), self.font_small)
            
            # Draw rarity buttons
            current_rarity = RESOURCE_DISTRIBUTION.get(resource, {}).get('rarity', 'NORMAL')
            
            for j, rarity in enumerate(rarity_options):
                rarity_rect = pygame.Rect(x + 150 + j * 72, res_y, 65, 20)
                color = LIGHT_GRAY if current_rarity == rarity else WHITE
                pygame.draw.rect(surface, color, rarity_rect)
                pygame.draw.rect(surface, BLACK, rarity_rect, 1)
                self.draw_text(surface, rarity[:4], (rarity_rect.x + 10, rarity_rect.y + 2), self.font_small, BLACK)
                self.settings_buttons[f'rarity_{resource}_{rarity}'] = rarity_rect
        
        # Apply button at the bottom
        current_y = y + panel_height - 40
        apply_rect = pygame.Rect(x + panel_width // 2 - 50, current_y, 100, 30)
        pygame.draw.rect(surface, GREEN, apply_rect)
        pygame.draw.rect(surface, BLACK, apply_rect, 1)
        self.draw_text(surface, "Apply", (apply_rect.x + 30, apply_rect.y + 5), self.font)
        self.settings_buttons['apply'] = apply_rect
