import os
import gradio as gr
import glob
import random
from pathlib import Path
from datetime import datetime
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.schema import HumanMessage
from langchain.tools import Tool
import mutagen
from mutagen.id3 import ID3

# Configure for LM Studio (local model)
# LM Studio typically runs on http://localhost:1234/v1 by default
os.environ["OPENAI_API_KEY"] = "lm-studio"  # Dummy key, not actually used by LM Studio
os.environ["OPENAI_API_BASE"] = "http://localhost:1234/v1"  # LM Studio local endpoint

# === MP3 Search and Playlist Lister Tool ===
# This is the only tool we're keeping

# === MP3 File Search and Playlist Listing ===
def search_mp3_files(query: str) -> str:
    """
    Search for MP3 files in the Desktop folder and list them as a playlist in the response.
    Extracts and displays BPM and genre information from ID3 tags when available.
    
    Args:
        query: A string containing search terms and optional commands.
              Format can be flexible:
              - "search: [search terms] | playlist: [playlist name]"
              - "[search terms] | playlist: [playlist name]"
              - Just plain search terms like "Ariana Grande god is a woman"
              
              The search uses loose matching - files will match if they contain any of the
              search words in their filename. Results are sorted by relevance (number of
              matching words).
    
    Returns:
        A formatted string with search results displayed as a playlist.
    """
    # Define the search directory as the Desktop folder
    music_dir = os.path.expanduser("~/Desktop")
    
    # Parse the query
    search_terms = ""
    playlist_name = f"Playlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Clean up the query - remove any tool name prefix if present
    if "MP3Search(" in query and ")" in query:
        # Extract content between parentheses
        start_idx = query.find("(") + 1
        end_idx = query.rfind(")")
        if start_idx > 0 and end_idx > start_idx:
            query = query[start_idx:end_idx].strip("'\"")
    
    # Handle different query formats
    if "|" in query:
        parts = query.split("|")
        for part in parts:
            part = part.strip()
            if part.lower().startswith("search:"):
                search_terms = part[7:].strip()
            elif part.lower().startswith("playlist:"):
                playlist_name = part[9:].strip()
            elif "playlist:" not in query and "search:" not in part:
                # If this part doesn't have a prefix but we haven't found search terms yet
                if not search_terms:
                    search_terms = part
    else:
        # If no pipe separator, treat the whole query as search terms
        search_terms = query.strip()
        
    # If search terms still have "search:" prefix, remove it
    if search_terms.lower().startswith("search:"):
        search_terms = search_terms[7:].strip()
    
    # Check if the Desktop directory exists
    if not os.path.exists(music_dir):
        return f"❌ Desktop directory not found at {music_dir}. Please check the path or create the directory."
    
    # First, get all MP3 files
    all_mp3_files = glob.glob(os.path.join(music_dir, "**", "*.mp3"), recursive=True)
    
    # If no search terms provided, return all MP3 files (limited to 20)
    if not search_terms:
        mp3_files = all_mp3_files[:20]
    else:
        # For loose matching, split search terms into individual words
        search_words = [word.lower() for word in search_terms.split() if word]
        
        # Filter files that match any of the search words
        mp3_files = []
        for file_path in all_mp3_files:
            file_name = os.path.basename(file_path).lower()
            # Check if any search word is in the filename
            if any(word in file_name for word in search_words):
                mp3_files.append(file_path)
                
        # Sort results by relevance (number of matching words)
        def relevance_score(file_path):
            file_name = os.path.basename(file_path).lower()
            # Count how many search words appear in the filename
            return sum(1 for word in search_words if word in file_name)
        
        mp3_files.sort(key=relevance_score, reverse=True)
    
    # Limit to 20 files for reasonable output
    mp3_files = mp3_files[:20]
    
    # Create response
    if mp3_files:
        if search_terms:
            response = f"🔍 Found {len(mp3_files)} MP3 files matching '{search_terms}':\n\n"
        else:
            response = f"🔍 Found {len(mp3_files)} MP3 files:\n\n"
        
        for i, file_path in enumerate(mp3_files, 1):
            file_name = os.path.basename(file_path)
            
            # Extract BPM and genre from ID3 tags if available
            bpm = "Unknown"
            genre = "Unknown"
            
            try:
                audio = ID3(file_path)
                
                # Try to get BPM
                if "TBPM" in audio:
                    bpm = audio["TBPM"].text[0]
                
                # Try to get genre
                if "TCON" in audio:
                    genre = audio["TCON"].text[0]
                
            except Exception:
                # If ID3 tag reading fails, continue without metadata
                pass
            
            response += f"{i}. {file_name}\n   BPM: {bpm} | Genre: {genre}\n"
        
        # Add a playlist-like listing to the response instead of creating a file
        response += f"\n📋 Playlist: {playlist_name} ({len(mp3_files)} tracks)\n"
        response += "----------------------------------------\n"
        for i, file_path in enumerate(mp3_files, 1):
            file_name = os.path.basename(file_path)
            response += f"{i}. {file_name}\n"
        response += "----------------------------------------"
    else:
        response = f"❌ No MP3 files found matching '{search_terms}'.\n"
        response += "Try different search terms or check if the Desktop folder contains MP3 files."
    
    return response

