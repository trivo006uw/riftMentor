from fastapi import FastAPI, HTTPException
import os
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

# Get RIOT API
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
app = FastAPI(title = "RiftMentor API")

@app.get("/health")
def healthCheck():
    return {"status" : "ok"}


@app.get("/player/{game_name}/{tag_line}")
async def get_player(game_name: str, tag_line: str):
    apiKey = os.getenv("RIOT_API_KEY")

    if not apiKey:
        raise HTTPException(
            status_code = 500,
            detail = "RIOT API Key not found"
        )
    
    url = (
        "https://americas.api.riotgames.com"
        "/riot/account/v1/accounts/by-riot-id"
        f"/{quote(game_name, safe='')}/{quote(tag_line, safe='')}"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                headers={"X-Riot-Token": apiKey},
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to Riot API",
        )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Riot API returned status {response.status_code}",
        )

    return response.json()

@app.get("/player/{game_name}/{tag_line}/matches")
async def get_matches(game_name: str, tag_line: str):
    apiKey = os.getenv("RIOT_API_KEY")

    if not apiKey:
        raise HTTPException(
            status_code = 500,
            detail = "RIOT API Key not found"
        )
    
    player_tag = await get_player(game_name, tag_line)
    
    puuid = player_tag["puuid"]

    url = (
        "https://americas.api.riotgames.com"
        "/lol/match/v5/matches/by-puuid"
        f"/{quote(puuid, safe='')}/ids"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                headers={"X-Riot-Token": apiKey},
                params={"start": 0, "count": 1}
            )

    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to Riot API",
        )
    
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Riot API returned status {response.status_code}",
        )

    return response.json()
    
