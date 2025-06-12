"""
MP3 Search & Playlist Lister - Main Application

This is the main entry point for the MP3 Search & Playlist Lister application.
It imports components from the modular structure and launches the Gradio UI.
"""

from ui import create_ui

if __name__ == "__main__":
    ui = create_ui()
    ui.launch()