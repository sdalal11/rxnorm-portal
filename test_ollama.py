import requests
import json

def test_ollama():
    try:
        response = requests.post('http://localhost:11434/api/generate', 
                               json={"model": "deepseek-r1:7b", 
                                    "prompt": "Hello, can you help with text analysis?", 
                                    "stream": False})
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Ollama is working!")
            print(f"Response: {result.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ Ollama API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_ollama()
