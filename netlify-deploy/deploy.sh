#!/bin/bash

# RBHS AIEP - Netlify Deployment Script
# This script helps you deploy to Netlify in one command

set -e

echo "🚀 RBHS AIEP - Netlify Deployment"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "netlify.toml" ]; then
    echo "❌ Error: Please run this script from the netlify-deploy directory"
    echo "   cd netlify-deploy && bash deploy.sh"
    exit 1
fi

# Check if netlify CLI is installed
if ! command -v netlify &> /dev/null; then
    echo "📦 Netlify CLI not found. Installing..."
    npm install -g netlify-cli
    echo "✅ Netlify CLI installed!"
    echo ""
fi

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo "✅ Dependencies installed!"
    echo ""
fi

# Check if user is logged in
echo "🔐 Checking Netlify authentication..."
if ! netlify status &> /dev/null; then
    echo "Please login to Netlify:"
    netlify login
    echo ""
fi

# Ask which deployment option
echo "🎯 Choose your deployment option:"
echo ""
echo "1. Hybrid Mode (Recommended)"
echo "   Frontend: Netlify | Backend: Render"
echo "   ✅ Easiest | ✅ No env vars needed | ✅ 5 minutes"
echo ""
echo "2. Full Netlify Mode"
echo "   Frontend: Netlify | Backend: Netlify Functions"
echo "   ⚠️  Requires env vars | ⚡ Serverless"
echo ""
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "2" ]; then
    echo ""
    echo "📝 Switching to Full Netlify mode..."
    
    # Update config.js
    cat > public/config.js << 'EOF'
// Configuration for API endpoints
const CONFIG = {
  // Using Netlify Functions (serverless)
  API_BASE_URL: '/.netlify/functions',
  
  USE_NETLIFY_FUNCTIONS: true
};

// Export for use in other scripts
window.CONFIG = CONFIG;
EOF
    
    echo "✅ Config updated to use Netlify Functions"
    echo ""
    echo "⚠️  IMPORTANT: You need to set environment variables in Netlify:"
    echo "   1. After deployment, go to Site settings → Environment variables"
    echo "   2. Add: CLARIFAI_PAT"
    echo "   3. Add: GOOGLE_API_KEY"
    echo ""
    read -p "Press Enter to continue with deployment..."
else
    echo ""
    echo "✅ Using Hybrid mode (Netlify + Render)"
    echo "   Your backend will continue to run on Render"
    echo ""
fi

# Deploy to Netlify
echo ""
echo "🚀 Deploying to Netlify..."
echo ""

# Check if site already exists
if netlify status &> /dev/null; then
    echo "📤 Deploying to existing site..."
    netlify deploy --prod
else
    echo "🆕 Creating new site..."
    netlify deploy --prod
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📝 Next steps:"
echo ""

if [ "$choice" = "2" ]; then
    echo "1. Go to your Netlify dashboard"
    echo "2. Set environment variables (Site settings → Environment variables):"
    echo "   - CLARIFAI_PAT"
    echo "   - GOOGLE_API_KEY"
    echo "3. Redeploy: netlify deploy --prod"
    echo "4. Test your app!"
else
    echo "1. Visit your Netlify URL"
    echo "2. Test the upload functionality"
    echo "3. Enjoy your app on Netlify! 🎊"
fi

echo ""
