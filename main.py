import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

@app.get("/")
def home():
    return {"status": "Server is running 24/7"}

@app.post("/generate_quest")
async def generate_quest():
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="API Key is missing on server")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    
    quest_prompt = """
    Ты NPC в 2D игре. Придумай случайный квест для игрока.
    Верни ответ СТРОГО в формате JSON со следующими полями:
    {
        "quest_title": "Название квеста",
        "dialogue": "Короткая фраза NPC при выдаче квеста (1 предложение)",
        "target_id": "название цели (например: goblin, slime, herb)",
        "amount": 5,
        "reward_gold": 50
    }
    """

    payload = {
        "contents": [{"role": "user", "parts": [{"text": quest_prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=15.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            data = response.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"status": "success", "quest_json": raw_text}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
