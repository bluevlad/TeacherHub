CREATE TABLE IF NOT EXISTS reputation_data (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(100) NOT NULL,
    site_name VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(500) NOT NULL,
    sentiment VARCHAR(20),
    score DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
