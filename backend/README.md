# EduRPG Backend Server

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Setup Instructions

### Windows

1. **Install Python and pip** (if not already installed):
   - Download Python from https://python.org
   - During installation, check "Add Python to PATH"
   - pip comes bundled with Python

2. **Setup and run**:
   ```batch
   # Navigate to backend directory
   cd backend

   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   venv\Scripts\activate

   # Install dependencies
   pip install -r requirements-dev.txt

   # Run the server
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Or simply run:
   ```batch
   start_server.bat
   ```

### Linux/macOS

1. **Install Python and pip**:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-venv

   # macOS (with Homebrew)
   brew install python3
   ```

2. **Setup and run**:
   ```bash
   # Navigate to backend directory
   cd backend

   # Create virtual environment
   python3 -m venv venv

   # Activate virtual environment
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements-dev.txt

   # Run the server
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Or simply run:
   ```bash
   chmod +x start_server.sh
   ./start_server.sh
   ```

### WSL (Windows Subsystem for Linux)

If you're using WSL without pip installed:

1. **Install pip manually**:
   ```bash
   # Download get-pip.py
   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
   
   # Install pip
   python3 get-pip.py --user
   
   # Add to PATH (add to ~/.bashrc for permanent)
   export PATH=$PATH:~/.local/bin
   ```

2. **Then follow Linux setup instructions above**

## API Endpoints

Once the server is running, you can access:

- **API Documentation**: http://localhost:8000/docs
- **Alternative API Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Root Endpoint**: http://localhost:8000/

## Available APIs

### Main Application (`app.main:app`)
- Full EduRPG platform with authentication, quests, mentoring, etc.
- Database: SQLite (edurpg.db)
- API prefix: `/api/v1`

### Mock Server (`main:app`)
- Simple mock API for testing
- In-memory storage
- Basic CRUD operations for users, products, orders

## Testing the API

### Using curl:
```bash
# Health check
curl http://localhost:8000/health

# Get root info
curl http://localhost:8000/

# Create a user (mock server)
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com"}'
```

### Using the Interactive Documentation:
1. Navigate to http://localhost:8000/docs
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"

## Environment Variables

The application uses the following environment variables (configured in `.env`):

- `DEBUG`: Enable debug mode (default: True)
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key
- `BACKEND_CORS_ORIGINS`: Allowed CORS origins

## Troubleshooting

### Port already in use
If port 8000 is already in use:
```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Use a different port
python -m uvicorn app.main:app --reload --port 8001
```

### Module not found errors
Make sure you're in the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### Database issues
If you encounter database errors:
```bash
# Delete existing database
rm edurpg.db

# The database will be recreated on server start
```

## Development

### Running with auto-reload
The `--reload` flag enables automatic server restart when code changes:
```bash
python -m uvicorn app.main:app --reload
```

### Running the mock server
For testing without the full application:
```bash
python main.py
# or
python -m uvicorn main:app --reload
```

### Database migrations
Currently using SQLAlchemy's `create_all()` for simplicity. For production, consider using Alembic for migrations.

## Frontend Integration

The backend is configured to accept requests from:
- http://localhost:3000 (default frontend port)
- http://localhost:3001 (alternative frontend port)

Make sure your frontend's API URL matches:
```javascript
// In frontend .env
VITE_API_URL=http://localhost:8000
```