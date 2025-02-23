# IPB Chatbot

An AI-powered chatbot system designed for the university website using Python and OpenAI models. The system includes a user-friendly chatbot interface with a Flask-based back-office for data management and real-time analytics.

## Features
- AI-driven chatbot using OpenAI models and LangChain  
- Streamlit-based UI for seamless interaction  
- Flask-powered back-office for chatbot management  
- MongoDB for data storage and analytics  
- Real-time performance monitoring with Chart.js  

## Installation

Ensure you have Python installed on your system. Then clone this repository:
```bash
git clone [repository-link]
cd [repository-directory]
```
Install the required packages:
```bash
pip install -r requirements.txt
```
Create your own .env file with the following variables:
```bash
OPENAI_API_KEY=your_openai_api_key
LANGCHAIN_ENDPOINT=your_langchain_endpoint
LANGCHAIN_API_KEY=your_langchain_api_key
LANGCHAIN_PROJECT=your_langchain_project
LANGCHAIN_TRACING_V2=true
PINECONE_API_KEY=your_pinecone_api_key
MONGO_URI=your_mongo_database_uri
```

## Usage

To run the Chatbot:
```bash
cd [repository-directory]\chatbot
streamlit run app.py
```
To run the backoffice:
```bash
cd [repository-directory]\chatbot\backoffice
flask run
```
