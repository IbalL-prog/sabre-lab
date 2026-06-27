import React, { useState, useEffect } from 'react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const [labs, setLabs] = useState([
    { id: 'Lab Komputer 1', icon: '⚙️', status: 'Memuat...' },
    { id: 'Lab Komputer 2', icon: '🌐', status: 'Memuat...' }
  ]);

  useEffect(() => {
    fetch('http://localhost:8000/api/labs')
      .then((res) => res.json())
      .then((data) => {
        setLabs(data.map((d) => ({
          id: d.id,
          icon: d.id.includes('1') ? '⚙️' : '🌐',
          status: d.status
        })));
      })
      .catch(() => {
        // fallback jika backend tidak jalan
      });
  }, []);

  return (
    <div className="w-[280px] bg-white border-r border-gray-200 flex flex-col p-6 shrink-0 h-full">
      {/* Logo */}
      <div className="flex items-center space-x-3 mb-8">
        <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white text-xl shadow-md">🔬</div>
        <span className="font-extrabold text-gray-900 text-lg tracking-tight">SABRELab</span>
      </div>

      <div className="flex-1 overflow-y-auto pr-2">
        {/* Menu Chat */}
        <button 
          onClick={() => setActiveTab('chat')}
          className={`w-full flex items-center space-x-3 px-4 py-3 rounded-2xl font-semibold transition-all mb-6 ${
            activeTab === 'chat' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-600 hover:bg-gray-50'
          }`}>
          <span>🤖</span>
          <span>Chat Reservasi</span>
        </button>

        {/* Menu Laboratorium */}
        <span className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 block">Laboratorium</span>
        <nav className="space-y-2">
          {labs.map((lab) => {
            const isPenuh = lab.status === 'Penuh';
            const dotColor = lab.status === 'Memuat...' ? 'bg-gray-300'
              : isPenuh ? 'bg-yellow-400'
              : lab.status === 'Terbooking' ? 'bg-orange-400'
              : 'bg-green-500';

            return (
              <button 
                key={lab.id}
                onClick={() => setActiveTab(lab.id)}
                className={`w-full flex items-center justify-between px-4 py-3 rounded-2xl font-medium transition-all ${
                  activeTab === lab.id ? 'bg-[#F0F5FF] text-blue-700' : 'text-gray-600 hover:bg-gray-50'
                }`}>
                <div className="flex items-center space-x-3">
                  <span>{lab.icon}</span>
                  <span>{lab.id}</span>
                </div>
                <span className={`w-2.5 h-2.5 rounded-full shadow-sm ${dotColor}`}></span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Legend Ketersediaan */}
      <div className="pt-6 border-t border-gray-100 flex items-center justify-between text-xs font-semibold text-gray-500 mt-4">
        <div className="flex items-center space-x-1.5"><span className="w-2 h-2 bg-green-500 rounded-full"></span><span>Tersedia</span></div>
        <div className="flex items-center space-x-1.5"><span className="w-2 h-2 bg-yellow-400 rounded-full"></span><span>Penuh</span></div>
        <div className="flex items-center space-x-1.5"><span className="w-2 h-2 bg-orange-400 rounded-full"></span><span>Terbooking</span></div>
      </div>
    </div>
  );
}
