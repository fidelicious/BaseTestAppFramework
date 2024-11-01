"""
-------------------------------------------------------------------------------
                                Fidelicious
File:       main.py
Purpose:    Main entry point of GUI Application for CDG Automation TestApp

Creator:    Fidel Quezada Guzman
Cr. Date:   10/30/2024
-------------------------------------------------------------------------------
"""
from ui import AutoTestApp

if __name__ == "__main__":          # Python construct to ensure script run directly (not imported as module)
    app = AutoTestApp()             # Create instance of main class from ui.py
    app.run()                       # Call method that starts Tkinter main loop
