from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx

app = FastAPI()

class QuestRequest(BaseModel):
    history: list = []
    speaker: str = "НПС"

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Server is running"}

# Поддерживаем оба формата пути
@app.post("/generate_quest")
@app.post("/generate-quest")
async def generate_quest(request: QuestRequest):
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")
    
    if not gemini_key:
        raise HTTPException(status_code=500, detail="API Key is missing on server")

    # Использование актуальной рабочей модели (gemini-1.5-flash или gemini-2.5-flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    
    prompt_text = (
        f"Ты NPC в 2D RPG. Твоё имя: {request.speaker}. "
        "Сгенерируй короткую реплику или квест. "
        "Ответь строго в формате JSON со следующими ключами: "
        '{"quest_title": "Название квеста", "dialogue": "Короткая реплика персонажа"}'
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=15.0)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"Request to Gemini failed: {str(exc)}")
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
            
        data = response.json()
        try:
            generated_text = data["candidates"][0]["content"]["parts"][0]["text"]
            clean_text = generated_text.strip()
            return {"status": "success", "quest_json": clean_text}
        except (KeyError, IndexError, TypeError):
            raise HTTPException(status_code=500, detail="Failed to parse Gemini response")
