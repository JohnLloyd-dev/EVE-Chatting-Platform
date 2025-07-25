# 🎯 User & Scenario Management System

## 📋 Overview

Your chat platform manages users and their AI scenarios through a sophisticated multi-layer system that maps user preferences to personalized AI experiences.

## 🏗️ Database Architecture

### Core Tables

```sql
-- Users: Basic user information
Users {
    id: UUID (Primary Key)
    tally_response_id: String (Unique - from Tally form)
    email: String (Optional)
    is_blocked: Boolean (Admin control)
    created_at: DateTime
    last_active: DateTime
}

-- Chat Sessions: Each user gets one session with their scenario
ChatSessions {
    id: UUID (Primary Key)
    user_id: UUID (Foreign Key → Users.id)
    scenario_prompt: TEXT (The AI's personality/scenario)
    created_at: DateTime
    updated_at: DateTime
    is_active: Boolean
}

-- Tally Submissions: Original form data and processed scenarios
TallySubmissions {
    id: UUID (Primary Key)
    user_id: UUID (Foreign Key → Users.id)
    form_data: JSONB (Original Tally form responses)
    processed_scenario: TEXT (Generated scenario text)
    created_at: DateTime
}

-- Messages: All conversation history
Messages {
    id: UUID (Primary Key)
    session_id: UUID (Foreign Key → ChatSessions.id)
    content: TEXT
    is_from_user: Boolean
    created_at: DateTime
    is_admin_intervention: Boolean
}
```

## 🔄 User Registration & Scenario Creation Flow

### Step 1: Tally Form Submission

```
User fills Tally form → Webhook triggers → /webhook/tally endpoint
```

### Step 2: Data Processing

```python
# In main.py - webhook handler
def process_tally_webhook(form_data):
    # 1. Extract user info
    user_id = form_data['data']['responseId']

    # 2. Generate scenario from form responses
    scenario = generate_story_from_json(form_data)  # extract_tally.py

    # 3. Create full AI prompt
    full_scenario = (
        "You are sexual fantasy Assistant. " + scenario +
        " Rules: 1) Always speak in the first person..."
    )

    # 4. Create user and session
    user = User(tally_response_id=user_id, ...)
    chat_session = ChatSession(
        user_id=user.id,
        scenario_prompt=full_scenario  # ← Stored here!
    )

    # 5. Store original form data
    tally_submission = TallySubmission(
        user_id=user.id,
        form_data=form_data,
        processed_scenario=full_scenario
    )
```

### Step 3: Scenario Examples

Based on Tally form responses, scenarios are generated like:

```
Form Input:
- My gender: Man
- Partner gender: Police
- Partner age: 25-35
- Location: Park
- Control dynamic: Submissive

Generated Scenario:
"You are sexual fantasy Assistant. You are Taylor, a 25-year-old Black police officer. You like to take control during encounters. You are in a park setting. Rules: 1) Always speak in the first person and always stay in character..."
```

## 🤖 AI Model Session Mapping

### How Each User Maps to AI Model

```python
# When user sends a message (celery_app.py)
def process_ai_response(session_id, user_message):
    # 1. Get user's chat session from database
    chat_session = db.query(ChatSession).filter(
        ChatSession.id == session_id
    ).first()

    # 2. Extract the stored scenario
    scenario_prompt = chat_session.scenario_prompt

    # 3. Call AI model with scenario
    ai_response = call_ai_model(scenario_prompt, history, max_tokens)

def call_ai_model(scenario_prompt, history, max_tokens):
    # 1. Set scenario on AI model (creates AI session)
    response = client.post(
        f"{AI_MODEL_URL}/scenario",
        json={"scenario": scenario_prompt},
        auth=(username, password)
    )

    # 2. Get AI session cookie
    session_cookie = response.cookies.get("session_id")

    # 3. Use cookie for chat
    chat_response = client.post(
        f"{AI_MODEL_URL}/chat",
        json={"message": user_message, "max_tokens": max_tokens},
        cookies={"session_id": session_cookie},
        auth=(username, password)
    )
```

### Session Lifecycle

