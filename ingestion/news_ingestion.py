import requests
import os
import json
import time
import logging
from kafka import KafkaProducer

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
if not NEWS_API_KEY:
    logger.error("Google News API Key is not set. Please check your environment variables.")
    raise ValueError("Google News API Key is not set. Please check your environment variables.")

NEWS_TOPIC = os.getenv("NEWS_TOPIC", "supply chain disruptions")
KAFKA_TOPIC = os.getenv("NEWS_TOPIC", "news_data")
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")
FETCH_INTERVAL = int(os.getenv("NEWS_FETCH_INTERVAL", 3600))  # Default to 1 hour

logger.info("Environment variables loaded successfully.")

def fetch_news_data():
    """Fetch news data from the News API."""
    try:
        logger.info(f"Fetching news data for topic: {NEWS_TOPIC}")
        url = f"https://newsapi.org/v2/everything?q={NEWS_TOPIC}&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            logger.info("Successfully fetched news data.")
            return response.json()["articles"]
        else:
            logger.error(f"Error fetching news data: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Exception while fetching news data: {e}", exc_info=True)
        return []

def main():
    """Fetch news articles and send them to Kafka."""
    try:
        # Initialize Kafka producer
        logger.info("Initializing Kafka producer...")
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVER,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        logger.info("Kafka producer initialized successfully.")

        seen_articles = set()  # Track seen articles
        while True:
            try:
                articles = fetch_news_data()
                for article in articles:
                    if article["url"] not in seen_articles:
                        data = {
                            "title": article["title"],
                            "description": article["description"],
                            "url": article["url"],
                            "published_at": article["publishedAt"]
                        }
                        producer.send(KAFKA_TOPIC, data)
                        seen_articles.add(article["url"])
                        logger.info(f"Sent article to Kafka: {data}")
            except Exception as e:
                logger.error(f"Error processing news articles: {e}", exc_info=True)
            logger.info(f"Sleeping for {FETCH_INTERVAL} seconds before next fetch.")
            time.sleep(FETCH_INTERVAL)
    except Exception as e:
        logger.critical(f"Fatal error in main loop: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting news ingestion script...")
    main()
