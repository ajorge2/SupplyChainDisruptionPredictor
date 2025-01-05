from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
import joblib
import os
from typing import Optional
import redis
import psycopg2
from psycopg2 import pool
import json
import logging
from datetime import datetime

# Initialize logging
logging.basicConfig(
    filename='api.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

app = FastAPI(title="Supply Chain Disruption Predictor")

# Define the data model for prediction requests
class PredictionRequest(BaseModel):
    temperature: float = Field(..., ge=-50, le=60, example=25.5, description="Current temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, example=60.0, description="Current humidity percentage")
    location: str = Field(..., example="Warehouse_A", description="Location identifier")

# Define the response model
class PredictionResponse(BaseModel):
    disruption_probability: float = Field(..., example=0.85, description="Probability of supply chain disruption")

# API Key for authentication
API_KEY = os.getenv("API_KEY", "your_secure_api_key")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

# Load the pre-trained machine learning model
MODEL_PATH = os.getenv("MODEL_PATH", "ml/model/model.joblib")
try:
    model = joblib.load(MODEL_PATH)
    logging.info("Machine learning model loaded successfully.")
except Exception as e:
    logging.error(f"Error loading model: {e}")
    model = None

# Initialize Redis client
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    # Test Redis connection
    redis_client.ping()
    logging.info("Connected to Redis successfully.")
except redis.RedisError as e:
    logging.error(f"Redis connection error: {e}")
    redis_client = None

# Initialize PostgreSQL connection pool
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "supplychaindb")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1,
        10,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB
    )
    if db_pool:
        logging.info("PostgreSQL connection pool created successfully.")
except psycopg2.DatabaseError as e:
    logging.error(f"Error creating PostgreSQL connection pool: {e}")
    db_pool = None

def get_db_connection():
    if db_pool:
        try:
            conn = db_pool.getconn()
            if conn:
                logging.info("PostgreSQL connection acquired from pool.")
                return conn
        except psycopg2.DatabaseError as e:
            logging.error(f"Error getting connection from pool: {e}")
            return None
    else:
        logging.error("PostgreSQL connection pool is not available.")
        return None

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Supply Chain Disruption Predictor!"}

@app.get("/health")
def health_check():
    health_status = {
        "model_loaded": model is not None,
        "redis_connected": redis_client is not None,
        "postgres_connected": db_pool is not None
    }
    return {"status": "healthy", "details": health_status}

@app.post("/predict", response_model=PredictionResponse, dependencies=[Depends(verify_api_key)])
def predict_disruption(request: PredictionRequest):
    if model is None:
        logging.error("Model not loaded.")
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    if redis_client is None:
        logging.error("Redis client not initialized.")
        raise HTTPException(status_code=500, detail="Cache system not available")
    
    try:
        # Fetch historical features
        avg_temp, avg_humidity = fetch_historical_features(request.location)
        
        if avg_temp is None or avg_humidity is None:
            logging.warning(f"Insufficient historical data for location {request.location}")
            raise HTTPException(status_code=400, detail="Insufficient historical data for prediction")
        
        # Feature preprocessing
        features = [request.temperature, request.humidity, avg_temp, avg_humidity]
        
        # Prepare the input for the model
        features_array = [features]
        
        # Make prediction
        prediction_proba = model.predict_proba(features_array)[0][1]  # Probability of class '1'
        logging.info(f"Prediction made: {prediction_proba} for location {request.location}")
        
        # Cache the prediction in Redis
        cache_key = f"prediction:{request.location}:{request.temperature}:{request.humidity}:{avg_temp}:{avg_humidity}"
        cache_value = {
            "temperature": request.temperature,
            "humidity": request.humidity,
            "avg_temperature_last_5_days": avg_temp,
            "avg_humidity_last_5_days": avg_humidity,
            "disruption_probability": prediction_proba,
            "timestamp": datetime.utcnow().isoformat()
        }
        redis_client.set(cache_key, json.dumps(cache_value), ex=3600)  # Cache expires in 1 hour
        logging.info(f"Cached prediction with key: {cache_key}")
        
        # Store the prediction in PostgreSQL
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                insert_query = """
                INSERT INTO predictions (timestamp, location, temperature, humidity, avg_temperature_last_5_days, avg_humidity_last_5_days, disruption_probability)
                VALUES (NOW(), %s, %s, %s, %s, %s, %s);
                """
                cursor.execute(insert_query, (request.location, request.temperature, request.humidity, avg_temp, avg_humidity, prediction_proba))
                conn.commit()
                cursor.close()
                logging.info(f"Stored prediction in PostgreSQL for location {request.location}")
            except psycopg2.DatabaseError as e:
                logging.error(f"Error inserting prediction into PostgreSQL: {e}")
            finally:
                db_pool.putconn(conn)
                logging.info("PostgreSQL connection returned to pool.")
        
        return PredictionResponse(disruption_probability=prediction_proba)
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error during prediction: {e}")
        raise HTTPException(status_code=400, detail="Prediction failed due to internal error")

def fetch_historical_features(location: str):
    """
    Fetch average temperature and humidity for the past 5 days for a given location.
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
            SELECT AVG(temperature), AVG(humidity)
            FROM weather_historical
            WHERE location = %s AND timestamp >= NOW() - INTERVAL '5 days';
            """
            cursor.execute(query, (location,))
            result = cursor.fetchone()
            cursor.close()
            if result:
                return result  # (avg_temperature, avg_humidity)
            else:
                return (None, None)
        except Exception as e:
            logging.error(f"Error fetching historical data: {e}")
            return (None, None)
        finally:
            db_pool.putconn(conn)
            logging.info("PostgreSQL connection returned to pool.")
    return (None, None)

# Additional endpoints can be added here (e.g., for data retrieval)