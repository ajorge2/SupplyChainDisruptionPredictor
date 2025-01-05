import os
import requests
import json
import time
import logging
from kafka import KafkaProducer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    logger.error("OpenWeather API Key is not set. Please check your environment variables.")
    raise ValueError("OpenWeather API Key is not set. Please check your environment variables.")

LOCATION = os.getenv("WEATHER_LOCATION", "New York")
KAFKA_TOPIC = os.getenv("WEATHER_TOPIC", "weather_data")
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")

logger.info("Environment variables loaded successfully.")

def fetch_weather_data():
    """Fetch weather data from the OpenWeather API."""
    try:
        logger.info(f"Fetching weather data for location: {LOCATION}")
        url = f"http://api.openweathermap.org/data/2.5/weather?q={LOCATION}&appid={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        logger.info("Successfully fetched weather data.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {e}", exc_info=True)
        return None

def main():
    """Fetch weather data and send it to Kafka."""
    try:
        # Initialize Kafka producer
        logger.info("Initializing Kafka producer...")
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVER,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        logger.info("Kafka producer initialized successfully.")

        while True:
            try:
                data = fetch_weather_data()
                if data:
                    producer.send(KAFKA_TOPIC, data)
                    logger.info(f"Sent weather data to Kafka: {data}")
                else:
                    logger.warning("No weather data to send.")
            except Exception as e:
                logger.error(f"Error sending weather data: {e}", exc_info=True)
            logger.info("Sleeping for 300 seconds before the next fetch.")
            time.sleep(300)
    except Exception as e:
        logger.critical(f"Fatal error in main loop: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting weather ingestion script...")
    main()
