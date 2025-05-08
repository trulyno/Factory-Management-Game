import time

class GameStats:
    """Class to track game statistics"""
    def __init__(self):
        # Initialize all stats
        self.tiles_owned = 0
        self.total_money_generated = 0
        self.total_money_spent = 0
        self.num_buildings = 0
        self.start_time = time.time()
        self.time_played = 0
        self.timer_stopped = False
    
    def update_time_played(self):
        """Update the time played stat"""
        if not self.timer_stopped:
            self.time_played = time.time() - self.start_time
    
    def stop_timer(self):
        """Stop the timer and record final time played"""
        if not self.timer_stopped:
            self.time_played = time.time() - self.start_time
            self.timer_stopped = True
    
    def format_time(self, seconds):
        """Format seconds into hours, minutes, seconds"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_stats_display(self):
        """Get formatted stats for display"""
        if not self.timer_stopped:
            self.update_time_played()
        return [
            f"Tiles Owned: {self.tiles_owned}",
            f"Total Money Generated: ${self.total_money_generated:,.2f}",
            f"Total Money Spent: ${self.total_money_spent:,.2f}",
            f"Number of Buildings: {self.num_buildings}",
            f"Time Played: {self.format_time(self.time_played)}"
        ]