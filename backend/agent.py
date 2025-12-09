import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

class Agent:
    def __init__(self):
        load_dotenv()
        self.client = genai.Client()
        self.chat = self.client.chats.create(model="gemini-2.5-flash")
        
    def generate(self, query):
        response = self.chat.send_message(query)
        return response.text
    
if __name__ == "__main__":
    agent = Agent()
    explanation = agent.generate("What is quantum computing?")
    print(explanation)