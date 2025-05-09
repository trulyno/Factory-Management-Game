import os
import time
import csv
import pygame
import matplotlib.pyplot as plt
from datetime import datetime
from logger import GameLogger
from config import MARKET_UPDATE_INTERVAL

class SessionSaver:
    """Class to handle saving session data to files"""
    def __init__(self, game):
        self.game = game
        self.session_start_time = time.time()
        self.session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_dir = os.path.join("sessions", self.session_id)
        self.player_logs = []
        self.ai_logs = []
        self.building_logs = []
        self.market_data = []  # Format: [timestamp, {resource: price, ...}]
        
        # Create session directory if it doesn't exist
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        os.mkdir(self.session_dir)
        
        # Initialize market data collection
        self._record_market_data()
    
    def _record_market_data(self):
        """Record current market data"""
        if hasattr(self.game, 'market') and self.game.market:
            timestamp = time.time() - self.session_start_time
            self.market_data.append([timestamp, self.game.market.prices.copy()])
    
    def capture_log(self, source, action_type, description, category):
        """Store logs by category for later saving"""
        log_entry = {
            'time': time.time() - self.session_start_time,
            'source': source,
            'action': action_type,
            'description': description
        }
        
        if category == 'player':
            self.player_logs.append(log_entry)
        elif category == 'ai':
            self.ai_logs.append(log_entry)
        elif category == 'building':
            self.building_logs.append(log_entry)
    
    def update(self, dt):
        """Update session data collection on market update interval"""
        if hasattr(self.game, 'time_since_update') and self.game.time_since_update == 0:
            # Market prices just updated, record the data
            self._record_market_data()
    
    def save_market_data_csv(self):
        """Save market price history to CSV file"""
        if not self.market_data:
            return
        
        csv_path = os.path.join(self.session_dir, "market.csv")
        
        # Get all resource types that have appeared in the market data
        resources = set()
        for _, prices in self.market_data:
            resources.update(prices.keys())
        
        resources = sorted(resources)  # Sort for consistent order
        
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row
            header = ['Time'] + resources
            writer.writerow(header)
            
            # Write data rows
            for timestamp, prices in self.market_data:
                row = [f"{timestamp:.2f}"]
                for resource in resources:
                    row.append(prices.get(resource, ""))
                writer.writerow(row)
    
    def generate_market_graph(self):
        """Generate a graph of market price changes"""
        if not self.market_data:
            return
        
        # Get all resource types that have appeared in the market data
        resources = set()
        for _, prices in self.market_data:
            resources.update(prices.keys())
        
        # Create a graph showing the price variation of all resources
        plt.figure(figsize=(12, 8))
        
        # Extract times and prices for each resource
        timestamps = [data[0] / 60 for data in self.market_data]  # Convert to minutes
        
        for resource in sorted(resources):
            prices = []
            for _, price_data in self.market_data:
                prices.append(price_data.get(resource, None))
            
            # Filter out None values
            valid_points = [(t, p) for t, p in zip(timestamps, prices) if p is not None]
            if valid_points:
                t_vals, p_vals = zip(*valid_points)
                plt.plot(t_vals, p_vals, label=resource, linewidth=2)
        
        plt.xlabel('Time (minutes)')
        plt.ylabel('Price ($)')
        plt.title('Resource Price Fluctuation')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.tight_layout()
        
        # Save the graph
        graph_path = os.path.join(self.session_dir, "market.png")
        plt.savefig(graph_path)
        plt.close()
    
    def save_world_data(self):
        """Save world data as a markdown table"""
        if not hasattr(self.game, 'world') or not self.game.world:
            return
        
        world = self.game.world
        md_path = os.path.join(self.session_dir, "world.md")
        
        with open(md_path, 'w') as mdfile:
            mdfile.write("# World Map\n\n")
            mdfile.write("Each cell represents a tile in the world with format: Resource (Owner) [Building] - Price\n\n")
            
            # Write the table header
            mdfile.write("| Coordinates |")
            for x in range(world.width):
                mdfile.write(f" {x} |")
            mdfile.write("\n")
            
            # Write the header separator
            mdfile.write("|------------|")
            for x in range(world.width):
                mdfile.write("---|")
            mdfile.write("\n")
            
            # Write the table rows
            for y in range(world.height):
                mdfile.write(f"| **{y}** |")
                for x in range(world.width):
                    if (x, y) in world.tiles:
                        tile = world.tiles[(x, y)]
                        
                        # Format the cell content
                        resource = tile.resource_type if tile.surveyed else "?"
                        owner = ""
                        if tile.owner:
                            if tile.owner == 'player':
                                owner = "(P)"
                            else:
                                ai_id = tile.owner.split('_')[1]
                                owner = f"(AI-{ai_id})"
                        
                        building = f"[{tile.building}]" if tile.building else ""
                        price = f"${tile.price}" if tile.surveyed else "$?"
                        
                        mdfile.write(f" {resource} {owner} {building} - {price} |")
                    else:
                        mdfile.write(" |")
                mdfile.write("\n")
    
    def capture_world_image(self):
        """Capture an image of the entire world"""
        if not hasattr(self.game, 'world') or not self.game.world:
            return
        
        world = self.game.world
        
        # Calculate the size needed for the entire world
        width = world.width * 50  # TILE_SIZE
        height = world.height * 50  # TILE_SIZE
        
        # Create a surface big enough to render the entire world
        surface = pygame.Surface((width, height))
        surface.fill((0, 0, 0))  # Black background
        
        # Draw the world on this surface without camera offset
        world.draw(surface, (0, 0))
        
        # Save the surface as an image
        image_path = os.path.join(self.session_dir, "world.png")
        pygame.image.save(surface, image_path)
    
    def save_stats(self):
        """Save player stats from game finish"""
        if hasattr(self.game, 'stats'):
            stats = self.game.stats
            stats_path = os.path.join(self.session_dir, "player_stats.txt")
            
            with open(stats_path, 'w') as statsfile:
                statsfile.write("# Player Statistics\n\n")
                
                stats_list = stats.get_stats_display()
                for stat in stats_list:
                    statsfile.write(f"{stat}\n")
    
    def save_logs(self):
        """Save log files for each source category"""
        # Save player logs
        if self.player_logs:
            player_log_path = os.path.join(self.session_dir, "player_logs.txt")
            with open(player_log_path, 'w') as logfile:
                logfile.write("# Player Logs\n\n")
                logfile.write("Time | Source | Action | Description\n")
                logfile.write("-----|--------|--------|------------\n")
                
                for log in self.player_logs:
                    time_str = f"{log['time']:.2f}s"
                    logfile.write(f"{time_str} | {log['source']} | {log['action']} | {log['description']}\n")
        
        # Save AI logs
        if self.ai_logs:
            ai_log_path = os.path.join(self.session_dir, "ai_logs.txt")
            with open(ai_log_path, 'w') as logfile:
                logfile.write("# AI Logs\n\n")
                logfile.write("Time | Source | Action | Description\n")
                logfile.write("-----|--------|--------|------------\n")
                
                for log in self.ai_logs:
                    time_str = f"{log['time']:.2f}s"
                    logfile.write(f"{time_str} | {log['source']} | {log['action']} | {log['description']}\n")
        
        # Save building logs
        if self.building_logs:
            building_log_path = os.path.join(self.session_dir, "building_logs.txt")
            with open(building_log_path, 'w') as logfile:
                logfile.write("# Building Logs\n\n")
                logfile.write("Time | Source | Action | Description\n")
                logfile.write("-----|--------|--------|------------\n")
                
                for log in self.building_logs:
                    time_str = f"{log['time']:.2f}s"
                    logfile.write(f"{time_str} | {log['source']} | {log['action']} | {log['description']}\n")
    
    def save_session(self):
        """Save all session data to files"""
        self.save_logs()
        self.save_world_data()
        self.save_market_data_csv()
        self.generate_market_graph()
        self.capture_world_image()
        self.save_stats()
