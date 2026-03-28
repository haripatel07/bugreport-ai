import React, { useEffect, useMemo, useState } from 'react';
import { apiService, HistoryRecordDetail, HistoryRecordSummary } from '../services/api';

const PAGE_SIZE = 20;

const formatDateTime = (value: string): string => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

const statusClass = (status: string): string => {
  if (status === 'completed') return 'badge badge-low';
  if (status === 'failed') return 'badge badge-high';
  return 'badge badge-medium';
};

const severityClass = (severity: string): string => {
  const normalized = severity.toLowerCase();
  if (normalized === 'critical') return 'badge badge-critical';
  if (normalized === 'high') return 'badge badge-high';
  if (normalized === 'low') return 'badge badge-low';
  return 'badge badge-medium';
};

const HistoryPage: React.FC = () => {
  const [records, setRecords] = useState<HistoryRecordSummary[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<HistoryRecordDetail | null>(null);
  const [drawerLoading, setDrawerLoading] = useState(false);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(totalCount / PAGE_SIZE)), [totalCount]);

  const loadHistory = async (page: number) => {
    if (!apiService.getToken()) {
      setError('Sign in to view your saved analysis history. Guest analyses are not stored.');
      setRecords([]);
      setTotalCount(0);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await apiService.getHistory(page, PAGE_SIZE);
      setRecords(result.records);
      setTotalCount(result.totalCount);
    } catch (loadError: unknown) {
      setError(loadError instanceof Error ? loadError.message : 'Failed to load history.');
      setRecords([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory(currentPage);
  }, [currentPage]);

  const handleViewRecord = async (recordId: number) => {
    setDrawerLoading(true);
    setError(null);
    try {
      const detail = await apiService.getHistoryRecord(recordId);
      setSelectedRecord(detail);
    } catch (loadError: unknown) {
      setError(loadError instanceof Error ? loadError.message : 'Failed to fetch record detail.');
    } finally {
      setDrawerLoading(false);
    }
  };

  const handleDeleteRecord = async (recordId: number) => {
    const confirmed = window.confirm('Delete this analysis record permanently?');
    if (!confirmed) {
      return;
    }

    setError(null);
    try {
      await apiService.deleteHistoryRecord(recordId);
      if (selectedRecord?.id === recordId) {
        setSelectedRecord(null);
      }

      const newTotal = Math.max(0, totalCount - 1);
      const newTotalPages = Math.max(1, Math.ceil(newTotal / PAGE_SIZE));
      if (currentPage > newTotalPages) {
        setCurrentPage(newTotalPages);
      } else {
        await loadHistory(currentPage);
      }
    } catch (deleteError: unknown) {
      setError(deleteError instanceof Error ? deleteError.message : 'Failed to delete record.');
    }
  };

  return (
    <section className="panel reveal">
      <div className="section-header">
        <h2 className="card-title" style={{ marginBottom: 0 }}>Analysis History</h2>
        <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
          {loading ? 'Loading...' : `${totalCount} total records`}
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="history-table-wrap">
        <table className="history-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Input Snippet</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {!loading && records.length === 0 && (
              <tr>
                <td colSpan={5} className="history-empty">
                  {error ? 'No records to display.' : 'No records found.'}
                </td>
              </tr>
            )}
            {records.map((record) => (
              <tr key={record.id} className="history-row" onClick={() => handleViewRecord(record.id)}>
                <td>{formatDateTime(record.created_at)}</td>
                <td title={record.description}>{record.description}</td>
                <td>
                  <span className={severityClass(record.severity || 'unknown')}>
                    {(record.severity || 'unknown').toUpperCase()}
                  </span>
                </td>
                <td>
                  <span className={statusClass(record.status)}>{record.status.toUpperCase()}</span>
                </td>
                <td>
                  <div className="pill-row" style={{ gap: 6 }}>
                    <button
                      type="button"
                      className="pill-btn"
                      onClick={(event) => {
                        event.stopPropagation();
                        handleViewRecord(record.id);
                      }}
                    >
                      View
                    </button>
                    <button
                      type="button"
                      className="pill-btn danger"
                      onClick={(event) => {
                        event.stopPropagation();
                        handleDeleteRecord(record.id);
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pagination-row">
        <button
          type="button"
          className="pill-btn"
          onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
          disabled={currentPage === 1 || loading}
        >
          Previous
        </button>
        <span style={{ color: 'var(--text-secondary)' }}>Page {currentPage} / {totalPages}</span>
        <button
          type="button"
          className="pill-btn"
          onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
          disabled={currentPage >= totalPages || loading}
        >
          Next
        </button>
      </div>

      <aside className={`history-drawer ${selectedRecord ? 'open' : ''}`} aria-hidden={!selectedRecord}>
        <div className="history-drawer-header">
          <h3 style={{ margin: 0 }}>Record Detail</h3>
          <button type="button" className="pill-btn" onClick={() => setSelectedRecord(null)}>Close</button>
        </div>

        {drawerLoading && <p style={{ color: 'var(--text-secondary)' }}>Loading record...</p>}
        {!drawerLoading && selectedRecord && (
          <div className="history-drawer-content">
            <p style={{ color: 'var(--text-secondary)', marginTop: 0 }}>{selectedRecord.description}</p>
            <div className="meta-grid">
              <span className="badge badge-medium">{selectedRecord.input_type}</span>
              <span className={statusClass(selectedRecord.status)}>{selectedRecord.status.toUpperCase()}</span>
              <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{formatDateTime(selectedRecord.created_at)}</span>
            </div>

            {selectedRecord.bug_report?.title && (
              <section className="panel" style={{ padding: 10 }}>
                <h4 style={{ margin: '0 0 6px' }}>Bug Report</h4>
                <p style={{ margin: 0, color: 'var(--text-secondary)' }}>{selectedRecord.bug_report.title}</p>
              </section>
            )}

            {selectedRecord.root_cause_analysis?.probable_causes?.length ? (
              <section className="panel" style={{ padding: 10 }}>
                <h4 style={{ margin: '0 0 6px' }}>Top Root Cause</h4>
                <p style={{ margin: 0, color: 'var(--text-secondary)' }}>
                  {selectedRecord.root_cause_analysis.probable_causes[0].cause}
                </p>
              </section>
            ) : null}

            {selectedRecord.recommendations?.recommendations?.length ? (
              <section className="panel" style={{ padding: 10 }}>
                <h4 style={{ margin: '0 0 6px' }}>Recommendations</h4>
                <ul className="checklist" style={{ marginTop: 0 }}>
                  {selectedRecord.recommendations.recommendations.slice(0, 3).map((recommendation, index) => (
                    <li key={`${recommendation.title}-${index}`}>{recommendation.title}</li>
                  ))}
                </ul>
              </section>
            ) : null}
          </div>
        )}
      </aside>
    </section>
  );
};

export default HistoryPage;
