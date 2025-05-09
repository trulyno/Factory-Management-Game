import random
import time
from config import *

class PriceManager:
    instance = None  # Class variable for global access
    
    def __init__(self):
        PriceManager.instance = self  # Set this instance as the global one
        self.last_update_time = time.time()
        self.time_elapsed = 0
        self.update_count = 0
        
        # Current multipliers
        self.survey_cost_multiplier = 1.0
        self.tile_cost_multiplier = 1.0
        self.building_cost_multiplier = 1.0
        
        # Initialize current costs
        self.update_costs()
    
    def update(self, dt):
        """Update prices based on game progress and time"""
        self.time_elapsed += dt
        
        current_time = time.time()
        if current_time - self.last_update_time < PRICE_UPDATE_INTERVAL:
            return
        
        self.last_update_time = current_time
        self.update_count += 1
        
        # Calculate economic factors for price adjustment
        self._calculate_price_adjustments()
        
        # Update all costs
        self.update_costs()
    
    def _calculate_price_adjustments(self):
        """Calculate price adjustments based on game state"""
        from game import Game
        
        # Get game difficulty scaling
        difficulty = AI_DIFFICULTY  # From config
        difficulty_scale = DIFFICULTY_SCALING.get(difficulty, 1.0)
        
        # Base time-based increase (now includes time elapsed in-game)
        base_increase = (PRICE_INCREASE_RATE * 
                        (1 + (self.update_count * 0.01)) * 
                        (1 + (self.time_elapsed * TIME_SCALING_FACTOR)))
        
        # Apply difficulty scaling
        base_increase *= difficulty_scale
        
        # Get economic statistics
        total_economy = Game.instance.stats.total_money_generated
        num_buildings = Game.instance.stats.num_buildings
        tiles_owned = Game.instance.stats.tiles_owned
        tiles_surveyed = Game.instance.stats.tiles_surveyed
        
        # Calculate total AI economy to add to economic pressure
        ai_economy = 0
        for ai in Game.instance.ai_factories:
            ai_economy += ai.money
            
        total_economy += ai_economy
        
        # Calculate multiplier adjustments with diminishing returns
        # Using logarithmic scaling to prevent runaway inflation
        from math import log
        
        # Add 1 to avoid log(0)
        economy_log_scale = log(total_economy + 1) / 10
        economy_factor = total_economy * ECONOMY_SCALING_FACTOR * economy_log_scale
        
        building_factor = num_buildings * BUILDINGS_SCALING_FACTOR
        tile_factor = (tiles_owned + tiles_surveyed) * TILES_SCALING_FACTOR
        
        # Apply different rates to different cost types
        # Survey costs rise slower than tile costs, which rise slower than building costs
        self.survey_cost_multiplier += base_increase * 0.7 + building_factor * 0.25 + economy_factor * 0.15
        self.tile_cost_multiplier += base_increase * 0.9 + tile_factor * 0.4 + economy_factor * 0.2
        self.building_cost_multiplier += base_increase * 1.1 + building_factor * 0.35 + economy_factor * 0.3
        
        # Cap multipliers with both minimum and maximum
        self.survey_cost_multiplier = max(MIN_PRICE_MULTIPLIER, min(self.survey_cost_multiplier, MAX_PRICE_MULTIPLIER))
        self.tile_cost_multiplier = max(MIN_PRICE_MULTIPLIER, min(self.tile_cost_multiplier, MAX_PRICE_MULTIPLIER))
        self.building_cost_multiplier = max(MIN_PRICE_MULTIPLIER, min(self.building_cost_multiplier, MAX_PRICE_MULTIPLIER))
        
        # Log significant price changes
        if self.update_count % 5 == 0 and Game.instance.logger:
            Game.instance.logger.log('ECONOMY', 'PRICES', 
                                   f"Price levels - Survey: {self.survey_cost_multiplier:.2f}x, " +
                                   f"Tiles: {self.tile_cost_multiplier:.2f}x, " +
                                   f"Buildings: {self.building_cost_multiplier:.2f}x")
    
    def update_costs(self):
        """Update all costs based on current multipliers"""
        # Update survey cost
        global SURVEY_COST
        SURVEY_COST = int(SURVEY_BASE_COST * self.survey_cost_multiplier)
        
        # Update building costs
        for building_type in BUILDINGS:
            if building_type != 'CENTRAL':  # Keep central building free
                BUILDINGS[building_type]['cost'] = int(BUILDINGS[building_type]['base_cost'] * self.building_cost_multiplier)
    
    def get_tile_cost_multiplier(self):
        """Return the current tile cost multiplier"""
        return self.tile_cost_multiplier
    
    def get_survey_cost(self):
        """Return the current survey cost"""
        return SURVEY_COST
    
    def get_building_cost(self, building_type):
        """Return the current cost for a building type"""
        return BUILDINGS[building_type]['cost']

