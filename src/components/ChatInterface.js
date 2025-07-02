import React, { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';

const ChatInterface = ({ messages, onSendMessage }) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-border overflow-hidden">
      {/* Messages container */}
      <div className="h-[600px] overflow-y-auto p-6 bg-white">
        {messages.length === 0 && (
          <div className="text-center text-text-secondary mt-8">
            <p className="text-lg">Start a conversation with GutiGPT</p>
            <p className="text-sm mt-2">Ask me anything!</p>
          </div>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            className={`mb-4 ${
              message.role === 'user' ? 'text-right' : 'text-left'
            }`}
          >
            <div
              className={`inline-block max-w-[70%] rounded-2xl p-4 shadow-sm ${
                message.role === 'user'
                  ? 'bg-primary text-white'
                  : 'bg-gray-lighter text-text-primary'
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit} className="border-t border-gray-border p-6 bg-white">
        <div className="flex space-x-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 rounded-xl border border-gray-border p-3 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent bg-white text-text-primary placeholder-text-secondary transition-all"
          />
          <button
            type="submit"
            className="bg-primary text-white rounded-xl px-6 py-3 hover:bg-primary-dark transition-colors duration-200 shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={!input.trim()}
          >
            <PaperAirplaneIcon className="h-5 w-5" />
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface; 