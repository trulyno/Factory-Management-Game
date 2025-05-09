import pygame
import sys
import random
from config import *
from world import World
from player import Player
from economy import Market
from ai import AIFactory
from ui import UI
from logger import GameLogger
from stats import GameStats
from session_saver import SessionSaver

class Camera:
    def __init__(self, width, height, world_width, world_height):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.world_width = world_width * TILE_SIZE
        self.world_height = world_height * TILE_SIZE
        # Add mouse drag tracking variables
        self.is_dragging = False
        self.drag_start = None
        # Add zoom variables
        
        self.zoom_level = 1.0
        self.min_zoom = 0.5
        
        # Calculate max zoom based on world size
        # For small worlds, allow more zoom in, for larger worlds, allow more zoom out
        world_diagonal = (world_width**2 + world_height**2)**0.5
        max_dimension = max(world_width, world_height)
        
        if max_dimension <= 20:  # Small world
            self.max_zoom = 3.0
        elif max_dimension <= 50:  # Medium world
            self.max_zoom = 2.0
        else:  # Large world
            self.max_zoom = 1.5
            
        # Adjust min zoom for very large worlds to allow seeing more of the map
        if max_dimension > 100:
            self.min_zoom = 0.2
        elif max_dimension > 50:
            self.min_zoom = 0.35
            
        self.zoom_speed = 0.1
        
    def move(self, dx, dy):
        """Move camera by an amount, keeping within world bounds"""
        # Account for zoom level when calculating boundaries
        visible_width = self.width / self.zoom_level
        visible_height = self.height / self.zoom_level
        
        # Apply the boundaries with zoom level considered
        self.x = max(0, min(self.world_width - visible_width, self.x + dx))
        self.y = max(0, min(self.world_height - visible_height, self.y + dy))
        
    def get_offset(self):
        """Get camera offset for rendering"""
        return (self.x, self.y, self.zoom_level)
    
    def screen_to_world(self, screen_pos):
        """Convert screen position to world position"""
        # Apply zoom factor to screen coordinates
        world_x = (screen_pos[0] / self.zoom_level) + self.x
        world_y = (screen_pos[1] / self.zoom_level) + self.y
        tile_x = int(world_x // TILE_SIZE)
        tile_y = int(world_y // TILE_SIZE)
        return (tile_x, tile_y)
        
    def start_drag(self, pos):
        """Start camera dragging from position"""
        self.is_dragging = True
        self.drag_start = pos
        
    def end_drag(self):
        """End camera dragging"""
        self.is_dragging = False
        self.drag_start = None
        
    def update_drag(self, pos):
        """Update camera position while dragging"""
        if self.is_dragging and self.drag_start:
            # Calculate drag distance (reversed to make drag feel natural)
            # Apply zoom factor to make the dragging speed match the visual scale
            dx = (self.drag_start[0] - pos[0]) / self.zoom_level
            dy = (self.drag_start[1] - pos[1]) / self.zoom_level
            
            # Move camera
            self.move(dx, dy)
            
            # Update drag start position
            self.drag_start = pos
            
    def zoom(self, direction, mouse_pos=None):
        """Zoom the camera in or out 
        direction: 1 for zoom in, -1 for zoom out
        mouse_pos: position of mouse when zooming (to zoom towards point)
        """
        # Store old zoom for calculations
        old_zoom = self.zoom_level
        
        # Update zoom level based on direction
        if direction > 0:  # Zoom in
            self.zoom_level = min(self.max_zoom, self.zoom_level + self.zoom_speed)
        else:  # Zoom out
            self.zoom_level = max(self.min_zoom, self.zoom_level - self.zoom_speed)
            
        # If mouse position is provided, adjust camera position to zoom towards that point
        if mouse_pos:
            # Convert mouse position to world coordinates before zoom
            mouse_world_x = (mouse_pos[0] / old_zoom) + self.x
            mouse_world_y = (mouse_pos[1] / old_zoom) + self.y
            
            # Calculate new camera position to keep mouse point at same relative position after zoom
            new_x = mouse_world_x - (mouse_pos[0] / self.zoom_level)
            new_y = mouse_world_y - (mouse_pos[1] / self.zoom_level)
            
            # Respect world boundaries when setting new position
            # Account for the zoom level when calculating the right and bottom boundaries
            visible_width = self.width / self.zoom_level
            visible_height = self.height / self.zoom_level
            
            # Make sure we don't go beyond the world boundaries
            self.x = max(0, min(self.world_width - visible_width, new_x))
            self.y = max(0, min(self.world_height - visible_height, new_y))

class Game:
    instance = None  # Class variable for global access
    def __init__(self, screen=None):
        Game.instance = self  # Set up global instance
        
        if screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("Factory Management Game")
        else:
            # Use the provided screen
            self.screen = screen
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.restart_game = False  # Flag to indicate when game should restart
        
        # Game objects
        from config import WORLD_SIZE, NUM_AI_PLAYERS
        from economy import PriceManager, Market
        self.world = World()  # World now uses WORLD_SIZE from config
        self.player = Player()
        self.market = Market()
        self.price_manager = PriceManager()  # Initialize the price manager
        self.logger = GameLogger()
        self.stats = GameStats()  # Initialize stats tracker
        
        # Set up player starting area
        self.world.setup_player_start(self.player)
        
        # Set up AI factories
        self.ai_factories = []
        self.world.setup_ai_factories()  # Uses NUM_AI_PLAYERS from config
        for i in range(NUM_AI_PLAYERS):
            self.ai_factories.append(AIFactory(i, self.world))
        
        # Camera and UI
        self.camera = Camera(SCREEN_WIDTH - UI_PANEL_WIDTH, SCREEN_HEIGHT, self.world.width, self.world.height)
        # Center camera on player's starting position (middle of the map)
        center_x, center_y = self.world.width // 2, self.world.height // 2
        self.camera.x = max(0, (center_x * TILE_SIZE) - (self.camera.width // 2))
        self.camera.y = max(0, (center_y * TILE_SIZE) - (self.camera.height // 2))
        self.ui = UI(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Game state
        self.game_over = False
        self.time_since_update = 0
        
        # Create session saver and connect it to logger
        self.session_saver = SessionSaver(self)
        self.logger.set_session_saver(self.session_saver)
        
    def handle_events(self):
        """Process game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:                
                # Game over state controls
                if self.game_over:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    return  # Skip other inputs when game is over
                
                # First check if UI needs to handle text input
                if self.ui.input_active:
                    if self.ui.handle_key_event(event):
                        continue  # Skip other keyboard handling if UI consumed the event
                
                # Camera movement with arrow keys
                if event.key == pygame.K_LEFT:
                    self.camera.move(-TILE_SIZE, 0)
                elif event.key == pygame.K_RIGHT:
                    self.camera.move(TILE_SIZE, 0)
                elif event.key == pygame.K_UP:
                    self.camera.move(0, -TILE_SIZE)
                elif event.key == pygame.K_DOWN:
                    self.camera.move(0, TILE_SIZE)                
                # Cancel building selection with Escape
                elif event.key == pygame.K_ESCAPE:
                    self.ui.selected_building_type = None
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Start camera drag with middle mouse button
                if event.button == 2:  # Middle mouse button
                    if event.pos[0] < SCREEN_WIDTH - UI_PANEL_WIDTH:
                        self.camera.start_drag(event.pos)
                # Handle UI clicks with left mouse button
                elif event.button == 1:  # Left mouse button
                    if not self.ui.handle_click(event.pos, self.player, self.world):
                        # Handle world clicks
                        if event.pos[0] < SCREEN_WIDTH - UI_PANEL_WIDTH:
                            world_pos = self.camera.screen_to_world(event.pos)
                            if world_pos in self.world.tiles:
                                tile = self.world.tiles[world_pos]
                                
                                # Select tile
                                self.ui.selected_tile = tile
                                  # If building type is selected and tile is owned, try to build
                                if self.ui.selected_building_type and tile.owner == 'player':
                                    if self.player.build(tile, self.ui.selected_building_type):
                                        self.ui.selected_building_type = None
              # Add these handlers for mouse up and motion            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:  # Middle mouse button
                    self.camera.end_drag()
            
            elif event.type == pygame.MOUSEMOTION:
                if self.camera.is_dragging:
                    self.camera.update_drag(event.pos)
            
            # Handle mouse wheel for zooming
            elif event.type == pygame.MOUSEWHEEL:
                # Check if mouse is in the game view area (not in UI panel)
                mouse_pos = pygame.mouse.get_pos()
                if mouse_pos[0] < SCREEN_WIDTH - UI_PANEL_WIDTH:
                    # Positive y means scroll up (zoom in), negative means scroll down (zoom out)
                    zoom_direction = event.y
                    self.camera.zoom(zoom_direction, mouse_pos)
    
    def update(self, dt):
        """Update game state"""
        if self.game_over:
            return
            
        # Update price manager continuously
        self.price_manager.update(dt)
            
        # Update market prices periodically
        self.time_since_update += dt
        if self.time_since_update >= MARKET_UPDATE_INTERVAL:
            self.time_since_update = 0
            self.market.update_prices()
            
            # Occasionally create market shocks (1% chance per update)
            if random.random() < 0.01:
                affected_resources = self.market.create_market_shock()
                # Log the market shock event if logger is available
                if hasattr(self, 'logger'):
                    resources_str = ', '.join(affected_resources)
                    self.logger.log("MARKET", "SHOCK", f"Market shock affecting: {resources_str}")
            
            # Update AI factories
            for ai in self.ai_factories:
                ai.update()
                
            # Update session saver to record market data
            if hasattr(self, 'session_saver'):
                self.session_saver.update(dt)
        
        # Update world (includes buildings)
        self.world.update(dt)        # Check win condition
        if self.player.money >= WIN_CONDITION:
            self.game_over = True
            # Stop the timer when the game ends
            self.stats.stop_timer()
            
            # Log win message with time
            time_played_str = self.stats.format_time(self.stats.time_played)
            win_message = f"You've reached the goal of $1,000,000! Time: {time_played_str}"
            
            # Check if this is a new personal best
            if self.stats.is_personal_best():
                win_message += " (New Personal Best!)"
                self.logger.log('GAME', 'WIN', win_message)
            else:
                self.logger.log('GAME', 'WIN', win_message)
            
            # Save session data when game ends
            if hasattr(self, 'session_saver'):
                self.session_saver.save_session()
    
    def draw(self):
        """Render the game"""
        # Clear screen
        self.screen.fill(BLACK)
          # Draw restart button at the top left corner of the screen
        restart_rect = pygame.Rect(10, 10, 100, 30)
        pygame.draw.rect(self.screen, GREEN, restart_rect)
        pygame.draw.rect(self.screen, BLACK, restart_rect, 1)
        font = pygame.font.SysFont('Arial', 16)
        restart_text = font.render("Restart Game", True, BLACK)
        self.screen.blit(restart_text, (restart_rect.x + 10, restart_rect.y + 7))
        self.ui.restart_button = restart_rect
        
        # Draw world
        world_surface = pygame.Surface((SCREEN_WIDTH - UI_PANEL_WIDTH, SCREEN_HEIGHT))
        world_surface.fill(BLACK)
        
        # Get zoom level from camera
        camera_offset = self.camera.get_offset()
        zoom_level = self.camera.zoom_level
        
        # Create a temporary surface at the zoomed size
        zoom_width = int((SCREEN_WIDTH - UI_PANEL_WIDTH) / zoom_level)
        zoom_height = int(SCREEN_HEIGHT / zoom_level)
        
        # Draw world onto the temporary surface
        temp_surface = pygame.Surface((zoom_width, zoom_height))
        temp_surface.fill(BLACK)
        self.world.draw(temp_surface, (camera_offset[0], camera_offset[1]))
        
        # Scale the temporary surface to apply zoom
        if zoom_level != 1.0:
            scaled_surface = pygame.transform.scale(
                temp_surface, 
                (int(zoom_width * zoom_level), int(zoom_height * zoom_level))
            )
            world_surface.blit(scaled_surface, (0, 0))
        else:
            world_surface.blit(temp_surface, (0, 0))
            
        # Blit world surface to screen
        self.screen.blit(world_surface, (0, 0))
        
        # Draw UI
        self.ui.draw(self.screen, self.player, self.market)
        
        # Draw logger messages
        if DEBUG_LOGGER:
            self.logger.draw(self.screen, 10, SCREEN_HEIGHT - 200, pygame.font.SysFont('Arial', 14))
        
        # Draw game over message if applicable
        if self.game_over:
            # Draw semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # Black with 70% opacity
            self.screen.blit(overlay, (0, 0))
            
            # Draw win message
            font_large = pygame.font.SysFont('Arial', 48)
            text_win = font_large.render("You Win!", True, GREEN)
            text_rect_win = text_win.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
            self.screen.blit(text_win, text_rect_win)
              # Draw stats
            font_stats = pygame.font.SysFont('Arial', 24)
            stats_list = self.stats.get_stats_display()
            for i, stat_text in enumerate(stats_list):
                # Highlight new personal best with gold color
                text_color = WHITE
                if "New Record" in stat_text:
                    text_color = (255, 215, 0)  # Gold color for new record
                
                text_surface = font_stats.render(stat_text, True, text_color)
                text_rect = text_surface.get_rect(
                    center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4 + 80 + i * 40)
                )
                self.screen.blit(text_surface, text_rect)
            # Draw restart button
            restart_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 120, 200, 40)
            pygame.draw.rect(self.screen, GREEN, restart_rect)
            pygame.draw.rect(self.screen, BLACK, restart_rect, 1)
            font_restart = pygame.font.SysFont('Arial', 20)
            restart_text = font_restart.render("Restart Game", True, BLACK)
            restart_text_rect = restart_text.get_rect(center=restart_rect.center)
            self.screen.blit(restart_text, restart_text_rect)
            self.ui.restart_button = restart_rect
            
            # Draw quit instruction
            text_quit = font_restart.render("Press ESC to quit", True, WHITE)
            text_rect_quit = text_quit.get_rect(
                center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 60)
            )
            self.screen.blit(text_quit, text_rect_quit)
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            
            self.handle_events()
            self.update(dt)
            self.draw()
            
            # Handle game restart if settings were changed
            if self.restart_game:
                self.restart_game = False
                self.logger.log('GAME', 'RESTART', "Restarting game...")
                
                # Save the current screen
                screen = self.screen
                
                # Show configuration screen
                from configuration import ConfigurationScreen
                config_screen = ConfigurationScreen(screen)
                if config_screen.run():
                    # Re-initialize the game with new settings
                    self.__init__(screen)
                    
                    # Log the new settings
                    from config import WORLD_SIZE, NUM_AI_PLAYERS, RESOURCE_DISTRIBUTION
                    world_size = f"{WORLD_SIZE['width']}x{WORLD_SIZE['height']}"
                    self.logger.log('GAME', 'SETTINGS', f"World Size: {world_size}")
                    self.logger.log('GAME', 'SETTINGS', f"AI Players: {NUM_AI_PLAYERS}")
                else:
                    # User quit during configuration
                    self.running = False
        
        # Save session data if the game is over
        if hasattr(self, 'session_saver') and self.game_over:
            self.session_saver.save_session()
            
        pygame.quit()
        sys.exit()
