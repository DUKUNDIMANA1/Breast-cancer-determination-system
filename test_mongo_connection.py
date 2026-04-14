
"""
Test script to verify MongoDB Atlas connection
"""
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get MongoDB URI from environment
MONGO_URI = os.environ.get('MONGO_URI')
MONGO_DB = os.environ.get('MONGO_DB_NAME', 'breastcare_ai')

print(f"MongoDB URI: {MONGO_URI}")
print(f"Database Name: {MONGO_DB}")
print("-" * 50)

try:
    # Connect to MongoDB Atlas
    print("Attempting to connect to MongoDB Atlas...")
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=50000,  # Increased timeout to 50 seconds
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        retryWrites=True,
        retryReads=True,
        tlsAllowInvalidCertificates=True  # Allow invalid certificates for testing
    )

    # Force connection to test
    print("Testing connection with ping command...")
    result = client.admin.command('ping')
    print(f"Ping result: {result}")
    print("✅ Successfully connected to MongoDB Atlas!")

    # Get database info
    db = client[MONGO_DB]
    print(f"✅ Successfully connected to database: {MONGO_DB}")

    # List collections
    collections = db.list_collection_names()
    print(f"Collections in database: {collections}")

except Exception as e:
    print(f"❌ Connection failed: {e}")
    import traceback
    traceback.print_exc()
