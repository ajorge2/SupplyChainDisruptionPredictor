from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import os
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)

class PredictionRequest(BaseModel):
    temperature: float
    humidity: float
    location: str

@app.get("/health")
def health_check():
    return {"status": "healthy"}

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
