const axios = require('axios');

async function testConnection() {
  try {
    console.log('Testing connection to backend...');
    const response = await axios.get('http://localhost:8000/');
    console.log('Backend root endpoint response:', response.data);
    
    const latestResponse = await axios.get('http://localhost:8000/content/latest?page=1');
    console.log('Latest content response:', latestResponse.data);
    
    console.log('Test completed successfully!');
  } catch (error) {
    console.error('Error testing connection:', error.message);
  }
}

testConnection();