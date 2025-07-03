# Chat Application MVP

A Streamlit-based chat application with prompt management, conversation tracking, and comprehensive logging for research purposes.

## 🏗️ Architecture Overview

This MVP implements a multi-page Streamlit application with the following structure:

```
v2/
├── main.py                 # Home page with login and consent
├── pages/
│   ├── 1_Chat.py          # Chat interface with OpenAI integration
│   ├── 2_Prompt.py        # Prompt creation and management
│   └── 3_Admin.py         # Admin panel (optional)
├── scripts/
│   ├── create_test_codes.py    # Generate test user codes
│   └── create_student_codes.py # Generate codes from CSV
├── utils/
│   ├── database.py        # MongoDB operations
│   ├── auth.py           # Authentication and session management
│   └── logging.py        # Logging utilities
├── requirements.txt       # Python dependencies
└── .streamlit/
    └── secrets.toml      # Configuration (API keys, DB connection)
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- MongoDB (local or MongoDB Atlas)
- OpenAI API key

### 2. Installation

```bash
# Clone or download the project
cd v2/

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create or update `.streamlit/secrets.toml`:

```toml
[openai]
api_key = "your-openai-api-key-here"

[mongodb]
connection_string = "your-mongodb-connection-string"
database_name = "chat_app_mvp"
```

**MongoDB Connection Examples:**
- MongoDB Atlas: `"mongodb+srv://username:password@cluster.mongodb.net/"`
- Local MongoDB: `"mongodb://localhost:27017/"`

### 4. Create User Codes

**Option A: Create test codes for development**
```bash
cd scripts/
python create_test_codes.py --count 5
```

**Option B: Create codes for students from CSV**
```bash
cd scripts/
# First create a sample CSV
python create_student_codes.py --sample

# Then process your actual student data
python create_student_codes.py students.csv
```

### 5. Run the Application

```bash
# From the v2/ directory
streamlit run main.py
```

## 📊 Database Schema

### Collections

#### `users`
```json
{
  "_id": ObjectId,
  "code": "ABC12",           // 5-character unique code
  "data_use_consent": true,  // true/false/null
  "created_at": ISODate,
  "last_login": ISODate
}
```

#### `prompts`
```json
{
  "_id": ObjectId,
  "prompt_id": "P001",       // Auto-incrementing
  "user_code": "ABC12",
  "content": "Your prompt text...",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

#### `conversations`
```json
{
  "_id": ObjectId,
  "conversation_id": "C001",
  "user_code": "ABC12",
  "prompt_id": "P001",
  "messages": [
    {"role": "user", "content": "...", "timestamp": ISODate},
    {"role": "assistant", "content": "...", "timestamp": ISODate}
  ],
  "created_at": ISODate,
  "updated_at": ISODate
}
```

#### `logs`
```json
{
  "_id": ObjectId,
  "user_code": "ABC12",
  "action": "login|prompt_create|chat_message|...",
  "data": {},               // Action-specific data
  "timestamp": ISODate
}
```

## 💬 Usage Guide

### For Users

1. **Login**: Enter your 5-character access code
2. **First-time Setup**: Complete data consent form
3. **Create Prompts**: Go to Prompts page and create conversation starters
4. **Start Chatting**: Go to Chat page, select a prompt, and start conversing
5. **Continue Conversations**: Access your chat history from the sidebar

### For Administrators

1. **Access Admin Panel**: Login with an admin code (defined in `pages/3_Admin.py`)
2. **View Statistics**: Monitor system usage and user activity
3. **Manage Users**: Search and view user information
4. **Analytics**: Track conversation and prompt usage patterns

## 🔧 Configuration Options

### Admin Codes

Edit `pages/3_Admin.py` to modify admin access:

```python
ADMIN_CODES = {"ADMIN", "SUPER", "YOUR_ADMIN_CODE"}
```

### OpenAI Model Settings

Edit `pages/1_Chat.py` to change AI model parameters:

```python
response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # or "gpt-4"
    messages=openai_messages,
    max_tokens=1000,        # Adjust as needed
    temperature=0.7         # Adjust creativity level
)
```

## 📝 Data Collection & Privacy

### What Data is Collected

- All user interactions and chat messages
- Prompt creation and usage
- Login patterns and timestamps  
- System interactions and errors

### Consent Handling

- **Data Collection**: Occurs regardless of consent status
- **Data Consent**: Only affects usage for research purposes
- **First-time Users**: Must acknowledge data collection notice
- **Existing Users**: Can view/modify consent in future versions

### Logged Actions

- `login` - User authentication
- `logout` - User logout
- `user_created` - New user registration
- `prompt_create` - Prompt creation
- `chat_message` - Chat messages (user and AI)
- `conversation_start` - New conversation
- `conversation_continue` - Resume conversation
- `page_visit` - Page navigation
- `error` - System errors

## 🛠️ Development

### Adding New Features

1. **New Pages**: Add to `pages/` directory with appropriate naming
2. **Database Operations**: Extend `utils/database.py`
3. **Authentication**: Modify `utils/auth.py` for new session requirements
4. **Logging**: Add new action types in `utils/logging.py`

### Testing

```bash
# Create test users
python scripts/create_test_codes.py --count 10

