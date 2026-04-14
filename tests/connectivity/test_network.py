
"""
Test script to check network connectivity to MongoDB Atlas
"""
import urllib.request
import socket
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB URI from environment
MONGO_URI = os.environ.get('MONGO_URI')

# Extract hostname from URI
import urllib.parse
parsed = urllib.parse.urlparse(MONGO_URI)
hostname = parsed.hostname

print(f"Testing network connectivity to: {hostname}")
print("-" * 50)

try:
    # Try to ping MongoDB Atlas using HTTP
    print("Attempting HTTP request to MongoDB Atlas...")
    url = f"https://{hostname}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req, timeout=10)
    print(f"✅ Successfully connected to {hostname} via HTTP")
    print(f"Response status: {response.status}")
except urllib.error.URLError as e:
    print(f"❌ HTTP request failed: {e}")
    print("This could indicate network connectivity issues or firewall restrictions")
except Exception as e:
    print(f"❌ Network test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Troubleshooting steps:")
print("1. Check your internet connection")
print("2. Try accessing https://www.mongodb.com in your browser")
print("3. Check if you're behind a corporate firewall or proxy")
print("4. Try changing your DNS server to 8.8.8.8 (Google) or 1.1.1.1 (Cloudflare)")
print("5. Verify your MongoDB Atlas cluster name and connection string")
