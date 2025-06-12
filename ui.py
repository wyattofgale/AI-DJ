import gradio as gr
from tools import search_mp3_files
from agent import create_llm, create_agent, create_fallback_agent

# Create the LLM and agent
llm = create_llm()
agent = create_agent(llm)

# Function to handle chat with agent and streaming
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
                simple_agent = create_fallback_agent(llm)
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

# Create the Gradio interface
def create_ui():
    return gr.Interface(
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