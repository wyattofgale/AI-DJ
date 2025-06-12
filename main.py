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

# === Tool 1: Get local time ===
def get_local_time():
    return datetime.now().strftime("🕒 %I:%M %p on %A, %B %d, %Y")

time_tool = Tool(
    name="Local Time Tool",
    func=lambda _: get_local_time(),
    description="Use this to find out the current local time. Useful for time-based recommendations or scheduling."
)

# === Tool 2: Music Knowledge Base ===
def music_knowledge(query: str) -> str:
    """Access music knowledge to answer questions about genres, artists, music theory, etc."""
    enhanced_query = f"""As a music expert, please answer this question about music: {query}
    
    Focus on providing accurate, detailed information about:
    - Music genres, history, and characteristics
    - Artists, bands, and their discographies
    - Music theory concepts
    - Instrument information
    - Music production techniques
    - DJ techniques and knowledge
    
    Be comprehensive but concise.
    """
    
    local_llm = ChatOpenAI(
        model="openhermes-2.5-mistral-7b",
        temperature=0.2,  # Slight randomness for more creative responses
    )
    response = local_llm([HumanMessage(content=enhanced_query)])
    return response.content

music_tool = Tool(
    name="Music Knowledge",
    func=music_knowledge,
    description="Use this to answer questions about music genres, artists, music theory, instruments, production, and DJ techniques."
)

# === Tool 3: Creative Assistant ===
def creative_assistant(request: str) -> str:
    """Generate creative content like playlist themes, song descriptions, or music recommendations."""
    enhanced_request = f"""As a creative DJ assistant, please help with this request: {request}
    
    If it's about:
    - Creating a playlist: Suggest 5-7 specific tracks with artists that would work well together
    - Music recommendations: Provide specific song and artist suggestions based on the request
    - Describing music: Use vivid, sensory language to describe the sound, mood, and feel
    - Writing content: Create engaging, music-focused content as requested
    
    Be specific, creative, and knowledgeable about music.
    """
    
    local_llm = ChatOpenAI(
        model="openhermes-2.5-mistral-7b",
        temperature=0.7,  # Higher temperature for more creative responses
    )
    response = local_llm([HumanMessage(content=enhanced_request)])
    return response.content

creative_tool = Tool(
    name="Creative Assistant",
    func=creative_assistant,
    description="Use this for creative tasks like generating playlist ideas, music recommendations, describing music, or creating music-related content."
)

# === Tool 4: General Knowledge ===
def general_knowledge(question: str) -> str:
    """Answer general knowledge questions not specifically about music."""
    local_llm = ChatOpenAI(
        model="openhermes-2.5-mistral-7b",
        temperature=0.1,  # Low temperature for factual responses
    )
    response = local_llm([HumanMessage(content=question)])
    return response.content

knowledge_tool = Tool(
    name="General Knowledge",
    func=general_knowledge,
    description="Use this for general questions not specifically about music. Only use when other tools don't apply."
)

