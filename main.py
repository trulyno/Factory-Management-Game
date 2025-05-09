import pygame
from game import Game
from configuration import ConfigurationScreen
from config import SCREEN_WIDTH, SCREEN_HEIGHT

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Factory Management Game")
      # Show configuration screen first
    config_screen = ConfigurationScreen(screen)
    if config_screen.run():
        # Start the game with the configured settings
        game = Game(screen)
        game.run()
    else:
        # User quit from configuration screen
        pygame.quit()

if __name__ == "__main__":
    main()
