import os
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from tools import mp3_search_tool

# Configure for LM Studio (local model)
# LM Studio typically runs on http://localhost:1234/v1 by default
os.environ["OPENAI_API_KEY"] = "lm-studio"  # Dummy key, not actually used by LM Studio
os.environ["OPENAI_API_BASE"] = "http://localhost:1234/v1"  # LM Studio local endpoint

# Initialize the LLM with streaming
def create_llm():
    return ChatOpenAI(
        model="openhermes-2.5-mistral-7b",  # This will be the model loaded in LM Studio
        temperature=0,
        streaming=True
    )

# Create the agent with tools
def create_agent(llm):
    return initialize_agent(
        tools=[mp3_search_tool],  # Only using the MP3 search tool
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True,
        verbose=True,
        max_iterations=5,  # Increased from 3 to 5 to allow more complex reasoning
        early_stopping_method="generate",  # Force generation of a final answer
        return_intermediate_steps=True  # Return intermediate steps for better error handling
    )

# Create a simpler fallback agent
def create_fallback_agent(llm):
    return initialize_agent(
        tools=[mp3_search_tool],
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True,
        verbose=False
    )