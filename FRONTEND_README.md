# AI CRM Frontend

A minimalistic and intuitive web interface for your AI CRM automation system, inspired by pg-lang's clean design.

## Features

- 🤖 **Natural Language Interface**: Chat with your CRM using plain English
- 👤 **Contact Management**: Create and update HubSpot contacts
- 💼 **Deal Management**: Create and manage sales deals
- 📧 **Email Integration**: Send confirmation emails
- 🎨 **Clean UI**: Minimalistic design inspired by pg-lang
- 📱 **Responsive**: Works on desktop and mobile devices

## Quick Start

### 1. Install Dependencies

```bash
# Install additional API server dependencies
pip install -r requirements-api.txt
```

### 2. Start the Backend API Server

```bash
# Make sure your .env file is configured with API keys
python api_server.py
```

The API server will start on `http://localhost:8000`

### 3. Start the Frontend Server

In a new terminal:

```bash
python serve_frontend.py
```

The frontend will open automatically in your browser at `http://localhost:3000`

## Usage

### Chat Interface

Simply type natural language requests like:
- "Create a contact for john@example.com named John Smith"
- "Add a new deal worth $5000 for Sarah"
- "Update contact info for jane@company.com with phone 555-1234"
- "Send a confirmation email to owner@company.com"

### Quick Actions

Use the sidebar buttons for common tasks:
- **Create Contact**: Add new contacts with a form
- **Create Deal**: Create sales opportunities
- **Update Contact**: Modify existing contact information
- **Send Email**: Send confirmation emails

## API Endpoints

The frontend connects to these backend endpoints:

- `POST /chat` - Natural language processing
- `POST /api/contacts` - Direct contact creation
- `POST /api/deals` - Direct deal creation
- `GET /health` - Health check

## Configuration

Make sure your `ai_crm_automation/config.json` is properly configured with:

- OpenAI API key
- HubSpot API key
- Email provider settings (SendGrid, Resend, or SMTP)

## File Structure

```
frontend/
├── index.html          # Main HTML file
├── styles.css          # CSS styles
└── script.js           # JavaScript functionality

api_server.py           # Flask API server
serve_frontend.py       # Frontend HTTP server
requirements-api.txt    # Additional dependencies
```

## Customization

### Styling

Edit `frontend/styles.css` to customize the appearance. The design uses:
- Inter font family
- CSS Grid and Flexbox layouts
- Smooth animations and transitions
- Responsive design patterns

### Functionality

Modify `frontend/script.js` to:
- Add new quick actions
- Customize form fields
- Change API endpoints
- Add new features

## Troubleshooting

### Backend Connection Issues

If you see "Unable to connect to the AI CRM backend":
1. Make sure `api_server.py` is running on port 8000
2. Check that your config.json has valid API keys
3. Verify CORS is enabled (should be automatic)

### API Key Issues

If you get API errors:
1. Check your `.env` file or `config.json`
2. Verify HubSpot and OpenAI API keys are valid
3. Ensure email provider credentials are correct

### Port Conflicts

If ports 3000 or 8000 are in use:
- Change `PORT = 3000` in `serve_frontend.py`
- Change `apiBaseUrl = 'http://localhost:8000'` in `frontend/script.js`
- Update `app.run(port=8000)` in `api_server.py`

## Development

To extend the frontend:

1. **Add new actions**: Update the `getModalContent()` method in `script.js`
2. **Modify styling**: Edit `styles.css` with your preferred colors/layout
3. **Add API endpoints**: Extend `api_server.py` with new routes
4. **Customize responses**: Modify the chat response handling in `script.js`

## Production Deployment

For production use:

1. Use a proper web server (nginx, Apache) for the frontend
2. Use a WSGI server (gunicorn, uWSGI) for the Flask API
3. Add proper error handling and logging
4. Implement authentication and rate limiting
5. Use environment variables for configuration

## License

This frontend is part of the AI CRM automation project.