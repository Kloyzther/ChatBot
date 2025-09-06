# Bot/Client.py
import requests

class LLMClient:
    def __init__(self, token):
        self.token = token
        self.messages = []

    def get_response(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/gpt-3.5-turbo",
                    "messages": self.messages
                }
            )
            response.raise_for_status()
            ai_response = response.json()["choices"][0]["message"]["content"]
            self.messages.append({"role": "assistant", "content": ai_response})
            return ai_response
        except requests.exceptions.RequestException as e:
            return f"[Error LLM] {e}"

