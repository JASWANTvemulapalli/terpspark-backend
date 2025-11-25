# 📦 Moving TerpSpark Backend to Your Project

## Current Location
The backend code is currently in: `/home/claude/terpspark-backend/`

## Target Location
You want it in: `/Users/ishaanbajpai/desktop/course_work/613/final-project/backend/`

## 🚀 Quick Migration Steps

### Option 1: Direct Copy (Simplest)

```bash
# 1. Navigate to your project root
cd /Users/ishaanbajpai/desktop/course_work/613/final-project/

# 2. Create backend directory if it doesn't exist
mkdir -p backend

# 3. Copy all files from the delivered backend
# (You'll need to manually copy from /home/claude/terpspark-backend/)
# Or use the file browser to copy the entire terpspark-backend folder

# 4. Rename if needed
mv terpspark-backend backend
# or copy contents into existing backend folder
```

### Option 2: Git Integration (Recommended)

```bash
# 1. Initialize git in the delivered backend (if not already)
cd /home/claude/terpspark-backend
git init
git add .
git commit -m "Initial backend setup - Phase 1 complete"

# 2. In your actual project directory
cd /Users/ishaanbajpai/desktop/course_work/613/final-project/

# 3. If you have existing git repo
# Option A: Add as subdirectory
cp -r /home/claude/terpspark-backend ./backend

# Option B: Use git subtree
git subtree add --prefix=backend /home/claude/terpspark-backend main --squash
```

## 📁 Expected Final Structure

```
/Users/ishaanbajpai/desktop/course_work/613/final-project/
├── frontend/
│   └── terpspark-frontend/
│       ├── src/
│       ├── public/
│       └── package.json
│
└── backend/                    # ← Your new backend
    ├── app/
    │   ├── api/
    │   ├── core/
    │   ├── middleware/
    │   ├── models/
    │   ├── repositories/
    │   ├── schemas/
    │   ├── services/
    │   └── utils/
    ├── alembic/
    ├── tests/
    ├── main.py
    ├── requirements.txt
    ├── docker-compose.yml
    ├── .env
    └── README.md
```

## ⚙️ Post-Migration Setup

### 1. Update Environment Variables

```bash
cd /Users/ishaanbajpai/desktop/course_work/613/final-project/backend

# Edit .env file
nano .env
# or
code .env
```

Update these values if needed:
```env
# Database - adjust if you have different credentials
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/terpspark_db

# CORS - add your frontend URL
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# JWT Secret - CHANGE THIS!
JWT_SECRET_KEY=<generate-a-new-random-32+-character-key>
```

### 2. Setup Virtual Environment

```bash
cd /Users/ishaanbajpai/desktop/course_work/613/final-project/backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Mac/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Database

#### Option A: Using Docker (Easiest)
```bash
# Start PostgreSQL with Docker
docker-compose up -d db

# Wait for it to be ready
docker-compose logs -f db
```

#### Option B: Local PostgreSQL
```bash
# Create database
createdb terpspark_db

# Or using psql
psql -U postgres
CREATE DATABASE terpspark_db;
CREATE USER terpspark_user WITH PASSWORD 'terpspark_pass';
GRANT ALL PRIVILEGES ON DATABASE terpspark_db TO terpspark_user;
\q
```

### 4. Run Migrations

```bash
# Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Verify
alembic current
```

### 5. Initialize Sample Data

```bash
python app/utils/init_db.py
```

Expected output:
```
🔧 Initializing database...
✅ Database tables created
📝 Creating sample users...
✅ Created admin: admin@umd.edu / admin123
✅ Created organizer: organizer@umd.edu / organizer123
✅ Created student: student@umd.edu / student123
✅ Created pending organizer: pending@umd.edu / pending123
🎉 Database initialization complete!
```

### 6. Start the Server

```bash
# Development mode
uvicorn main:app --reload

# Or using Make
make dev

# Or using Docker
docker-compose up -d
```

### 7. Verify It's Working

```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","service":"TerpSpark","version":"1.0.0"}
```

Open in browser:
- http://localhost:8000 - API info
- http://localhost:8000/docs - Swagger UI
- http://localhost:8000/redoc - ReDoc

### 8. Test Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@umd.edu",
    "password": "student123"
  }'
```

Should return a JWT token and user info.

## 🔧 Integration with Frontend

### Update Frontend API URL

In your frontend code (likely in `terpspark-frontend/src/config` or similar):

```javascript
// config/api.js or similar
export const API_BASE_URL = 'http://localhost:8000';

// or use environment variable
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

### CORS Setup

Ensure your backend .env includes your frontend URL:
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Example Frontend API Call

```javascript
// Login example
const login = async (email, password) => {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  const data = await response.json();
  
  if (data.success) {
    // Store token
    localStorage.setItem('token', data.token);
    return data.user;
  }
  
  throw new Error(data.error);
};

// Authenticated request example
const getUserInfo = async () => {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:8000/api/auth/user', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  
  return response.json();
};
```

## 📝 Checklist After Migration

- [ ] Backend code copied to correct location
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] .env file created and configured
- [ ] PostgreSQL database created
- [ ] Migrations run (`alembic upgrade head`)
- [ ] Sample data initialized (`python app/utils/init_db.py`)
- [ ] Server starts successfully (`uvicorn main:app --reload`)
- [ ] Health check works (`curl http://localhost:8000/health`)
- [ ] Can login with test credentials
- [ ] Swagger UI accessible at `/docs`
- [ ] Frontend can communicate with backend

## 🐛 Common Issues After Migration

### Issue: Module not found
```bash
# Solution: Ensure you're in the right directory
cd /Users/ishaanbajpai/desktop/course_work/613/final-project/backend
pip install -r requirements.txt
```

### Issue: Database connection error
```bash
# Solution: Check PostgreSQL is running
pg_isready

# Check DATABASE_URL in .env is correct
echo $DATABASE_URL
```

### Issue: Port 8000 already in use
```bash
# Solution: Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn main:app --reload --port 8001
```

### Issue: CORS errors in frontend
```bash
# Solution: Update CORS_ORIGINS in .env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Restart backend
```

### Issue: Alembic can't find models
```bash
# Solution: Ensure models are imported in alembic/env.py
# Check line: from app.models import *
```

## 🎯 Next Steps After Migration

1. **Verify Everything Works**
   - Run tests: `pytest`
   - Test all auth endpoints
   - Check database connections

2. **Connect Frontend**
   - Update API URLs in frontend
   - Test login flow
   - Ensure CORS is working

3. **Start Phase 2 Development**
   - Review Phase 2 requirements
   - Create Event models
   - Build Event API endpoints

4. **Setup Git (if not already)**
   ```bash
   cd /Users/ishaanbajpai/desktop/course_work/613/final-project/backend
   git init
   git add .
   git commit -m "Initial backend setup - Phase 1"
   ```

## 📚 Documentation References

After migration, these docs will be available in your backend folder:

- `README.md` - Complete setup and API documentation
- `QUICKSTART.md` - Quick start guide
- `ARCHITECTURE.md` - Architecture patterns
- `PROJECT_SUMMARY.md` - Current status and roadmap
- `DELIVERY.md` - This complete package info

## 🎉 You're Ready!

Once migration is complete:
1. Backend runs at `http://localhost:8000`
2. Frontend runs at `http://localhost:3000` (or 5173)
3. Both can communicate via REST API
4. Authentication works end-to-end

**Start building Phase 2! 🚀**
