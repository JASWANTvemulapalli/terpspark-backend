# TerpSpark API Quick Reference

**Base URL**: `http://127.0.0.1:8000`

## 🔐 Authentication Endpoints

### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "student@umd.edu",
  "password": "password123",
  "name": "Student Name",
  "role": "student",
  "department": "Computer Science"
}
```

### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "student@umd.edu",
  "password": "student123"
}
```
**Response**: Returns `{ token: "JWT_TOKEN", user: {...} }`

### Get Current User
```http
GET /api/auth/user
Authorization: Bearer YOUR_JWT_TOKEN
```

### Validate Token
```http
GET /api/auth/validate
Authorization: Bearer YOUR_JWT_TOKEN
```

### Logout
```http
POST /api/auth/logout
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## 📅 Event Endpoints

### List All Events
```http
GET /api/events
```

### List Events with Filters
```http
GET /api/events?category=technology&sortBy=popularity&page=1&limit=20
```

**Available Query Parameters:**
- `search` - Search term (title, description, tags, venue)
- `category` - Category slug (technology, sports, career, etc.)
- `startDate` - YYYY-MM-DD (events after this date)
- `endDate` - YYYY-MM-DD (events before this date)
- `organizer` - Organizer name
- `availability` - true/false (show only available events)
- `sortBy` - date | title | popularity
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 20, max: 100)

### Get Event Details
```http
GET /api/events/{event_id}
```

### Get Categories
```http
GET /api/categories
```

### Get Venues
```http
GET /api/venues
```

---

## 🎨 Category Slugs

Use these slugs for filtering events:
- `academic` - Academic events 📚
- `career` - Career fairs 💼
- `cultural` - Cultural events 🌍
- `sports` - Sports events ⚽
- `arts` - Arts events 🎨
- `technology` - Tech events 💻
- `wellness` - Wellness events 🧘
- `environmental` - Environmental events 🌱

---

## 🧪 Test Credentials

### Admin
- Email: `admin@umd.edu`
- Password: `admin123`

### Organizers
- `organizer@umd.edu` / `organizer123`
- `techclub@umd.edu` / `organizer123`
- `sportsclub@umd.edu` / `organizer123`
- `artscenter@umd.edu` / `organizer123`

### Students
- `student@umd.edu` / `student123`
- `jane.smith@umd.edu` / `student123`
- `mike.wilson@umd.edu` / `student123`

---

## 📊 Sample Event Data

The database includes 5 published events:

1. **AI & Machine Learning Workshop**
   - Category: Technology
   - Date: Dec 2, 2025
   - Capacity: 100 (75 registered)
   - Featured: Yes

2. **Spring Career Fair 2025**
   - Category: Career
   - Date: Dec 9, 2025
   - Capacity: 500 (450 registered)
   - Featured: Yes

3. **International Food Festival**
   - Category: Cultural
   - Date: Dec 16, 2025
   - Capacity: 1000 (350 registered)
   - Featured: Yes

4. **Basketball Tournament Finals**
   - Category: Sports
   - Date: Dec 5, 2025
   - Capacity: 200 (180 registered)

5. **Mindfulness & Meditation**
   - Category: Wellness
   - Date: Nov 30, 2025
   - Capacity: 50 (45 registered)

---

## 💡 Example Workflows

### 1. Browse Events as Guest
```bash
# Get all events
curl http://127.0.0.1:8000/api/events

# Filter technology events
curl http://127.0.0.1:8000/api/events?category=technology

# Search for basketball
curl "http://127.0.0.1:8000/api/events?search=basketball"

# Get event details
curl http://127.0.0.1:8000/api/events/{event_id}
```

### 2. Register and Login as Student
```bash
# Register
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newstudent@umd.edu",
    "password": "password123",
    "name": "New Student"
  }'

# Login (if already registered)
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@umd.edu",
    "password": "student123"
  }'

# Save the token from response
TOKEN="your_jwt_token_here"

# Get current user info
curl http://127.0.0.1:8000/api/auth/user \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Search and Filter Events
```bash
# Events in December 2025
curl "http://127.0.0.1:8000/api/events?startDate=2025-12-01&endDate=2025-12-31"

# Technology events sorted by popularity
curl "http://127.0.0.1:8000/api/events?category=technology&sortBy=popularity"

# Events with available spots
curl "http://127.0.0.1:8000/api/events?availability=true"

# Search with pagination
curl "http://127.0.0.1:8000/api/events?search=workshop&page=1&limit=10"
```

---

## ⚡ Quick Start

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies (if not done)
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# 4. Initialize database with sample data
PYTHONPATH=. python app/utils/init_db.py

# 5. Start the server
python -m uvicorn main:app --reload --port 8000

# 6. Visit API docs
# Open http://127.0.0.1:8000/docs in your browser

# 7. Test endpoints
curl http://127.0.0.1:8000/api/events
curl http://127.0.0.1:8000/api/categories
```

---

## 🌟 Key Features

- ✅ **8 Data Models** - Fully implemented with relationships
- ✅ **8 Repositories** - Clean data access layer
- ✅ **7 Schema Files** - Comprehensive request/response validation
- ✅ **2 Service Layers** - Auth & Event business logic
- ✅ **10 API Endpoints** - Phase 1 & 2 complete
- ✅ **Role-Based Access** - Student, Organizer, Admin roles
- ✅ **Advanced Search** - Multi-field search & filtering
- ✅ **Pagination** - Efficient data retrieval
- ✅ **Auto Documentation** - Swagger UI & ReDoc
- ✅ **Sample Data** - Ready-to-use test data

---

## 📱 Response Format

All API responses follow a consistent format:

**Success Response:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": { ... }
}
```

---

## 🔍 Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `422 Unprocessable Entity` - Validation failed
- `500 Internal Server Error` - Server error

---

**Happy Coding! 🚀**

