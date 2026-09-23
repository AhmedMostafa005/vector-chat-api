import requests
import json

BASE_URL = "http://localhost:8000"

def test_get_users():
    response = requests.get(f"{BASE_URL}/users")
    print("GET /users:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_store_text(user_id, text):
    response = requests.post(
        f"{BASE_URL}/users/{user_id}/text",
        json={"text": text}
    )
    print(f"\nPOST /users/{user_id}/text:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_chat(user_id, message):
    response = requests.post(
        f"{BASE_URL}/users/{user_id}/chat",
        json={"message": message}
    )
    print(f"\nPOST /users/{user_id}/chat:")
    print(json.dumps(response.json(), indent=2))
    return response.json()

if __name__ == "__main__":
    # First, get existing users
    users = test_get_users()
    
    if not users:
        print("No users found. Please create a user first using create_user.py")
        exit(1)
    
    user_id = users[0]["id"]
    print(f"\nUsing user ID: {user_id}")
    
    # Store some sample text
    sample_texts = [
        "Python is a high-level programming language known for its simplicity and readability.",
        "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.",
        "PostgreSQL is a powerful, open source object-relational database system with over 30 years of active development.",
        "Vector embeddings are numerical representations of text that capture semantic meaning."
    ]
    
    for text in sample_texts:
        test_store_text(user_id, text)
    
    # Test chat
    test_chat(user_id, "What is FastAPI?")
    test_chat(user_id, "Tell me about databases")
