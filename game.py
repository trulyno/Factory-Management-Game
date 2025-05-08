import pygame
import sys
from config import *
from world import World
from player import Player
from economy import Market
from ai import AIFactory
from ui import UI

class Camera:
    def __init__(self, width, height, world_width, world_height):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.world_width = world_width * TILE_SIZE
        self.world_height = world_height * TILE_SIZE
        
    def move(self, dx, dy):
        """Move camera by an amount, keeping within world bounds"""
        self.x = max(0, min(self.world_width - self.width, self.x + dx))
        self.y = max(0, min(self.world_height - self.height, self.y + dy))
        
    def get_offset(self):
        """Get camera offset for rendering"""
        return (self.x, self.y)
        
    def screen_to_world(self, screen_pos):
        """Convert screen position to world position"""
        world_x = screen_pos[0] + self.x
        world_y = screen_pos[1] + self.y
        tile_x = world_x // TILE_SIZE
        tile_y = world_y // TILE_SIZE
        return (tile_x, tile_y)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Factory Management Game")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game objects
        self.world = World(GRID_WIDTH, GRID_HEIGHT)
        self.player = Player()
        self.market = Market()
        
        # Set up player starting area
        self.world.setup_player_start(self.player)
        
        # Set up AI factories
        self.ai_factories = []
        self.world.setup_ai_factories(2)
        for i in range(2):
            self.ai_factories.append(AIFactory(i, self.world))
        
        # Camera and UI
        self.camera = Camera(SCREEN_WIDTH - UI_PANEL_WIDTH, SCREEN_HEIGHT, GRID_WIDTH, GRID_HEIGHT)
        self.ui = UI(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Game state
        self.game_over = False
        self.time_since_update = 0
        
    def handle_events(self):
        """Process game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
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
                # Handle UI clicks
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
    
    def update(self, dt):
        """Update game state"""
        if self.game_over:
            return
            
        # Update market prices periodically
        self.time_since_update += dt
        if self.time_since_update >= 1.0:  # Every second
            self.time_since_update = 0
            self.market.update_prices()
            
            # Update AI factories
            for ai in self.ai_factories:
                ai.update()
            
            # Check win condition
            if self.player.money >= WIN_CONDITION:
                self.game_over = True
                print("You win! You've reached the goal of $1,000,000!")
    
    def draw(self):
        """Render the game"""
        # Clear screen
        self.screen.fill(BLACK)
        
        # Draw world
        world_surface = pygame.Surface((SCREEN_WIDTH - UI_PANEL_WIDTH, SCREEN_HEIGHT))
        world_surface.fill(BLACK)
        self.world.draw(world_surface, self.camera.get_offset())
        self.screen.blit(world_surface, (0, 0))
        
        # Draw UI
        self.ui.draw(self.screen, self.player, self.market)
        
        # Draw game over message if applicable
        if self.game_over:
            font = pygame.font.SysFont('Arial', 48)
            text = font.render("You Win!", True, GREEN)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(text, text_rect)
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        sys.exit()
