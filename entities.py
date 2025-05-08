import pygame
from config import *
import random

class Building:
    def __init__(self, tile, building_type):
        self.tile = tile
        self.type = building_type
        self.resources = {}
        self.processing_time = 0
        self.processing_resource = None
        self.collection_time = 0
        self.transport_time = 0
        self.target_deposit = None
        self.autosell = {}  # Resource type -> bool dictionary
        self.last_autosell_time = 0
        # Add error logging cooldown to prevent spam
        self.last_error_log_time = 0
        self.error_log_cooldown = 10.0  # Only log an error once every 10 seconds
        # Add deposit finding cooldown
        self.deposit_find_cooldown = 0
        self.deposit_find_interval = 5.0  # Only search for deposits every 5 seconds when none found
        
        # Processing building attributes
        self.selected_recipe = None
        self.processing_state = "idle"  # idle, requesting_resources, processing, delivering_output
        self.resource_requests = {}  # Resource -> amount needed
        self.processing_progress = 0
        self.input_transport_time = 0
        self.output_transport_time = 0
        self.resource_source = None  # Source deposit for input resources
        self.output_target = None  # Target deposit for output
        self.is_inactive = False  # Whether the processing building is active
        
        # Commerce building attributes
        self.commerce_resource = None  # Resource type being traded
        self.commerce_price = 0  # Price per unit
        self.commerce_amount = 0  # Amount of resource available for trade
        self.commerce_last_check_time = 0  # Time since last AI check
        self.commerce_check_interval = 3.0  # Seconds between AI checks
    
    def update(self, dt):
        """Update building state"""
        if self.type == 'COLLECTION':
            self.update_collection(dt)
        elif self.type == 'PROCESSING':
            # Skip processing update if inactive
            if not self.is_inactive:
                self.update_processing(dt)
        elif self.type == 'DEPOSIT':
            self.update_deposit(dt)
        elif self.type == 'COMMERCE':
            self.update_commerce(dt)
            
    def update_collection(self, dt):
        """Handle resource collection and transport"""
        from config import COLLECTION_DURATION, TRANSPORT_DURATION_PER_UNIT_OF_DISTANCE, DEPOSIT_SIZE
        
        # Debug logging for collection status
        ai_id = None
        if self.tile.owner and self.tile.owner.startswith('ai_'):
            ai_id = self.tile.owner.split('_')[1]
        
        # Skip if no target deposit
        if not self.target_deposit:
            self.deposit_find_cooldown -= dt
            if self.deposit_find_cooldown <= 0:
                self.target_deposit = self.find_closest_deposit()
                self.deposit_find_cooldown = self.deposit_find_interval
                if not self.target_deposit and ai_id:
                    # Log issue finding deposit
                    from game import Game
                    if Game.instance and hasattr(Game.instance, 'ai_factories'):
                        for ai in Game.instance.ai_factories:
                            if str(ai.id) == ai_id:
                                current_time = pygame.time.get_ticks() / 1000.0
                                if current_time - self.last_error_log_time >= self.error_log_cooldown:
                                    ai.logger.log('COLLECTOR', 'ERROR', f"No deposit found for collection at ({self.tile.x}, {self.tile.y})")
                                    self.last_error_log_time = current_time
                                break
            return

        # Check if target deposit exists and has space
        if not self.target_deposit or self.get_deposit_building(self.target_deposit).get_total_resources() >= DEPOSIT_SIZE:
            previous_target = self.target_deposit
            self.deposit_find_cooldown -= dt
            if self.deposit_find_cooldown <= 0:
                self.target_deposit = self.find_closest_deposit()
                self.deposit_find_cooldown = self.deposit_find_interval
                if not self.target_deposit and previous_target and ai_id:
                    # Log issue with deposit being full
                    from game import Game
                    if Game.instance and hasattr(Game.instance, 'ai_factories'):
                        for ai in Game.instance.ai_factories:
                            if str(ai.id) == ai_id:
                                current_time = pygame.time.get_ticks() / 1000.0
                                if current_time - self.last_error_log_time >= self.error_log_cooldown:
                                    ai.logger.log('COLLECTOR', 'ERROR', f"Deposit full or unavailable at ({self.tile.x}, {self.tile.y})")
                                    self.last_error_log_time = current_time
                                break
            return

        if self.transport_time > 0:
            # Currently transporting
            self.transport_time -= dt
            if self.transport_time <= 0:
                # Deliver resource
                deposit_building = self.get_deposit_building(self.target_deposit)
                for resource, amount in list(self.resources.items()):
                    if deposit_building.can_accept_resource(resource, amount):
                        deposit_building.resources[resource] = deposit_building.resources.get(resource, 0) + amount
                        self.resources[resource] = 0
                        if ai_id:
                            # Log successful delivery
                            from game import Game
                            if Game.instance and hasattr(Game.instance, 'ai_factories'):
                                for ai in Game.instance.ai_factories:
                                    if str(ai.id) == ai_id:
                                        ai.logger.log('COLLECTOR', 'TRANSFER', f"Delivered {amount} {resource} to deposit")
                                        break
        else:
            # Check collection timing
            self.collection_time -= dt
            if self.collection_time <= 0:
                if self.tile.resource_type != 'EMPTY':
                    # Collect new resource
                    self.resources[self.tile.resource_type] = self.resources.get(self.tile.resource_type, 0) + 1
                    self.collection_time = COLLECTION_DURATION
                    
                    if ai_id:
                        # Log successful collection
                        from game import Game
                        if Game.instance and hasattr(Game.instance, 'ai_factories'):
                            for ai in Game.instance.ai_factories:
                                if str(ai.id) == ai_id:
                                    ai.logger.log('COLLECTOR', 'GATHER', f"Collected 1 {self.tile.resource_type}")
                                    break
                    
                    # Start transport
                    # Get the actual tile for distance calculation
                    target_tile = self.target_deposit
                    if hasattr(self.target_deposit, 'tile'):
                        target_tile = self.target_deposit.tile
                    distance = self.get_distance_to(target_tile)
                    self.transport_time = distance * TRANSPORT_DURATION_PER_UNIT_OF_DISTANCE
    
    def update_processing(self, dt):
        """Handle processing building functionality"""
        from config import RECIPES, TRANSPORT_DURATION_PER_UNIT_OF_DISTANCE, DEPOSIT_SIZE
        from game import Game
        
        # Skip processing if inactive
        if self.is_inactive:
            return
            
        # Skip processing if no recipe is selected
        if not self.selected_recipe:
            return
            
        # Get recipe details
        recipe = RECIPES.get(self.selected_recipe)
        if not recipe:
            return
            
        # Log ID for debugging
        ai_id = None
        if self.tile.owner and self.tile.owner.startswith('ai_'):
            ai_id = self.tile.owner.split('_')[1]
            
        # State machine for processing
        if self.processing_state == "idle":
            # Find the closest deposit to check for input resources
            if not self.resource_source:
                self.resource_source = self.find_closest_deposit_with_resources(recipe['input1'], 1)
                # If there's a second input, make sure deposit has that too or find another deposit
                if recipe['input2'] and self.resource_source:
                    if not self.has_resource_in_deposit(self.resource_source, recipe['input2'], 1):
                        other_deposit = self.find_closest_deposit_with_resources(recipe['input2'], 1)
                        if other_deposit:
                            # Need to choose one that has both or just use two separate requests
                            if not self.resource_source or self.get_distance_to(other_deposit.tile) < self.get_distance_to(self.resource_source.tile):
                                self.resource_source = other_deposit
                
                if not self.resource_source:
                    # Log resource shortage
                    if Game.instance:
                        current_time = pygame.time.get_ticks() / 1000.0
                        if current_time - self.last_error_log_time >= self.error_log_cooldown:
                            Game.instance.logger.log('PROCESSING', 'ERROR', 
                                                    f"No deposit found with required resources for {self.selected_recipe} at ({self.tile.x}, {self.tile.y})")
                            self.last_error_log_time = current_time
                    return
                
            # Find output deposit
            if not self.output_target:
                self.output_target = self.find_closest_deposit_with_space()
                if not self.output_target:
                    # Log no output deposit
                    if Game.instance:
                        current_time = pygame.time.get_ticks() / 1000.0
                        if current_time - self.last_error_log_time >= self.error_log_cooldown:
                            Game.instance.logger.log('PROCESSING', 'ERROR', 
                                                   f"No deposit found with space for output at ({self.tile.x}, {self.tile.y})")
                            self.last_error_log_time = current_time
                    return
            
            # Request resources from deposit
            self.resource_requests = {}
            self.resource_requests[recipe['input1']] = 1
            if recipe['input2']:
                self.resource_requests[recipe['input2']] = 1
                
            # Calculate transport time for input resources
            distance = self.get_distance_to(self.resource_source.tile)
            self.input_transport_time = distance * TRANSPORT_DURATION_PER_UNIT_OF_DISTANCE
            self.processing_state = "requesting_resources"
            
            # Log resource request
            if Game.instance:
                resource_list = f"{recipe['input1']}"
                if recipe['input2']:
                    resource_list += f", {recipe['input2']}"
                Game.instance.logger.log('PROCESSING', 'REQUEST', 
                                        f"Requesting {resource_list} for {self.selected_recipe} at ({self.tile.x}, {self.tile.y})")
            
        elif self.processing_state == "requesting_resources":
            # Wait for resources to arrive
            self.input_transport_time -= dt
            if self.input_transport_time <= 0:
                # Check if source deposit still has the resources
                have_resources = True
                for resource, amount in self.resource_requests.items():
                    if not self.has_resource_in_deposit(self.resource_source, resource, amount):
                        have_resources = False
                        break
                        
                if have_resources:
                    # Take resources from deposit
                    for resource, amount in self.resource_requests.items():
                        self.resource_source.resources[resource] -= amount
                        self.resources[resource] = self.resources.get(resource, 0) + amount
                    
                    # Start processing
                    self.processing_state = "processing"
                    self.processing_progress = 0
                    
                    # Log processing start
                    if Game.instance:
                        Game.instance.logger.log('PROCESSING', 'START', 
                                               f"Started processing {self.selected_recipe} at ({self.tile.x}, {self.tile.y})")
                else:
                    # Resources no longer available, reset and try again
                    self.processing_state = "idle"
                    self.resource_source = None
                    
                    # Log resource shortage
                    if Game.instance:
                        Game.instance.logger.log('PROCESSING', 'ERROR', 
                                               f"Resources no longer available at source deposit for {self.selected_recipe}")
            
        elif self.processing_state == "processing":
            # Process the resources
            self.processing_progress += dt
            if self.processing_progress >= recipe['duration']:
                # Processing complete, prepare output
                output_resource = recipe['output']
                output_amount = recipe.get('output_amount', 1)
                
                self.resources[output_resource] = self.resources.get(output_resource, 0) + output_amount
                
                # Consume input resources
                self.resources[recipe['input1']] -= 1
                if recipe['input2']:
                    self.resources[recipe['input2']] -= 1
                    
                # Calculate transport time for output
                distance = self.get_distance_to(self.output_target.tile)
                self.output_transport_time = distance * TRANSPORT_DURATION_PER_UNIT_OF_DISTANCE
                self.processing_state = "delivering_output"
                
                # Log processing complete
                if Game.instance:
                    Game.instance.logger.log('PROCESSING', 'COMPLETE', 
                                           f"Completed processing {output_amount} {output_resource} at ({self.tile.x}, {self.tile.y})")
            
        elif self.processing_state == "delivering_output":
            # Wait for output to be delivered
            self.output_transport_time -= dt
            if self.output_transport_time <= 0:
                # Deliver output to target deposit
                output_resource = recipe['output']
                output_amount = recipe.get('output_amount', 1)
                
                # Check if target deposit still has space
                if self.output_target.get_total_resources() + output_amount <= DEPOSIT_SIZE:
                    # Deliver the output
                    self.output_target.resources[output_resource] = self.output_target.resources.get(output_resource, 0) + output_amount
                    self.resources[output_resource] = 0
                    
                    # Log delivery
                    if Game.instance:
                        Game.instance.logger.log('PROCESSING', 'DELIVERY', 
                                               f"Delivered {output_amount} {output_resource} to deposit at ({self.output_target.tile.x}, {self.output_target.tile.y})")
                else:
                    # Target deposit is full, find a new one
                    new_target = self.find_closest_deposit_with_space()
                    if new_target:
                        self.output_target = new_target
                        # Recalculate transport time
                        distance = self.get_distance_to(self.output_target.tile)
                        self.output_transport_time = distance * TRANSPORT_DURATION_PER_UNIT_OF_DISTANCE
                        
                        # Log rerouting
                        if Game.instance:
                            Game.instance.logger.log('PROCESSING', 'REROUTE', 
                                                  f"Rerouting output delivery to deposit at ({new_target.tile.x}, {new_target.tile.y})")
                        return
                    else:
                        # No available deposit, keep output in processor
                        # Log storage
                        if Game.instance:
                            Game.instance.logger.log('PROCESSING', 'STORAGE', 
                                                  f"Storing {output_amount} {output_resource} in processor - no available deposits")
                
                # Reset to idle state to start a new processing cycle
                self.processing_state = "idle"
                self.resource_source = None
                self.output_target = None
    
    def get_deposit_building(self, target):
        """Helper method to get the Building object from a target, whether it's a Tile or Building"""
        if hasattr(target, 'building_instance') and target.building_instance:
            # Target is a Tile, return its building_instance
            return target.building_instance
        # Target is already a Building
        return target

    def update_deposit(self, dt):
        """Handle deposit autoselling"""
        from config import AUTOSELL_DURATION
        
        self.last_autosell_time -= dt
        if self.last_autosell_time <= 0:
            self.last_autosell_time = AUTOSELL_DURATION
            for resource, should_autosell in self.autosell.items():
                if should_autosell and resource in self.resources and self.resources[resource] > 0:
                    # Trigger autosell
                    amount = self.resources[resource]
                    if self.tile.owner == 'player':
                        from game import Game
                        price = Game.instance.market.prices[resource]
                        if Game.instance.player.sell_resources(self, resource, amount, price):
                            Game.instance.logger.log('DEPOSIT', 'AUTOSELL', f'Auto-sold {amount} {resource} for ${amount * price}')
            
            # Handle AI-owned deposit autoselling
            if self.tile.owner and self.tile.owner.startswith('ai_'):
                ai_id = self.tile.owner.split('_')[1]
                # Check if there are resources to sell
                for resource, amount in list(self.resources.items()):
                    if amount >= 10:  # Only sell if we have at least 10 units
                        from economy import Market
                        # Get current market price
                        price = Market.instance.get_price(resource)
                        
                        # Sell the resources
                        earned = amount * price
                        self.resources[resource] = 0  # Clear out the resource
                        
                        # Find the corresponding AI and add money to it
                        from game import Game
                        if Game.instance and hasattr(Game.instance, 'ai_factories'):
                            for ai in Game.instance.ai_factories:
                                if str(ai.id) == ai_id:
                                    ai.money += earned
                                    ai.logger.log('DEPOSIT', 'AUTOSELL', f"Sold {amount} units of {resource} for ${earned}")
                                    break

    def find_closest_deposit(self):
        """Find the closest deposit building that can accept resources"""
        from config import DEPOSIT_SIZE, MAX_RESOURCE_TYPES_PER_DEPOSIT
        closest = None
        min_distance = float('inf')
        
        # First try to find a deposit that already contains this resource type
        for pos, tile in self.tile.world.tiles.items():
            if (tile.owner == self.tile.owner and 
                tile.building == 'DEPOSIT' and 
                hasattr(tile, 'building_instance') and 
                tile.building_instance and
                tile.building_instance.get_total_resources() < DEPOSIT_SIZE):
                
                # Check if this deposit already has the resource type or has space for a new type
                deposit_can_accept = False
                resource_type = self.tile.resource_type if hasattr(self, 'tile') and hasattr(self.tile, 'resource_type') else None
                
                if resource_type:
                    # Check if the deposit already has this resource type
                    if resource_type in tile.building_instance.resources:
                        deposit_can_accept = True
                    # Or check if it has room for a new resource type
                    elif len(tile.building_instance.resources.keys()) < MAX_RESOURCE_TYPES_PER_DEPOSIT:
                        deposit_can_accept = True
                else:
                    # If we don't know the resource type, assume it can accept it
                    deposit_can_accept = True
                
                if deposit_can_accept:
                    distance = self.get_distance_to(tile)
                    if distance < min_distance:
                        min_distance = distance
                        closest = tile
        return closest
    
    def find_closest_deposit_with_resources(self, resource_type, amount=1):
        """Find the closest deposit that contains the required resource"""
        closest = None
        min_distance = float('inf')
        
        for pos, tile in self.tile.world.tiles.items():
            if (tile.owner == self.tile.owner and 
                tile.building == 'DEPOSIT' and
                tile.building_instance):
                if self.has_resource_in_deposit(tile.building_instance, resource_type, amount):
                    distance = self.get_distance_to(tile)
                    if distance < min_distance:
                        min_distance = distance
                        closest = tile.building_instance
        return closest
    
    def find_closest_deposit_with_space(self):
        """Find the closest deposit with available space"""
        from config import DEPOSIT_SIZE, MAX_RESOURCE_TYPES_PER_DEPOSIT
        closest = None
        min_distance = float('inf')
        
        # The resource type we're looking to store (for processing buildings)
        output_resource = None
        if self.type == 'PROCESSING' and self.selected_recipe:
            from config import RECIPES
            if self.selected_recipe in RECIPES:
                output_resource = RECIPES[self.selected_recipe]['output']
        
        for pos, tile in self.tile.world.tiles.items():
            if (tile.owner == self.tile.owner and 
                tile.building == 'DEPOSIT' and
                tile.building_instance and
                tile.building_instance.get_total_resources() < DEPOSIT_SIZE):
                
                # Check if the deposit can accept a new resource type, if applicable
                can_accept = True
                if output_resource:
                    # If the deposit doesn't already have this resource and is at the type limit, skip it
                    if (output_resource not in tile.building_instance.resources and
                        len(tile.building_instance.resources.keys()) >= MAX_RESOURCE_TYPES_PER_DEPOSIT):
                        can_accept = False
                
                if can_accept:
                    distance = self.get_distance_to(tile)
                    if distance < min_distance:
                        min_distance = distance
                        closest = tile.building_instance
        return closest
    
    def has_resource_in_deposit(self, deposit, resource_type, amount=1):
        """Check if a deposit has enough of the specified resource"""
        if hasattr(deposit, 'resources'):
            return deposit.resources.get(resource_type, 0) >= amount
        return False
    
    def get_distance_to(self, other_tile):
        """Calculate Manhattan distance to another tile"""
        return abs(self.tile.x - other_tile.x) + abs(self.tile.y - other_tile.y)
    
    def get_total_resources(self):
        """Get total amount of resources stored"""
        return sum(self.resources.values())
    
    def can_accept_resource(self, resource_type, amount):
        """Check if deposit can accept more of a resource"""
        from config import DEPOSIT_SIZE, MAX_RESOURCE_TYPES_PER_DEPOSIT
        
        # Check if we have enough space in total
        current_total = self.get_total_resources()
        if current_total + amount > DEPOSIT_SIZE:
            return False
            
        # If the resource is already in the deposit, we can accept more of it
        if resource_type in self.resources:
            return True
            
        # Check if we're at the limit of different resource types
        current_unique_resources = len(self.resources.keys())
        if current_unique_resources >= MAX_RESOURCE_TYPES_PER_DEPOSIT:
            from game import Game
            if Game.instance:
                Game.instance.logger.log('DEPOSIT', 'LIMIT', 
                    f"Deposit at ({self.tile.x}, {self.tile.y}) reached the limit of {MAX_RESOURCE_TYPES_PER_DEPOSIT} different resource types")
            return False
            
        # We have space and we're not at the resource type limit
        return True

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

    def update_commerce(self, dt):
        """Handle commerce station behavior - check if AI should buy resources"""
        from game import Game
        
        # Skip if no resource is being traded
        if not self.commerce_resource or self.commerce_amount <= 0:
            return
            
        # AI owned commerce station
        if self.tile.owner and self.tile.owner.startswith('ai_'):
            return  # AI selling logic is handled by the AI class
            
        # Player owned commerce station - allow AIs to buy
        self.commerce_last_check_time += dt
        if self.commerce_last_check_time >= self.commerce_check_interval:
            self.commerce_last_check_time = 0
            
            # Check if any AI wants to buy
            if Game.instance and hasattr(Game.instance, 'ai_factories'):
                for ai in Game.instance.ai_factories:
                    # AI decides whether to buy based on price and need
                    if self._ai_decides_to_buy(ai):
                        amount_to_buy = min(self.commerce_amount, 10)  # Buy up to 10 units at a time
                        total_cost = amount_to_buy * self.commerce_price
                        
                        # Check if AI can afford it
                        if ai.money >= total_cost:
                            # Process the transaction
                            self.commerce_amount -= amount_to_buy
                            ai.money -= total_cost
                            
                            # Add money to player
                            Game.instance.player.money += total_cost
                            
                            # Add resource to AI's deposits
                            self._add_resource_to_ai_deposit(ai, self.commerce_resource, amount_to_buy)
                            
                            # Notify player of sale
                            Game.instance.logger.log('COMMERCE', 'SOLD', 
                                f"AI-{ai.id} bought {amount_to_buy} units of {self.commerce_resource} for ${total_cost}")
                            
                            # Reset commerce station if sold out
                            if self.commerce_amount <= 0:
                                self.commerce_resource = None
                                self.commerce_price = 0
                                break
                                
    def _ai_decides_to_buy(self, ai):
        """AI decision logic for purchasing from commerce stations"""
        from economy import Market
        from config import RECIPES, PROCESSED_RESOURCES
        
        # Skip if AI can't afford minimum purchase
        if ai.money < self.commerce_price:
            return False
            
        # Get market price for comparison
        market_price = Market.instance.get_price(self.commerce_resource)
        
        # Calculate price ratio (lower is better deal)
        price_ratio = self.commerce_price / market_price
        
        # Basic buying logic:
        # 1. Always buy if it's cheaper than market
        if price_ratio < 0.9:  # At least 10% cheaper than market
            return True
            
        # 2. Buy with decreasing probability as price increases
        if price_ratio < 1.1:  # Up to 10% more expensive than market
            return random.random() < 0.7  # 70% chance
        
        if price_ratio < 1.3:  # Up to 30% more expensive than market
            return random.random() < 0.3  # 30% chance
            
        # 3. Additional logic for resources needed by processing buildings
        for tile in ai.owned_tiles:
            if (tile.building == 'PROCESSING' and 
                hasattr(tile, 'building_instance') and 
                tile.building_instance and
                tile.building_instance.selected_recipe):
                recipe = RECIPES.get(tile.building_instance.selected_recipe)
                if recipe:
                    # Check if this resource is needed for the recipe
                    if (recipe['input1'] == self.commerce_resource or 
                        recipe['input2'] == self.commerce_resource):
                        # More eager to buy resources needed for processing
                        return random.random() < 0.5  # 50% chance regardless of price
                        
        # Default: unlikely to buy at high prices
        return random.random() < 0.1  # 10% chance
        
    def _add_resource_to_ai_deposit(self, ai, resource_type, amount):
        """Add purchased resources to an AI's deposit"""
        # Find a deposit with space
        for tile in ai.owned_tiles:
            if (tile.building == 'DEPOSIT' and 
                hasattr(tile, 'building_instance') and 
                tile.building_instance):
                
                deposit = tile.building_instance
                if deposit.can_accept_resource(resource_type, amount):
                    deposit.resources[resource_type] = deposit.resources.get(resource_type, 0) + amount
                    ai.logger.log('COMMERCE', 'BUY', 
                        f"Added {amount} {resource_type} from commerce purchase to deposit at ({tile.x}, {tile.y})")
                    return True
                    
        # If no deposit has enough space, create/add to resources in commerce building itself
        self.resources[resource_type] = self.resources.get(resource_type, 0) + amount
        ai.logger.log('COMMERCE', 'BUY', 
            f"No deposit available, stored {amount} {resource_type} in commerce building at ({self.tile.x}, {self.tile.y})")
        return False

    def setup_commerce_trade(self, resource_type, amount, price):
        """Set up a commerce station to trade a specific resource"""
        # Check if we have enough of the resource across all deposits
        if self.tile.owner == 'player':
            from game import Game
            
            # First count total resources available across all deposits
            total_available = 0
            deposits_with_resource = []
            
            for tile in Game.instance.player.owned_tiles:
                if (tile.building == 'DEPOSIT' and 
                    hasattr(tile, 'building_instance') and 
                    tile.building_instance):
                    
                    deposit = tile.building_instance
                    resource_amount = deposit.resources.get(resource_type, 0)
                    if resource_amount > 0:
                        total_available += resource_amount
                        deposits_with_resource.append((deposit, resource_amount))
            
            # Check if we have enough resources in total
            if total_available >= amount:
                # Take resources from deposits, starting with those that have the most
                deposits_with_resource.sort(key=lambda x: x[1], reverse=True)
                remaining_to_take = amount
                
                for deposit, available in deposits_with_resource:
                    take_amount = min(available, remaining_to_take)
                    deposit.resources[resource_type] -= take_amount
                    remaining_to_take -= take_amount
                    
                    if remaining_to_take <= 0:
                        break
                
                # Set up trade
                self.commerce_resource = resource_type
                self.commerce_amount = amount
                self.commerce_price = price
                
                Game.instance.logger.log('COMMERCE', 'SETUP', 
                    f"Set up trade for {amount} {resource_type} at ${price} per unit")
                return True
            
            Game.instance.logger.log('COMMERCE', 'ERROR', 
                f"Not enough {resource_type} across all deposits ({total_available}/{amount} needed) to set up commerce station")
            return False
        
        # For AI, assume resources are available
        self.commerce_resource = resource_type
        self.commerce_amount = amount
        self.commerce_price = price
        return True
        
    def buy_from_commerce(self, buyer_type, amount=None):
        """Player or AI buys from this commerce station"""
        if not self.commerce_resource or self.commerce_amount <= 0:
            return False
            
        # Default: buy all available if amount not specified
        if amount is None:
            amount = self.commerce_amount
        else:
            amount = min(amount, self.commerce_amount)
            
        if amount <= 0:
            return False
            
        total_cost = amount * self.commerce_price
        
        # Handle player buying from AI commerce station
        if buyer_type == 'player' and self.tile.owner and self.tile.owner.startswith('ai_'):
            from game import Game
            
            # Check if player can afford
            if Game.instance.player.money < total_cost:
                Game.instance.logger.log('COMMERCE', 'ERROR', 
                    f"Not enough money to buy {amount} {self.commerce_resource} for ${total_cost}")
                return False
                
            # Process transaction
            Game.instance.player.money -= total_cost
            
            # Find player deposit to add resources to
            for tile in Game.instance.player.owned_tiles:
                if (tile.building == 'DEPOSIT' and 
                    hasattr(tile, 'building_instance') and 
                    tile.building_instance and
                    tile.building_instance.can_accept_resource(self.commerce_resource, amount)):
                    
                    deposit = tile.building_instance
                    deposit.resources[self.commerce_resource] = deposit.resources.get(self.commerce_resource, 0) + amount
                    
                    # Update AI owner's money
                    ai_id = self.tile.owner.split('_')[1]
                    for ai in Game.instance.ai_factories:
                        if str(ai.id) == ai_id:
                            ai.money += total_cost
                            ai.logger.log('COMMERCE', 'SOLD', 
                                f"Player bought {amount} {self.commerce_resource} for ${total_cost}")
                            break
                    
                    # Update commerce station
                    self.commerce_amount -= amount
                    if self.commerce_amount <= 0:
                        self.commerce_resource = None
                        self.commerce_price = 0
                        
                    Game.instance.logger.log('COMMERCE', 'BUY', 
                        f"Bought {amount} {self.commerce_resource} from AI-{ai_id} for ${total_cost}")
                    return True
                    
            Game.instance.logger.log('COMMERCE', 'ERROR', 
                f"No deposit with enough space to store {amount} {self.commerce_resource}")
            return False
            
        return False
