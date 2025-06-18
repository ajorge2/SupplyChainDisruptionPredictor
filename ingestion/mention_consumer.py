import os
import json
import logging
import psycopg2
from kafka import KafkaConsumer
from datetime import datetime
from psycopg2.extras import Json
import redis

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "supplychaindb")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def store_mention(conn, data, source):
    """Store a mention in the database."""
    try:
        with conn.cursor() as cur:
            # Extract common fields
            material = data.get('material')
            location = data.get('location')
            url = data.get('url')
            published_at = data.get('published_at')
            
            # Get content based on source
            if source == 'news':
                content = f"{data.get('title', '')} {data.get('description', '')}"
            elif source == 'social_media':
                content = f"{data.get('title', '')} {data.get('content', '')}"
            else:  # weather
                content = json.dumps(data)
            
            # Store in mentions table
            cur.execute("""
                INSERT INTO mentions 
                (source, material, location, url, published_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                source,
                material,
                location,
                url,
                published_at,
                Json(data)  # Store full data as metadata
            ))
            
            conn.commit()
            logger.info(f"Stored mention: {material or 'N/A'} - {location or 'N/A'} from {source}")
            
            # Push to Redis (keep only 500 most recent)
            redis_client.lpush('recent_mentions', json.dumps(data))
            redis_client.ltrim('recent_mentions', 0, 499)
            
    except Exception as e:
        logger.error(f"Error storing mention: {e}")
        conn.rollback()

def main():
    """Main consumer loop."""
    try:
        # Initialize Kafka consumers
        consumers = {
            'news': KafkaConsumer(
                'news_data',
                bootstrap_servers=KAFKA_SERVER,
                auto_offset_reset='latest',
                enable_auto_commit=True
            ),
            'social_media': KafkaConsumer(
                'social_media_data',
                bootstrap_servers=KAFKA_SERVER,
                auto_offset_reset='latest',
                enable_auto_commit=True
            ),
            'weather': KafkaConsumer(
                'weather_data',
                bootstrap_servers=KAFKA_SERVER,
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
        }
        
        # Initialize database connection
        conn = get_db_connection()
        logger.info("Database connection established")
        
        while True:
            for source, consumer in consumers.items():
                try:
                    # Poll for messages
                    messages = consumer.poll(timeout_ms=100)
                    
                    for message_set in messages.values():
                        for message in message_set:
                            try:
                                # Parse message
                                data = json.loads(message.value.decode('utf-8'))
                                
                                # Store mention
                                store_mention(conn, data, source)
                                
                            except json.JSONDecodeError as e:
                                logger.error(f"Error decoding message: {e}")
                            except Exception as e:
                                logger.error(f"Error processing message: {e}")
                                
                except Exception as e:
                    logger.error(f"Error polling {source} consumer: {e}")
                    
    except Exception as e:
        logger.critical(f"Fatal error in main loop: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    logger.info("Starting mention consumer...")
    main() 