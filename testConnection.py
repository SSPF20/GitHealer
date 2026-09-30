import os
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env file
load_dotenv()

# Initialize the Gemini API client
geminiClient = genai.Client()

print("🤖 Connecting to Gemini API...")

# Send request to Gemini model (using the modern gemini-3.8-flash)
modelResponse = geminiClient.models.generate_content(
    model="gemini-3.8-flash",
    contents="Hello, I am GitHealer. In a single, short, witty sentence, introduce yourself as an expert code surgeon who fixes broken software.",
)

# Display the output
print("\n--- GitHealer Diagnostic ---")
print(modelResponse.text)