import random
from config import *

class Market:
    instance = None  # Class variable for global access
    
    def __init__(self):
        Market.instance = self  # Set this instance as the global one
        self.prices = {}
        self.supply = {}
        self.demand = {}
        self.initialize_market()
    
    def initialize_market(self):
        """Set up initial market conditions"""
        # Set base prices for resources
        for resource, details in RESOURCE_TYPES.items():
            self.prices[resource] = details['value']
            self.supply[resource] = random.randint(10, 100)
            self.demand[resource] = random.randint(10, 100)
        
        # Set prices for processed goods
        for resource, details in PROCESSED_RESOURCES.items():
            self.prices[resource] = details['value']
            self.supply[resource] = random.randint(5, 50)
            self.demand[resource] = random.randint(5, 50)
    
    def update_prices(self):
        """Update market prices based on supply and demand"""
        for resource in self.prices:
            supply = max(1, self.supply.get(resource, 10))
            demand = max(1, self.demand.get(resource, 10))
            
            # Calculate price change based on supply/demand ratio
            ratio = demand / supply
            adjustment = 0.1  # Max 10% change per update
            
            if ratio > 1:  # Demand exceeds supply, price goes up
                change = min(adjustment, ratio - 1)
            else:  # Supply exceeds demand, price goes down
                change = max(-adjustment, ratio - 1)
                
            base_price = RESOURCE_TYPES.get(resource, {}).get('value', 10)
            if resource in PROCESSED_RESOURCES:
                base_price = PROCESSED_RESOURCES[resource]['value']
                
            # Apply change but keep within reasonable bounds
            self.prices[resource] = max(
                base_price * 0.5,
                min(base_price * 2, self.prices[resource] * (1 + change))
            )
            
    def sell(self, resource, amount):
        """Handle resource selling to the market"""
        if resource not in self.prices:
            return 0
            
        price = self.prices[resource]
        self.supply[resource] = self.supply.get(resource, 0) + amount
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
