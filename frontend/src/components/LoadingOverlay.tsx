import React from 'react';

interface LoadingOverlayProps {
  open: boolean;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ open }) => {
  if (!open) {
    return null;
  }

  return (
    <div className="overlay" role="status" aria-live="polite">
      <div className="overlay-card">
        <div className="loader" />
        <div style={{ fontWeight: 700, marginBottom: 6 }}>Analyzing Error</div>
        <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
          Processing input, root-cause analysis, recommendations, and semantic search.
        </div>
      </div>
    </div>
  );
};

export default LoadingOverlay;
