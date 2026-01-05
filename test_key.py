import os
from openai import OpenAI

# Usage: 
# export OPENAI_API_KEY="sk-..."
# python3 test_key.py

def test_key():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("❌ Error: OPENAI_API_KEY environment variable is not set.")
        print("Run: export OPENAI_API_KEY='sk-...' then try again.")
        return

    print(f"✅ Found Key: {key[:5]}...{key[-4:]}")
    
    try:
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello, are you working?"}],
            max_tokens=10
        )
        print("✅ OpenAI Connection Successful!")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ API Call Failed: {e}")

if __name__ == "__main__":
    test_key()
