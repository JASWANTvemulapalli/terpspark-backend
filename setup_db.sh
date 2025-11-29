#!/bin/bash
# Setup PostgreSQL database and user for TerpSpark

echo "🔧 Setting up PostgreSQL database..."

# Create user (will fail if exists, that's OK)
createuser terpspark_user 2>/dev/null || echo "  ℹ️  User terpspark_user already exists"

# Create database
createdb terpspark_db -O terpspark_user 2>/dev/null || echo "  ℹ️  Database terpspark_db already exists"

# Set password for user
psql postgres -c "ALTER USER terpspark_user WITH PASSWORD 'terpspark_pass';" 2>/dev/null

echo "✅ Database setup complete!"
echo ""
echo "Database Details:"
echo "  Database: terpspark_db"
echo "  User: terpspark_user"
echo "  Password: terpspark_pass"
echo "  Port: 5432"
echo ""
echo "Connection String:"
echo "  postgresql://terpspark_user:terpspark_pass@localhost:5432/terpspark_db"

