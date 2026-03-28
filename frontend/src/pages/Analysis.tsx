import React, { useState } from 'react';
import { AnalysisResult } from '../types';
import ErrorForm from '../components/ErrorForm';
import BugReportViewer from '../components/BugReportViewer';
import RCAResultsPanel from '../components/RCAResultsPanel';
import LoadingOverlay from '../components/LoadingOverlay';
import SimilarBugsPanel from '../components/SimilarBugsPanel';

const difficultyClass = (difficulty: string): string => {
  if (difficulty === 'easy') return 'badge badge-low';
  if (difficulty === 'hard') return 'badge badge-high';
  return 'badge badge-medium';
};

interface AnalysisPageProps {
  onAuthStateChange?: (isAuthenticated: boolean) => void;
}

const AnalysisPage: React.FC<AnalysisPageProps> = ({ onAuthStateChange }) => {
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  return (
    <>
      <LoadingOverlay open={loading} />

      {error && <div className="error-banner">{error}</div>}

      <div className="analysis-grid">
        <ErrorForm
          onAnalysisStart={() => setLoading(true)}
          onAnalysisComplete={(result) => {
            setLoading(false);
            setError(null);
            setAnalysisResult(result);
          }}
          onError={(message) => {
            setLoading(false);
            setAnalysisResult(null);
            setError(message);
          }}
          onAuthStateChange={onAuthStateChange}
        />

        <div className="results-stack">
          {!analysisResult && (
            <section className="panel reveal">
              <h3 className="card-title" style={{ marginBottom: 4 }}>Paste an error to begin</h3>
              <p style={{ color: 'var(--text-secondary)', marginTop: 0, fontFamily: 'var(--font-code)' }}>
                Results will appear here as bug report, root causes, recommendations, and similar issues.
              </p>
            </section>
          )}

          {analysisResult && (
            <>
              <BugReportViewer report={analysisResult.bug_report} />
              <RCAResultsPanel rca={analysisResult.root_cause_analysis} />

              {analysisResult.recommendations && (
                <section className="panel reveal reveal-delay-2">
                  <h3 className="card-title">Fix Recommendations</h3>
                  <div style={{ display: 'grid', gap: 10 }}>
                    {analysisResult.recommendations.recommendations.map((recommendation, index) => (
                      <article key={`${recommendation.title}-${index}`} className="recommendation-item">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                          <h4 style={{ margin: 0 }}>{index + 1}. {recommendation.title}</h4>
                          <span className={difficultyClass(recommendation.difficulty)}>
                            {recommendation.difficulty.toUpperCase()}
                          </span>
                        </div>
                        <p style={{ color: 'var(--text-secondary)', marginBottom: 0 }}>{recommendation.description}</p>

                        {recommendation.implementation_steps?.length > 0 && (
                          <ul className="checklist">
                            {recommendation.implementation_steps.map((step, stepIndex) => (
                              <li key={`${step}-${stepIndex}`}>{step}</li>
                            ))}
                          </ul>
                        )}

                        {recommendation.code_example && (
                          <details style={{ marginTop: 8 }}>
                            <summary style={{ cursor: 'pointer', color: 'var(--accent-cyan)' }}>Code example</summary>
                            <pre className="code-block">{recommendation.code_example}</pre>
                          </details>
                        )}
                      </article>
                    ))}
                  </div>
                </section>
              )}

              <SimilarBugsPanel similarBugs={analysisResult.similar_bugs} loading={loading} />
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default AnalysisPage;
