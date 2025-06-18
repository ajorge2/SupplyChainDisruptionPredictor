from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
import json
from datetime import datetime
from kafka import KafkaConsumer
from fastapi import WebSocket
import asyncio
from .product_analyzer import analyze_product

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

@app.websocket("/ws/realtime")
async def realtime_websocket(websocket: WebSocket):
    print("WebSocket endpoint hit")
    await websocket.accept()
    
    try:
        # Create Kafka consumers
        consumers = {
            'weather': KafkaConsumer(
                'weather_data', 
                bootstrap_servers=['kafka:9092'],
                auto_offset_reset='latest',
                enable_auto_commit=False
            ),
            'reddit': KafkaConsumer(
                'social_media_data', 
                bootstrap_servers=['kafka:9092'],
                auto_offset_reset='latest',
                enable_auto_commit=False
            ),
            'news': KafkaConsumer(
                'news_data', 
                bootstrap_servers=['kafka:9092'],
                auto_offset_reset='latest',
                enable_auto_commit=False
            )
        }
        print("Kafka consumers created")
        
        while True:
            for source, consumer in consumers.items():
                print(f"Polling {source} consumer...")
                messages = consumer.poll(timeout_ms=100)
                print(f"Got {len(messages)} message sets from {source}")
                for message_set in messages.values():
                    for message in message_set:
                        data = json.loads(message.value.decode('utf-8'))
                        data['source'] = source
                        data['timestamp'] = datetime.now().isoformat()
                        print(f"Sending data: {data}")
                        await websocket.send_json(data)
            await asyncio.sleep(0.1)
                    
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        print("WebSocket connection closed")
        await websocket.close()

@app.post("/analyze")
async def analyze(request: Request):
    data = await request.json()
    product = data.get("product")
    location = data.get("location")
    result = analyze_product(product, location)
    return result