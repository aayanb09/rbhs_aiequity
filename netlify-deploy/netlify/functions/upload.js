// Netlify Function to proxy the food identification API
const fetch = require('node-fetch');

exports.handler = async (event, context) => {
  // Only allow POST requests
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method Not Allowed' })
    };
  }

  try {
    const data = JSON.parse(event.body);
    const base64_image = data.image;

    if (!base64_image) {
      return {
        statusCode: 400,
        body: JSON.stringify({ error: 'No image provided' })
      };
    }

    console.log('Processing food identification request');

    // Get API keys from environment variables
    const CLARIFAI_PAT = process.env.CLARIFAI_PAT;
    const GOOGLE_API_KEY = process.env.GOOGLE_API_KEY;

    if (!CLARIFAI_PAT) {
      return {
        statusCode: 500,
        body: JSON.stringify({ error: 'CLARIFAI_PAT not configured' })
      };
    }

    // Call Clarifai API
    const clarifaiResponse = await fetch(
      'https://api.clarifai.com/v2/models/food-item-v1-recognition/outputs',
      {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Authorization': `Key ${CLARIFAI_PAT}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_app_id: {
            user_id: 'clarifai',
            app_id: 'main'
          },
          inputs: [{
            data: {
              image: {
                base64: base64_image
              }
            }
          }]
        })
      }
    );

    if (!clarifaiResponse.ok) {
      const errorData = await clarifaiResponse.json();
      return {
        statusCode: clarifaiResponse.status,
        body: JSON.stringify(errorData)
      };
    }

    const clarifaiData = await clarifaiResponse.json();

    // Get concepts and add Gemini advice if available
    if (clarifaiData.outputs?.[0]?.data?.concepts?.length > 0) {
      const concepts = clarifaiData.outputs[0].data.concepts;
      const maxConfidence = concepts[0].value;
      const topItems = concepts.filter(c => Math.abs(c.value - maxConfidence) < 0.001);

      // Pick best item (avoid generic terms)
      const genericTerms = ['food', 'dish', 'meal', 'plate', 'cuisine'];
      let bestItem = null;
      
      for (const item of topItems) {
        const name = item.name.toLowerCase();
        if (!genericTerms.some(term => name.includes(term))) {
          if (!bestItem || name.length > bestItem.name.length) {
            bestItem = item;
          }
        }
      }
      
      if (!bestItem) {
        bestItem = topItems[0];
      }

      // TODO: Add Gemini API integration if needed
      // For now, add a placeholder
      if (GOOGLE_API_KEY) {
        clarifaiData.outputs[0].data.concepts[0].gemini_advice = 
          `This is ${bestItem.name}. For detailed nutritional advice, the Gemini integration needs to be configured.`;
      }
    }

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify(clarifaiData)
    };

  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
};
