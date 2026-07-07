import React, { useState, useRef } from 'react';

export default function ChatSection() {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const sessionId = useRef(null);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      type: 'text',
      content: 'Halo! Saya asisten reservasi laboratorium. Saya dapat membantu kamu memesan ruang lab, cek ketersediaan, atau batalkan reservasi.',
      time: ''
    }
  ]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    setMessages((prev) => [...prev, { role: 'user', type: 'text', content: userMessage, time: currentTime }]);
    setInput('');
    setIsLoading(true);

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (import.meta.env.VITE_API_TOKEN) {
        headers['Authorization'] = `Bearer ${import.meta.env.VITE_API_TOKEN}`;
      }
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers,
        body: JSON.stringify({ message: userMessage, session_id: sessionId.current })
      });
      const data = await response.json();

      sessionId.current = data.session_id;
      
      setMessages((prev) => [...prev, { 
        role: 'assistant', 
        type: 'text', 
        content: data.reply, 
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
      }]);
    } catch (error) {
      console.error("Error connecting to backend:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col relative bg-[#FAFBFF] h-full">
      {/* Header Chat */}
      <div className="h-[76px] bg-white border-b border-gray-200 flex items-center px-8 shadow-sm shrink-0">
        <div className="flex items-center space-x-4">
          <div className="w-11 h-11 bg-[#EEF2FF] rounded-full flex items-center justify-center text-blue-600 text-lg">🤖</div>
          <div>
            <h3 className="font-bold text-gray-900 text-[15px]">Asisten Reservasi Lab</h3>
            <p className="text-xs text-green-600 font-semibold mt-0.5">● Online</p>
          </div>
        </div>
      </div>

      {/* Area Pesan */}
      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {messages.map((msg, index) => (
          <div key={index} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className="flex items-end space-x-2 max-w-[75%]">
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-[#EEF2FF] flex-shrink-0 flex items-center justify-center text-blue-600 text-sm mb-1">🤖</div>
              )}
              <div className={`p-4 rounded-3xl text-[15px] leading-relaxed shadow-sm whitespace-pre-wrap ${msg.role === 'user' ? 'bg-[#1C5CE5] text-white rounded-br-sm' : 'bg-white text-gray-700 border border-gray-200 rounded-bl-sm'}`}>
                {msg.content}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex items-end space-x-2">
            <div className="w-8 h-8 rounded-full bg-[#EEF2FF] flex-shrink-0 flex items-center justify-center text-blue-600 text-sm">🤖</div>
            <div className="bg-white border border-gray-200 px-4 py-3 rounded-3xl rounded-bl-sm flex space-x-1.5 h-11 items-center">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
            </div>
          </div>
        )}
      </div>

      {/* Kolom Input */}
      <div className="p-6 bg-white border-t border-gray-200 shrink-0">
        <form onSubmit={handleSendMessage} className="flex items-center bg-gray-50 border border-gray-200 rounded-full p-2 pl-4 shadow-sm focus-within:ring-2 ring-blue-200">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ketik pesan..." 
            className="flex-1 bg-transparent text-gray-800 px-4 py-2 outline-none text-[15px]"
          />
          <button type="submit" className="bg-blue-600 text-white w-11 h-11 rounded-full flex items-center justify-center">↑</button>
        </form>
      </div>
    </div>
  );
}