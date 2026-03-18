# 🚀 Gmail Agent Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Environment Setup
- [ ] All API keys added to `.env` file
- [ ] `credentials.json` file present (Gmail API)
- [ ] `token.json` generated (run `python test_auth.py`)
- [ ] Test Flask app works (`python test_flask.py`)

### 2. Google Cloud Configuration
- [ ] Gmail API enabled
- [ ] Cloud Pub/Sub API enabled
- [ ] Topic `gmail-notifications` created
- [ ] Subscription `gmail-notifications-sub` created
- [ ] Project ID matches `.env` file

### 3. Docker Testing (Optional)
- [ ] Docker and Docker Compose installed
- [ ] Test locally: `docker-compose up --build`
- [ ] Health check passes: `curl http://localhost:5000/`

## 🌐 Render Deployment Steps

### 1. Repository Setup
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit: Gmail Agent with webhook support"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/gmail-agent.git
git push -u origin main
```

### 2. Render Service Creation
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure service:
   - **Name**: `gmail-agent`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Plan**: `Free` (or paid for better performance)

### 3. Environment Variables Setup
Add these in Render dashboard → Environment:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
MY_NUMBER=whatsapp:+YOUR_NUMBER
GOOGLE_PROJECT_ID=project-adccce59-2a50-4dce-87f
WEBHOOK_SECRET=your-random-secret-key
GMAIL_TOKEN_JSON={"token":"ya29.a0ATkoC...","refresh_token":"1//03Xqm..."}
```

**IMPORTANT: Getting the GMAIL_TOKEN_JSON value:**
1. Run: `python get_token_for_render.py`
2. Copy the entire JSON string output
3. Paste it as the value for GMAIL_TOKEN_JSON in Render

### 4. File Upload (Important!)
Since Render doesn't support file uploads via dashboard, you need to:

**Option A: Include in repository (NOT recommended for security)**
- Add `credentials.json` and `token.json` to repository
- Make sure `.gitignore` excludes them from public repos

**Option B: Use environment variables (Recommended)**
- Convert `credentials.json` to base64 and store as env var
- Modify `app.py` to decode from env var

**Option C: Use Google Cloud Service Account (Best for production)**
- Create service account in Google Cloud Console
- Download service account key
- Use service account authentication instead of OAuth

## 🔧 Post-Deployment Configuration

### 1. Get Your Webhook URL
After Render deployment, you'll get a URL like:
```
https://gmail-agent-xyz.onrender.com
```

### 2. Configure Google Pub/Sub Push
Run this command in Google Cloud Shell:
```bash
gcloud pubsub subscriptions modify gmail-notifications-sub \
    --push-endpoint=https://gmail-agent-xyz.onrender.com/webhook/gmail \
    --project=project-adccce59-2a50-4dce-87f
```

### 3. Setup Gmail Watch
Run the setup script:
```bash
python setup_webhook.py
```
Enter your Render URL when prompted.

### 4. Test the Deployment
```bash
# Health check
curl https://gmail-agent-xyz.onrender.com/

# Test email processing (if you have unread emails)
curl -X POST https://gmail-agent-xyz.onrender.com/test
```

## 🧪 Testing

### 1. Send Test Email
1. Send yourself an email
2. Check Render logs for webhook activity
3. Verify WhatsApp message received

### 2. Monitor Logs
- Render Dashboard → Your Service → Logs
- Look for webhook notifications and processing messages

### 3. Debug Common Issues
- **No webhook calls**: Check Pub/Sub push subscription configuration
- **Authentication errors**: Verify credentials and scopes
- **Twilio errors**: Check account balance and phone number format

## 🔒 Security Considerations

### Production Recommendations
1. **Use Service Account**: Replace OAuth with service account
2. **Enable Webhook Authentication**: Uncomment auth check in webhook endpoint
3. **Use HTTPS**: Render provides HTTPS by default
4. **Environment Variables**: Never commit secrets to repository
5. **Rate Limiting**: Consider adding rate limiting for webhook endpoint

### Service Account Setup (Recommended)
```bash
# Create service account
gcloud iam service-accounts create gmail-agent \
    --display-name="Gmail Agent Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:gmail-agent@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber"

# Create and download key
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=gmail-agent@PROJECT_ID.iam.gserviceaccount.com
```

## 📊 Monitoring

### Health Checks
- Render automatically monitors: `https://your-app.onrender.com/`
- Set up external monitoring (e.g., UptimeRobot) for additional reliability

### Logging
- Render provides built-in logging
- Consider external logging service for production (e.g., Papertrail)

### Metrics
- Monitor webhook response times
- Track email processing success rate
- Monitor Twilio message delivery

## 🚨 Troubleshooting

### Common Issues
1. **Service won't start**: Check build logs in Render dashboard
2. **Webhook not receiving data**: Verify Pub/Sub push subscription
3. **Authentication failures**: Check token expiration and refresh
4. **Twilio errors**: Verify account status and phone number format

### Debug Commands
```bash
# Test authentication locally
python test_auth.py

# Test Flask app locally
python test_flask.py

# Check Pub/Sub subscription
gcloud pubsub subscriptions describe gmail-notifications-sub
```

## ✅ Final Checklist

- [ ] Service deployed successfully on Render
- [ ] Environment variables configured
- [ ] Webhook URL configured in Pub/Sub
- [ ] Gmail watch activated
- [ ] Test email processed successfully
- [ ] WhatsApp notification received
- [ ] Logs showing healthy operation

## 🎉 Success!

Your Gmail Agent is now running in production with:
- ⚡ Real-time webhook notifications
- 🤖 AI-powered email summarization
- 📱 WhatsApp notifications
- 🐳 Containerized deployment
- ☁️ Cloud-native architecture

Monitor the logs and enjoy your automated Gmail assistant!