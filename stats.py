import time
import os

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
        self.tiles_surveyed = 0
        self.personal_best_time = self.load_personal_best_time()
    
    def update_time_played(self):
        """Update the time played stat"""
        if not self.timer_stopped:
            self.time_played = time.time() - self.start_time
    
    def stop_timer(self):
        """Stop the timer and record final time played"""
        if not self.timer_stopped:
            self.time_played = time.time() - self.start_time
            self.timer_stopped = True
            # Check if this is a new personal best
            if self.is_personal_best():
                self.personal_best_time = self.time_played
    
    def format_time(self, seconds):
        """Format seconds into hours, minutes, seconds"""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_stats_display(self):
        """Get formatted stats for display"""
        if not self.timer_stopped:
            self.update_time_played()
            
        stats_list = [
            f"Tiles Owned: {self.tiles_owned}",
            f"Total Money Generated: ${self.total_money_generated:,.2f}",
            f"Total Money Spent: ${self.total_money_spent:,.2f}",
            f"Number of Buildings: {self.num_buildings}",
            f"Time Played: {self.format_time(self.time_played)}"
        ]
        
        # Add personal best time if available
        if self.personal_best_time:
            pb_display = f"Personal Best Time: {self.format_time(self.personal_best_time)}"
            if self.is_personal_best() and self.timer_stopped:
                pb_display += " (New Record!)"
            stats_list.append(pb_display)
            
        return stats_list
    
    def load_personal_best_time(self):
        """Load personal best time from previous sessions"""
        best_time = float('inf')  # Initialize with infinity
        found_time = False
        
        # Check all session directories for player_stats.txt files
        if os.path.exists("sessions"):
            for session_dir in os.listdir("sessions"):
                stats_path = os.path.join("sessions", session_dir, "player_stats.txt")
                if os.path.exists(stats_path):
                    try:
                        with open(stats_path, 'r') as statsfile:
                            for line in statsfile:
                                if "Time Played:" in line:
                                    # Extract time in format HH:MM:SS
                                    time_str = line.split("Time Played:")[1].strip()
                                    h, m, s = map(int, time_str.split(':'))
                                    seconds = h * 3600 + m * 60 + s
                                    
                                    if seconds < best_time:
                                        best_time = seconds
                                        found_time = True
                    except Exception:
                        # Skip files that can't be read properly
                        pass
        
        return best_time if found_time else None
    
    def is_personal_best(self):
        """Check if current time is a new personal best"""
        # Only count it as a personal best if the timer was stopped (game completed)
        if not self.timer_stopped:
            return False
            
        if self.personal_best_time is None:
            return True
        return self.time_played < self.personal_best_time