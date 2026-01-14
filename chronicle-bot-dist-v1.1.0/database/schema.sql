-- Chronicle Bot Database Schema
-- PostgreSQL 14+

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    creator_id BIGINT NOT NULL,
    name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_status CHECK (status IN ('active', 'completed', 'abandoned'))
);

-- Participants table
CREATE TABLE IF NOT EXISTS participants (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, user_id)
);

-- Audio files table
CREATE TABLE IF NOT EXISTS audio_files (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    file_path TEXT NOT NULL,
    duration REAL,
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Transcription jobs table
CREATE TABLE IF NOT EXISTS transcription_jobs (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    audio_file_path TEXT NOT NULL,
    transcript_text TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    CONSTRAINT valid_transcription_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_sessions_guild_id ON sessions(guild_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_guild_status ON sessions(guild_id, status);
CREATE INDEX IF NOT EXISTS idx_participants_session ON participants(session_id);
CREATE INDEX IF NOT EXISTS idx_audio_files_session ON audio_files(session_id);
CREATE INDEX IF NOT EXISTS idx_transcription_jobs_session ON transcription_jobs(session_id);

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Verify tables created
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
