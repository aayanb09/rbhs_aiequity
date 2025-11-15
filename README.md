# RBHS AIEP - AI-Powered Food Recognition & Health App

You can access the website at [rbhs-aiep.onrender.com](https://rbhs-aiep.onrender.com) (actually type the link into your browser, it won't work if you just click on it here). When you commit a change on GitHub, it will take a minute or so for it to update on the website (but it will do it automatically).

## 🚀 Deployment

### ✅ NOW WORKS ON NETLIFY!

**Want to deploy on Netlify?** We've made it work! 🎉

#### Quick Start (5 minutes):
```bash
cd netlify-deploy
bash deploy.sh
```

See [QUICK_START.md](QUICK_START.md) or [NETLIFY_DEPLOYMENT.md](NETLIFY_DEPLOYMENT.md) for full instructions.

### Current Deployment: Render ✅
This app is currently deployed on **Render**, which works great for Flask applications.

### Netlify Deployment (NEW!)
- **Option 1 (Hybrid):** Frontend on Netlify + Backend on Render
- **Option 2 (Full):** Everything on Netlify with serverless functions
- See `netlify-deploy/` folder for the Netlify-ready version

### Alternative Deployment Options
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions on deploying to:
- ✅ **Netlify** (static + hybrid - NEW!)
- ✅ **Render** (current - recommended)
- **Railway** (easy alternative)
- **Fly.io** (production-ready)
- **Vercel** (serverless)
- **Heroku** (classic)
- **Docker** (any container platform)

## 🛠️ Technology Stack
- **Backend:** Flask (Python)
- **APIs:** Clarifai (food recognition), Google Gemini (AI advice)
- **Deployment:** Render
- **Server:** Gunicorn

## 📦 Files Included
- `main.py` - Flask application
- `requirements.txt` - Python dependencies
- `Procfile` - Process configuration for deployment
- `render.yaml` - Render deployment config
- `railway.json` - Railway deployment config
- `fly.toml` - Fly.io deployment config
- `vercel.json` - Vercel deployment config
- `Dockerfile` - Container deployment config
- `netlify.toml` - Reference only (Netlify doesn't support Flask)

## 🔐 Environment Variables Required
- `CLARIFAI_PAT` - Clarifai API key
- `GOOGLE_API_KEY` - Google Gemini API key

## 📚 Learn More
Read the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive deployment instructions and platform comparisons.