# List existing users
python scripts/create_test_codes.py --list

# Test with sample student data
python scripts/create_student_codes.py --sample
python scripts/create_student_codes.py sample_students.csv
```

### Deployment Considerations

1. **Environment Variables**: Move secrets to environment variables
2. **Database Security**: Use MongoDB authentication and SSL
3. **API Rate Limits**: Implement OpenAI usage monitoring
4. **Logging**: Set up centralized logging for production
5. **Backup**: Regular database backups for research data

## 🔍 Troubleshooting

### Common Issues

**MongoDB Connection Fails**
- Check connection string format
- Verify network access (Atlas whitelist)
- Ensure database credentials are correct

**OpenAI API Errors**
- Verify API key is valid and has credits
- Check rate limits and quotas
- Review model availability

**Authentication Issues**
- Ensure user codes exist in database
- Check session state persistence
- Verify code format (5 alphanumeric characters)

**Import Errors**
- Install all requirements: `pip install -r requirements.txt`
- Check Python version compatibility
- Verify virtual environment activation

### Getting Help

1. Check Streamlit logs in terminal
2. Review MongoDB logs for database issues
3. Verify secrets.toml configuration
4. Test with simple test codes first

## 📄 File Overview

### Core Files

- **`main.py`**: Entry point, handles login and navigation
- **`pages/1_Chat.py`**: Chat interface with OpenAI integration
- **`pages/2_Prompt.py`**: Prompt creation and management
- **`pages/3_Admin.py`**: Admin dashboard (optional)

### Utilities

- **`utils/database.py`**: All MongoDB operations
- **`utils/auth.py`**: Session management and authentication
- **`utils/logging.py`**: Comprehensive action logging

### Scripts

- **`scripts/create_test_codes.py`**: Generate test user codes
- **`scripts/create_student_codes.py`**: Process student CSV files

## 🎯 MVP Features Implemented

✅ **Authentication System**
- 5-character code validation
- Session management
- First-time user handling

✅ **Data Consent Management**
- Consent collection interface
- Consent tracking in database
- Clear data collection notice

✅ **Prompt Management**
- Create and store conversation prompts
- View and manage existing prompts
- Prompt usage statistics

✅ **Chat Interface**
- OpenAI integration
- Conversation persistence
- Chat history and continuation
- Real-time messaging

✅ **Comprehensive Logging**
- All user actions logged
- Detailed conversation tracking
- Error logging and monitoring

✅ **Admin Dashboard**
- System statistics
- User management
- Usage analytics

✅ **User Management Scripts**
- Test code generation
- CSV-based student code creation
- Bulk user operations

This MVP provides a solid foundation for research-oriented chat applications with comprehensive data collection and user management capabilities.