# Runner Attendance Tracker

A web-based system designed for the UQ Social Runners Club to efficiently track attendance at daily social runs. The system provides a configurable calendar for scheduling runs, quick QR code-based registration for runners, and real-time attendance reporting through a web interface.

## Features

- **Calendar Management**: Configure which days have scheduled runs
- **QR Code Registration**: Quick attendance registration via QR code scanning
- **Real-time Updates**: Live attendance tracking with WebSocket connections
- **Admin Dashboard**: Monitor participation and manage attendance records
- **Data Export**: Export attendance data in CSV format
- **Attendance Override**: Add, edit, or remove attendance records manually
- **Historical Data**: View and analyze participation trends

## Tech Stack

### Backend
- **Python 3.13** with FastAPI
- **SQLite** database with SQLAlchemy ORM
- **Alembic** for database migrations
- **JWT** tokens for secure QR code validation
- **WebSocket** support for real-time updates
- **Pytest** for comprehensive testing

### Frontend
- **React 18** with TypeScript
- **Socket.IO** client for real-time updates
- **React Router** for navigation
- **Responsive design** for mobile and desktop

## Project Structure

```
runner-attendance-tracker/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── database/       # Database connection and models
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic services
│   │   └── main.py         # FastAPI application
│   ├── tests/              # Unit and integration tests
│   ├── alembic/            # Database migrations
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend (to be implemented)
│   ├── src/
│   ├── public/
│   └── package.json
├── .kiro/                  # Kiro AI specifications
│   └── specs/
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+ (for frontend)
- Git

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### API Documentation

Once the backend is running, you can access:
- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`

### Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

## API Endpoints

### Calendar Management
- `GET /api/calendar` - Get calendar configuration
- `POST /api/calendar/configure` - Update run day settings
- `GET /api/calendar/today` - Check today's run status

### QR Code System
- `GET /api/qr/{session_id}` - Generate QR code for session
- `GET /api/qr/validate/{token}` - Validate QR code token

### Attendance Registration
- `POST /api/register` - Register attendance
- `GET /api/attendance/today` - Get current day attendance
- `GET /api/attendance/history` - Get historical attendance data

### Attendance Override (Admin)
- `POST /api/attendance/override/add` - Add attendance record manually
- `PUT /api/attendance/override/{attendance_id}` - Edit existing record
- `DELETE /api/attendance/override/{attendance_id}` - Remove attendance record
- `POST /api/attendance/override/bulk` - Bulk operations on multiple records

## Database Schema

### Tables
- **runs**: Scheduled run sessions with unique session IDs
- **attendances**: Individual attendance records linked to runs
- **calendar_config**: Calendar configuration for run days

## Development

### Adding New Features

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Implement your changes following the existing patterns
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

### Code Quality

- Follow PEP 8 for Python code
- Use type hints throughout
- Maintain test coverage above 90%
- Document all public APIs

## Deployment

The application is designed for easy deployment on free hosting platforms:

- **Backend**: Railway, Render, or PythonAnywhere
- **Frontend**: Vercel, Netlify, or GitHub Pages
- **Database**: SQLite with persistent storage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues, please create an issue in the GitHub repository.