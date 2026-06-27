import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatSection from './components/ChatSection';
import LabDashboard from './components/LabDashboard';

function App() {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="h-screen w-screen bg-white flex overflow-hidden font-sans text-gray-800">
      
      {/* Panggil komponen Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Tampilkan Chat atau Dashboard tergantung menu yang diklik */}
      {activeTab === 'chat' ? (
        <ChatSection />
      ) : (
        <LabDashboard labName={activeTab} />
      )}
      
    </div>
  );
}

export default App;