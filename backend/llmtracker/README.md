# LLM Tracker App

A Django app for tracking and managing LLM prompts across different AI models.

## Features

- Store prompts with associated AI models
- Track execution status of prompts
- Search and filter prompts by text and model
- Position-based ordering within groups

## Models

### LLMPrompt
- `promptId`: Unique UUID identifier
- `prompt`: The actual prompt text
- `fk_user`: Foreign key to user account
- `fk_group`: Foreign key to project group
- `model`: AI model (ChatGPT, Gemini, Claude, Perplexity)
- `position`: Ordering position within group
- `track_status`: Execution status (INIT, SCHD, DONE, FAIL)
- `track_message`: Status message or error details
- `created_date`: Creation timestamp
- `modified_date`: Last modification timestamp

## API Endpoints

### 1. Add Prompt
- **URL**: `POST /llmtracker/add`
- **Required Fields**: `userid`, `groupid`, `prompt`, `model`
- **Response**: Success message with generated `promptId`

### 2. List Prompts
- **URL**: `POST /llmtracker/list`
- **Required Fields**: `userid`, `groupid`
- **Optional Fields**: `search` (text search), `model` (filter by model)
- **Response**: List of prompts with details

### 3. Delete Prompt
- **URL**: `POST /llmtracker/delete`
- **Required Fields**: `userid`, `promptId`
- **Response**: Success message

## Usage

1. Add the app to your Django project's `INSTALLED_APPS`
2. Include the URLs in your main `urls.py`
3. Run migrations: `python manage.py makemigrations llmtracker && python manage.py migrate`
4. Access the admin interface to manage prompts

## Dependencies

- Django
- Django REST Framework
- djongo (for MongoDB support)
- account app (for user management)
- serp app (for group management)
