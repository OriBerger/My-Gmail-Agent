# פריסת Gmail Agent ב-Render - מדריך בעברית

## 🎯 הפתרון הפשוט לטוקן Gmail

הסוכן זקוק לקובץ `token.json` כדי להתחבר לג'ימייל. הדרך הכי פשוטה למפתחים היא להשתמש במשתנה סביבה ב-Render.

## 📋 שלבי הפריסה

### שלב 1: הכנת הטוקן
```bash
# הרץ את הסקריפט להוצאת הטוכן
python get_token_for_render.py
```

הסקריפט יציג לך טקסט כזה:
```json
{"token":"ya29.a0ATkoCc4DORr...","refresh_token":"1//03Xqmdjj..."}
```

**העתק את כל הטקסט הזה!**

### שלב 2: העלאה ל-GitHub
```bash
git init
git add .
git commit -m "Gmail Agent ready for Render"
git remote add origin https://github.com/YOUR_USERNAME/gmail-agent.git
git push -u origin main
```

### שלב 3: יצירת שירות ב-Render
1. כנס ל-[Render Dashboard](https://dashboard.render.com/)
2. לחץ "New" → "Web Service"
3. חבר את ה-GitHub repository שלך
4. הגדר:
   - **Name**: `gmail-agent`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`

### שלב 4: הגדרת משתני סביבה
ב-Render Dashboard → Environment, הוסף:

| משתנה | ערך |
|-------|-----|
| `ANTHROPIC_API_KEY` | המפתח שלך מ-Claude |
| `TWILIO_ACCOUNT_SID` | מ-Twilio |
| `TWILIO_AUTH_TOKEN` | מ-Twilio |
| `TWILIO_WHATSAPP_NUMBER` | `whatsapp:+14155238886` |
| `MY_NUMBER` | `whatsapp:+972523640773` |
| `GOOGLE_PROJECT_ID` | `project-adccce59-2a50-4dce-87f` |
| `GMAIL_TOKEN_JSON` | **הדבק כאן את הטקסט מהשלב 1** |

### שלב 5: פריסה
לחץ "Deploy" ב-Render. התהליך יקח כמה דקות.

## 🔧 הגדרת Webhook אחרי הפריסה

אחרי שהשירות עולה, תקבל URL כמו:
```
https://gmail-agent-xyz.onrender.com
```

### הגדרת Google Pub/Sub
ב-Google Cloud Shell:
```bash
# מחק את המנוי הקיים
gcloud pubsub subscriptions delete gmail-notifications-sub \
    --project=project-adccce59-2a50-4dce-87f

# צור מנוי חדש עם push
gcloud pubsub subscriptions create gmail-notifications-sub \
    --topic=gmail-notifications \
    --push-endpoint=https://gmail-agent-xyz.onrender.com/webhook/gmail \
    --project=project-adccce59-2a50-4dce-87f
```

### הפעלת Gmail Watch
```bash
python setup_webhook.py
```
הכנס את ה-URL של Render כשהסקריפט יבקש.

## ✅ בדיקה שהכל עובד

### בדיקת בריאות
```bash
curl https://gmail-agent-xyz.onrender.com/
```

צריך להחזיר:
```json
{"status": "healthy", "service": "Gmail Agent"}
```

### בדיקת עיבוד מייל
```bash
curl -X POST https://gmail-agent-xyz.onrender.com/test
```

### שלח לעצמך מייל
שלח מייל לעצמך ובדוק שמגיעה הודעת WhatsApp עם סיכום.

## 🔒 אבטחה

- ✅ הטוקן נשמר כמשתנה סביבה (לא בקוד)
- ✅ קבצים רגישים לא נכללים ב-Docker image
- ✅ כל הנתונים הרגישים מוגנים

## 🚨 פתרון בעיות נפוצות

### השירות לא עולה
- בדוק את הלוגים ב-Render Dashboard
- וודא שכל משתני הסביבה מוגדרים

### לא מגיעים webhooks
- בדוק שה-Pub/Sub subscription מוגדר נכון
- וודא שה-URL נכון

### שגיאות אימות
- בדוק שה-GMAIL_TOKEN_JSON תקין
- הרץ `python test_auth.py` מקומית לוודא שהטוקן עובד

## 📞 תמיכה

אם יש בעיות:
1. בדוק את הלוגים ב-Render
2. הרץ את הבדיקות המקומיות:
   ```bash
   python test_flask.py
   python test_env_token.py
   python security_check.py
   ```

## 🎉 סיכום

עכשיו יש לך Gmail Agent שרץ בענן עם:
- 📧 עיבוד מיילים בזמן אמת
- 🤖 סיכום מיילים עם AI
- 📱 הודעות WhatsApp
- ☁️ פריסה מקצועית בענן

**מזל טוב! הסוכן שלך עובד!** 🚀