import os
import streamlit as st
from streamlit_feedback import streamlit_feedback
from langchain_core.messages import AIMessage, HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import DirectoryLoader
from langchain.storage import LocalFileStore
from langchain.embeddings import CacheBackedEmbeddings
from langchain_pinecone import PineconeVectorStore
import asyncio
import time
import tiktoken
import re
import uuid
from langsmith import Client
import logging
from langchain.callbacks import collect_runs 
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import CharacterTextSplitter
from typing import List, Tuple
from langchain.schema import Document
from fuzzywuzzy import fuzz
import unicodedata
from pymongo import MongoClient
from datetime import datetime
from dict import abbreviation_dict, course_options, replace_abbreviations
from ambiguity import check_for_ambiguity
from stats import calculate_cost, save_chat_statistics, calculate_tokens, update_feedback

load_dotenv()


LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

client = Client(
    api_url=LANGCHAIN_ENDPOINT,
    api_key=LANGCHAIN_API_KEY,
)

# Define Pinecone index name
INDEX_NAME = "teste2"


fs = LocalFileStore("./cache/")

directory_to_load = r"./mdfiles"

@st.cache_data(show_spinner=False)
def load_documents(directory_to_load):
    loader = DirectoryLoader(directory_to_load)
    loaded_docs = loader.load()
    print(f"Number of documents loaded: {len(loaded_docs)}")
    return loaded_docs

loaded_docs = load_documents(directory_to_load)


#Embeddings
def get_vectorstore_from_docs(loaded_docs):
    embedding = OpenAIEmbeddings(model="text-embedding-3-small")
    cached_embedder = CacheBackedEmbeddings.from_bytes_store(embedding, fs, namespace="openai")
    splitter_text = RecursiveCharacterTextSplitter(separators="#####", chunk_size=2000, chunk_overlap=400)
    
    for doc in loaded_docs:
     print(f"Original document length: {len(doc.page_content)}")   

    documents = splitter_text.split_documents(loaded_docs)
     
    for doc in documents:
     print(f"Chunked document length: {len(doc.page_content)}")

    print(f"Number of documents after splitting: {len(documents)}")
    
    vector_store = PineconeVectorStore.from_documents(documents, embedding=cached_embedder, index_name=INDEX_NAME)
    return vector_store


# Prompt de pesquisa
def get_context_retriever_chain(vector_store):
    llm = ChatOpenAI(model="gpt-4o-mini")
    retriever = vector_store.as_retriever(search_kwargs={"k": 10})   
    prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        ("user", """Dada a conversa acima, gere uma consulta de pesquisa para obter informações relevantes e precisas para a conversa.
         Ao pesquisar por programas ou cursos:
         1. Considere SEMPRE TODAS as áreas de estudo de forma equitativa, não apenas as mais óbvias ou comuns.
         2. Se a consulta não for específica de uma área, certifique-se de pesquisar amplamente em todas as disciplinas.
         3. Se os resultados parecerem demasiado restritos, alargue a pesquisa para incluir outras áreas.
         Se não houver contexto suficiente, faça uma pergunta complementar.""")
    ])
    retriever_chain = create_history_aware_retriever(llm, retriever, prompt)
    return retriever_chain


# Prompt de resposta
def get_conversational_rag_chain(retriever_chain):
    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = ChatPromptTemplate.from_messages([
        ("system", """És o chatbot do IPB. Responde às perguntas do utilizador com base nos ficheiros dados.
          Aguarda a resposta do utilizador e depois responde a pergunta mencionada anteriormente pelo utilizador.
          Se a pergunta do utilizador não tiver contexto suficiente, faz uma pergunta complementar para obter mais detalhes.
          Devolve sempre o URL fonte de onde obtiveste a informação  e outros links uteis presentes no ficheiro ao utilizador.\n\n{context}"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
    ])
    stuff_documents_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever_chain, stuff_documents_chain)
 
async def get_response(user_input):

    start_time = time.time()
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = get_vectorstore_from_docs(loaded_docs)
    

    processed_input = replace_abbreviations(user_input, abbreviation_dict)

    clarification_needed = check_for_ambiguity(processed_input, course_options)
    if clarification_needed:
        st.session_state.chat_history.append(HumanMessage(content=user_input))
        st.session_state.chat_history.append(AIMessage(content=clarification_needed))

        latency = time.time() - start_time
        tokens_used = (0, 0) 
        cost = calculate_cost(*tokens_used)
        save_chat_statistics(user_input, clarification_needed, tokens_used, latency, cost)
        return clarification_needed
    
    retriever_chain = get_context_retriever_chain(st.session_state.vector_store)
    conversation_rag_chain = get_conversational_rag_chain(retriever_chain)

    input_dict = {
        "chat_history": st.session_state.chat_history[-5:], 
        "input": processed_input,
    }
    
    with collect_runs() as cb:
        response = await asyncio.to_thread(conversation_rag_chain.invoke, input_dict)
        full_response = response['answer']
        st.session_state.run_id = cb.traced_runs[0].id

    st.session_state.chat_history.append(HumanMessage(content=user_input))
    st.session_state.chat_history.append(AIMessage(content=full_response))

    end_time = time.time()
    latency = end_time - start_time
    input_tokens, output_tokens, tokens_used = calculate_tokens(user_input, full_response)
    cost = calculate_cost(input_tokens, output_tokens)
    chat_id = save_chat_statistics(user_input, full_response, tokens_used, latency, cost)
    st.session_state.last_chat_id = chat_id
    return full_response


def display_word_by_word(text, placeholder):
    words = text.split()
    cumulative_text = ""
    for word in words:
        cumulative_text += word + " "
        placeholder.write(cumulative_text)  
        time.sleep(0.1)  

# Streamlit UI setup
st.set_page_config( page_icon="🤖")
st.title("IPB Chatbot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [AIMessage(content="Olá! Em que posso ajudar?")]
if "run_id" not in st.session_state:
    st.session_state.run_id = str(uuid.uuid4())

user_query = st.chat_input("Escreva a sua mensagem aqui")

if user_query is not None and user_query != "":
    response = asyncio.run(get_response(user_query))

for message in st.session_state.chat_history[:-1]:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.write(message.content)

if st.session_state.chat_history and isinstance(st.session_state.chat_history[-1], AIMessage):
    with st.chat_message("AI"):
        placeholder = st.empty()
        display_word_by_word(st.session_state.chat_history[-1].content, placeholder)

    #Feedback
    if len(st.session_state.chat_history) > 2:
        feedback = streamlit_feedback(
            feedback_type="faces", 
            optional_text_label="[Opcional] Adicione um comentário",
            key=f"feedback_{st.session_state.run_id}",
        )
         
        scores = {"😀": 5, "🙂": 4, "😐": 3, "🙁": 2, "😞": 1}
        
        if feedback:
            score = scores.get(feedback["score"])
            feedback_message = feedback.get("text", "")
            if score is not None and hasattr(st.session_state, 'last_chat_id'):
                update_feedback(st.session_state.last_chat_id, score, feedback_message)
                
                feedback_record = client.create_feedback(
                    st.session_state.run_id,
                    "faces",
                    score=score,
                    comment=feedback_message,
                )
                st.session_state.feedback = {
                    "feedback_id": str(feedback_record.id),
                    "score": score,
                    "message": feedback_message
                }


st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)
