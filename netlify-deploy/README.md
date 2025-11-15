# RBHS AIEP - Netlify Deployment

This directory contains the Netlify-compatible version of the RBHS AIEP application.

## 🎯 Two Deployment Options

### Option 1: Static Frontend + Render Backend (Recommended)
- Frontend hosted on Netlify (fast, free)
- Backend stays on Render (your current setup)
- No code changes needed to backend
- **Status: ✅ Ready to deploy**

### Option 2: Full Netlify (Functions + Frontend)
- Frontend on Netlify
- Backend as Netlify Functions (serverless)
- Requires environment variables setup
- **Status: ✅ Ready to deploy**

---

## 🚀 Quick Start

### Prerequisites
```bash
npm install -g netlify-cli
```

### Deploy to Netlify

#### Step 1: Install dependencies
```bash
cd netlify-deploy
npm install
```

#### Step 2: Choose your approach

**Option A: Use Render Backend (Easiest)**
No changes needed! The frontend is already configured to call your Render backend.

**Option B: Use Netlify Functions**
Edit `public/config.js`:
```javascript
const CONFIG = {
  API_BASE_URL: '/.netlify/functions',
  USE_NETLIFY_FUNCTIONS: true
};
```

#### Step 3: Deploy
```bash
# Login to Netlify
netlify login

# Deploy to production
netlify deploy --prod

# Or initialize and link first
netlify init
netlify deploy --prod
```

---

## 🔐 Environment Variables

If using **Netlify Functions** (Option 2), set these in Netlify dashboard:

1. Go to: Site settings → Environment variables
2. Add:
   - `CLARIFAI_PAT` - Your Clarifai API key
   - `GOOGLE_API_KEY` - Your Google Gemini API key

Or set via CLI:
```bash
netlify env:set CLARIFAI_PAT "your_clarifai_key"
netlify env:set GOOGLE_API_KEY "your_google_key"
```

---

## 📁 Directory Structure

```
netlify-deploy/
├── public/                 # Static files (HTML, CSS, JS)
│   ├── index.html         # Main page (converted from welcome.html)
│   ├── home.html          # Landing page
│   ├── upload.html        # Food upload
│   ├── reminders.html     # Reminders
│   ├── symptom-tracker.html
│   ├── glucose.html
│   ├── settings.html
│   ├── config.js          # API configuration
│   └── static/            # Images, etc.
├── netlify/
│   └── functions/         # Serverless functions
│       └── upload.js      # Food identification API
├── netlify.toml           # Netlify configuration
├── package.json           # Dependencies
└── README.md             # This file
```

---

## 🔄 How It Works

### Architecture

```
User Browser
    ↓
Netlify CDN (Static HTML/CSS/JS)
    ↓
    ├─→ Option 1: Render Backend API (https://rbhs-aiep.onrender.com)
    └─→ Option 2: Netlify Functions (Serverless)
```

### Option 1: Hybrid Deployment
1. User visits: `your-site.netlify.app`
2. Netlify serves static HTML/CSS/JS
3. JavaScript calls: `https://rbhs-aiep.onrender.com/upload`
4. Render processes request and returns data
5. JavaScript displays results

**Pros:**
- ✅ No backend changes needed
- ✅ Fastest deployment
- ✅ Backend stays on Render (already working)
- ✅ Netlify only hosts static files (free)

**Cons:**
- ⚠️ Requires CORS headers on Render backend
- ⚠️ Two separate deployments to manage

### Option 2: Full Netlify
1. User visits: `your-site.netlify.app`
2. Netlify serves static HTML/CSS/JS
3. JavaScript calls: `your-site.netlify.app/.netlify/functions/upload`
4. Netlify Function processes request
5. JavaScript displays results

**Pros:**
- ✅ Everything on Netlify (single platform)
- ✅ No CORS issues
- ✅ Netlify's global CDN

**Cons:**
- ⚠️ Serverless functions have timeouts
- ⚠️ Cold starts possible
- ⚠️ Need to migrate all backend logic

---

## 🛠️ Development

### Local Development
```bash
cd netlify-deploy
npm install

# Start local dev server with functions
netlify dev
```

Visit: `http://localhost:8888`

---

## 🔧 Troubleshooting

### CORS Errors (Option 1)
If using Render backend, add CORS headers to your Flask app:

```python
from flask_cors import CORS
CORS(app, origins=['https://your-site.netlify.app'])
```

Or add to `requirements.txt`:
```
flask-cors
```

### Function Timeout (Option 2)
Netlify Functions timeout after 10 seconds (free tier) or 26 seconds (paid).
If API calls take longer, use Option 1.

### Missing Environment Variables
Check Netlify dashboard → Site settings → Environment variables

---

## 📊 Performance

### Option 1 (Recommended)
- Frontend: ⚡ Instant (Netlify CDN)
- Backend: ~500ms-2s (Render)
- Total: ~500ms-2s

### Option 2 (Functions)
- Frontend: ⚡ Instant (Netlify CDN)
- Backend: ~100ms-1s (+ cold start)
- Total: ~100ms-3s (with cold start)

---

## 🎉 Success Checklist

- [ ] Run `npm install` in `netlify-deploy/`
- [ ] Choose Option 1 or Option 2
- [ ] Configure `public/config.js` accordingly
- [ ] Run `netlify login`
- [ ] Run `netlify deploy --prod`
- [ ] Set environment variables (if Option 2)
- [ ] Test all pages
- [ ] Verify upload functionality

---

## 📚 Additional Resources

- [Netlify Functions Docs](https://docs.netlify.com/functions/overview/)
- [Netlify Deploy Docs](https://docs.netlify.com/site-deploys/overview/)
- [Netlify CLI Docs](https://docs.netlify.com/cli/get-started/)

---

## 🆘 Need Help?

1. **CORS issues**: Add flask-cors to backend
2. **Function errors**: Check Netlify function logs
3. **Missing pages**: Run `../convert_to_static.py` again
4. **API not working**: Verify environment variables

---

## 🎯 Recommended Deployment

**For easiest deployment: Use Option 1**
1. Deploy this Netlify site (static files only)
2. Keep backend on Render (already working)
3. Update CORS headers on backend if needed
4. Done! 🎉
