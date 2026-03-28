import React from 'react';
import { BugReport } from '../types';

interface BugReportViewerProps {
  report: BugReport;
}

const severityClass = (severity: string | undefined): string => {
  const normalized = (severity || 'medium').toLowerCase();
  if (normalized === 'critical') return 'badge badge-critical pulse-once';
  if (normalized === 'high') return 'badge badge-high';
  if (normalized === 'low') return 'badge badge-low';
  return 'badge badge-medium';
};

const BugReportViewer: React.FC<BugReportViewerProps> = ({ report }) => {
  return (
    <section className="panel reveal reveal-delay-1">
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start', flexWrap: 'wrap' }}>
        <div>
          <h3 className="card-title" style={{ marginBottom: 4 }}>{report.title}</h3>
          <p style={{ marginTop: 0, color: 'var(--text-secondary)' }}>{report.description}</p>
        </div>
        <div className={severityClass(report.severity)}>Severity: {(report.severity || 'medium').toUpperCase()}</div>
      </div>

      <div className="summary-grid">
        <div className="panel" style={{ margin: 0, padding: 12, background: '#101a12' }}>
          <h4 style={{ margin: '0 0 8px', color: 'var(--accent-green)' }}>Expected</h4>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>{report.expected_behavior}</p>
        </div>
        <div className="panel" style={{ margin: 0, padding: 12, background: '#201213' }}>
          <h4 style={{ margin: '0 0 8px', color: 'var(--accent-red)' }}>Actual</h4>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>{report.actual_behavior}</p>
        </div>
      </div>

      <div style={{ marginTop: 12 }}>
        <h4 style={{ margin: '0 0 8px' }}>Steps to Reproduce</h4>
        <ol style={{ margin: 0, paddingLeft: 20 }}>
          {report.steps_to_reproduce.map((step, index) => (
            <li key={`${step}-${index}`} style={{ marginBottom: 6, color: 'var(--text-secondary)' }}>{step}</li>
          ))}
        </ol>
      </div>

      {report.affected_components?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <h4 style={{ margin: '0 0 8px' }}>Affected Components</h4>
          <div className="pill-row">
            {report.affected_components.map((component, index) => (
              <span className="badge badge-medium" key={`${component}-${index}`}>{component}</span>
            ))}
          </div>
        </div>
      )}

      {report.environment && Object.keys(report.environment).length > 0 && (
        <div style={{ marginTop: 12 }}>
          <h4 style={{ margin: '0 0 8px' }}>Environment</h4>
          <div className="panel" style={{ margin: 0, padding: 12 }}>
            {Object.entries(report.environment).map(([key, value]) => (
              <div key={key} style={{ marginBottom: 5, fontFamily: 'var(--font-code)', fontSize: 12, color: 'var(--text-secondary)' }}>
                <strong style={{ color: 'var(--text-primary)' }}>{key}</strong>: {String(value)}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
};

export default BugReportViewer;
