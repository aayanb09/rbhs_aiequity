// Configuration for API endpoints
const CONFIG = {
  // Change this to your Render backend URL
  API_BASE_URL: 'https://rbhs-aiep.onrender.com',
  
  // Or use Netlify Functions (serverless)
  // API_BASE_URL: '/.netlify/functions',
  
  // Toggle between Render backend or Netlify Functions
  USE_NETLIFY_FUNCTIONS: false
};

// Export for use in other scripts
window.CONFIG = CONFIG;