mp3_search_tool = Tool(
    name="MP3Search",
    func=search_mp3_files,
    description="""Search for MP3 files on the Desktop folder and list them as a playlist in the response. Use this when the user wants to find music files. 
Shows BPM and genre information. The tool accepts flexible input formats:
1. Simple search terms: 'Ariana Grande god is a woman'
2. Formatted search: 'search: Ariana Grande | playlist: My Playlist'
3. Just search with playlist: 'Ariana Grande | playlist: My Playlist'

The search uses loose matching - files will match if they contain any of the search words in their filename. Results are sorted by relevance (number of matching words). The playlist name is used for display purposes only and no physical playlist file is created."""
)

# === Main LLM with Streaming ===
llm = ChatOpenAI(
    model="openhermes-2.5-mistral-7b",  # This will be the model loaded in LM Studio
    temperature=0,
    streaming=True
)

# Using the default agent prompt template

# === Agent with tools ===
agent = initialize_agent(
    tools=[mp3_search_tool],  # Only using the MP3 search tool
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True,
    max_iterations=5,  # Increased from 3 to 5 to allow more complex reasoning
    early_stopping_method="generate",  # Force generation of a final answer
    return_intermediate_steps=True  # Return intermediate steps for better error handling
)

# === Gradio UI ===
def chat_with_agent_stream(message):
    try:
        # Try to directly use the MP3Search tool if the message looks like a search query
        if any(term in message.lower() for term in ["find", "search", "song", "music", "mp3", "playlist"]):
            try:
                # Direct tool call for simple queries
                result = search_mp3_files(message)
                yield result + "\n\n[Tools used: MP3Search]"
                return
            except Exception:
                # If direct call fails, continue with the agent approach
                pass
        
        # Use the agent without streaming first to get the complete response
        result = agent(message)
        
        # Extract the final answer from the result
        final_answer = result["output"]
        
        # Extract tools used from intermediate steps
        tools_used = []
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if step[0].tool not in tools_used:
                    tools_used.append(step[0].tool)
        
        # Format the response
        response = final_answer
        if tools_used:
            response += f"\n\n[Tools used: {', '.join(tools_used)}]"
        
        yield response
    except Exception as e:
        error_message = str(e)
        
        # Try a simpler approach if the agent fails
        try:
            # First, try direct tool call as a fallback
            result = search_mp3_files(message)
            yield result + "\n\n[Tools used: MP3Search (direct call)]"
        except Exception:
            try:
                # Use the agent without streaming and with more robust error handling
                simple_agent = initialize_agent(
                    tools=[mp3_search_tool],  # Only using the MP3 search tool
                    llm=llm,
                    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                    handle_parsing_errors=True,  # Add this to handle parsing errors
                    verbose=False
                )
                result = simple_agent(message)
                yield f"{result['output']}\n\n[Tools used: MP3Search (fallback agent)]"
            except Exception as fallback_error:
                # If all else fails, just search with the message as is
                try:
                    # Last resort: just use the message as search terms
                    result = search_mp3_files(message)
                    yield result + "\n\n[Tools used: MP3Search (direct search)]"
                except Exception:
                    yield f"⚠️ Sorry, I couldn't process your request. Please try a simpler search query like 'Ariana Grande' or 'jazz'."

ui = gr.Interface(
    fn=chat_with_agent_stream,
    inputs=gr.Textbox(
        lines=2, 
        placeholder="Enter your search query"
    ),
    outputs=gr.Textbox(lines=12),
    title="🎧 MP3 Search & Playlist Lister 🎵",
    theme=gr.themes.Soft(),
    allow_flagging="never"
)

if __name__ == "__main__":
    ui.launch()