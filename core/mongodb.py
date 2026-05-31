from pymongo import MongoClient

client = MongoClient("mongodb://mongodb:27017/")

mongo_db = client["simple_lms"]

activity_logs = mongo_db["activity_logs"]

learning_analytics = mongo_db["learning_analytics"]