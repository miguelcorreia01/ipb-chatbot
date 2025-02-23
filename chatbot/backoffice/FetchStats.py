import os
from dotenv import load_dotenv
from langsmith import Client
import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["chatbot_data"]
stats_collection = db["chat_statistics"]
users_collection = db["users"]

def get_chatbot_files():
    chatbot_files_dir = "../mdfiles"
    files = []
    for filename in os.listdir(chatbot_files_dir):
        file_path = os.path.join(chatbot_files_dir, filename)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            files.append({
                'name': filename,
                'size': f'{size / 1024:.2f} KB'
            })
    return files

def fetch_chat_statistics(time_range):
    end_date = datetime.utcnow()
    
    if time_range == '1d':
        start_date = end_date - timedelta(days=1)
    elif time_range == '1w':
        start_date = end_date - timedelta(weeks=1)
    elif time_range == '30d':
        start_date = end_date - timedelta(days=30)
    elif time_range == '1y':
        start_date = end_date - timedelta(days=365)
    else:  
        start_date = datetime.min

    pipeline = [
        {
            "$match": {
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }
        },
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "total_interactions": {"$sum": 1},
                "total_tokens": {"$sum": "$tokens_used"},
                "avg_latency": {"$avg": "$latency"},
                "total_cost": {"$sum": "$cost"},
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    result = list(stats_collection.aggregate(pipeline))

    dates = []
    interactions = []
    tokens = []
    latencies = []
    costs = []

    for day in result:
        dates.append(day['_id'])
        interactions.append(day['total_interactions'])
        tokens.append(day['total_tokens'])
        latencies.append(day['avg_latency'])
        costs.append(day['total_cost'])

    feedback_pipeline = [
        {
            "$match": {
                "timestamp": {"$gte": start_date, "$lte": end_date},
                "feedback_score": {"$ne": None}
            }
        },
        {
            "$group": {
                "_id": "$feedback_score",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    feedback_result = list(stats_collection.aggregate(feedback_pipeline))
    feedback_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for item in feedback_result:
        if 1 <= item['_id'] <= 5:
            feedback_distribution[item['_id']] = item['count']

    total_interactions = sum(interactions)
    max_tokens = max(tokens) if tokens else 0
    min_tokens = min(tokens) if tokens else 0
    max_latency = max(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    total_cost = sum(costs)

    total_feedback = sum(feedback_distribution.values())
    weighted_sum = sum(score * count for score, count in feedback_distribution.items())
    avg_feedback = weighted_sum / total_feedback if total_feedback > 0 else 0

    general_stats = {
        'total_interactions': total_interactions,
        'max_tokens': max_tokens,
        'min_tokens': min_tokens,
        'max_latency': max_latency,
        'min_latency': min_latency,
        'avg_latency': avg_latency,
        'avg_feedback': avg_feedback,
        'total_cost': total_cost
    }

    feedback_messages = list(stats_collection.find(
        {
            "timestamp": {"$gte": start_date, "$lte": end_date},
            "feedback_message": {"$exists": True, "$ne": ""}
        },
        {"feedback_message": 1, "timestamp": 1, "_id": 0}
    ).sort("timestamp", -1))  

    return {
        'dates': dates,
        'interactions': interactions,
        'tokens': tokens,
        'latencies': latencies,
        'feedback_distribution': feedback_distribution,
        'general_stats': general_stats,
        'feedback_messages': feedback_messages,
        'last_updated': datetime.utcnow()
    }