# === Tool 5: MP3 File Search and Playlist Creation ===
def search_mp3_files(query: str) -> str:
    """
    Search for MP3 files in the music directory and create playlists based on search criteria.
    Extracts and displays BPM and genre information from ID3 tags when available.
    
    Args:
        query: A string containing search terms and optional commands.
              Format: "search: [search terms] | playlist: [playlist name]"
              Example: "search: rock 80s | playlist: Classic Rock Hits"
    
    Returns:
        A formatted string with search results and/or playlist creation confirmation.
    """
    # Define the music directory - this should be updated to the actual music directory path
    music_dir = os.path.expanduser("~/Music")
    
    # Parse the query
    search_terms = ""
    playlist_name = f"Playlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if "|" in query:
        parts = query.split("|")
        for part in parts:
            part = part.strip()
            if part.lower().startswith("search:"):
                search_terms = part[7:].strip()
            elif part.lower().startswith("playlist:"):
                playlist_name = part[9:].strip()
    else:
        # If no pipe separator, treat the whole query as search terms
        search_terms = query.strip()
    
    # Check if the music directory exists
    if not os.path.exists(music_dir):
        return f"❌ Music directory not found at {music_dir}. Please check the path or create the directory."
    
    # Perform the search
    search_pattern = f"*{search_terms.replace(' ', '*')}*.mp3"
    mp3_files = glob.glob(os.path.join(music_dir, "**", search_pattern), recursive=True)
    
    # Limit to 20 files for reasonable output
    mp3_files = mp3_files[:20]
    
    # Create response
    if mp3_files:
        response = f"🔍 Found {len(mp3_files)} MP3 files matching '{search_terms}':\n\n"
        
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
        
        # Create a playlist file (M3U format)
        playlist_path = os.path.join(music_dir, f"{playlist_name}.m3u")
        try:
            with open(playlist_path, 'w', encoding='utf-8') as playlist_file:
                playlist_file.write("#EXTM3U\n")
                for file_path in mp3_files:
                    playlist_file.write(f"{file_path}\n")
            response += f"\n✅ Created playlist '{playlist_name}.m3u' with {len(mp3_files)} tracks."
        except Exception as e:
            response += f"\n❌ Failed to create playlist file: {str(e)}"
    else:
        response = f"❌ No MP3 files found matching '{search_terms}'.\n"
        response += "Try different search terms or check if the music directory contains MP3 files."
    
    return response

mp3_search_tool = Tool(
    name="MP3 Search and Playlist Creator",
    func=search_mp3_files,
    description="Search for MP3 files and create playlists. Use this when the user wants to find music files or create a playlist. Shows BPM and genre information. Input format: 'search: [search terms] | playlist: [playlist name]'. Example: 'search: jazz piano | playlist: Jazz Collection'"
)

# === Main LLM with Streaming ===
llm = ChatOpenAI(
    model="openhermes-2.5-mistral-7b",  # This will be the model loaded in LM Studio
    temperature=0,
    streaming=True
)

# Define a custom prompt template for the agent
from langchain.prompts import PromptTemplate

# Custom prompt template with better instructions
agent_prompt = PromptTemplate.from_template("""You are an intelligent AI DJ assistant that helps users with music-related questions and tasks.
You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: """)

