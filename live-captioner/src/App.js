import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Safe import for Electron IPC
const ipcRenderer = window.require ? window.require('electron').ipcRenderer : null;

// Available languages configuration
const LANGUAGES = [
  { code: 'en', name: 'English', flag: '/flags/us.svg' },
  { code: 'es', name: 'Spanish', flag: '/flags/es.svg' },
  { code: 'fr', name: 'French', flag: '/flags/fr.svg' }
];

function App() {
  const [status, setStatus] = useState('Connecting...');

  // Language selection state
  const [leftLanguage, setLeftLanguage] = useState('en');
  const [rightLanguage, setRightLanguage] = useState('es');

  // State for finalized sentences
  // Note: englishHistory = Left Pane History, spanishHistory = Right Pane History
  const [englishHistory, setEnglishHistory] = useState([]);
  const [spanishHistory, setSpanishHistory] = useState([]);

  // State for current active sentence (interim)
  const [englishInterim, setEnglishInterim] = useState('');
  const [spanishInterim, setSpanishInterim] = useState('');

  const enEndRef = useRef(null);
  const esEndRef = useRef(null);
  const enScrollRef = useRef(null);
  const esScrollRef = useRef(null);

  // Send language selection to Python backend
  useEffect(() => {
    if (ipcRenderer) {
      ipcRenderer.send('set-languages', [leftLanguage, rightLanguage]);
    }
  }, [leftLanguage, rightLanguage]);

  const scrollToBottomIfNeeded = (scrollContainer, endRef) => {
    if (!scrollContainer) return;

    const { scrollTop, scrollHeight, clientHeight } = scrollContainer;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 50; // Within 50px of bottom

    if (isNearBottom) {
      endRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottomIfNeeded(enScrollRef.current, enEndRef);
  }, [englishHistory, englishInterim]);

  useEffect(() => {
    scrollToBottomIfNeeded(esScrollRef.current, esEndRef);
  }, [spanishHistory, spanishInterim]);

  // Refs to hold current language state for the event listener
  const leftLanguageRef = useRef(leftLanguage);
  const rightLanguageRef = useRef(rightLanguage);

  useEffect(() => {
    leftLanguageRef.current = leftLanguage;
  }, [leftLanguage]);

  useEffect(() => {
    rightLanguageRef.current = rightLanguage;
  }, [rightLanguage]);

  useEffect(() => {
    if (!ipcRenderer) {
      setStatus('Error: Not running in Electron');
      return;
    }

    ipcRenderer.on('python-data', (event, rawData) => {
      try {
        const data = JSON.parse(rawData);

        if (data.type === 'status' && data.message === 'ready') {
          setStatus('Ready');
        }
        else if (data.type === 'transcription') {
          const text = data.text ? data.text.trim() : "";
          if (!text) return;

          const currentLeft = leftLanguageRef.current;
          const currentRight = rightLanguageRef.current;

          // Route to left pane if it matches left language
          if (data.language === currentLeft) {
            if (data.is_final) {
              setEnglishHistory(prev => [...prev, text]);
              setEnglishInterim('');
            } else {
              setEnglishInterim(text);
            }
          }
          // Route to right pane if it matches right language
          else if (data.language === currentRight) {
            if (data.is_final) {
              setSpanishHistory(prev => [...prev, text]);
              setSpanishInterim('');
            } else {
              setSpanishInterim(text);
            }
          }
          // Ignore transcriptions that don't match either selected language
        }
      } catch (e) {
        console.error("Parse error:", e);
      }
    });

    return () => {
      ipcRenderer.removeAllListeners('python-data');
    };
  }, []);

  // Maintain scroll position during window resize
  useEffect(() => {
    const handleResize = () => {
      // Check if either scroll container is near bottom, and if so, scroll both to bottom
      const enContainer = enScrollRef.current;
      const esContainer = esScrollRef.current;

      if (enContainer && esContainer) {
        const enIsNearBottom = enContainer.scrollHeight - enContainer.scrollTop - enContainer.clientHeight < 50;
        const esIsNearBottom = esContainer.scrollHeight - esContainer.scrollTop - esContainer.clientHeight < 50;

        if (enIsNearBottom || esIsNearBottom) {
          enEndRef.current?.scrollIntoView({ behavior: "auto" });
          esEndRef.current?.scrollIntoView({ behavior: "auto" });
        }
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Synchronized scrolling between both text boxes
  useEffect(() => {
    const enContainer = enScrollRef.current;
    const esContainer = esScrollRef.current;

    if (!enContainer || !esContainer) return;

    let isScrolling = false;

    const syncScroll = (source, target) => {
      if (isScrolling) return;
      isScrolling = true;

      const scrollPercentage = source.scrollTop / (source.scrollHeight - source.clientHeight);
      target.scrollTop = scrollPercentage * (target.scrollHeight - target.clientHeight);

      setTimeout(() => { isScrolling = false; }, 10);
    };

    const handleEnScroll = () => syncScroll(enContainer, esContainer);
    const handleEsScroll = () => syncScroll(esContainer, enContainer);

    enContainer.addEventListener('scroll', handleEnScroll);
    esContainer.addEventListener('scroll', handleEsScroll);

    return () => {
      enContainer.removeEventListener('scroll', handleEnScroll);
      esContainer.removeEventListener('scroll', handleEsScroll);
    };
  }, []);

  // Settings State
  const [showSettings, setShowSettings] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [alwaysOnTop, setAlwaysOnTop] = useState(false);
  const [opacity, setOpacity] = useState(0.9);
  const [fontSize, setFontSize] = useState(18);

  const toggleSettings = () => {
    if (showSettings) {
      // Start closing animation
      setIsClosing(true);
      setTimeout(() => {
        setShowSettings(false);
        setIsClosing(false);
      }, 250); // Match animation duration
    } else {
      setShowSettings(true);
    }
  };

  const handleAlwaysOnTop = (e) => {
    const value = e.target.checked;
    setAlwaysOnTop(value);
    if (ipcRenderer) ipcRenderer.send('set-always-on-top', value);
  };

  const handleOpacity = (e) => {
    const value = parseFloat(e.target.value);
    setOpacity(value);
    if (ipcRenderer) ipcRenderer.send('set-opacity', value);
  };

  const handleFontSize = (e) => {
    const value = parseInt(e.target.value);
    setFontSize(value);
  };

  // Resize Logic
  const handleResizeStart = (e, direction) => {
    e.preventDefault();
    const startX = e.screenX;
    const startY = e.screenY;
    const startWidth = window.outerWidth;
    const startHeight = window.outerHeight;
    const startLeft = window.screenX;
    const startTop = window.screenY;

    const onMouseMove = (e) => {
      const deltaX = e.screenX - startX;
      const deltaY = e.screenY - startY;

      let newWidth = startWidth;
      let newHeight = startHeight;
      let newX = startLeft;
      let newY = startTop;

      if (direction.includes('e')) newWidth = startWidth + deltaX;
      if (direction.includes('s')) newHeight = startHeight + deltaY;
      if (direction.includes('w')) {
        newWidth = startWidth - deltaX;
        newX = startLeft + deltaX;
      }
      if (direction.includes('n')) {
        newHeight = startHeight - deltaY;
        newY = startTop + deltaY;
      }

      // Enforce minimums
      if (newWidth < 620) newWidth = 620;
      if (newHeight < 300) newHeight = 300;

      // Apply changes
      // Send to Main Process via IPC
      if (ipcRenderer) {
        ipcRenderer.send('resize-window', {
          width: Math.round(newWidth),
          height: Math.round(newHeight),
          x: Math.round(newX),
          y: Math.round(newY)
        });
      }
    };

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  const handleSwapLanguages = () => {
    // Swap languages
    const tempLeft = leftLanguage;
    setLeftLanguage(rightLanguage);
    setRightLanguage(tempLeft);

    // Swap history
    const tempLeftHistory = englishHistory;
    setEnglishHistory(spanishHistory);
    setSpanishHistory(tempLeftHistory);

    // Swap interim text
    const tempLeftInterim = englishInterim;
    setEnglishInterim(spanishInterim);
    setSpanishInterim(tempLeftInterim);
  };

  const handleLeftLanguageChange = (e) => {
    setLeftLanguage(e.target.value);
    setEnglishHistory([]);
    setEnglishInterim('');
  };

  const handleRightLanguageChange = (e) => {
    setRightLanguage(e.target.value);
    setSpanishHistory([]);
    setSpanishInterim('');
  };

  return (
    <div className="App" style={{ '--app-opacity': opacity }}>
      {/* Resize Handles */}
      <div className="resize-handle n" onMouseDown={(e) => handleResizeStart(e, 'n')} />
      <div className="resize-handle s" onMouseDown={(e) => handleResizeStart(e, 's')} />
      <div className="resize-handle e" onMouseDown={(e) => handleResizeStart(e, 'e')} />
      <div className="resize-handle w" onMouseDown={(e) => handleResizeStart(e, 'w')} />
      <div className="resize-handle ne" onMouseDown={(e) => handleResizeStart(e, 'ne')} />
      <div className="resize-handle nw" onMouseDown={(e) => handleResizeStart(e, 'nw')} />
      <div className="resize-handle se" onMouseDown={(e) => handleResizeStart(e, 'se')} />
      <div className="resize-handle sw" onMouseDown={(e) => handleResizeStart(e, 'sw')} />

      {/* Title Bar / Header */}
      <div className="title-bar">
        <div className="drag-region">
          <div className="status-indicator" style={{
            backgroundColor: status === 'Ready' ? '#4ade80' : '#fbbf24'
          }}></div>
          <span className="app-title">Vosk Interpreter Helper</span>
        </div>

        {/* Window Controls */}
        <div className="window-controls">
          <button className="window-button settings-button" onClick={toggleSettings} title="Settings">
            ⚙️
          </button>
          <button className="window-button minimize" onClick={() => ipcRenderer?.send('minimize-window')} title="Minimize">
            −
          </button>
          <button className="window-button close" onClick={() => ipcRenderer?.send('close-window')} title="Close">
            ×
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className={`settings-panel ${isClosing ? 'closing' : ''}`}>
          <div className="setting-item">
            <label style={{ minWidth: '80px' }}>Opacity: {Math.round(opacity * 100)}%</label>
            <input
              type="range"
              min="0.2"
              max="1.0"
              step="0.01"
              value={opacity}
              onChange={handleOpacity}
            />
          </div>
          <div className="setting-item">
            <label style={{ minWidth: '45px' }}>Font:</label>
            <input
              type="range"
              min="12"
              max="32"
              step="1"
              value={fontSize}
              onChange={handleFontSize}
            />
          </div>
          <div className="setting-item align-right">
            <label>
              <input
                type="checkbox"
                checked={alwaysOnTop}
                onChange={handleAlwaysOnTop}
              />
              On Top
            </label>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="main-container">

        {/* English Pane */}
        <div className="language-pane">
          <div className="pane-header">
            <img
              src={LANGUAGES.find(l => l.code === leftLanguage)?.flag}
              alt="flag"
              className="flag-icon"
            />
            <select
              className="language-selector"
              value={leftLanguage}
              onChange={handleLeftLanguageChange}
            >
              {LANGUAGES.map(lang => (
                <option
                  key={lang.code}
                  value={lang.code}
                  disabled={lang.code === rightLanguage}
                >
                  {lang.name}
                </option>
              ))}
            </select>
          </div>
          <div className="transcription-area" ref={enScrollRef}>
            {englishHistory.map((text, i) => (
              <p key={i} className="segment final" style={{ fontSize: `${fontSize}px` }}>{text}</p>
            ))}
            {englishInterim && (
              <p className="segment interim" style={{ fontSize: `${fontSize}px` }}>{englishInterim}</p>
            )}
            <div ref={enEndRef} />
          </div>
        </div>

        {/* Swap Button */}
        <div className="swap-container">
          <button className="swap-button" onClick={handleSwapLanguages} title="Swap Languages">
            ⇄
          </button>
        </div>

        {/* Spanish Pane */}
        <div className="language-pane">
          <div className="pane-header">
            <img
              src={LANGUAGES.find(l => l.code === rightLanguage)?.flag}
              alt="flag"
              className="flag-icon"
            />
            <select
              className="language-selector"
              value={rightLanguage}
              onChange={handleRightLanguageChange}
            >
              {LANGUAGES.map(lang => (
                <option
                  key={lang.code}
                  value={lang.code}
                  disabled={lang.code === leftLanguage}
                >
                  {lang.name}
                </option>
              ))}
            </select>
          </div>
          <div className="transcription-area" ref={esScrollRef}>
            {spanishHistory.map((text, i) => (
              <p key={i} className="segment final" style={{ fontSize: `${fontSize}px` }}>{text}</p>
            ))}
            {spanishInterim && (
              <p className="segment interim" style={{ fontSize: `${fontSize}px` }}>{spanishInterim}</p>
            )}
            <div ref={esEndRef} />
          </div>
        </div>

      </div>
    </div>
  );
}

export default App;
