# AI DJ Prototype

A simple AI assistant that uses a local LLM (Large Language Model) through LM Studio to answer questions and provide information.

## Features

- Uses a local LLM through LM Studio
- Provides current time information
- Answers general knowledge questions
- Simple Gradio web interface

## Setup

1. Install the required packages:
```bash
python -m venv venv
source venv/bin/activate
pip install gradio langchain langchain-community openai
```

2. Make sure LM Studio is running with a model loaded (e.g., openhermes-2.5-mistral-7b)

3. Run the application:
```bash
python a
```

4. Access the web interface at http://127.0.0.1:7860

## Usage

- Type any question in the text box
- For direct LLM queries, use the format: "Ask Local LLM: your question here"
- The application will automatically detect time-related queries

## Technologies Used

- LM Studio for local LLM hosting
- LangChain for agent and tool integration
- Gradio for the web interface