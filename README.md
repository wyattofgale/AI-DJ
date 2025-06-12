# MP3 Search & Playlist Lister

A simple application that allows you to search for MP3 files on your Desktop and create virtual playlists using a local LLM through LM Studio.

## Features

- Search for MP3 files using natural language queries
- Display BPM and genre information from ID3 tags
- Create virtual playlists from search results
- Uses a local LLM through LM Studio
- User-friendly Gradio interface

## Project Structure

The project has been refactored into a modular structure:

- `main.py`: Entry point for the application
- `tools.py`: Contains the MP3 search functionality
- `agent.py`: Sets up the LangChain agent and LLM
- `ui.py`: Implements the Gradio user interface
- `requirements.txt`: Lists all dependencies

## Setup

1. Install the required packages:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Make sure LM Studio is running with a model loaded (e.g., openhermes-2.5-mistral-7b)

3. Run the application:
```bash
python main.py
```

4. Access the web interface at http://127.0.0.1:7860

## Usage

Enter search queries in the text box, such as:
- "Find songs by Ariana Grande"
- "search: jazz | playlist: My Jazz Collection"
- "Electronic music with high BPM"

The application will search for matching MP3 files on your Desktop and display them as a playlist.

## Technologies Used

- LM Studio for local LLM hosting
- LangChain for agent and tool integration
- Mutagen for MP3 metadata extraction
- Gradio for the web interface