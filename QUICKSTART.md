# TerpSpark Backend - Quick Start Guide

## 🚀 5-Minute Setup

### Option 1: Docker (Recommended)

```bash
# 1. Create environment file
cp .env.example .env

# 2. Start services
docker-compose up -d

# 3. Initialize database (in a new terminal)
docker-compose exec api python app/utils/init_db.py

# 4. Access API
open http://localhost:8000/docs
```

### Option 2: Local Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup PostgreSQL
createdb terpspark_db

# 3. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 4. Run migrations
alembic upgrade head

# 5. Initialize sample data
python app/utils/init_db.py

# 6. Start server
uvicorn main:app --reload
```

## 🔐 Test Credentials

After running `init_db.py`, use these credentials:

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@umd.edu | admin123 |
| **Organizer** | organizer@umd.edu | organizer123 |
| **Student** | student@umd.edu | student123 |

## 📝 Quick API Test

### 1. Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@umd.edu",
    "password": "student123"
  }'
```

### 2. Get User Info

```bash
# Replace {TOKEN} with the token from login response
curl -X GET http://localhost:8000/api/auth/user \
  -H "Authorization: Bearer {TOKEN}"
```

## 📚 API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🏗️ Project Structure

```
app/
├── api/          # Route handlers
├── core/         # Config, database, security
├── middleware/   # Auth & RBAC
├── models/       # Database models
├── repositories/ # Data access layer
├── schemas/      # Request/response schemas
├── services/     # Business logic
└── utils/        # Utilities
```

## 🔧 Common Tasks

```bash
# Run tests
pytest

# Format code
black app/

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🎯 Next Steps

1. ✅ Complete Phase 1 (Authentication) - **DONE**
2. 📋 Phase 2: Event Discovery & Browse
3. 🎫 Phase 3: Student Registration Flow
4. 🎪 Phase 4: Organizer Event Management
5. ⚙️ Phase 5: Admin Console & Management
6. ✔️ Phase 6: Check-in & Notifications

## 🐛 Troubleshooting

**Database Connection Error:**
```bash
# Check PostgreSQL is running
pg_isready

# Verify DATABASE_URL in .env
echo $DATABASE_URL
```

**Port 8000 Already in Use:**
```bash
# Change port in main.py or use:
uvicorn main:app --port 8001
```

**Import Errors:**
```bash
# Ensure you're in the right directory
cd terpspark-backend

# Reinstall dependencies
pip install -r requirements.txt
```

## 📞 Need Help?

- Check the full [README.md](README.md)
- Review [API Documentation](docs/API_SPEC.md)
- Create an issue on GitHub

---

**Ready to code?** Start with `uvicorn main:app --reload` 🚀
