import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OpenAI.API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI()
response = client.images.generate(
    model="dall-e-3",
    prompt="a beautifu cat flying sky",
    size="1024x1024",
    quality="standard",
    style="natural",
    response_format="url",
    n=1,
    user="SD2_CUI",
)
print(response)
