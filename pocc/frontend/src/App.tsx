import React, { useState, useEffect, useCallback } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import MissionControl from './pages/MissionControl';
import DataAcquisition from './pages/DataAcquisition';
import StationMap from './pages/StationMap';
import Scientific from './pages/Scientific';
import BurnIn from './pages/BurnIn';
import Predictions from './pages/Predictions';
import Runtime from './pages/Runtime';
import Infrastructure from './pages/Infrastructure';
import Release from './pages/Release';
import Reports from './pages/Reports';
import { WS_URL, fetchData } from './services/api';

const DRAWER_WIDTH = 260;

interface DashboardData {
  utc: string;
  wita: string;
  pipeline_uuid: string;
  burnin: any;
  collector: any;
  runtime: any;
  scientific: any;
  release: any;
  stations: any[];
  csv_tail: any[];
  latest_prediction: any;
}

export default function App() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const loadData = useCallback(async () => {
    try {
      const d = await fetchData('/api/dashboard');
      setData(d);
    } catch {}
  }, []);

  useEffect(() => {
    loadData();
    const ws = new WebSocket(WS_URL);
    ws.onmessage = (e) => {
      try { setData(JSON.parse(e.data)); } catch {}
    };
    ws.onclose = () => setTimeout(() => {
      const w = new WebSocket(WS_URL);
      w.onmessage = ws.onmessage;
      setWs(w);
    }, 5000);
    setWs(ws);
    return () => ws.close();
  }, [loadData]);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', background: '#0a0e1a' }}>
      <Sidebar />
      <Box sx={{ flexGrow: 1, ml: `${DRAWER_WIDTH}px` }}>
        <Header data={data} />
        <Box component="main" sx={{ p: 3, mt: '64px' }}>
          <Routes>
            <Route path="/" element={<MissionControl data={data} />} />
            <Route path="/acquisition" element={<DataAcquisition data={data} />} />
            <Route path="/stations" element={<StationMap data={data} />} />
            <Route path="/scientific" element={<Scientific data={data} />} />
            <Route path="/burnin" element={<BurnIn data={data} />} />
            <Route path="/predictions" element={<Predictions data={data} />} />
            <Route path="/runtime" element={<Runtime data={data} />} />
            <Route path="/infrastructure" element={<Infrastructure data={data} />} />
            <Route path="/release" element={<Release data={data} />} />
            <Route path="/reports" element={<Reports data={data} />} />
          </Routes>
        </Box>
      </Box>
    </Box>
  );
}
