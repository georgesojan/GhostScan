import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Activity, Shield, Globe, Terminal, Search, Zap, List } from 'lucide-react'

const API_BASE = 'http://localhost:8002'

function App() {
  const [devices, setDevices] = useState([])
  const [status, setStatus] = useState({ device_count: 0, engine: 'GhostScan v1.0' })
  const [scanTargets, setScanTargets] = useState('192.168.1.1/24')
  const [isScanning, setIsScanning] = useState(false)

  const fetchStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/status`)
      setStatus(res.data)
    } catch (err) { console.error(err) }
  }

  const fetchDevices = async () => {
    try {
      const res = await axios.get(`${API_BASE}/devices`)
      setDevices(res.data)
    } catch (err) { console.error(err) }
  }

  const startScan = async () => {
    setIsScanning(true)
    try {
      // Very simple expansion for the demo
      const ips = scanTargets.includes('/') ? [scanTargets] : scanTargets.split(',')
      await axios.post(`${API_BASE}/scan`, {
        ips: ips,
        ports: [80, 443, 22, 3306, 8080]
      })
      setTimeout(() => setIsScanning(false), 3000)
    } catch (err) {
      console.error(err)
      setIsScanning(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    fetchDevices()
    const interval = setInterval(() => {
      fetchStatus()
      fetchDevices()
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="dashboard">
      <header className="header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Shield color="#00ff9d" size={24} />
          <h1>GhostScan <span style={{ opacity: 0.5 }}>Recon Console</span></h1>
        </div>
        <div style={{ display: 'flex', gap: '20px', fontSize: '0.8rem' }}>
          <span>UPTIME: 100%</span>
          <span style={{ color: '#00ff9d' }}>SYSTEM: ACTIVE</span>
        </div>
      </header>

      <aside className="sidebar">
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
            <Zap size={18} color="#00ff9d" />
            <span style={{ fontSize: '0.9rem' }}>Scan Engine</span>
          </div>
          <div className="scan-controls">
            <input
              type="text"
              value={scanTargets}
              onChange={(e) => setScanTargets(e.target.value)}
              placeholder="IP range or CSV"
            />
            <button className="btn" onClick={startScan} disabled={isScanning}>
              {isScanning ? 'Probing...' : 'Initialize Scan'}
            </button>
          </div>
        </div>

        <div className="card" style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
            <Activity size={18} color="#00ff9d" />
            <span style={{ fontSize: '0.9rem' }}>Telemetry</span>
          </div>
          <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Devices Mapped</span>
              <span style={{ color: '#00ff9d' }}>{status.device_count}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Intelligence Hits</span>
              <span style={{ color: '#00ff9d' }}>{devices.length * 2}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Node Integrity</span>
              <span style={{ color: '#00ff9d' }}>99.8%</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '1rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
            <List size={18} style={{ marginRight: '10px', verticalAlign: 'middle' }} />
            Active Discovery Log
          </h2>
          <span className="status-tag">Real-time Feed</span>
        </div>

        <div className="device-list">
          <div className="device-row" style={{ borderBottom: '2px solid #333', fontWeight: 'bold', color: '#888' }}>
            <div>IP ADDRESS</div>
            <div>OPEN PORTS</div>
            <div>LOCATION</div>
            <div>STATUS</div>
          </div>
          {devices.map((device) => (
            <div key={device.id} className="device-row">
              <div className="ip">{device.ip}</div>
              <div className="ports">{device.ports}</div>
              <div className="location">{device.location}</div>
              <div style={{ color: '#00ff9d', fontSize: '0.7rem' }}>[ UNMASKED ]</div>
            </div>
          ))}
          {devices.length === 0 && (
            <div style={{ padding: '40px', textAlign: 'center', color: '#333' }}>
              No active discoveries. Start a scan to map the network.
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App
