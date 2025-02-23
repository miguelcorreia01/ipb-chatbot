import os
from pymongo import MongoClient
from datetime import datetime
import tiktoken
from dotenv import load_dotenv

load_dotenv()

INPUT_TOKEN_COST_PER_MILLION = 0.150 / 1_000_000
OUTPUT_TOKEN_COST_PER_MILLION = 0.600 / 1_000_000



def calculate_tokens(input_text, output_text):

    tokenizer = tiktoken.get_encoding("cl100k_base")

    input_tokens = len(tokenizer.encode(input_text))
    output_tokens = len(tokenizer.encode(output_text))

    tokens_used = input_tokens + output_tokens

    return input_tokens, output_tokens, tokens_used

def calculate_cost(input_tokens, output_tokens):
    input_cost = input_tokens * INPUT_TOKEN_COST_PER_MILLION
    output_cost = output_tokens * OUTPUT_TOKEN_COST_PER_MILLION
    total_cost = input_cost + output_cost
    return total_cost


# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["chatbot_data"]
stats_collection = db["chat_statistics"]


def save_chat_statistics(user_input, response, tokens_used, latency, cost, feedback_score=None, feedback_message=None):
    stat = {
        "timestamp": datetime.utcnow(),
        "user_input": user_input,
        "response": response,
        "tokens_used": tokens_used,
        "latency": latency,
        "cost": cost, 
        "feedback_score": feedback_score,
        "feedback_message": feedback_message,

    }
    result = stats_collection.insert_one(stat)
    return result.inserted_id

def update_feedback(chat_id, feedback_score, feedback_message=None):
    update_fields = {"feedback_score": feedback_score}
    if feedback_message is not None:
        update_fields["feedback_message"] = feedback_message

    stats_collection.update_one(
        {"_id": chat_id},
        {"$set": update_fields}
    )



