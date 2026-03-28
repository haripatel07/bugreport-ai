import { useEffect, useMemo, useState } from 'react';
import AnalysisPage from './pages/Analysis';
import HistoryPage from './pages/History';
import SearchPage from './pages/Search';
import SettingsPage from './pages/Settings';
import { apiService } from './services/api';

type AppSection = 'analyze' | 'history' | 'search' | 'settings';

function App() {
  const [section, setSection] = useState<AppSection>('analyze');
  const [llmLabel, setLlmLabel] = useState('LLM: unavailable');
  const [llmDotColor, setLlmDotColor] = useState('var(--accent-red)');
  const [dbLabel, setDbLabel] = useState('DB: unavailable');
  const [dbDotColor, setDbDotColor] = useState('var(--accent-red)');
  const [isAuthenticated, setIsAuthenticated] = useState(Boolean(apiService.getToken()));

  const headerMeta = useMemo(() => {
    if (section === 'history') return { breadcrumb: 'Workspace / History', title: 'Analysis History' };
    if (section === 'search') return { breadcrumb: 'Workspace / Search', title: 'Search Workspace' };
    if (section === 'settings') return { breadcrumb: 'Workspace / Settings', title: 'Project Settings' };
    return { breadcrumb: 'Workspace / Analysis', title: 'Error Analysis' };
  }, [section]);

  useEffect(() => {
    apiService
      .getInfrastructureHealth()
      .then((payload) => {
        const services = (payload.services || {}) as Record<string, string>;
        const provider = services.llm_provider || 'fallback';
        const database = services.database || 'unknown';

        setLlmLabel(`LLM: ${provider}`);
        setLlmDotColor(provider === 'fallback' ? 'var(--accent-amber)' : 'var(--accent-green)');

        const dbHealthy = String(database).toLowerCase().includes('operational');
        setDbLabel(`DB: ${database}`);
        setDbDotColor(dbHealthy ? 'var(--accent-green)' : 'var(--accent-red)');
      })
      .catch(() => {
        setLlmLabel('LLM: unavailable');
        setLlmDotColor('var(--accent-red)');
        setDbLabel('DB: unavailable');
        setDbDotColor('var(--accent-red)');
      });
  }, []);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="logo">BugReport AI</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 12, marginTop: 4 }}>Precision debugging assistant</div>
        </div>

        <nav className="sidebar-nav" aria-label="Primary navigation">
          <button className={section === 'analyze' ? 'active' : ''} type="button" onClick={() => setSection('analyze')}>Analyze</button>
          <button className={section === 'history' ? 'active' : ''} type="button" onClick={() => setSection('history')}>History</button>
          <button className={section === 'search' ? 'active' : ''} type="button" onClick={() => setSection('search')}>Search</button>
          <button className={section === 'settings' ? 'active' : ''} type="button" onClick={() => setSection('settings')}>Settings</button>
        </nav>

        <div className="sidebar-status">
          <div className="status-item">
            <span className="status-dot" style={{ background: llmDotColor }} />
            {llmLabel}
          </div>
          <div className="status-item">
            <span className="status-dot" style={{ background: dbDotColor }} />
            {dbLabel}
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>{headerMeta.breadcrumb}</div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>{headerMeta.title}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className={`badge ${isAuthenticated ? 'badge-low' : 'badge-medium'}`}>
              {isAuthenticated ? 'SIGNED IN' : 'GUEST MODE'}
            </span>
            <div className="avatar" aria-label="user avatar" />
          </div>
        </header>

        <div className="main-content">
          {section === 'analyze' && <AnalysisPage onAuthStateChange={setIsAuthenticated} />}
          {section === 'history' && <HistoryPage />}
          {section === 'search' && <SearchPage />}
          {section === 'settings' && <SettingsPage />}
        </div>
      </main>
    </div>
  );
}

export default App;
