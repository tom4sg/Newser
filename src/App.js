import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [apiUrlWarning, setApiUrlWarning] = useState('');
  
  // Get the API URL from environment variable
  const API_URL = process.env.REACT_APP_API_URL;
  
  useEffect(() => {
    // Check if API_URL is properly configured
    if (!API_URL) {
      console.error('REACT_APP_API_URL is not set! Please configure it in Vercel.');
      setApiUrlWarning('Warning: API URL is not configured. Please set REACT_APP_API_URL in Vercel settings.');
    } else if (API_URL.includes('vercel.app')) {
      console.error('REACT_APP_API_URL should point to your Railway deployment, not Vercel!');
      setApiUrlWarning('Warning: API URL is incorrectly pointing to Vercel instead of Railway.');
    } else {
      console.log('Using API URL:', API_URL);
    }
  }, [API_URL]);

  const handleSendMessage = async (message) => {
    // Don't proceed if API_URL is not set
    if (!API_URL) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Error: Backend API URL is not configured. Please set REACT_APP_API_URL in Vercel settings.' 
      }]);
      return;
    }

    // Add user message to chat
    setMessages(prev => [...prev, { role: 'user', content: message }]);

    try {
      const fullUrl = `${API_URL}/api/chat`;
      console.log('Making request to:', fullUrl);
      console.log('Request body:', { message });

      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      const data = await response.json();
      console.log('Response data:', data);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status} - ${JSON.stringify(data)}`);
      }

      // Add AI response to chat
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.response || 'No response received from the server' 
      }]);
    } catch (error) {
      console.error('Full error details:', {
        message: error.message,
        stack: error.stack,
        error
      });
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error: ${error.message}\n\nPlease check the browser console for more details.` 
      }]);
    }
  };

  // Try to connect to health endpoint on mount
  useEffect(() => {
    if (!API_URL) return;

    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        console.log('Health check response:', data);
      } catch (error) {
        console.error('Health check failed:', error);
        setApiUrlWarning('Warning: Could not connect to backend API. Please verify the API URL and ensure the backend is running.');
      }
    };
    checkHealth();
  }, [API_URL]);

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-center mb-8">
          Chat with me!
        </h1>
        <ChatInterface 
          messages={messages} 
          onSendMessage={handleSendMessage} 
        />
      </div>
    </div>
  );
}

export default App; 