```
User Registration → Database Session Created → AI Model Session Created Per Message

Database Session (Persistent):
├── User: 2de89288-7fc2-4d47-950b-f6a5ea07bb7f
├── ChatSession: a08ff733-28c6-42ae-8c83-e0c129424fe1
└── Scenario: "You are Taylor, a police officer..."

AI Model Session (Per Message):
├── POST /scenario → Creates temporary AI session
├── Session Cookie: fdf7d789-5bb4-4619-9...
├── POST /chat → Uses session cookie
└── Response → Saved to database
```

## 👥 User Management Operations

### View All Users

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/admin/conversations
```

### View User's Scenario

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/admin/conversation/{session_id}
```

### Block/Unblock User

```bash
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/admin/user/{user_id}/block
```

### Admin Intervention

```bash
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/admin/conversation/{session_id}/message \
  -d '{"message": "Admin message here"}'
```

## 🔧 Scenario Management

### Current Scenario Sources

1. **Tally Form Responses**: Processed by `extract_tally.py`
2. **Fixed Template**: Sexual fantasy assistant with rules
3. **User Preferences**: Gender, partner type, age, location, etc.

### Scenario Customization

```python
# In extract_tally.py
def generate_story_from_json(json_data):
    generator = FantasyStoryGenerator(json_data)
    return generator.generate_story()

class FantasyStoryGenerator:
    def __init__(self, json_data):
        self.story_elements = {
            "my_gender": self.get_answer('question_zMKJN1'),
            "partner_gender": self.get_answer('question_59dv4M'),
            "partner_age": self.get_answer('question_d0YjNz'),
            # ... more elements
        }
```

### Adding New Scenario Types

1. **Modify Tally Form**: Add new questions
2. **Update extract_tally.py**: Handle new question keys
3. **Extend FantasyStoryGenerator**: Add new story elements
4. **Test**: Create test user with new scenario

## 📊 Monitoring & Analytics

### User Activity

```python
# Get user statistics
def get_user_stats():
    total_users = db.query(User).count()
    active_sessions = db.query(ChatSession).filter(
        ChatSession.is_active == True
    ).count()
    total_messages = db.query(Message).count()
```

### Scenario Performance

```python
# Analyze popular scenarios
def analyze_scenarios():
    scenarios = db.query(TallySubmission.processed_scenario).all()
    # Analyze common patterns, preferences, etc.
```

## 🛠️ Management Tools

### 1. User Scenario Manager

```bash
python3 user_scenario_manager.py
```

- View all users and scenarios
- Analyze user-scenario mapping
- Test AI model integration
- Create test users

### 2. Admin Dashboard

- Web interface: http://localhost:3000/admin
- View conversations
- Monitor user activity
- Admin interventions

### 3. API Endpoints

- `/admin/conversations` - List all users
- `/admin/conversation/{id}` - User details
- `/chat/session/{user_id}` - User's chat session
- `/admin/user/{id}/block` - Block user

## 🔄 Data Flow Summary

```
1. User Registration:
   Tally Form → extract_tally.py → Generate Scenario → Create User + ChatSession

2. Chat Message:
   User Message → Celery Worker → AI Model (Set Scenario) → Get Response → Save to DB

3. AI Model Interaction:
   ChatSession.scenario_prompt → AI /scenario → Session Cookie → AI /chat → Response

4. Admin Monitoring:
   Admin Dashboard → Database Queries → User Management → Interventions
```

## 🎯 Key Benefits

1. **Personalized AI**: Each user gets a unique AI personality based on their preferences
2. **Persistent Sessions**: User scenarios are stored and reused across conversations
3. **Admin Control**: Full monitoring and intervention capabilities
4. **Scalable**: Can handle multiple users with different scenarios simultaneously
5. **Flexible**: Easy to add new scenario types and preferences

## 🚀 Next Steps

1. **Enhanced Scenarios**: Add more question types to Tally form
2. **Scenario Templates**: Create predefined scenario templates
3. **User Preferences**: Allow users to modify their scenarios
4. **Analytics**: Track scenario popularity and effectiveness
5. **A/B Testing**: Test different scenario variations

Your system is already production-ready with sophisticated user and scenario management! 🎉
