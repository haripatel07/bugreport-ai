import React, { useState } from 'react';
import { RCAResult } from '../types';

interface RCAResultsPanelProps {
  rca: RCAResult;
}

const RCAResultsPanel: React.FC<RCAResultsPanelProps> = ({ rca }) => {
  const [expandedIndex, setExpandedIndex] = useState<number>(0);
  const probableCauses = Array.isArray(rca?.probable_causes) ? rca.probable_causes.slice(0, 3) : [];

  return (
    <section className="panel reveal reveal-delay-2">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <h3 className="card-title" style={{ marginBottom: 0 }}>Root Cause Analysis</h3>
        <span className="badge badge-medium">{rca.error_type || 'unknown'}</span>
      </div>

      {probableCauses.length === 0 && (
        <p style={{ color: 'var(--text-secondary)' }}>No probable causes available for this input.</p>
      )}

      {probableCauses.map((cause, index) => {
        const score = Math.round(cause.confidence * 100);
        return (
          <article className="rca-item" key={`${cause.cause}-${index}`}>
            <button
              type="button"
              onClick={() => setExpandedIndex((current) => (current === index ? -1 : index))}
              style={{
                width: '100%',
                border: 0,
                background: 'transparent',
                color: 'inherit',
                textAlign: 'left',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              <div style={{ fontWeight: 700 }}>{cause.cause}</div>
              <div className="confidence-row">
                <div style={{ color: 'var(--accent-cyan)', fontSize: 22, fontWeight: 700 }}>{score}%</div>
                <div className="progress-track" role="progressbar" aria-valuenow={score} aria-valuemin={0} aria-valuemax={100}>
                  <div className="progress-fill" style={{ width: `${score}%` }} />
                </div>
              </div>
            </button>

            {expandedIndex === index && (
              <div>
                <p style={{ color: 'var(--text-secondary)', marginTop: 0 }}>{cause.recommendation}</p>
                {cause.code_example && <pre className="code-block">{cause.code_example}</pre>}
                {cause.evidence?.length > 0 && (
                  <ul style={{ color: 'var(--text-secondary)', paddingLeft: 18, marginBottom: 0 }}>
                    {cause.evidence.map((entry, evidenceIndex) => (
                      <li key={`${entry}-${evidenceIndex}`}>{entry}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </article>
        );
      })}
    </section>
  );
};

export default RCAResultsPanel;
