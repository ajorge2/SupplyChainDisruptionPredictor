from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import os
import logging
import json
from datetime import datetime
from kafka import KafkaConsumer
from fastapi import WebSocket
import asyncio

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

# Model for prediction requests
class PredictionRequest(BaseModel):
    temperature: float
    humidity: float
    location: str

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "API is running!"}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Predict endpoint
@app.post("/predict")
def predict(request: PredictionRequest):
    model_path = os.getenv("MODEL_PATH", "/app/model/model.joblib")

    # Check if the model file exists
    if not os.path.exists(model_path):
        raise HTTPException(status_code=500, detail=f"Model file not found at {model_path}")

    try:
        model = joblib.load(model_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading model: {str(e)}")

    # Validate inputs
    if not (0 <= request.humidity <= 100):
        raise HTTPException(status_code=400, detail="Humidity must be between 0 and 100")
    if not (-50 <= request.temperature <= 60):
        raise HTTPException(status_code=400, detail="Temperature must be between -50 and 60")

    # Feature processing
    features = [[request.temperature, request.humidity]]

    # Make prediction
    try:
        prediction = model.predict_proba(features)[0][1]  # Assuming binary classification
        logging.info(f"Prediction successful: {prediction}")
        return {"disruption_probability": prediction}
    except Exception as e:
        logging.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

# Alerts endpoint
@app.get("/alerts")
def get_alerts():
    return [
        {"id": 1, "message": "High risk of disruption in Area A"},
        {"id": 2, "message": "Severe weather warning for Region B"}
    ]

# Vehicle locations endpoint
@app.get("/vehicle-locations")
def get_vehicle_locations():
    return [
        {"name": "Truck 1", "latitude": 51.505, "longitude": -0.09},
        {"name": "Truck 2", "latitude": 52.505, "longitude": -1.09}
    ]

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
