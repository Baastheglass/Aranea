import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="Explain how AI works in simple terms."
)

print(response.text)
