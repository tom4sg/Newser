import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const API_URL = process.env.REACT_APP_API_URL || window.location.origin;

  useEffect(() => {
    // Log the API URL when component mounts
    console.log('Environment:', {
      REACT_APP_API_URL: process.env.REACT_APP_API_URL,
      origin: window.location.origin,
      finalApiUrl: API_URL
    });
  }, []);

  const handleSendMessage = async (message) => {
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
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        console.log('Health check response:', data);
      } catch (error) {
        console.error('Health check failed:', error);
      }
    };
    checkHealth();
  }, [API_URL]);

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-center mb-8">
          LangChain Tavily Agent Chat
        </h1>
        <div className="text-center mb-4 text-sm text-gray-600">
          API URL: {API_URL}
        </div>
        <ChatInterface 
          messages={messages} 
          onSendMessage={handleSendMessage} 
        />
      </div>
    </div>
  );
}

export default App; 