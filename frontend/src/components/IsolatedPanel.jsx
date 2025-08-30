import React, { useState, useEffect, useRef } from 'react';

const IsolatedPanel = ({ 
  children, 
  panelKey, 
  loading = false, 
  error = null,
  fallback = null 
}) => {
  const [mounted, setMounted] = useState(false);
  const [hasError, setHasError] = useState(false);
  const containerRef = useRef(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    // Delay mounting to prevent race conditions
    timeoutRef.current = setTimeout(() => {
      setMounted(true);
    }, 50);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      setMounted(false);
    };
  }, [panelKey]);

  useEffect(() => {
    if (error) {
      setHasError(true);
      console.warn(`Panel ${panelKey} has error:`, error);
    } else {
      setHasError(false);
    }
  }, [error, panelKey]);

  // Reset error state when key changes
  useEffect(() => {
    setHasError(false);
  }, [panelKey]);

  if (hasError) {
    return (
      <div 
        key={`error-${panelKey}`}
        className="isolated-panel-error"
        style={{
          padding: '2rem',
          textAlign: 'center',
          background: 'rgba(231, 76, 60, 0.1)',
          border: '1px solid rgba(231, 76, 60, 0.3)',
          borderRadius: '15px',
          margin: '1rem'
        }}
      >
        <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⚠️</div>
        <div style={{ color: '#e74c3c', fontWeight: '600' }}>
          Panel Error
        </div>
        <div style={{ fontSize: '0.9rem', color: '#666', marginTop: '0.5rem' }}>
          {error || 'Something went wrong'}
        </div>
        <button
          onClick={() => {
            setHasError(false);
            // Force remount by changing the key
            window.location.reload();
          }}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            background: '#e74c3c',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '0.9rem'
          }}
        >
          🔄 Reload Page
        </button>
      </div>
    );
  }

  if (!mounted || loading) {
    return (
      <div 
        key={`loading-${panelKey}`}
        className="isolated-panel-loading"
        style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(20px)',
          borderRadius: '20px',
        }}
      >
        <div className="loading-spinner" style={{
          width: '40px',
          height: '40px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #667eea',
          borderRadius: '50%',
          margin: '0 auto 1rem'
        }}></div>
        <div style={{ color: '#666' }}>
          {loading ? 'Loading...' : 'Preparing...'}
        </div>
      </div>
    );
  }

  return (
    <div 
      key={`panel-${panelKey}`}
      ref={containerRef}
      className="isolated-panel-container"
      style={{ isolation: 'isolate' }}
    >
      {children}
    </div>
  );
};

export default IsolatedPanel;