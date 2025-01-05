-- weather_current table
CREATE TABLE IF NOT EXISTS weather_current (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    location VARCHAR(100) NOT NULL,
    temperature FLOAT,
    humidity FLOAT,
    weather_description VARCHAR(255),
    wind_speed FLOAT,
    precipitation FLOAT,
    UNIQUE (location, timestamp)
);

-- weather_historical table
CREATE TABLE IF NOT EXISTS weather_historical (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    location VARCHAR(100) NOT NULL,
    temperature FLOAT,
    humidity FLOAT,
    weather_description VARCHAR(255),
    wind_speed FLOAT,
    precipitation FLOAT,
    disruption BOOLEAN NOT NULL,
    UNIQUE (location, timestamp)
);

CREATE TABLE IF NOT EXISTS reddit_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    location VARCHAR(100) NOT NULL,
    sentiment_score FLOAT,
    mention_count INT,
    topic VARCHAR(100),
    UNIQUE (location, timestamp, topic)
);

CREATE TABLE IF NOT EXISTS news_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    location VARCHAR(100) NOT NULL,
    sentiment_score FLOAT,
    mention_count INT,
    topic VARCHAR(100),
    source_credibility FLOAT,
    UNIQUE (location, timestamp, topic)
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    location VARCHAR(100) NOT NULL,
    temperature FLOAT NOT NULL,
    humidity FLOAT NOT NULL,
    wind_speed FLOAT,
    precipitation FLOAT,
    reddit_sentiment FLOAT,
    reddit_mentions INT,
    reddit_topic VARCHAR(100),
    news_sentiment FLOAT,
    news_mentions INT,
    news_topic VARCHAR(100),
    news_source_credibility FLOAT,
    disruption_probability FLOAT NOT NULL
);
