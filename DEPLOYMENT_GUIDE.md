# Deployment Guide for RBHS AIEP Flask Application

## ⚠️ Important Note About Netlify

**Netlify does not support Flask applications** because it's designed for:
- Static sites (HTML, CSS, JavaScript)
- Serverless functions (limited Python support)

Your Flask app needs a traditional server or container-based hosting platform.

---

## ✅ Recommended Deployment Platforms

### 1. **Render** (Currently Used) ⭐ RECOMMENDED
Your app is already on Render: https://rbhs-aiep.onrender.com

**Advantages:**
- Already configured with `render.yaml`
- Auto-deploys from GitHub
- Free tier available
- Great for Flask/Python apps

**Steps:**
1. Already set up! Just push to GitHub
2. Render auto-deploys changes
3. Set environment variables in Render dashboard:
   - `CLARIFAI_PAT`
   - `GOOGLE_API_KEY`

---

### 2. **Railway** ⭐ GREAT ALTERNATIVE

**Why Railway:**
- Simple deployment
- Free $5/month credit
- Great developer experience

**Steps:**
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Initialize project
railway init

# 4. Add environment variables
railway variables set CLARIFAI_PAT=your_key
railway variables set GOOGLE_API_KEY=your_key

# 5. Deploy
railway up
```

Configuration file already created: `railway.json`

---

### 3. **Fly.io** ⭐ PRODUCTION-READY

**Why Fly.io:**
- Global edge deployment
- Free tier includes 3 VMs
- Fast and reliable

**Steps:**
```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Login
fly auth login

# 3. Launch app
fly launch

# 4. Set secrets
fly secrets set CLARIFAI_PAT=your_key
fly secrets set GOOGLE_API_KEY=your_key

# 5. Deploy
fly deploy
```

Configuration file already created: `fly.toml`

---

### 4. **Vercel** (With Python Runtime)

**Why Vercel:**
- Good for serverless
- Fast deployments
- Generous free tier

**Steps:**
```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Login
vercel login

# 3. Deploy
vercel

# 4. Add environment variables via dashboard
```

Configuration file already created: `vercel.json`

---

### 5. **Heroku** (Classic Choice)

**Why Heroku:**
- Well-established platform
- Easy to use
- Many tutorials available

**Steps:**
```bash
# 1. Install Heroku CLI
# Download from: https://devcenter.heroku.com/articles/heroku-cli

# 2. Login
heroku login

# 3. Create app
heroku create rbhs-aiep

# 4. Add environment variables
heroku config:set CLARIFAI_PAT=your_key
heroku config:set GOOGLE_API_KEY=your_key

# 5. Deploy
git push heroku main
```

Files needed:
- ✅ `Procfile` (already exists)
- ✅ `requirements.txt` (already exists)

---

### 6. **Docker Deployment** (Any Container Platform)

Use the included `Dockerfile` to deploy on:
- Google Cloud Run
- AWS ECS
- Azure Container Apps
- DigitalOcean App Platform

**Steps:**
```bash
# Build image
docker build -t rbhs-aiep .

# Run locally to test
docker run -p 5000:5000 \
  -e CLARIFAI_PAT=your_key \
  -e GOOGLE_API_KEY=your_key \
  rbhs-aiep

# Push to registry and deploy on your chosen platform
```

---

## 🚫 Why NOT Netlify?

| Feature | Netlify | Your Flask App Needs |
|---------|---------|---------------------|
| Server Type | Static/Serverless | Always-on Python server |
| Python Support | Limited functions | Full Flask framework |
| Runtime | Short-lived | Persistent connections |
| Best For | React/Vue/Static | Backend APIs/Flask |

---

## 📊 Platform Comparison

| Platform | Free Tier | Best For | Difficulty |
|----------|-----------|----------|------------|
| **Render** | ✅ 750 hrs/month | Current setup | ⭐ Easy |
| **Railway** | ✅ $5 credit | Quick deploys | ⭐ Easy |
| **Fly.io** | ✅ 3 VMs | Production | ⭐⭐ Medium |
| **Vercel** | ✅ Generous | Serverless | ⭐⭐ Medium |
| **Heroku** | ⚠️ Paid only | Traditional | ⭐ Easy |
| **Docker** | Varies | Flexibility | ⭐⭐⭐ Advanced |

---

## 🔧 Environment Variables Needed

Make sure to set these on your chosen platform:

```
CLARIFAI_PAT=your_clarifai_api_key
GOOGLE_API_KEY=your_google_api_key
```

---

## 📝 Current Status

✅ Your app is already deployed on **Render**
✅ Configuration files created for multiple platforms
✅ Ready to deploy to any alternative platform

---

## 💡 Recommendation

**Stick with Render** (your current platform) unless you have specific needs:
- It's already working
- Auto-deploys from GitHub
- Great for Flask apps
- Free tier is sufficient

If you want to try alternatives, **Railway** or **Fly.io** are excellent choices!

---

## 🆘 Need Help?

1. **Staying on Render:** Just push to GitHub, it auto-deploys
2. **Trying Railway:** Run `railway init` and `railway up`
3. **Trying Fly.io:** Run `fly launch` and follow prompts
4. **Questions:** Check each platform's documentation

---

## 📚 Additional Resources

- [Render Docs](https://render.com/docs)
- [Railway Docs](https://docs.railway.app/)
- [Fly.io Docs](https://fly.io/docs/)
- [Vercel Python Docs](https://vercel.com/docs/functions/runtimes/python)
- [Heroku Python Docs](https://devcenter.heroku.com/articles/getting-started-with-python)
