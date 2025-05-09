import random
import time
from config import *

class Market:
    instance = None  # Class variable for global access
    def __init__(self):
        Market.instance = self  # Set this instance as the global one
        self.prices = {}
        self.supply = {}
        self.demand = {}
        self.last_update_time = time.time()
        self.trading_activity = {}  # Track resource trading activity
        self.initialize_market()
        
    def initialize_market(self):
        """Set up initial market conditions"""
        # Set base prices for resources
        for resource, details in RESOURCE_TYPES.items():
            self.prices[resource] = details['value']
            self.supply[resource] = random.randint(10, 100)
            self.demand[resource] = random.randint(10, 100)
            self.trading_activity[resource] = {
                'sell_volume': 0,
                'buy_volume': 0,
                'base_price': details['value']
            }
        
        # Set prices for processed goods
        for resource, details in PROCESSED_RESOURCES.items():
            self.prices[resource] = details['value']
            self.supply[resource] = random.randint(5, 50)
            self.demand[resource] = random.randint(5, 50)
            self.trading_activity[resource] = {
                'sell_volume': 0,
                'buy_volume': 0,
                'base_price': details['value']
            }
    
    def update_prices(self):
        """Update market prices based on supply and demand and trading activity"""
        # Check if we should update prices based on the elapsed time
        current_time = time.time()
        if current_time - self.last_update_time < MARKET_UPDATE_INTERVAL:
            return
            
        self.last_update_time = current_time
        
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
            
            # Trading activity affects price:
            # - More selling pressure lowers prices
            # - More buying pressure raises prices
            trading_pressure = 0
            total_volume = sell_volume + buy_volume
            
            if total_volume > 0:
                # Calculate trading pressure between -1 (all selling) and 1 (all buying)
                trading_pressure = (buy_volume - sell_volume) / total_volume
                
            # Combine supply/demand ratio with trading pressure
            # Weight: 50% supply/demand, 50% trading activity
            adjustment = MARKET_PRICE_ADJUSTMENT_FACTOR
            
            if ratio > 1:  # Demand exceeds supply, price goes up
                supply_demand_change = min(adjustment, ratio - 1)
            else:  # Supply exceeds demand, price goes down
                supply_demand_change = max(-adjustment, ratio - 1)
                
            # Trading pressure change (scaled by adjustment factor)
            trading_change = trading_pressure * adjustment
            
            # Combined change (average of the two factors)
            change = (supply_demand_change + trading_change) / 2
                
            # Apply change but keep within reasonable bounds
            self.prices[resource] = max(
                base_price * MARKET_MIN_PRICE_MULTIPLIER,
                min(base_price * MARKET_MAX_PRICE_MULTIPLIER, self.prices[resource] * (1 + change))
            )
            
        # Reset trading activity counters after price update
        for resource in self.trading_activity:
            self.trading_activity[resource]['sell_volume'] = 0
            self.trading_activity[resource]['buy_volume'] = 0
            
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
