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
    product: str
    location: str

# Load data files
script_dir = os.path.dirname(os.path.abspath(__file__))
products_path = os.path.join(script_dir, "products.json")
locations_path = os.path.join(script_dir, "locations.json")

with open(products_path, "r") as f:
    products_data = json.load(f)

with open(locations_path, "r") as f:
    locations_data = json.load(f)

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "API is running!"}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/products")
async def get_products():
    return products_data

@app.get("/locations")
async def get_locations():
    return locations_data

@app.post("/analyze")
async def analyze(request: ProductAnalysisRequest):
    try:
        # Load data
        script_dir = os.path.dirname(os.path.abspath(__file__))
        products_path = os.path.join(script_dir, "products.json")
        with open(products_path, "r") as f:
            products_data = json.load(f)

        # Check if this is a direct selection from our database
        product_info = None
        for category, items in products_data["raw_materials"].items():
            if isinstance(items, dict):
                for subcat, subitems in items.items():
                    if isinstance(subitems, dict):
                        if request.product in subitems:
                            product_info = subitems[request.product]
                            break
                    elif request.product == subcat:
                        product_info = items[subcat]
                        break
            if product_info:
                break

        # If product was found in database, use direct lookup
        if product_info:
            return {
                "raw_materials": [request.product],
                "material_source_locations": {
                    request.product: product_info.get("regions", [])[:3]  # Get up to 3 source locations
                },
                "risk_score": 0  # This will be calculated by the risk_score endpoint
            }
        # If product wasn't found, use OpenAI to analyze it
        else:
            result = analyze_product(request.product, request.location)
            if not result:
                raise HTTPException(status_code=404, detail="Analysis not found")
            return {
                "raw_materials": result.get("raw_materials", []),
                "material_source_locations": result.get("material_source_locations", {}),
                "risk_score": 0  # This will be calculated by the risk_score endpoint
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
def get_risk_score(material: str, locations: list[str] = Query(None)):
    """
    Calculate risk scores for a material across multiple locations.
    Returns both individual location scores and an aggregate score.
    """
    try:
        material = material.lower()
        locations = [loc.lower() for loc in locations]
        recent_mentions = [json.loads(x) for x in redis_client.lrange('recent_mentions', 0, 499)]
        
        location_scores = {}
        max_risk = 0  # Track highest risk score for aggregate
        total_together = 0  # Track total mentions of material+location together
        material_mentions = 0  # Track total material mentions
        
        # Calculate individual scores for each location
        for location in locations:
            together = 0
            material_only = 0
            location_only = 0
            
            for mention in recent_mentions:
                m = mention.get("material", "").lower() if mention.get("material") else ""
                l = mention.get("location", "").lower() if mention.get("location") else ""
                
                if m == material and l == location:
                    together += 1
                    total_together += 1
                elif m == material:
                    material_only += 1
                    material_mentions += 1
                elif l == location:
                    location_only += 1
            
            # Calculate individual location score
            if together > 1 or material_only > 2 or location_only > 3:
                score = 3
            elif together == 1 or material_only == 2 or location_only == 3:
                score = 2
            elif material_only == 1 or location_only == 2:
                score = 1
            else:
                score = 0
                
            location_scores[location] = {
                "risk_score": score,
                "mentions": {
                    "together": together,
                    "material_only": material_only,
                    "location_only": location_only
                }
            }
            
            max_risk = max(max_risk, score)
        
        # Calculate aggregate score based on:
        # - Highest individual location score
        # - Total mentions across all locations
        # - Total material mentions
        aggregate_score = max_risk
        if total_together > len(locations) or material_mentions > len(locations) * 2:
            aggregate_score = min(3, aggregate_score + 1)  # Increase risk if many mentions across locations
            
        return {
            "material": material,
            "aggregate_risk_score": aggregate_score,
            "location_scores": location_scores,
            "total_mentions": {
                "material": material_mentions,
                "together": total_together
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)