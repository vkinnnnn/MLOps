"""
Generate API Keys for Friends
"""
import sys
import os

# Add api directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from auth import create_api_key, list_api_keys

def generate_keys_for_friends():
    """Generate 2 API keys for friends"""
    
    print("\n" + "="*60)
    print("GENERATING API KEYS FOR YOUR FRIENDS")
    print("="*60 + "\n")
    
    # Friend 1 - Standard Tier
    friend1 = create_api_key(
        user_name="Friend_1",
        tier="standard",
        rate_limit=1000  # 1000 requests per day
    )
    
    print("🔑 API KEY #1 - Friend 1")
    print("-" * 60)
    print(f"User Name:    {friend1['user_name']}")
    print(f"API Key:      {friend1['api_key']}")
    print(f"Tier:         {friend1['tier']}")
    print(f"Rate Limit:   {friend1['rate_limit']} requests/day")
    print(f"Created:      {friend1['created_at']}")
    print(f"Status:       {'Active' if friend1['is_active'] else 'Inactive'}")
    print()
    
    # Friend 2 - Standard Tier
    friend2 = create_api_key(
        user_name="Friend_2",
        tier="standard",
        rate_limit=1000  # 1000 requests per day
    )
    
    print("🔑 API KEY #2 - Friend 2")
    print("-" * 60)
    print(f"User Name:    {friend2['user_name']}")
    print(f"API Key:      {friend2['api_key']}")
    print(f"Tier:         {friend2['tier']}")
    print(f"Rate Limit:   {friend2['rate_limit']} requests/day")
    print(f"Created:      {friend2['created_at']}")
    print(f"Status:       {'Active' if friend2['is_active'] else 'Inactive'}")
    print()
    
    print("="*60)
    print("API KEYS GENERATED SUCCESSFULLY!")
    print("="*60)
    print()
    print("📋 INSTRUCTIONS FOR YOUR FRIENDS:")
    print()
    print("1. Use the API key in the request header:")
    print("   X-API-Key: <their-api-key>")
    print()
    print("2. Example curl command:")
    print('   curl -H "X-API-Key: <their-api-key>" \\')
    print('        http://your-server:8000/api/v1/extract \\')
    print('        -F "file=@document.pdf"')
    print()
    print("3. Rate Limit: 1000 requests per day")
    print()
    print("4. Keys are stored in: api_keys.json")
    print()
    print("="*60)
    print()
    
    # Save keys to a file for easy sharing
    with open("API_KEYS_FOR_FRIENDS.txt", "w") as f:
        f.write("="*60 + "\n")
        f.write("API KEYS FOR YOUR FRIENDS\n")
        f.write("="*60 + "\n\n")
        
        f.write("🔑 FRIEND 1\n")
        f.write("-" * 60 + "\n")
        f.write(f"API Key: {friend1['api_key']}\n")
        f.write(f"Tier: {friend1['tier']}\n")
        f.write(f"Rate Limit: {friend1['rate_limit']} requests/day\n\n")
        
        f.write("🔑 FRIEND 2\n")
        f.write("-" * 60 + "\n")
        f.write(f"API Key: {friend2['api_key']}\n")
        f.write(f"Tier: {friend2['tier']}\n")
        f.write(f"Rate Limit: {friend2['rate_limit']} requests/day\n\n")
        
        f.write("="*60 + "\n")
        f.write("HOW TO USE\n")
        f.write("="*60 + "\n\n")
        
        f.write("Add the API key to your request header:\n")
        f.write('X-API-Key: <your-api-key>\n\n')
        
        f.write("Example with curl:\n")
        f.write('curl -H "X-API-Key: <your-api-key>" \\\n')
        f.write('     http://your-server:8000/api/v1/extract \\\n')
        f.write('     -F "file=@document.pdf"\n\n')
        
        f.write("Example with Python:\n")
        f.write('import requests\n\n')
        f.write('headers = {"X-API-Key": "<your-api-key>"}\n')
        f.write('files = {"file": open("document.pdf", "rb")}\n')
        f.write('response = requests.post(\n')
        f.write('    "http://your-server:8000/api/v1/extract",\n')
        f.write('    headers=headers,\n')
        f.write('    files=files\n')
        f.write(')\n\n')
        
        f.write("="*60 + "\n")
    
    print("✅ Keys saved to: API_KEYS_FOR_FRIENDS.txt")
    print()


if __name__ == "__main__":
    generate_keys_for_friends()
