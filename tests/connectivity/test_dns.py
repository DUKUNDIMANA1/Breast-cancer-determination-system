
"""
Test script to check if MongoDB Atlas hostname can be resolved
"""
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

print(f"Testing DNS resolution for: {hostname}")
print("-" * 50)

try:
    # Try to resolve the hostname
    ip_address = socket.gethostbyname(hostname)
    print(f"✅ Successfully resolved hostname: {hostname} -> {ip_address}")

    # Try to connect to the MongoDB port (27017)
    print(f"Testing connection to {hostname} on port 27017...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    result = sock.connect_ex((hostname, 27017))

    if result == 0:
        print(f"✅ Successfully connected to {hostname} on port 27017")
    else:
        print(f"❌ Failed to connect to {hostname} on port 27017 (Error code: {result})")

    sock.close()

except socket.gaierror as e:
    print(f"❌ DNS resolution failed: {e}")
    print("This could indicate:")
    print("  - Network connectivity issues")
    print("  - Incorrect MongoDB Atlas cluster name")
    print("  - DNS server issues")
except Exception as e:
    print(f"❌ Connection test failed: {e}")
    import traceback
    traceback.print_exc()
