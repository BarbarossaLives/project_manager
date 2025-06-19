# 🚀 AI-Powered Project Manager

A modern, intelligent project management application with AI-powered planning, automatic schedule adjustment, and smart task management.

## ✨ Features

### 🤖 AI-Powered Planning
- **Intelligent Project Creation**: Describe your project and get a complete plan with tasks, milestones, and timelines
- **Progress Analysis**: AI analyzes your work patterns and provides actionable insights
- **Automatic Schedule Adjustment**: Smart deadline adjustments when delays occur
- **Task Breakdown**: Break complex tasks into manageable subtasks

### 📋 Project Management
- **Project & Task Tracking**: Organize work with projects, tasks, and subtasks
- **Pomodoro Timer**: Built-in focus timer with time logging
- **Development Logs**: Track daily progress and insights
- **File Attachments**: Upload and organize project files

### 🔔 Smart Reminders
- **Automatic Social Media Reminders**: AI generates reminders to share your progress
- **Content Generation**: Smart social media content based on your work
- **Flexible Scheduling**: Manual and automatic reminder creation

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Application
```bash
python start_project_manager.py
```

The startup script will automatically:
- ✅ Set up the database
- ✅ Install and configure Ollama AI (if needed)
- ✅ Download the AI model
- ✅ Start the server on http://localhost:8080

### 3. Access Your Project Manager
Open your browser and go to: **http://localhost:8080**

## ⚙️ Configuration

### Port Configuration
The app runs on port **8080** by default to avoid conflicts with other development servers.

To change the port, set the environment variable:
```bash
export PROJECT_MANAGER_PORT=8081
python start_project_manager.py
```

### Environment Variables
Copy `.env.example` to `.env` and customize:
```bash
cp .env.example .env
```

Key configuration options:
- `PROJECT_MANAGER_PORT=8080` - Server port
- `OLLAMA_BASE_URL=http://localhost:11434` - AI service URL
- `AUTO_SETUP_AI=true` - Automatically set up AI features
- `AUTO_SETUP_DATABASE=true` - Automatically create database tables

## 🤖 AI Setup

### Automatic Setup (Recommended)
The startup script handles AI setup automatically. Just run:
```bash
python start_project_manager.py
```

### Manual Setup
If you prefer manual setup:
```bash
python setup_ollama.py
```

### AI Requirements
- **Ollama**: Local AI runtime (automatically installed)
- **Model**: llama3.2 (automatically downloaded)
- **Storage**: ~2GB for the AI model

## 📁 Project Structure

```
project_manager/
├── backend/           # FastAPI backend
│   ├── models/        # Database models
│   ├── routes/        # API endpoints
│   └── services/      # Business logic
├── frontend/          # HTML templates and static files
├── uploads/           # File attachments
├── config.py          # Configuration management
├── start_project_manager.py  # Main startup script
└── setup_ollama.py    # AI setup script
```

## 🔧 Development

### Running in Development Mode
```bash
export ENVIRONMENT=development
export DEBUG=true
python start_project_manager.py
```

### Running Multiple Instances
Use different ports for different projects:
```bash
# Project 1
export PROJECT_MANAGER_PORT=8080
python start_project_manager.py

# Project 2 (in another terminal)
export PROJECT_MANAGER_PORT=8081
python start_project_manager.py
```

### Database Management
The app uses SQLite by default. Database file: `project_tracker.db`

**Automatic Migration**: The startup script automatically detects and runs database migrations for AI features.

**Manual Migration**: If needed, run the migration manually:
```bash
python migrate_database.py
```

To use a different database:
```bash
export DATABASE_URL="sqlite:///./my_project.db"
python start_project_manager.py
```

**Database Backup**: Migrations automatically create backups (`.backup` files).

## 🎯 Usage Examples

### Creating an AI Project Plan
1. Go to the "AI Project Planning" section
2. Describe your project: "Build a web app for recipe management with user accounts"
3. Click "Generate AI Project Plan"
4. Review the generated tasks, milestones, and timeline

### Analyzing Project Progress
1. Select a project from the "Analyze Project Progress" dropdown
2. Click "AI Analysis"
3. Review insights on project health, bottlenecks, and recommendations

### Auto-Adjusting Schedules
1. When tasks are delayed, select the project
2. Optionally provide a reason for the delay
3. Click "Auto-Adjust Schedule"
4. AI will suggest and apply new deadlines

## 🛠️ Troubleshooting

### AI Features Not Working
1. Check if Ollama is running: `ollama list`
2. Restart the AI service: `python setup_ollama.py`
3. Check the logs for error messages

### Port Already in Use
Change the port in your environment:
```bash
export PROJECT_MANAGER_PORT=8081
python start_project_manager.py
```

### Database Issues
Delete the database file to reset:
```bash
rm project_tracker.db
python start_project_manager.py
```

## 🔒 Privacy & Security

- **Local AI**: All AI processing happens locally with Ollama
- **No Data Sharing**: Your project data never leaves your machine
- **SQLite Database**: Local file-based database storage
- **Open Source**: Full transparency of all code

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

---

**Happy Project Managing! 🎉**
