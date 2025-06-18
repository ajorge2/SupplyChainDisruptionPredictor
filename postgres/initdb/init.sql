-- Create risk_scores table
CREATE TABLE IF NOT EXISTS risk_scores (
    id SERIAL PRIMARY KEY,
    material VARCHAR(100),
    location VARCHAR(100),
    timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(material, location, timestamp)
);

-- Create mentions table for storing material/location mentions from various sources
CREATE TABLE IF NOT EXISTS mentions (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- 'news', 'social_media', 'weather'
    material VARCHAR(100),
    location VARCHAR(100),
    content TEXT,  -- The actual text content where the mention was found
    url TEXT,      -- URL of the source (if applicable)
    published_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB  -- Additional source-specific metadata
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_mentions_source ON mentions(source);
CREATE INDEX IF NOT EXISTS idx_mentions_material ON mentions(material);
CREATE INDEX IF NOT EXISTS idx_mentions_location ON mentions(location);
CREATE INDEX IF NOT EXISTS idx_mentions_published_at ON mentions(published_at);
