import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  
  // Get the API URL from environment variable
  const API_URL = process.env.REACT_APP_API_URL;
  
  useEffect(() => {
    // Check if API_URL is properly configured (logging only for debugging)
    if (!API_URL) {
      console.error('REACT_APP_API_URL is not set! Please configure it in Vercel.');
    } else if (API_URL.includes('vercel.app')) {
      console.error('REACT_APP_API_URL should point to your Railway deployment, not Vercel!');
    }
  }, [API_URL]);

  const handleSendMessage = async (message) => {
    // Don't proceed if API_URL is not set
    if (!API_URL) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I cannot process your message at the moment. Please try again later.' 
      }]);
      return;
    }

    // Add user message to chat
    setMessages(prev => [...prev, { role: 'user', content: message }]);

    try {
      const fullUrl = `${API_URL}/api/chat`;
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status} - ${JSON.stringify(data)}`);
      }

      // Add AI response to chat
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.response || 'No response received from the server' 
      }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, there was an error processing your message. Please try again.' 
      }]);
    }
  };

  // Try to connect to health endpoint on mount
  useEffect(() => {
    if (!API_URL) return;

    const checkHealth = async () => {
      try {
        await fetch(`${API_URL}/health`);
      } catch (error) {
        console.error('Health check failed:', error);
      }
    };
    checkHealth();
  }, [API_URL]);

  return (
    <div className="min-h-screen bg-white">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center mb-8 text-text-primary">
          GutiGPT
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