class Market:
    instance = None  # Class variable for global access
    def __init__(self):
        Market.instance = self  # Set this instance as the global one
        self.prices = {}
        self.supply = {}
        self.demand = {}
        self.last_update_time = time.time()
        self.trading_activity = {}  # Track resource trading activity
        self.time_elapsed = 0  # Track time elapsed since game start for long-term market changes
        self.cycle_count = 0  # Track number of price updates for pattern detection
        self.initialize_market()
        
    def initialize_market(self):
        """Set up initial market conditions"""
        # Set base prices for resources with some initial randomness
        for resource, details in RESOURCE_TYPES.items():
            base_price = details['value']
            # Start with a slightly randomized price
            initial_price = base_price * random.uniform(0.9, 1.1)
            self.prices[resource] = initial_price
            
            # More variable supply and demand
            self.supply[resource] = random.randint(5, 150)
            self.demand[resource] = random.randint(5, 150)
            self.trading_activity[resource] = {
                'sell_volume': 0,
                'buy_volume': 0,
                'base_price': base_price,
                'trend_direction': random.choice([-1, 1]),  # Random initial trend
                'trend_duration': random.randint(3, 10)  # How long the trend will last
            }
            # Start with a slightly randomized price
            initial_price = base_price * random.uniform(0.9, 1.1)
            self.prices[resource] = initial_price
            
            # More variable supply and demand
            self.supply[resource] = random.randint(5, 150)
            self.demand[resource] = random.randint(5, 150)
            self.trading_activity[resource] = {
                'sell_volume': 0,
                'buy_volume': 0,
                'base_price': base_price
            }
        
        # Set prices for processed goods with more initial variability
        for resource, details in PROCESSED_RESOURCES.items():
            base_price = details['value']
            # Start with a more randomized price for processed goods
            initial_price = base_price * random.uniform(0.85, 1.15)
            self.prices[resource] = initial_price
            
            self.supply[resource] = random.randint(2, 75)
            self.demand[resource] = random.randint(2, 75)
            self.trading_activity[resource] = {
                'sell_volume': 0,
                'buy_volume': 0,
                'base_price': base_price
            }
    
    def update_prices(self):
        """Update market prices based on supply and demand and trading activity with randomness"""
        # Check if we should update prices based on the elapsed time
        current_time = time.time()
        if current_time - self.last_update_time < MARKET_UPDATE_INTERVAL:
            return
            
        self.last_update_time = current_time
        
        # Add a volatile market factor (varies between updates)
        market_volatility = random.uniform(0.8, 1.5)
        
        # Add random events that might affect all market prices
        market_event = random.random()
        global_modifier = 1.0
        
        # Occasionally trigger market events (10% chance)
        if market_event < 0.10:
            # Random market-wide fluctuation
            global_modifier = random.uniform(0.9, 1.1)
        
        for resource in self.prices:
            supply = max(1, self.supply.get(resource, 10))
            demand = max(1, self.demand.get(resource, 10))
            
            # Calculate price change based on supply/demand ratio
            ratio = demand / supply
            
            # Get trading activity for this resource
            trading = self.trading_activity[resource]
            sell_volume = trading['sell_volume']
            buy_volume = trading['buy_volume']
            base_price = trading['base_price']
            
            # Add resource-specific randomness
            resource_randomness = random.uniform(-0.02, 0.02)
            
            # Trading activity affects price:
            # - More selling pressure lowers prices
            # - More buying pressure raises prices
            trading_pressure = 0
            total_volume = sell_volume + buy_volume
            
            if total_volume > 0:
                # Calculate trading pressure between -1 (all selling) and 1 (all buying)
                trading_pressure = (buy_volume - sell_volume) / total_volume
                
            # Combine supply/demand ratio with trading pressure
            # Apply volatility to adjustment factor
            adjustment = MARKET_PRICE_ADJUSTMENT_FACTOR * market_volatility
            
            if ratio > 1:  # Demand exceeds supply, price goes up
                supply_demand_change = min(adjustment, ratio - 1)
            else:  # Supply exceeds demand, price goes down
                supply_demand_change = max(-adjustment, ratio - 1)
                
            # Trading pressure change (scaled by adjustment factor)
            trading_change = trading_pressure * adjustment
            
            # Combined change (average of factors + randomness)
            change = ((supply_demand_change + trading_change) / 2 + resource_randomness) * global_modifier
                
            # Apply change but keep within reasonable bounds
            self.prices[resource] = max(
                base_price * MARKET_MIN_PRICE_MULTIPLIER,
                min(base_price * MARKET_MAX_PRICE_MULTIPLIER, self.prices[resource] * (1 + change))
            )
        # Reset trading activity counters after price update and introduce supply/demand changes
        for resource in self.trading_activity:
            self.trading_activity[resource]['sell_volume'] = 0
            self.trading_activity[resource]['buy_volume'] = 0
            
            # Randomly adjust supply and demand values to keep market dynamic
            supply_change = random.uniform(-10, 10)
            demand_change = random.uniform(-10, 10)
            
            # Apply changes but ensure values stay positive
            self.supply[resource] = max(5, self.supply.get(resource, 10) + supply_change)
            self.demand[resource] = max(5, self.demand.get(resource, 10) + demand_change)
            
    def sell(self, resource, amount):
        """Handle resource selling to the market"""
        if resource not in self.prices:
            return 0
            
        price = self.prices[resource]
        self.supply[resource] = self.supply.get(resource, 0) + amount
        
        # Track selling activity for price adjustment
        if resource in self.trading_activity:
            self.trading_activity[resource]['sell_volume'] += amount
            return price * amount
        
    def buy(self, resource, amount):
        """Handle resource buying from the market"""
        if resource not in self.prices:
            return 0
            
        price = self.prices[resource]
        available = self.supply.get(resource, 0)
        actual_amount = min(amount, available)
        
        if actual_amount > 0:
            self.supply[resource] = available - actual_amount
            self.demand[resource] = self.demand.get(resource, 0) + actual_amount
            
            # Track buying activity for price adjustment
            if resource in self.trading_activity:
                self.trading_activity[resource]['buy_volume'] += actual_amount
            
        return price * actual_amount, actual_amount

    def get_price(self, resource):
        """Get current price for a resource"""
        return self.prices.get(resource, 0)

    def create_market_shock(self):
        """Create a significant market event affecting multiple resources"""
        # Choose how many resources will be affected (between 1 and 3)
        num_affected = random.randint(1, 3)
        
        # Get a list of resources and randomly choose which ones to affect
        resources = list(self.prices.keys())
        affected_resources = random.sample(resources, min(num_affected, len(resources)))
        
        for resource in affected_resources:
            # Determine if it's a positive or negative shock
            is_positive = random.random() > 0.5
            
            # Create a significant price change (10%-30%)
            shock_magnitude = random.uniform(0.1, 0.3)
            
            if is_positive:
                # Price increase
                self.prices[resource] = min(
                    self.prices[resource] * (1 + shock_magnitude),
                    self.trading_activity[resource]['base_price'] * MARKET_MAX_PRICE_MULTIPLIER
                )
            else:
                # Price decrease
                self.prices[resource] = max(
                    self.prices[resource] * (1 - shock_magnitude),
                    self.trading_activity[resource]['base_price'] * MARKET_MIN_PRICE_MULTIPLIER
                )
                
        return affected_resources

class TradeOffer:
    def __init__(self, sender, receiver, offer_resource, offer_amount, request_resource, request_amount):
        self.sender = sender
        self.receiver = receiver
        self.offer_resource = offer_resource
        self.offer_amount = offer_amount
        self.request_resource = request_resource
        self.request_amount = request_amount
        self.forced = False
        self.penalty = 0
    
    def make_forced(self, penalty):
        """Make this a forced trade with a penalty for refusal"""
        self.forced = True
        self.penalty = penalty
