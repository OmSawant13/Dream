import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Cpu, Zap, Radio } from 'lucide-react';
import './App.css';

const App = () => {
  const [state, setState] = useState('sleeping'); 
  const [status, setStatus] = useState('OFFLINE');
  const [messages, setMessages] = useState([]);
  const [transcript, setTranscript] = useState('');
  const [streamingText, setStreamingText] = useState('');
  
  const stateRef = useRef('sleeping');
  const ws = useRef(null);
  const feedRef = useRef(null);
  const speakingRef = useRef(false);

  useEffect(() => { stateRef.current = state; }, [state]);

  useEffect(() => {
    const connect = () => {
      console.log("🔗 Attempting Neural Link...");
      ws.current = new WebSocket('ws://localhost:8000/ws');
      
      ws.current.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'transcript') {
          setTranscript(data.text);
          updateState('listening');
        } else if (data.type === 'chunk') {
          setStreamingText(prev => prev + data.text);
          updateState('thinking');
        } else if (data.type === 'done') {
          const fullText = data.text;
          setStreamingText('');
          addMessage('friday', fullText);
          speak(fullText);
        }
      };

      ws.current.onclose = () => {
        console.log("🔌 Link Lost. Retrying in 3s...");
        setTimeout(connect, 3000);
      };

      ws.current.onerror = () => ws.current.close();
    };

    connect();
    return () => { if (ws.current) ws.current.close(); };
  }, []);

  const updateState = (s) => {
    stateRef.current = s;
    setState(s);
  };

  const addMessage = (role, text) => {
    setMessages(prev => [...prev, { role, text, id: Date.now() }]);
    setTimeout(() => { if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight; }, 100);
  };

  const speak = (text) => {
    if (!text || speakingRef.current) return;
    speakingRef.current = true;
    updateState('speaking');
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    const finish = () => {
      speakingRef.current = false;
      updateState('sleeping');
      setTranscript('');
    };
    utter.onend = finish;
    utter.onerror = finish;
    setTimeout(finish, 15000);
    window.speechSynthesis.speak(utter);
  };

  return (
    <div className="dashboard">
      <div className="nexus-grid" />
      <motion.div className="reactor-container" animate={{ scale: state === 'listening' ? [1, 1.1, 1] : 1, rotate: state === 'thinking' ? 360 : 0 }}>
        <div className="reactor-core" style={{ position: 'absolute', inset: '60px', borderRadius: '50%', background: state === 'thinking' ? 'radial-gradient(circle, #ff9f1a, #ff7800)' : 'radial-gradient(circle, #00d4ff, #004466)', boxShadow: state === 'listening' ? '0 0 60px #00d4ff' : '0 0 30px rgba(0,212,255,0.3)', transition: 'all 0.5s ease' }} />
        <svg viewBox="0 0 100 100" style={{ width: '100%', height: '100%', position: 'absolute' }}>
          <circle cx="50" cy="50" r="48" fill="none" stroke="rgba(0,212,255,0.1)" strokeWidth="0.5" />
          <motion.circle cx="50" cy="50" r="40" fill="none" stroke="var(--blue)" strokeWidth="1" strokeDasharray="10 5" animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 10, ease: "linear" }} />
        </svg>
      </motion.div>
      <div className={`status-label ${state !== 'sleeping' ? state : ''}`}>{state === 'sleeping' ? 'Protocol: SLEEP' : `Protocol: ${state.toUpperCase()}`}</div>
      
      <div className="input-container">
        <input 
          type="text" 
          placeholder="Type a command, Boss..." 
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              const cmd = e.target.value;
              addMessage('user', cmd);
              updateState('thinking');
              ws.current?.send(JSON.stringify({ type: 'command', text: cmd }));
              e.target.value = '';
            }
          }}
        />
      </div>

      <div className="nexus-status">
        <div className="status-dot active"></div>
        <span>SYSTEM ONLINE</span>
      </div>

      <div className="hologram-card">
        <div className="feed" ref={feedRef}>
          <AnimatePresence>
            {messages.map((m) => (
              <motion.div key={m.id} className={`msg ${m.role}`} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
                <div className="msg-role">{m.role === 'user' ? 'BOSS' : 'FRIDAY'}</div>
                <div className="msg-content">{m.text}</div>
              </motion.div>
            ))}
            {streamingText && (
               <div className="msg friday">
                 <div className="msg-role">FRIDAY (STREAMING)</div>
                 <div className="msg-content">{streamingText}</div>
               </div>
            )}
          </AnimatePresence>
        </div>
      </div>
      <div style={{ position: 'fixed', bottom: 20, right: 20, display: 'flex', gap: 20, opacity: 0.3 }}><Mic size={16} color={state === 'listening' ? 'var(--blue)' : 'white'} /><Cpu size={16} /><Radio size={16} /></div>
    </div>
  );
};

export default App;
