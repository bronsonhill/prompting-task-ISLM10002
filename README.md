# Chat Application MVP

A Streamlit-based chat application with prompt management, conversation tracking, comprehensive logging for research purposes, and document upload functionality.

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
│   ├── create_student_codes.py # Generate codes from CSV
│   └── manage_admin_codes.py   # Manage admin codes in database
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

# Note: The application now includes document processing capabilities
# Additional dependencies: PyPDF2 (for PDF processing), python-docx (for DOCX processing)
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
  "documents": [             // Array of attached documents
    {
      "filename": "document.pdf",
      "file_type": "application/pdf",
      "file_size": 1024,
      "content": "Extracted text content...",
      "uploaded_at": ISODate
    }
  ],
  "prompt_token_count": 15,      // Number of tokens in prompt text only
  "document_token_count": 10,    // Number of tokens in documents only
  "total_token_count": 25,       // Total tokens (prompt + documents)
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
    {"role": "user", "content": "...", "timestamp": ISODate, "token_count": 15},
    {"role": "assistant", "content": "...", "timestamp": ISODate, "token_count": 25}
  ],
  "token_stats": {
    "total_input_tokens": 150,
    "total_output_tokens": 300
  },
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

**Chat Message Logs Include Token Counts:**
```json
{
  "action": "chat_message",
  "data": {
    "prompt_id": "P001",
    "role": "user|assistant",
    "content": "Message content...",
    "token_count": 15,
    "message_timestamp": "2024-01-01T12:00:00"
  }
}
```

#### `admin_codes`
```json
{
  "_id": ObjectId,
  "code": "ADMIN",          // 5-character admin code
  "level": "super_admin",   // "admin" or "super_admin"
  "added_by": "system",     // Who added this code
  "created_at": ISODate,
  "is_active": true,        // Soft delete flag
  "removed_by": "user123",  // Who removed it (if inactive)
  "removed_at": ISODate     // When it was removed (if inactive)
}
```

## 📎 Document Upload Feature

The application now supports uploading documents as part of prompt creation. When a prompt with attached documents is used in a chat, the document content is automatically included as context for the AI.

### Supported File Types:
- **PDF** (.pdf) - Text extraction from PDF documents
- **DOCX** (.docx) - Microsoft Word documents  
- **TXT** (.txt) - Plain text files

### How to Use Document Upload:

1. **Create a Prompt**: Go to the "Prompts" page
2. **Enter Prompt Content**: Write your conversation prompt
3. **Upload Documents**: Use the file uploader to attach one or more documents
4. **Create Prompt**: Click "Create Prompt" to save with attached documents
5. **Use in Chat**: When you start a new chat, select the prompt and the documents will be automatically included as context

### Document Processing:
- Documents are processed and their text content is extracted
- Content is stored securely in the database
- Token counts are tracked separately for prompts and documents
- Documents are displayed in the prompt interface for review

### Token Count Tracking:
The system now tracks token counts separately:
- **Prompt Tokens**: Number of tokens in the prompt text only
- **Document Tokens**: Number of tokens in attached documents only  
- **Total Tokens**: Combined total of prompt and document tokens
- **Migration**: The update script will remove legacy `token_count` fields and replace them with the new separate fields

## 💬 Usage Guide

### For Users

1. **Login**: Enter your 5-character access code
2. **First-time Setup**: Complete data consent form
3. **Create Prompts**: Go to Prompts page and create conversation starters with optional document attachments
4. **Start Chatting**: Go to Chat page, select a prompt, and start conversing (documents will be included as context)
5. **Continue Conversations**: Access your chat history from the sidebar

### For Administrators

1. **Access Admin Panel**: Login with an admin code (see Admin System below)
2. **View Statistics**: Monitor system usage and user activity
3. **Manage Users**: Search and view user information
4. **Analytics**: Track conversation and prompt usage patterns
5. **Admin Management**: Manage admin codes and system settings

## 👑 Admin System

### Admin Access Levels

