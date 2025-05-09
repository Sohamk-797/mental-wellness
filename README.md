# Mental Wellness Chatbot

A Django-based mental wellness chatbot application that provides support and guidance for mental health.

## Features

- Chat interface for mental health support
- Mood tracking
- Journal entries
- Response generation using OpenAI's GPT models

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Create a superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

8. Open your browser and navigate to `http://127.0.0.1:8000/`

## Project Structure

- `mental_wellness/`: Main project directory
  - `settings.py`: Project settings
  - `urls.py`: URL routing
- `chatbot/`: Main application directory
  - `models.py`: Database models
  - `views.py`: View functions
  - `urls.py`: Application URL routing
  - `templates/`: HTML templates
  - `static/`: Static files (CSS, JS, images)
  - `forms.py`: Form definitions
  - `utils.py`: Utility functions

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License. 