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

# get the matches id of a user
@app.get("/player/{game_name}/{tag_line}/matches")
async def get_matches(game_name: str, tag_line: str, count : int = 1):
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
                params={"start": 0, "count": count}
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
    
# get detail of a match from match_id, call this to get a full detail of 1 specific match
@app.get("/matches/{match_id}")
async def get_match_detail(match_id: str):
    print("Fetching match:", match_id, flush=True)
    apiKey = os.getenv("RIOT_API_KEY")

    if not apiKey:
        raise HTTPException(
            status_code = 500,
            detail = "RIOT API Key not found"
        )

    url = (
        f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}'
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


# process and return match data with user puuid, this is a helper function use by get match summary
def get_match_data(match_data, puuid : str):
    my_data = {}
    length = len(match_data["info"]["participants"])

    for i in range(length):
        currInfo = match_data["info"]["participants"][i]
        if currInfo["puuid"] == puuid:
            my_data["championName"] = currInfo["championName"]
            my_data["kills"] = currInfo['kills']
            my_data["deaths"] = currInfo['deaths']
            my_data["assists"] = currInfo['assists']
            my_data["role"] = currInfo["role"]
            my_data["goldEarned"] = currInfo["goldEarned"]
            my_data["total_cs"] = currInfo["totalMinionsKilled"] + currInfo["neutralMinionsKilled"]
            my_data["Win/Loss"] = currInfo["win"]   
            kda = round((my_data["kills"] + my_data["assists"]) / max(my_data["deaths"], 1), 2)
            cs_per_min = round(my_data["total_cs"] / (match_data["info"]["gameDuration"] / 60), 2)
            my_data["kda"] = kda
            my_data["cs_per_min"] = cs_per_min
            return my_data
    
    
    return None


# get the latest match, call this instead of get summary for the latest match 
@app.get("/player/{game_name}/{tag_line}/matches/latest/summary")
async def get_latest_match(game_name: str, tag_line: str):
    matches = await get_matches(game_name, tag_line)
    if not matches:
        raise HTTPException(
            status_code= 404,
            detail="No matches found for this player",
        )
    data = await get_match_summary(game_name, tag_line, matches[0])
    return data


# 
@app.get("/player/{game_name}/{tag_line}/matches/recent/summary")
async def get_recent_summary(game_name : str, tag_line : str):
    matches_id = await get_matches(game_name, tag_line, count=5)
    player = await get_player(game_name, tag_line)
    puuid = player["puuid"]

    


# get summary of a match with player game name, tag line and specific match id
@app.get("/player/{game_name}/{tag_line}/matches/{match_id}/summary")
async def get_match_summary(game_name: str, tag_line: str, match_id: str):
    player = await get_player(game_name, tag_line)
    puuid = player["puuid"]
    current_match = await get_match_detail(match_id)

    data = get_match_data(current_match, puuid)

    if not data:
        raise HTTPException(
            status_code=404,
            detail="Player not found in this match",
        )
    return data


