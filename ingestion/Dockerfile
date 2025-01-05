FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add wait-for-it.sh for delay handling
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Copy source code
COPY . .

# Command to run ingestion script
CMD ["/wait-for-it.sh", "kafka:9092", "--", "sh", "-c", "python weather_ingestion.py & python social_media_ingestion.py & python news_ingestion.py"]