- **Regular Users**: Standard access to Chat and Prompts
- **Administrators**: Access to admin panel with analytics
- **Super Administrators**: Can manage admin codes and system settings

### Database-Based Admin Management

Admin codes are now stored in the database instead of being hardcoded. This provides:
- **Flexibility**: Add/remove admin codes without code changes
- **Security**: Admin codes are stored securely in the database
- **Audit Trail**: Track who added/removed admin codes and when
- **Soft Deletion**: Admin codes are deactivated rather than deleted

### Secure Admin Code Management

**⚠️ SECURITY UPDATE**: Admin codes are no longer hardcoded for security reasons.

**For First-Time Setup:**
```bash
# Create your first secure admin code
python scripts/manage_admin_codes.py --init-secure
```

**For Additional Admin Codes:**
```bash
# Add new admin codes
python scripts/manage_admin_codes.py --add YOUR_CODE --level admin
python scripts/manage_admin_codes.py --add YOUR_CODE --level super_admin
```

**For Updating Existing Prompts:**
```bash
# Update existing prompts with new token count fields
python scripts/update_prompt_token_counts.py
```

### Managing Admin Codes

#### Via Script (Recommended)
```bash
# Create secure initial admin code (first-time setup)
python scripts/manage_admin_codes.py --init-secure

# List all admin codes
python scripts/manage_admin_codes.py --list

# Add a new admin code
python scripts/manage_admin_codes.py --add ABC12 --level admin
python scripts/manage_admin_codes.py --add XYZ99 --level super_admin

# Remove an admin code (cannot remove super admins)
python scripts/manage_admin_codes.py --remove ABC12
```

#### Via Admin Interface
- Super administrators can manage admin codes through the web interface
- Navigate to Admin → Admin Management tab
- Add new codes with specified admin levels
- Remove existing admin codes (except super admins)

### Admin Features

- **System Statistics**: User counts, activity metrics, consent statistics
- **User Management**: Search users, view profiles, activity tracking
- **Conversation Analytics**: Usage patterns, message statistics
- **Prompt Analytics**: Most used prompts, creation trends
- **Token Analytics**: Input/output token usage, cost tracking
- **Logs Analytics**: Comprehensive logging analysis and export
- **Admin Management**: Add/remove admin codes (Super Admins only)

### Dynamic Admin Interface

- Admin status is automatically detected on login
- Admin users see an additional "Admin" navigation option
- Admin badge (👑) appears next to username for admin users
- Admin metrics are shown in user statistics
- **Five-tab admin dashboard**: Statistics, Users, Prompts, Logs, and Admin Management

## 🔧 Configuration Options

### Admin Codes

Admin codes are now managed securely through the database. Use the management script:

```bash
# Create secure initial admin code (first-time setup)
python scripts/manage_admin_codes.py --init-secure

# Add new admin codes
python scripts/manage_admin_codes.py --add YOUR_CODE --level admin
```

Or use the Admin Management interface (Super Admins only) to add/remove admin codes dynamically.

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
- **Token usage statistics** (input/output tokens for cost tracking)

### Token Tracking

The application tracks token usage for research and cost monitoring purposes:

- **Input Tokens**: Tokens in user messages and system prompts
- **Output Tokens**: Tokens in AI assistant responses
- **Prompt Tokens**: Token count for each created prompt
- **Message-level Tokens**: Individual token counts for each message
- **Conversation-level Tokens**: Total token statistics per conversation

Token counting uses the `tiktoken` library with GPT-4o encoding (o200k_base) for accurate OpenAI API token estimation.

#### Prompt Token Counts
- **Automatic Calculation**: Token counts are automatically calculated when prompts are created
- **Database Storage**: Token counts are stored in the `token_count` field for each prompt
- **CSV Export**: Prompt token counts are included in all CSV exports
- **Admin Dashboard**: Token statistics are displayed in the Prompts tab
- **Update Tool**: Existing prompts without token counts can be updated via admin interface

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