# === Agent with tools ===
agent = initialize_agent(
    tools=[music_tool, creative_tool, mp3_search_tool, time_tool, knowledge_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True,
    max_iterations=5,  # Increased from 3 to 5 to allow more complex reasoning
    early_stopping_method="generate",  # Force generation of a final answer
    return_intermediate_steps=True,  # Return intermediate steps for better error handling
    agent_kwargs={
        "prefix": agent_prompt.template
    }
)

# === Gradio UI ===
def chat_with_agent_stream(message):
    try:
        # If the message starts with "Ask Local LLM:", bypass the agent and use the LLM directly
        if message.lower().startswith("ask local llm:"):
            query = message[len("Ask Local LLM:"):].strip()
            yield f"Asking the local LLM: {query}\n\n"
            
            # Use streaming for direct LLM queries too
            local_llm_stream = ChatOpenAI(
                model="openhermes-2.5-mistral-7b",
                temperature=0,
                streaming=True
            )
            
            response_text = ""
            for chunk in local_llm_stream.stream([HumanMessage(content=query)]):
                if chunk.content:
                    response_text += chunk.content
                    yield f"Asking the local LLM: {query}\n\n{response_text}\n\n[Tools used: Direct LLM]"
            return
        
        # Otherwise, use the agent with streaming
        full_response = ""
        current_output = ""
        last_observation = ""
        in_final_answer = False
        thinking_shown = False
        tools_used = []  # Track which tools were used
        current_tool = None  # Track the current tool being used
        
        try:
            for chunk in agent.stream(message):
                # Accumulate the full response
                full_response += chunk
                
                # Extract tool information from the response
                if "Action:" in full_response and "Action Input:" in full_response:
                    action_parts = full_response.split("Action:")
                    for part in action_parts[1:]:  # Skip the first part before any Action:
                        if "Action Input:" in part:
                            tool_part = part.split("Action Input:")[0].strip()
                            if tool_part and tool_part not in tools_used:
                                tools_used.append(tool_part)
                
                # Check if we're in the final answer section
                if "Final Answer:" in full_response and not in_final_answer:
                    in_final_answer = True
                    parts = full_response.split("Final Answer:")
                    current_output = parts[1].strip()
                    
                    # Add the tools used information to the response
                    if tools_used:
                        tools_info = "\n\n[Tools used: " + ", ".join(tools_used) + "]"
                        current_output += tools_info
                    
                    yield current_output
                elif in_final_answer:
                    # Continue streaming the final answer
                    current_output += chunk
                    yield current_output
                else:
                    # Track the last observation as a fallback
                    if "Observation:" in full_response:
                        parts = full_response.split("Observation:")
                        if len(parts) > 1:
                            last_observation = parts[-1].split("Thought:")[0].strip() if "Thought:" in parts[-1] else parts[-1].strip()
                            # Show "Thinking..." while the agent is working
                            if not thinking_shown:
                                yield f"Thinking... 🤔"
                                thinking_shown = True
        except Exception as agent_error:
            # If there's an error during streaming, show it and continue with fallback
            yield f"Agent error: {agent_error}\n\nTrying alternative approach..."
            # We'll continue to the fallback mechanisms below
        
        # If we never got a final answer but have an observation, return that
        if not in_final_answer:
            if last_observation:
                yield f"Result: {last_observation}"
                if tools_used:
                    yield f"\n\n[Tools used: {', '.join(tools_used)}]"
            else:
                # Direct query to the LLM as a last resort
                yield "Let me answer that directly..."
                response_text = ""
                local_llm_stream = ChatOpenAI(
                    model="openhermes-2.5-mistral-7b",
                    temperature=0,
                    streaming=True
                )
                
                for chunk in local_llm_stream.stream([HumanMessage(content=message)]):
                    if chunk.content:
                        response_text += chunk.content
                        yield f"Let me answer that directly...\n\n{response_text}\n\n[Tools used: Direct LLM]"
    except Exception as e:
        error_message = str(e)
        yield f"⚠️ Error: {error_message}"
        
        # If it's a parsing error, fall back to direct LLM response
        if "Could not parse LLM output" in error_message:
            yield "\n\nFalling back to direct response...\n"
            try:
                # Use the LLM directly without the agent framework
                direct_llm = ChatOpenAI(
                    model="openhermes-2.5-mistral-7b",
                    temperature=0,
                    streaming=True
                )
                
                response_text = ""
                for chunk in direct_llm.stream([HumanMessage(content=message)]):
                    if chunk.content:
                        response_text += chunk.content
                        yield f"\n\nFalling back to direct response...\n\n{response_text}\n\n[Tools used: Direct LLM]"
            except Exception as fallback_error:
                yield f"\n\nEven fallback failed: {fallback_error}"

ui = gr.Interface(
    fn=chat_with_agent_stream,
    inputs=gr.Textbox(
        lines=2, 
        placeholder="Ask about music, request playlists, or get DJ advice..."
    ),
    outputs=gr.Textbox(lines=12),
    title="🎧 AI DJ Assistant 🎵",
    description="""
    Your intelligent music companion! Ask me about:
    • Music genres, artists, and theory
    • Creating themed playlists
    • DJ techniques and advice
    • Music recommendations based on mood, genre, or occasion
    • Search your MP3 collection with BPM and genre info (e.g., "Find jazz MP3s and create a playlist called Jazz Favorites")
    """,
    theme=gr.themes.Soft(),
    allow_flagging="never"
)

if __name__ == "__main__":
    ui.launch()