#!/usr/bin/env python3
import os
import time
import json
import logging
import requests
from kafka import KafkaProducer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables once at the top
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_SEARCH_QUERY = os.getenv("NEWS_SEARCH_QUERY")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "news_data")
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")
WEATHER_TOPIC = os.getenv("WEATHER_TOPIC", "weather_data")
REDDIT_TOPIC = os.getenv("REDDIT_TOPIC", "reddit_data")  # if applicable

def init_kafka_producer():
    """
    Initialize and return a KafkaProducer instance.
    """
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    logging.info("Kafka producer initialized successfully.")
    return producer

def fetch_news():
    """
    Fetch news articles from NewsAPI.
    """
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": NEWS_SEARCH_QUERY,
        "apiKey": NEWS_API_KEY,
        "language": "en",
        "pageSize": 10
    }
    logging.info("Making NewsAPI request for query: '%s'", NEWS_SEARCH_QUERY)
    logging.info("Making request to: %s with parameters: %s", url, json.dumps(params))
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
        data = response.json()
        articles = data.get("articles", [])
        logging.info("Found %d articles", len(articles))
        return articles
    else:
        logging.error("Failed to fetch news articles, status code: %s", response.status_code)
        return []

def fetch_weather():
    """
    Fetch weather data for a fixed location.
    """
    # Example using OpenWeatherMap API; assumes WEATHER_API_KEY is set
    weather_api_key = os.getenv("WEATHER_API_KEY")
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": "New York",
        "appid": weather_api_key,
        "units": "metric"
    }
    logging.info("Fetching weather data for location: New York")
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
        logging.info("Successfully fetched weather data.")
        return response.json()
    else:
        logging.error("Failed to fetch weather data, status code: %s", response.status_code)
        return {}

def fetch_reddit_posts():
    """
    Stub for fetching Reddit posts.
    Replace this with your actual Reddit ingestion code.
    """
    logging.info("Fetching posts from subreddits: supplychain, PrepperIntel, Shortages")
    # Actual implementation would use a Reddit API client like PRAW.
    # For now, we'll return an empty list.
    return []

def publish_message(producer, topic, message):
    """
    Publish a message to the given Kafka topic.
    """
    producer.send(topic, value=message)
    producer.flush()
    # Print the title if it exists, otherwise a generic label.
    logging.info("Published to topic '%s': %s", topic, message.get("title", "No Title"))

def run_news_ingestion(producer):
    """
    Run a complete news ingestion cycle.
    """
    articles = fetch_news()
    if articles:
        for article in articles:
            publish_message(producer, KAFKA_TOPIC, article)
    else:
        logging.warning("No news articles fetched.")

def run_weather_ingestion(producer):
    """
    Run a weather data fetch-and-publish cycle.
    """
    weather_data = fetch_weather()
    if weather_data:
        producer.send(WEATHER_TOPIC, value=weather_data)
        producer.flush()
        logging.info("Sent weather data to Kafka.")
    else:
        logging.warning("No weather data fetched.")

def run_reddit_ingestion(producer):
    """
    Run a Reddit posts ingestion cycle.
    """
    posts = fetch_reddit_posts()
    if posts:
        for post in posts:
            publish_message(producer, REDDIT_TOPIC, post)
    else:
        logging.info("No Reddit posts fetched.")

def main():
    logging.info("=== Starting news ingestion service ===")
    producer = init_kafka_producer()
    
    # The following cycles preserve the sleep intervals seen in your logs.
    while True:
        logging.info("=== Starting news fetch cycle ===")
        run_news_ingestion(producer)
        logging.info("Sleeping for 3600 seconds before next news fetch.")
        time.sleep(3600)  # Sleep for 1 hour before next news fetch

        logging.info("=== Starting weather fetch cycle ===")
        run_weather_ingestion(producer)
        logging.info("Sleeping for 300 seconds before next weather fetch.")
        time.sleep(300)

        logging.info("=== Starting Reddit fetch cycle ===")
        run_reddit_ingestion(producer)
        logging.info("Sleeping for 300 seconds before next Reddit fetch.")
        time.sleep(300)

if __name__ == "__main__":
    main() 