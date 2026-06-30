import React, { useState, useEffect } from 'react';

export default function LabDashboard({ labName }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`http://localhost:8000/api/lab/${encodeURIComponent(labName)}`)
      .then((res) => {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Gagal fetch lab:', err);
        setData(null);
        setLoading(false);
      });
  }, [labName]);

  if (loading) {
    return (
      <div className="flex-1 bg-[#FAFBFF] p-10 overflow-y-auto h-full flex items-center justify-center">
        <div className="text-gray-400 text-lg font-semibold">Memuat data...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex-1 bg-[#FAFBFF] p-10 overflow-y-auto h-full flex items-center justify-center">
        <div className="text-red-400 text-lg font-semibold">Gagal memuat data.</div>
      </div>
    );
  }

  const statusColor = data.status === 'Tersedia' ? 'bg-green-100 text-green-700'
    : data.status === 'Penuh' ? 'bg-red-100 text-red-700'
    : 'bg-yellow-100 text-yellow-700';

  return (
    <div className="flex-1 bg-[#FAFBFF] p-10 overflow-y-auto h-full flex flex-col items-center">
      <div className="w-full max-w-3xl bg-white p-8 rounded-3xl shadow-sm border border-gray-200 mt-8">
        <div className="flex items-center justify-between border-b border-gray-100 pb-6 mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">{data.lab_name}</h2>
            <p className="text-sm text-gray-400 mt-1">{data.tanggal_format}</p>
          </div>
          <span className={`px-4 py-1.5 rounded-full text-sm font-bold ${statusColor}`}>
            {data.status}
          </span>
        </div>

        {data.bookings.length === 0 ? (
          <div className="text-center py-12 text-gray-400 font-medium">
            Belum ada booking untuk hari ini.
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Daftar Booking</p>
            {data.bookings.map((b, i) => (
              <div key={i} className="p-5 bg-gray-50 rounded-2xl border border-gray-100">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">NIM/NIDN</p>
                    <p className="font-bold text-lg text-gray-800">{b.nim_nidn}</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Waktu</p>
                    <p className="font-bold text-lg text-gray-800">{b.jam_mulai} - {b.jam_selesai}</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Kegiatan</p>
                    <p className="font-bold text-lg text-gray-800">{b.nama_kegiatan}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {data.slot_tersedia && data.slot_tersedia.length > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-100">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Slot Kosong</p>
            <div className="flex flex-wrap gap-2">
              {data.slot_tersedia.map((s, i) => (
                <span key={i} className="px-3 py-1.5 bg-green-50 text-green-700 rounded-full text-sm font-medium border border-green-200">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
