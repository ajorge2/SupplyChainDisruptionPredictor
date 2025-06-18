import os
import json
import time
import praw
import logging
from kafka import KafkaProducer
from material_location_extractor import create_material_location_map, find_material_location_mentions

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "SupplyChainDisruptionPredictor/0.1")
if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
    logger.error("Reddit API Keys are not set. Please check your environment variables.")
    raise ValueError("Reddit API Keys are not set. Please check your environment variables.")

REDDIT_SUBREDDITS = os.getenv("REDDIT_SUBREDDITS", "supplychain,logistics").split(",")
KAFKA_TOPIC = os.getenv("SOCIAL_MEDIA_TOPIC", "social_media_data")
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")
FETCH_INTERVAL = int(os.getenv("REDDIT_FETCH_INTERVAL", 300))  # Default: 5 minutes

logger.info("Environment variables loaded successfully.")

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

def main():
    """Fetch Reddit posts and send them to Kafka."""
    try:
        # Initialize Reddit client
        logger.info("Initializing Reddit client...")
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        logger.info("Reddit client initialized successfully.")

        # Initialize Kafka producer
        logger.info("Initializing Kafka producer...")
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVER,
            value_serializer=lambda v: json.dumps(v).encode("utf-8")
        )
        logger.info("Kafka producer initialized successfully.")

        seen_posts = set()  # Track seen posts
        while True:
            for subreddit_name in REDDIT_SUBREDDITS:
                try:
                    logger.info(f"Fetching posts from subreddit: {subreddit_name}")
                    subreddit = reddit.subreddit(subreddit_name)
                    for submission in subreddit.new(limit=10):
                        if submission.id not in seen_posts:
                            post_text = f"{submission.title} {submission.selftext}"
                            mentions = find_material_location_mentions(post_text, material_locations)
                            if mentions:
                                logger.info(f"Found {len(mentions)} material/location mentions in post")
                                for material, location in mentions:
                                    data = {
                                        "subreddit": subreddit_name,
                                        "title": submission.title,
                                        "created_utc": submission.created_utc,
                                        "url": submission.url,
                                        "content": submission.selftext,
                                        "material": material,
                                        "location": location
                                    }
                                    producer.send(KAFKA_TOPIC, data)
                                    logger.info(f"Sent post to Kafka: {material or 'N/A'} - {location or 'N/A'}")
                                seen_posts.add(submission.id)
                            else:
                                logger.info("No material/location mentions found in post")
                except Exception as e:
                    logger.error(f"Error fetching posts from {subreddit_name}: {e}")
            logger.info(f"Sleeping for {FETCH_INTERVAL} seconds before next fetch.")
            time.sleep(FETCH_INTERVAL)
    except Exception as e:
        logger.critical(f"Fatal error in main loop: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting social media ingestion script...")
    main()
