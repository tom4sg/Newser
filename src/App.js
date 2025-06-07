import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const API_URL = process.env.REACT_APP_API_URL || window.location.origin;

  const handleSendMessage = async (message) => {
    // Add user message to chat
    setMessages(prev => [...prev, { role: 'user', content: message }]);

    try {
      console.log('Sending request to:', `${API_URL}/api/chat`);
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();
      console.log('Response data:', data);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status} - ${data.detail || 'Unknown error'}`);
      }

      // Add AI response to chat
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      console.error('Error details:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error: ${error.message}\n\nPlease check the browser console for more details.` 
      }]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-center mb-8">
          LangChain Tavily Agent Chat
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