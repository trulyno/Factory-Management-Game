import random
import time
from config import *
import utils
from logger import GameLogger
from economy import PriceManager

class AIFactory:
    def __init__(self, factory_id, world):
        self.id = factory_id
        self.world = world
        self.money = INITIAL_MONEY
        self.owned_tiles = []
        self.buildings = []
        self.update_owned_tiles()
        
        # Generate a unique color for this AI factory that differs from player's BLUE
        # and from other AI factories
        self.color = self.generate_unique_color(factory_id)
        
        # Use AI difficulty settings from config
        self.difficulty = AI_DIFFICULTY
        difficulty_settings = AI_DIFFICULTY_LEVELS[self.difficulty]
        
        # Apply difficulty settings
        self.decision_speed_multiplier = difficulty_settings['decision_speed']
        self.expansion_rate = difficulty_settings['expansion_rate']
        self.survey_probability = difficulty_settings['survey_probability']
        
        self.last_decision_time = time.time()
        self.next_decision_delay = random.uniform(
            AI_DECISION_MIN_TIME * self.decision_speed_multiplier, 
            AI_DECISION_MAX_TIME * self.decision_speed_multiplier
        )
        self.development_phase = "initial"  # initial, expanding, or advanced
        self.surveyed_tiles = set()
        self.consecutive_failed_decisions = 0  # Counter for failed decisions
        # Create our own logger instance
        self.logger = GameLogger()
        self.log(f"Initialized AI Factory {self.id} with difficulty: {self.difficulty}")
    
    def generate_unique_color(self, factory_id):
        """Generate a unique color for this AI factory"""
        # Predefined list of distinct colors to avoid close shades
        # Avoiding blue (player color) and colors that are too similar
        distinct_colors = [
            (255, 0, 0),     # Red
            (0, 180, 0),     # Green
            (255, 165, 0),   # Orange
            (128, 0, 128),   # Purple
            (255, 192, 203), # Pink
            (0, 255, 255),   # Cyan
            (255, 255, 0),   # Yellow
            (165, 42, 42),   # Brown
            (100, 100, 100), # Dark Gray
            (220, 20, 60),   # Crimson
        ]
        
        # If we have more AIs than predefined colors, generate random ones
        if factory_id < len(distinct_colors):
            return distinct_colors[factory_id]
        else:
            # Generate a random color that's not too close to BLUE (player color)
            while True:
                r = random.randint(50, 255)
                g = random.randint(50, 255)
                b = random.randint(50, 255)
                # Make sure it's not too close to blue (player color)
                if not (b > 200 and r < 100 and g < 100):
                    # Also check it's not too close to WHITE or BLACK
                    if not (r > 200 and g > 200 and b > 200) and not (r < 50 and g < 50 and b < 50):
                        return (r, g, b)
        
    def log(self, message):
        """Helper method to log AI actions"""
        # Include color in initialization message
        if message.startswith("Initialized AI Factory"):
            color_info = f"Color: RGB{self.color}"
            message = f"{message} - {color_info}"
        self.logger.log(f'AI-{self.id}', 'INFO', message)
        
    def update_owned_tiles(self):
        """Update the list of owned tiles"""
        self.owned_tiles = []
        for pos, tile in self.world.tiles.items():
            if tile.owner == f'ai_{self.id}':
                self.owned_tiles.append(tile)
    
    def update(self):
        """Update AI factory state"""
        current_time = time.time()
        
        # Only make decisions after delay has passed
        if current_time - self.last_decision_time < self.next_decision_delay:
            return
            
        # Reset decision timer and set new delay using difficulty-specific decision speed
        self.last_decision_time = current_time
        self.next_decision_delay = random.uniform(
            AI_DECISION_MIN_TIME * self.decision_speed_multiplier, 
            AI_DECISION_MAX_TIME * self.decision_speed_multiplier
        )
        
        # Update development phase based on conditions
        prev_phase = self.development_phase
        self._update_development_phase()
        if prev_phase != self.development_phase:
            self.log(f"Phase changed: {prev_phase} -> {self.development_phase}")
        
        # Manage processing buildings
        self._manage_processing_buildings()
        
        # Manage commerce buildings
        self._manage_commerce_buildings()
        
        # Make a decision based on current phase and state
        if self._make_strategic_decision():
            # Decision was successful, reset the counter
            self.consecutive_failed_decisions = 0
        else:
            # Increment counter if no decision was made
            self.consecutive_failed_decisions += 1
            if self.consecutive_failed_decisions >= 3:
                self.log(f"STUCK: Failed to make decisions {self.consecutive_failed_decisions} times in a row")
                self._log_stuck_reason()
                
    def _log_stuck_reason(self):
        """Log detailed information about why the AI might be stuck"""
        resource_tiles = sum(1 for tile in self.owned_tiles if tile.resource_type != 'EMPTY')
        empty_tiles = sum(1 for tile in self.owned_tiles if tile.building is None)
        collection_buildings = sum(1 for tile in self.owned_tiles if tile.building == 'COLLECTION')
        deposit_buildings = sum(1 for tile in self.owned_tiles if tile.building == 'DEPOSIT')
        
        self.log(f"Status: Money=${self.money}, Tiles={len(self.owned_tiles)}, Empty={empty_tiles}, " +
                 f"Resources={resource_tiles}, Collections={collection_buildings}, Deposits={deposit_buildings}")
        
        if self.money < min(b['cost'] for b in BUILDINGS.values() if b['cost'] > 0) and self.money < TILE_BASE_COST:
            self.log("STUCK: Not enough money to buy tiles or build")
        elif len(self.owned_tiles) == 0:
            self.log("STUCK: No owned tiles")
        elif resource_tiles == 0:
            self.log("STUCK: No resource tiles available")
        elif empty_tiles == 0:
            self.log("STUCK: No empty tiles to build on")
        elif collection_buildings == 0:
            self.log("STUCK: No collection buildings")
        elif deposit_buildings == 0 and collection_buildings > 0:
            self.log("STUCK: Resources being collected but no deposits")
        
    def _update_development_phase(self):
        """Update the AI's development phase based on its progress"""
        collection_buildings = sum(1 for tile in self.owned_tiles if tile.building == 'COLLECTION')
        deposit_buildings = sum(1 for tile in self.owned_tiles if tile.building == 'DEPOSIT')
        processing_buildings = sum(1 for tile in self.owned_tiles if tile.building == 'PROCESSING')
        commerce_buildings = sum(1 for tile in self.owned_tiles if tile.building == 'COMMERCE')
        
        # Determine phase based on buildings and money
        if collection_buildings <= 1 and deposit_buildings == 0:
            self.development_phase = "initial"
        elif self.money >= AI_PROCESSING_THRESHOLD and len(self.owned_tiles) >= 8:
            self.development_phase = "advanced"
        else:
            self.development_phase = "expanding"

        # Track number of commerce buildings for later decisions
        self.commerce_building_count = commerce_buildings
    
    def _make_strategic_decision(self):
        """Make a strategic decision based on current state and phase
        Returns True if a decision was made, False otherwise"""
        # Check if we should buy from player commerce stations
        if self._make_commerce_purchase_decisions():
            self.log(f"Decision: Purchased resources from player commerce station")
            return True
            
        # Try to sell resources first
        if self.try_sell_resources():
            return True
            
        # First check if we should survey a tile - use difficulty-specific survey probability
        if random.random() < self.survey_probability:
            if self.try_survey_tile():
                self.log(f"Decision: Survey tile")
                return True
        
        # Then decide between buying a tile or building
        if random.random() < AI_BUILD_TILE_PROBABILITY:
            if self.try_buy_tile():
                return True
            
        # If we couldn't buy a tile, try to build
        if self.try_build():
            return True
            
        # If we couldn't build, try to buy a tile again
        if self.try_buy_tile():
            return True
            
        # If everything else fails, try surveying
        if self.try_survey_tile():
            self.log(f"Decision: Survey tile (fallback)")
            return True
            
        # If we reach here, no decision was made
        return False
        
    def try_sell_resources(self):
        """Try to sell resources from deposit buildings
        Returns True if resources were sold, False otherwise"""
        from economy import Market
        
        # Find all deposit buildings
        deposit_tiles = [tile for tile in self.owned_tiles if tile.building == 'DEPOSIT' and hasattr(tile, 'building_instance')]
        
        if not deposit_tiles:
            return False
            
        # Try to sell from each deposit building
        for tile in deposit_tiles:
            if not hasattr(tile, 'building_instance') or not tile.building_instance:
                continue
                
            resources = tile.building_instance.resources
            
            # Check each resource type
            for resource_type, amount in list(resources.items()):
                if amount >= 10:  # Only sell if we have at least 10 units
                    # Get current market price
                    price = Market.instance.get_price(resource_type)
                    
                    # Sell the resources
                    amount_to_sell = amount  # Sell all available resources
                    resources[resource_type] -= amount_to_sell
                    earned = amount_to_sell * price
                    self.money += earned
                    
                    self.log(f"Decision: Sold {amount_to_sell} units of {resource_type} for ${earned}")
                    return True
                    
        return False
        
    def try_buy_tile(self):
        """Try to buy an adjacent tile, returns True if successful"""
        # We now use a higher threshold since tile prices have increased
        min_tile_cost_threshold = TILE_BASE_COST * 1.5  # Set minimum money threshold higher
        if self.money < min_tile_cost_threshold:
            return False
            
        # Find adjacent tiles that can be bought
        potential_tiles = []
        for tile in self.owned_tiles:
            for adj_x, adj_y in utils.get_adjacent_coords(tile.x, tile.y):
                if (adj_x, adj_y) in self.world.tiles:
                    adj_tile = self.world.tiles[(adj_x, adj_y)]
                    if adj_tile.owner is None:
                        # Prioritize surveyed tiles with resources
                        if (adj_x, adj_y) in self.surveyed_tiles and adj_tile.resource_type != 'EMPTY':
                            potential_tiles.insert(0, adj_tile)  # Add to front of list (prioritize)
                        else:
                            potential_tiles.append(adj_tile)
        
        # Adjust for expansion rate - use the difficulty-specific expansion rate
        if random.random() > self.expansion_rate and self.development_phase != "initial":
            return False
        
        if potential_tiles:
            tile = potential_tiles[0] if len(potential_tiles) > 0 and potential_tiles[0].resource_type != 'EMPTY' else random.choice(potential_tiles)
            cost = tile.get_tile_cost()
            if self.money >= cost:
                self.money -= cost
                tile.owner = f'ai_{self.id}'
                tile.surveyed = True  # Auto-survey when buying a tile
                self.owned_tiles.append(tile)
                self.log(f"Decision: Buy tile at ({tile.x}, {tile.y}) for ${cost}")
                return True
        
        return False
    
    def try_build(self):
        """Try to build a structure, returns True if successful"""
        min_building_cost = min(b['cost'] for b in BUILDINGS.values() if b['cost'] > 0)
        if self.money < min_building_cost:
            return False
        
        # Build logic based on development phase
        if self.development_phase == "initial":
            return self._build_initial_phase()
        elif self.development_phase == "expanding":
            return self._build_expanding_phase()
        else:  # advanced phase
            return self._build_advanced_phase()
    
    def _build_initial_phase(self):
        """Initial building strategy: focus on collection and first deposit"""
        collection_count = sum(1 for tile in self.owned_tiles if tile.building == 'COLLECTION')
        deposit_count = sum(1 for tile in self.owned_tiles if tile.building == 'DEPOSIT')
        
        # If we have at least one collection but no deposits, prioritize building a deposit
        if collection_count > 0 and deposit_count == 0:
            # Try to build a deposit on any empty tile
            for tile in self.owned_tiles:
                if tile.building is None and tile.can_build('DEPOSIT'):
                    if self.money >= BUILDINGS['DEPOSIT']['cost']:
                        # Use set_building method to properly initialize the building instance
                        tile.set_building('DEPOSIT')
                        self.money -= BUILDINGS['DEPOSIT']['cost']
                        self.log(f"Decision: Build DEPOSIT (high priority) at ({tile.x}, {tile.y})")
                        return True
        
        # First, build collection on resource tiles
        for tile in self.owned_tiles:
            if tile.building is None and tile.resource_type != 'EMPTY' and tile.can_build('COLLECTION'):
                if self.money >= BUILDINGS['COLLECTION']['cost']:
                    # Use set_building method to properly initialize the building instance
                    tile.set_building('COLLECTION')
                    self.money -= BUILDINGS['COLLECTION']['cost']
                    self.log(f"Decision: Build COLLECTION at ({tile.x}, {tile.y})")
                    return True
        
        # Then build a deposit (if we have space and we're at the original logic)
        for tile in self.owned_tiles:
            if tile.building is None and tile.can_build('DEPOSIT'):
                if self.has_nearby_building('COLLECTION', tile):
                    if self.money >= BUILDINGS['DEPOSIT']['cost']:
                        # Use set_building method to properly initialize the building instance
                        tile.set_building('DEPOSIT')
                        self.money -= BUILDINGS['DEPOSIT']['cost']
                        self.log(f"Decision: Build DEPOSIT at ({tile.x}, {tile.y})")
                        return True
        return False
    
    def _build_expanding_phase(self):
        """Expanding phase strategy: balance collection and deposits"""
        collection_count = sum(1 for tile in self.owned_tiles if tile.building == 'COLLECTION')
        deposit_count = sum(1 for tile in self.owned_tiles if tile.building == 'DEPOSIT')
        
        # Critical: If we have collections but no deposits at all, build a deposit ASAP
        if collection_count > 0 and deposit_count == 0:
            for tile in self.owned_tiles:
                if tile.building is None and tile.can_build('DEPOSIT'):
                    if self.money >= BUILDINGS['DEPOSIT']['cost']:
                        # Use set_building method to properly initialize the building instance
                        tile.set_building('DEPOSIT')
                        self.money -= BUILDINGS['DEPOSIT']['cost']
                        self.log(f"Decision: Build DEPOSIT (critical) at ({tile.x}, {tile.y})")
                        return True
        
        # If we have more collections than deposits, prioritize deposits
        if collection_count > deposit_count:
            # Try to build a deposit near collection
            for tile in self.owned_tiles:
                if tile.building is None and tile.can_build('DEPOSIT') and self.has_nearby_building('COLLECTION', tile):
                    if self.money >= BUILDINGS['DEPOSIT']['cost']:
                        # Use set_building method to properly initialize the building instance
                        tile.set_building('DEPOSIT')
                        self.money -= BUILDINGS['DEPOSIT']['cost']
                        self.log(f"Decision: Build DEPOSIT at ({tile.x}, {tile.y})")
                        return True
                        
            # If we can't find a tile near collection but still need deposits, build one anywhere
            if collection_count > deposit_count * 2:
                for tile in self.owned_tiles:
                    if tile.building is None and tile.can_build('DEPOSIT'):
                        if self.money >= BUILDINGS['DEPOSIT']['cost']:
                            # Use set_building method to properly initialize the building instance
                            tile.set_building('DEPOSIT')
                            self.money -= BUILDINGS['DEPOSIT']['cost']
                            self.log(f"Decision: Build DEPOSIT (fallback) at ({tile.x}, {tile.y})")
                            return True
        
        # Otherwise prioritize collection on resources
        for tile in self.owned_tiles:
            if tile.building is None and tile.resource_type != 'EMPTY' and tile.can_build('COLLECTION'):
                if self.money >= BUILDINGS['COLLECTION']['cost']:
                    # Use set_building method to properly initialize the building instance
                    tile.set_building('COLLECTION')
                    self.money -= BUILDINGS['COLLECTION']['cost']
                    self.log(f"Decision: Build COLLECTION at ({tile.x}, {tile.y})")
                    return True
                    
        # If we have enough money, consider a processing building
        if self.money >= BUILDINGS['PROCESSING']['cost'] and self.money >= AI_PROCESSING_THRESHOLD:
            for tile in self.owned_tiles:
                if tile.building is None and tile.can_build('PROCESSING') and self.has_nearby_building('DEPOSIT', tile):
                    # Use set_building method to properly initialize the building instance
                    tile.set_building('PROCESSING')
                    self.money -= BUILDINGS['PROCESSING']['cost']
                    self.log(f"Decision: Build PROCESSING at ({tile.x}, {tile.y})")
                    return True
                    
        return False
    
    def _build_advanced_phase(self):
        """Advanced phase strategy: add processing and commerce"""
        # First check for commerce buildings if we have enough money
        if self.money >= BUILDINGS['COMMERCE']['cost'] and self.money >= AI_COMMERCE_THRESHOLD:
            for tile in self.owned_tiles:
                if tile.building is None and tile.can_build('COMMERCE') and self.has_nearby_building('PROCESSING', tile):
                    # Use set_building method to properly initialize the building instance
                    tile.set_building('COMMERCE')
                    self.money -= BUILDINGS['COMMERCE']['cost']
                    self.log(f"Decision: Build COMMERCE at ({tile.x}, {tile.y})")
                    return True
        
        # Then check for processing buildings
        if self.money >= BUILDINGS['PROCESSING']['cost']:
            for tile in self.owned_tiles:
                if tile.building is None and tile.can_build('PROCESSING') and self.has_nearby_building('DEPOSIT', tile):
                    # Use set_building method to properly initialize the building instance
                    tile.set_building('PROCESSING')
                    self.money -= BUILDINGS['PROCESSING']['cost']
                    self.log(f"Decision: Build PROCESSING at ({tile.x}, {tile.y})")
                    return True
        
        # Then fallback to basic building strategies
        return self._build_expanding_phase()
    
    def try_survey_tile(self):
        """Try to survey a tile to find resources, returns True if successful"""
        # Get current survey cost from global config (updated by PriceManager)
        
        if self.money < PriceManager.instance.get_survey_cost():
            return False
            
        # Find adjacent tiles that can be surveyed
        potential_tiles = []
        for tile in self.owned_tiles:
            for adj_x, adj_y in utils.get_adjacent_coords(tile.x, tile.y):
                if (adj_x, adj_y) in self.world.tiles:
                    adj_tile = self.world.tiles[(adj_x, adj_y)]
                    if adj_tile.owner is None and (adj_x, adj_y) not in self.surveyed_tiles:
                        potential_tiles.append((adj_x, adj_y))
        
        if potential_tiles:
            pos = random.choice(potential_tiles)
            self.money -= PriceManager.instance.get_survey_cost()
            self.surveyed_tiles.add(pos)  # Track surveyed tiles
            
            # Also mark the tile as surveyed so it's visible to the player
            tile = self.world.tiles[pos]
            tile.surveyed = True
            
            # Log with current cost
            self.log(f"Decision: Survey tile at ({tile.x}, {tile.y}) for ${PriceManager.instance.get_survey_cost()}")
            
            self.log(f"Decision: Survey tile at {pos}")
            return True
        
        return False
    
    def has_nearby_building(self, building_type, tile):
        """Check if there's a specific building type near this tile"""
        for adj_x, adj_y in utils.get_adjacent_coords(tile.x, tile.y):
            if (adj_x, adj_y) in self.world.tiles:
                adj_tile = self.world.tiles[(adj_x, adj_y)]
                if adj_tile.owner == f'ai_{self.id}' and adj_tile.building == building_type:
                    return True
        return False
    
    def _manage_processing_buildings(self):
        """Configure and manage processing buildings"""
        from config import RECIPES
        
        # Find all processing buildings
        processing_buildings = []
        for tile in self.owned_tiles:
            if (tile.building == 'PROCESSING' and 
                hasattr(tile, 'building_instance') and 
                tile.building_instance):
                processing_buildings.append(tile)
        
        # Nothing to do if no processing buildings
        if not processing_buildings:
            return
        
        # Check available resources in deposits
        deposit_resources = {}
        for tile in self.owned_tiles:
            if (tile.building == 'DEPOSIT' and 
                hasattr(tile, 'building_instance') and 
                tile.building_instance):
                for resource, amount in tile.building_instance.resources.items():
                    if resource not in deposit_resources:
                        deposit_resources[resource] = 0
                    deposit_resources[resource] += amount
        
        # Process each building
        for tile in processing_buildings:
            # Skip if already has a recipe selected and is working
            if (tile.building_instance.selected_recipe and 
                tile.building_instance.processing_state != 'idle'):
                continue
            
            # Pick the best recipe based on available resources
            best_recipe = None
            best_score = -1
            
            for recipe_name, recipe in RECIPES.items():
                input1 = recipe['input1']
                input2 = recipe['input2']
                output = recipe['output']
                
                # Check if we have both inputs
                has_input1 = deposit_resources.get(input1, 0) >= 1
                has_input2 = True if input2 is None else deposit_resources.get(input2, 0) >= 1
                
                if has_input1 and has_input2:
                    # Calculate recipe score (higher is better)
                    # Base score on output value and recipe duration
                    output_value = PROCESSED_RESOURCES.get(output, {}).get('value', 0)
                    if output_value == 0:  # Fallback if not in PROCESSED_RESOURCES
                        output_value = 50
                        
                    # Faster recipes and more valuable outputs score higher
                    score = (output_value / recipe['duration']) * recipe.get('output_amount', 1)
                    
                    # Bonus for steel as it's more valuable
                    if output == 'STEEL':
                        score *= 1.2
                    
                    if score > best_score:
                        best_score = score
                        best_recipe = recipe_name
            
            # Set the recipe
            if best_recipe:
                tile.building_instance.selected_recipe = best_recipe
                self.log(f"Decision: Set processing building at ({tile.x}, {tile.y}) to recipe {best_recipe}")
                
                # Make sure the building is active
                tile.building_instance.is_inactive = False
            else:
                self.log(f"Decision: No suitable recipe found for processing building at ({tile.x}, {tile.y})")
                
    def _manage_commerce_buildings(self):
        """Configure and manage commerce buildings"""
        from economy import Market
        
        # Find all commerce buildings
        commerce_buildings = []
        for tile in self.owned_tiles:
            if (tile.building == 'COMMERCE' and 
                hasattr(tile, 'building_instance') and 
                tile.building_instance):
                commerce_buildings.append(tile)
        
        # Nothing to do if no commerce buildings
        if not commerce_buildings:
            return
        
        # Check available resources in deposits for potential trade
        deposit_resources = {}
        for tile in self.owned_tiles:
            if (tile.building == 'DEPOSIT' and 
                hasattr(tile, 'building_instance') and 
                tile.building_instance):
                for resource, amount in tile.building_instance.resources.items():
                    if resource not in deposit_resources:
                        deposit_resources[resource] = 0
                    deposit_resources[resource] += amount
        
        # Process each commerce building
        for tile in commerce_buildings:
            # Skip if commerce is already set up
            if (tile.building_instance.commerce_resource and 
                tile.building_instance.commerce_amount > 0):
                continue
            
            # Find the best resource to sell
            best_resource = None
            best_amount = 0
            best_price = 0
            best_score = -1
            
            for resource, amount in deposit_resources.items():
                # Only consider resources we have at least 10 units of
                if amount < 10:
                    continue
                    
                market_price = Market.instance.get_price(resource)
                if market_price <= 0:
                    continue
                
                # Calculate a score based on resource value and availability
                # We prefer selling higher-value resources that we have plenty of
                score = market_price * (amount / 100.0)  # Higher score for more valuable and abundant resources
                
                # Check for processed resources - prefer selling these
                if resource in PROCESSED_RESOURCES:
                    score *= 1.5  # 50% bonus for processed resources
                
                if score > best_score:
                    best_score = score
                    best_resource = resource
                    best_amount = min(amount, 20)  # Sell up to 20 units at a time
                    
                    # Set price slightly higher than market for valuable resources,
                    # slightly lower for common resources to attract buyers
                    if market_price > 50:
                        best_price = market_price * (1.0 + random.uniform(0.05, 0.2))  # 5-20% higher
                    else:
                        best_price = market_price * (1.0 - random.uniform(0.05, 0.1))  # 5-10% lower
            
            # If we found a good resource to sell, set up commerce
            if best_resource and best_amount > 0:
                # Take resources from deposits
                remaining_amount = best_amount
                for deposit_tile in self.owned_tiles:
                    if remaining_amount <= 0:
                        break
                        
                    if (deposit_tile.building == 'DEPOSIT' and 
                        hasattr(deposit_tile, 'building_instance') and 
                        deposit_tile.building_instance):
                        
                        deposit = deposit_tile.building_instance
                        available = deposit.resources.get(best_resource, 0)
                        take_amount = min(available, remaining_amount)
                        
                        if take_amount > 0:
                            deposit.resources[best_resource] -= take_amount
                            remaining_amount -= take_amount
                
                # Set up the commerce trade
                actual_amount = best_amount - remaining_amount
                if actual_amount > 0:
                    tile.building_instance.commerce_resource = best_resource
                    tile.building_instance.commerce_amount = actual_amount
                    tile.building_instance.commerce_price = round(best_price, 2)
                    
                    self.log(f"Commerce: Set up trade for {actual_amount} {best_resource} at ${tile.building_instance.commerce_price} each")
                    
            # If no good resource found, log the issue
            else:
                self.log(f"Commerce: No suitable resources to sell in commerce building at ({tile.x}, {tile.y})")
                
    def _make_commerce_purchase_decisions(self):
        """Check for player commerce stations and decide if we should buy anything"""
        from game import Game
        
        # Check if we have enough money to consider purchases
        if self.money < 100:  # Arbitrary minimum to consider buying
            return False
            
        # Find all player commerce stations
        player_commerce = []
        for pos, tile in self.world.tiles.items():
            if (tile.owner == 'player' and 
                tile.building == 'COMMERCE' and
                hasattr(tile, 'building_instance') and 
                tile.building_instance and
                tile.building_instance.commerce_resource and
                tile.building_instance.commerce_amount > 0):
                player_commerce.append(tile)
                
        if not player_commerce:
            return False
            
        # Pick a random commerce station to evaluate
        if random.random() < 0.3:  # Only check occasionally
            tile = random.choice(player_commerce)
            building = tile.building_instance
            
            # Use the AI decides to buy method to evaluate the offer
            if building._ai_decides_to_buy(self):
                # Calculate how much to buy
                amount_to_buy = min(building.commerce_amount, 10)  # Buy up to 10 units at a time
                total_cost = amount_to_buy * building.commerce_price
                
                # Check if AI can afford it
                if self.money >= total_cost:
                    # Process the transaction
                    building.commerce_amount -= amount_to_buy
                    self.money -= total_cost
                    
                    # Add money to player
                    Game.instance.player.money += total_cost
                    
                    # Add resource to AI's deposits
                    if building.commerce_resource not in self.deposit_resources:
                        self.deposit_resources[building.commerce_resource] = 0
                    self.deposit_resources[building.commerce_resource] += amount_to_buy
                    
                    self.log(f"Decision: Bought {amount_to_buy} units of {building.commerce_resource} from player for ${total_cost}")
                    return True
                    
        return False