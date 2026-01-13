-- RPG Transcription Bot Database Schema

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    creator_id BIGINT NOT NULL,
    name TEXT,
    status VARCHAR(20) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_guild ON sessions(guild_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);

-- Participants table
CREATE TABLE IF NOT EXISTS participants (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    discord_user_id BIGINT NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, discord_user_id)
);

-- Audio files table
CREATE TABLE IF NOT EXISTS audio_files (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    discord_user_id BIGINT NOT NULL,
    file_path TEXT NOT NULL,
    duration_seconds FLOAT,
    size_bytes BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audio_files_session ON audio_files(session_id);

-- Transcription jobs table (NEW)
CREATE TABLE IF NOT EXISTS transcription_jobs (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    audio_file_id INTEGER REFERENCES audio_files(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    provider VARCHAR(50),
    transcript_text TEXT,
    confidence FLOAT,
    processing_time FLOAT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transcription_jobs_session ON transcription_jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_transcription_jobs_status ON transcription_jobs(status);