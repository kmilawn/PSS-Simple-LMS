from pymongo import MongoClient
from django.conf import settings

# MongoDB Connection
MONGODB_HOST = getattr(settings, 'MONGODB_SETTINGS', {}).get('host', 'mongodb')
MONGODB_PORT = getattr(settings, 'MONGODB_SETTINGS', {}).get('port', 27017)
MONGODB_DB = getattr(settings, 'MONGODB_SETTINGS', {}).get('db', 'simple_lms')

# Create MongoDB client
client = MongoClient(f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/")
db = client[MONGODB_DB]

# Collections
activity_logs = db["activity_logs"]
learning_analytics = db["learning_analytics"]

# Create indexes for better performance
activity_logs.create_index("timestamp")
activity_logs.create_index("username")
learning_analytics.create_index("user_id")
learning_analytics.create_index("course_id")