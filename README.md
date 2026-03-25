# Gmail Agent with LangChain

A containerized Python web service that processes Gmail notifications in real-time using webhooks, LangChain Anthropic for AI summarization, and Twilio for WhatsApp notifications.

## 🚀 Quick Start with Docker

```bash
# Clone and setup
git clone <your-repo>
cd gmail-agent

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Build and run with Docker
docker-compose up --build
```

Your service will be available at `http://localhost:5000`

## 📋 Prerequisites

- Docker and Docker Compose
- Gmail API credentials from Google Cloud Console
- Anthropic API key
- Twilio account for WhatsApp notifications
- Google Cloud Project with Pub/Sub enabled

## 🏗️ Architecture

**Push-based Architecture (Webhook)**:
```
Gmail → Google Pub/Sub → Your Webhook → AI Processing → WhatsApp
```

Benefits over polling:
- ⚡ Real-time notifications
- 💰 Lower costs (no constant polling)
- 🔋 Better resource efficiency
- 📈 Scales automatically

## 🐳 Docker Deployment

### Local Development

1. **Environment Setup**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Build and Run**:
   ```bash
   docker-compose up --build
   ```

3. **Test the Service**:
   ```bash
   curl http://localhost:5000/
   # Should return: {"status": "healthy"}
   ```

### Production Build

```bash
# Build production image
docker build -t gmail-agent:latest .

# Run production container
docker run -d \
  --name gmail-agent \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/token.json:/app/token.json:ro \
  -v $(pwd)/credentials.json:/app/credentials.json:ro \
  gmail-agent:latest
```

## ☁️ Render Deployment

### 1. Prepare for Render

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

2. **Environment Variables**:
   Set these in Render dashboard:
   ```
   ANTHROPIC_API_KEY=your_key_here
   TWILIO_ACCOUNT_SID=your_sid_here
   TWILIO_AUTH_TOKEN=your_token_here
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   MY_NUMBER=whatsapp:+your_number
   GOOGLE_PROJECT_ID=your_project_id
   ```

### 2. Deploy to Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Environment**: `Python 3.11`

### 3. Configure Webhook

After deployment, run the setup script:
```bash
python setup_webhook.py
```

Enter your Render URL (e.g., `https://your-app.onrender.com`)

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-api03-...` |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | `AC...` |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | `...` |
| `TWILIO_WHATSAPP_NUMBER` | Twilio WhatsApp number | `whatsapp:+14155238886` |
| `MY_NUMBER` | Your WhatsApp number | `whatsapp:+1234567890` |
| `GOOGLE_PROJECT_ID` | Google Cloud project ID | `my-project-123` |
| `WEBHOOK_SECRET` | Optional webhook security | `your-secret-key` |

### Google Cloud Setup

1. **Enable APIs**:
   ```bash
   gcloud services enable gmail.googleapis.com
   gcloud services enable pubsub.googleapis.com
   ```

2. **Create Pub/Sub Resources**:
   ```bash
   # Create topic
   gcloud pubsub topics create gmail-notifications
   
   # Create push subscription (replace YOUR_WEBHOOK_URL)
   gcloud pubsub subscriptions create gmail-notifications-sub \
     --topic=gmail-notifications \
     --push-endpoint=YOUR_WEBHOOK_URL/webhook/gmail
   ```

3. **Setup Gmail Watch**:
   ```bash
   python setup_webhook.py
   ```

## 🛠️ API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/webhook/gmail` | POST | Gmail notification webhook |
| `/test` | POST | Test email processing |

### Test the Service

```bash
# Health check
curl https://your-app.onrender.com/

# Test email processing
curl -X POST https://your-app.onrender.com/test
```

## 📁 Project Structure

```
├── app.py                 # Flask web service
├── setup_webhook.py      # Webhook configuration script
├── test_auth.py          # Authentication test script
├── Dockerfile            # Container definition
├── docker-compose.yml    # Local development setup
├── render.yaml           # Render deployment config
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── .dockerignore         # Docker ignore rules
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## 🔍 Monitoring and Logs

### Local Development
```bash
# View logs
docker-compose logs -f gmail-agent

# Check container status
docker-compose ps
```

### Render Production
- View logs in Render dashboard
- Monitor health at: `https://your-app.onrender.com/`
- Check metrics in Render dashboard

## 🐛 Troubleshooting

### Common Issues

1. **Webhook not receiving notifications**:
   ```bash
   # Check Pub/Sub subscription
   gcloud pubsub subscriptions describe gmail-notifications-sub
   
   # Test webhook manually
   curl -X POST https://your-app.onrender.com/test
   ```

2. **Authentication errors**:
   ```bash
   # Test authentication
   python test_auth.py
   ```

3. **Container issues**:
   ```bash
   # Check logs
   docker logs gmail-agent
   
   # Rebuild
   docker-compose up --build --force-recreate
   ```

### Gmail API Issues
- Ensure OAuth consent screen is configured
- Check that Gmail API is enabled
- Verify `credentials.json` is valid

### Twilio Issues
- Verify WhatsApp sandbox setup
- Check account balance
- Validate phone number format

## 🛡️ Circuit Breaker Protection

The system includes a circuit breaker to prevent infinite loops when processing fails repeatedly (e.g., when Claude models are deprecated).

### How it works:
- **Max attempts**: 3 failed attempts per message
- **Reset time**: 5 minutes after last failure
- **Behavior**: Skip messages that exceed failure limit

### Monitoring:
```bash
# Check circuit breaker status
curl https://your-app.onrender.com/circuit-breaker

# Reset circuit breaker (clear all failures)
curl -X POST https://your-app.onrender.com/circuit-breaker/reset

# Test circuit breaker functionality
python test_circuit_breaker.py
```

### Example response:
```json
{
  "max_attempts": 3,
  "reset_time_seconds": 300,
  "failed_messages": {
    "msg_123": {
      "failed_attempts": 2,
      "last_attempt_ago": "45s",
      "will_reset_in": "255s"
    }
  },
  "total_failed_messages": 1
}
```

## 🔒 Security

- All sensitive data in environment variables
- OAuth tokens stored securely
- Optional webhook authentication
- Container runs as non-root user
- No sensitive files in Docker image

## 📈 Scaling

- Render auto-scales based on traffic
- Stateless design for horizontal scaling
- Webhook architecture handles high throughput
- Consider Redis for session storage if needed

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.