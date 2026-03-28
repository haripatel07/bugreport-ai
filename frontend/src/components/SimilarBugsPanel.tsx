import React from 'react';
import { SimilarBug } from '../types';

interface SimilarBugsPanelProps {
  similarBugs?: SimilarBug[] | null;
  loading?: boolean;
}

const parseSimilarity = (value: string | undefined): number => {
  if (!value) return 0;
  const numeric = parseFloat(value.replace('%', '').trim());
  if (Number.isNaN(numeric)) return 0;
  return Math.max(0, Math.min(numeric, 100));
};

const SimilarBugsPanel: React.FC<SimilarBugsPanelProps> = ({ similarBugs, loading = false }) => {
  if (loading) {
    return (
      <section className="panel reveal reveal-delay-3">
        <h3 className="card-title">Similar Bugs</h3>
        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>Scanning issue corpus...</p>
      </section>
    );
  }

  const bugs = Array.isArray(similarBugs) ? similarBugs : [];

  if (bugs.length === 0) {
    return (
      <section className="panel reveal reveal-delay-3">
        <h3 className="card-title">Similar Bugs</h3>
        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>No similar bugs found.</p>
      </section>
    );
  }

  return (
    <section className="panel reveal reveal-delay-3">
      <h3 className="card-title">Similar Bugs</h3>
      <table className="similar-table">
        <thead>
          <tr>
            <th>Repo</th>
            <th>Title</th>
            <th>Similarity</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
          {bugs.map((bug, index) => {
            const similarity = parseSimilarity(bug.similarity_pct);
            return (
              <tr key={`${bug.repository}-${bug.number ?? index}`}>
                <td>{bug.repository || '-'}</td>
                <td>{bug.title || 'Untitled issue'}</td>
                <td>
                  <div className="similar-bar" aria-label={`Similarity ${similarity}%`}>
                    <span style={{ width: `${similarity}%` }} />
                  </div>
                  <div style={{ marginTop: 4, color: 'var(--text-secondary)', fontSize: 12 }}>{similarity.toFixed(1)}%</div>
                </td>
                <td>
                  {bug.url ? (
                    <a className="link" href={bug.url} target="_blank" rel="noreferrer">
                      View
                    </a>
                  ) : (
                    <span style={{ color: 'var(--text-dim)' }}>N/A</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
};

export default SimilarBugsPanel;
