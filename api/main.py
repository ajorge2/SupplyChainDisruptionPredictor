from fastapi import FastAPI, HTTPException, Request, APIRouter, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
import json
from datetime import datetime
from kafka import KafkaConsumer
from fastapi import WebSocket
import asyncio
from product_analyzer import analyze_product
import redis

app = FastAPI()

# Logging configuration
logging.basicConfig(level=logging.INFO)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product analysis request model
class ProductAnalysisRequest(BaseModel):
    product_name: str

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "API is running!"}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    product = data.get("product")
    location = data.get("location")
    result = analyze_product(product, location)
    return result

# RISK SCORE LOGIC (documented for future reference)
# 0 - neither the material or the location are ever mentioned, or only the location is mentioned once
# 1 - the material is mentioned once by itself, or the location is mentioned twice by itself
# 2 - both the material and location are mentioned together in the same data point once,
#     the material is mentioned twice by itself, or the location is mentioned three times by itself.
# 3 - both the material and location are mentioned together in the same data point more than once,
#     the material is mentioned more than twice by itself, or the location is mentioned more than three times by itself.

router = APIRouter()

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

@router.get("/risk_score")
def get_risk_score(material: str, location: str):
    """
    Calculate risk score for a material/location combo based on recent_mentions in Redis.
    """
    # RISK SCORE LOGIC (see above)
    material = material.lower()
    location = location.lower()
    recent_mentions = [json.loads(x) for x in redis_client.lrange('recent_mentions', 0, 499)]
    together = 0
    material_only = 0
    location_only = 0

    for mention in recent_mentions:
        m = mention.get("material")
        l = mention.get("location")
        if m:
            m = m.lower()
        if l:
            l = l.lower()
        if m == material and l == location:
            together += 1
        elif m == material:
            material_only += 1
        elif l == location:
            location_only += 1

    # Apply your risk score rules
    if together > 1 or material_only > 2 or location_only > 3:
        score = 3
    elif together == 1 or material_only == 2 or location_only == 3:
        score = 2
    elif material_only == 1 or location_only == 2:
        score = 1
    else:
        score = 0

    return {"material": material, "location": location, "risk_score": score}

app.include_router(router)