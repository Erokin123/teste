from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx

app = FastAPI()

# Считываем ключ из GEMINI_API_KEY или API_KEY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")

class QuestRequest(BaseModel):
    history: list = []
    speaker: str = "НПС"

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Server is running"}

@app.post("/generate_quest")
async def generate_quest(request: QuestRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="API Key is missing on server")

    # Формируем запрос к Gemini API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt_text = (
        "Ты генерируешь короткие диалоги для 2D RPG. "
        "Ответь строго в формате JSON без разметки markdown:\n"
        '{"quest_title": "Название квеста", "dialogue": "Короткая реплика персонажа"}'
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=10.0)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
        data = response.json()
        try:
            generated_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"status": "success", "quest_json": generated_text}
        except (KeyError, IndexError, TypeError):
            raise HTTPException(status_code=500, detail="Failed to parse Gemini response")
