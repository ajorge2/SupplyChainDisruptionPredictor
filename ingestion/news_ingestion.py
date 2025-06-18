import requests
import os
import json
import time
import logging
from kafka import KafkaProducer
from time import sleep
from datetime import datetime, timedelta
from material_location_extractor import create_material_location_map, find_material_location_mentions

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_SEARCH_QUERY = os.getenv("NEWS_SEARCH_QUERY", "supply chain disruption")  # What to search for
KAFKA_TOPIC = os.getenv("NEWS_TOPIC", "news_data")  # Where to send the data
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")
FETCH_INTERVAL = int(os.getenv("NEWS_FETCH_INTERVAL", 3600))  # Default to 1 hour

# Load materials data
def load_materials_data():
    try:
        with open('/app/products.json', 'r') as f:
            data = json.load(f)
        return data  # Return the whole object
    except Exception as e:
        logger.error(f"Error loading materials data: {e}")
        return {}

# Initialize materials data
materials_data = load_materials_data()
material_locations = create_material_location_map(materials_data)

logger.info(f"Loaded {len(material_locations)} materials with their locations")

# Initialize Kafka producer at module level
logger.info("Initializing Kafka producer...")
producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)
logger.info("Kafka producer initialized successfully.")

logger.info("Current environment variables:")
logger.info(f"NEWS_API_KEY (length): {len(NEWS_API_KEY) if NEWS_API_KEY else 0}")
logger.info(f"NEWS_SEARCH_QUERY: {NEWS_SEARCH_QUERY}")
logger.info(f"KAFKA_TOPIC: {KAFKA_TOPIC}")
logger.info(f"KAFKA_SERVER: {KAFKA_SERVER}")

def fetch_news():
    try:
        logger.info("\n=== Starting NewsAPI Request ===")
        
        # Check API key
        if not NEWS_API_KEY:
            logger.error("NEWS_API_KEY is missing!")
            return []
            
        logger.info(f"API Key length: {len(NEWS_API_KEY)}")
        logger.info(f"Search query: '{NEWS_SEARCH_QUERY}'")
        
        # Build request
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': NEWS_SEARCH_QUERY,
            'apiKey': NEWS_API_KEY,
            'language': 'en',
            'pageSize': 10
        }
        
        # Log request details (safely)
        safe_params = params.copy()
        safe_params['apiKey'] = 'HIDDEN'
        logger.info(f"Making request to: {url}")
        logger.info(f"With parameters: {json.dumps(safe_params, indent=2)}")
        
        # Make request with error handling
        try:
            response = requests.get(url, params=params, timeout=10)
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"NewsAPI request failed!")
                logger.error(f"Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return []
                
            # Parse response
            data = response.json()
            logger.info(f"Response status: {data.get('status')}")
            
            if data.get('status') != 'ok':
                logger.error("NewsAPI returned error:")
                logger.error(json.dumps(data, indent=2))
                return []
                
            articles = data.get('articles', [])
            logger.info(f"Found {len(articles)} articles")
            
            if articles:
                logger.info("First article preview:")
                preview = articles[0]
                logger.info(f"- Title: {preview.get('title')}")
                logger.info(f"- Source: {preview.get('source', {}).get('name')}")
                logger.info(f"- Published: {preview.get('publishedAt')}")
            
            return articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed:")
            logger.error(f"- Error type: {type(e).__name__}")
            logger.error(f"- Error message: {str(e)}")
            return []
            
    except Exception as e:
        logger.error("Unexpected error in fetch_news:")
        logger.error(f"- Error type: {type(e).__name__}")
        logger.error(f"- Error message: {str(e)}")
        logger.error("- Traceback:", exc_info=True)
        return []

def main():
    """Fetch news articles and send them to Kafka."""
    try:
        logger.info("=== Starting news ingestion service ===")
        seen_articles = set()
        
        while True:
            try:
                logger.info("\n=== Starting news fetch cycle ===")
                logger.info(f"Making NewsAPI request for query: '{NEWS_SEARCH_QUERY}'")
                
                articles = fetch_news()
                
                if articles:
                    logger.info(f"Processing {len(articles)} articles...")
                    for article in articles:
                        if article["url"] not in seen_articles:
                            # Combine title and description for text analysis
                            article_text = f"{article['title']} {article.get('description', '')}"
                            
                            # Find material and location mentions
                            mentions = find_material_location_mentions(article_text, material_locations)
                            
                            if mentions:
                                logger.info(f"Found {len(mentions)} material/location mentions in article")
                                for material, location in mentions:
                                    data = {
                                        "source": "news",
                                        "title": article["title"],
                                        "description": article.get("description", ""),
                                        "url": article["url"],
                                        "published_at": article["publishedAt"],
                                        "material": material,
                                        "location": location
                                    }
                                    producer.send(KAFKA_TOPIC, data)
                                    logger.info(f"Sent to Kafka: {material or 'N/A'} - {location or 'N/A'}")
                            else:
                                logger.info("No material/location mentions found in article")
                            
                            seen_articles.add(article["url"])
                else:
                    logger.warning(f"No new articles found for query: '{NEWS_SEARCH_QUERY}'")
                    
            except Exception as e:
                logger.error(f"Error processing news articles:")
                logger.error(f"- Error type: {type(e).__name__}")
                logger.error(f"- Error message: {str(e)}")
                logger.error("- Traceback:", exc_info=True)
                
            logger.info(f"Sleeping for {FETCH_INTERVAL} seconds...")
            sleep(FETCH_INTERVAL)
            
    except Exception as e:
        logger.critical(f"Fatal error in main loop:")
        logger.critical(f"- Error type: {type(e).__name__}")
        logger.critical(f"- Error message: {str(e)}")
        logger.critical("- Traceback:", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting news ingestion service...")
    main()
