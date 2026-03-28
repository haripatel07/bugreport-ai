import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';

const SettingsPage: React.FC = () => {
  const [model, setModel] = useState<string>('');
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [apiStatus, setApiStatus] = useState<'loading' | 'ok' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const savedModel = localStorage.getItem('bugreport_preferred_model') || '';
    setModel(savedModel);

    apiService
      .getAvailableModels()
      .then((models) => {
        setAvailableModels(models || []);
      })
      .catch(() => {
        setAvailableModels([]);
      });

    apiService
      .getInfrastructureHealth()
      .then(() => setApiStatus('ok'))
      .catch(() => setApiStatus('error'));
  }, []);

  const handleSave = () => {
    try {
      localStorage.setItem('bugreport_preferred_model', model);
      setError(null);
      window.alert('Settings saved.');
    } catch (saveError: unknown) {
      setError(saveError instanceof Error ? saveError.message : 'Failed to save settings.');
    }
  };

  const tokenExists = Boolean(apiService.getToken());

  return (
    <section className="panel reveal">
      <h2 className="card-title">Settings</h2>
      <p style={{ color: 'var(--text-secondary)', marginTop: 0 }}>
        Configure local preferences and validate service readiness.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <div className="settings-grid">
        <article className="panel" style={{ padding: 12 }}>
          <h3 style={{ marginTop: 0 }}>Preferences</h3>
          <label className="settings-label" htmlFor="preferred-model">Preferred Model</label>
          <select
            id="preferred-model"
            className="settings-select"
            value={model}
            onChange={(event) => setModel(event.target.value)}
          >
            <option value="">Auto-select</option>
            {availableModels.map((entry) => (
              <option key={entry} value={entry}>{entry}</option>
            ))}
          </select>

          <div style={{ marginTop: 10 }}>
            <button type="button" className="btn-primary" onClick={handleSave}>Save Settings</button>
          </div>
        </article>

        <article className="panel" style={{ padding: 12 }}>
          <h3 style={{ marginTop: 0 }}>Runtime Status</h3>
          <div className="status-list">
            <div className="status-row">
              <span>API Reachability</span>
              <span className={apiStatus === 'ok' ? 'badge badge-low' : apiStatus === 'error' ? 'badge badge-high' : 'badge badge-medium'}>
                {apiStatus.toUpperCase()}
              </span>
            </div>
            <div className="status-row">
              <span>Auth Token</span>
              <span className={tokenExists ? 'badge badge-low' : 'badge badge-medium'}>
                {tokenExists ? 'AVAILABLE' : 'MISSING'}
              </span>
            </div>
            <div className="status-row">
              <span>LLM Models</span>
              <span className={availableModels.length > 0 ? 'badge badge-low' : 'badge badge-medium'}>
                {availableModels.length > 0 ? `${availableModels.length} FOUND` : 'UNAVAILABLE'}
              </span>
            </div>
          </div>
        </article>
      </div>
    </section>
  );
};

export default SettingsPage;
