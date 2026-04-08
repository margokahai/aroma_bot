import os
from dotenv import load_dotenv
import openai

# Загружаем ключ из .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

try:
    # Синхронный вызов OpenAI (v1.x)
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Привет, проверь API"}],
        max_tokens=50
    )
    print("✅ OpenAI отвечает:")
    print(response.choices[0].message.content)
except Exception as e:
    print("❌ Ошибка подключения к OpenAI:", e)