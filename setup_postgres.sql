-- Setup script for TerpSpark PostgreSQL database

-- Create user if not exists
DO
$$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'terpspark_user') THEN
    CREATE USER terpspark_user WITH PASSWORD 'terpspark_pass';
  END IF;
END
$$;

-- Create database if not exists
SELECT 'CREATE DATABASE terpspark_db OWNER terpspark_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'terpspark_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE terpspark_db TO terpspark_user;

-- Output success message
SELECT 'Database setup complete!' as status;

