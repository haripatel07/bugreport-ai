import React, { useEffect, useMemo, useState } from 'react';
import { apiService } from '../services/api';
import { AnalysisResult, InputType } from '../types';

interface ErrorFormProps {
  onAnalysisStart: () => void;
  onAnalysisComplete: (result: AnalysisResult) => void;
  onError: (message: string) => void;
  onAuthStateChange?: (isAuthenticated: boolean) => void;
}

const inputTypeDescriptions: Record<InputType, string> = {
  text: 'Plain text bug description',
  stack_trace: 'Stack trace payload',
  log: 'Log file fragment',
  json: 'JSON error object',
};

const exampleInputs: Record<InputType, string> = {
  text: 'NullPointerException in UserController.getUserProfile when user.address is null',
  stack_trace: `Traceback (most recent call last):\n  File "/app/main.py", line 45, in process_data\n    result = processor.handle(data)\nKeyError: \"key\"`,
  log: `[2026-03-17 14:23:45] ERROR Connection refused to localhost:5432\n[2026-03-17 14:23:47] CRITICAL Fallback exhausted`,
  json: `{"error_type":"TypeError","message":"Cannot read property map of undefined","file":"src/components/List.tsx","line":42}`,
};

const quickExamples = [
  {
    label: 'Python Exception',
    value: `AttributeError: 'NoneType' object has no attribute 'split'\nFile \"/app/parser.py\", line 42, in parse`,
  },
  {
    label: 'JavaScript Error',
    value: `TypeError: Cannot read property 'map' of undefined\nat processItems (app.js:45:12)`,
  },
  {
    label: 'Network Error',
    value: `ConnectionRefusedError: [Errno 111] Connection refused\nFailed to connect to 127.0.0.1:5432`,
  },
];

const ErrorForm: React.FC<ErrorFormProps> = ({
  onAnalysisStart,
  onAnalysisComplete,
  onError,
  onAuthStateChange,
}) => {
  const [errorInput, setErrorInput] = useState('');
  const [inputType, setInputType] = useState<InputType>('text');
  const [environment, setEnvironment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showEnvironment, setShowEnvironment] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authUserEmail, setAuthUserEmail] = useState<string | null>(null);
  const [modeNotice, setModeNotice] = useState('Guest mode active. Limited free analysis is available without login.');

  const hasToken = useMemo(() => Boolean(apiService.getToken()), []);

  useEffect(() => {
    let mounted = true;
    if (!hasToken) {
      onAuthStateChange?.(false);
      return;
    }

    setAuthLoading(true);
    apiService
      .getCurrentUser()
      .then((user) => {
        if (mounted) {
          setAuthUserEmail(user.email);
          onAuthStateChange?.(true);
          setModeNotice('Signed in. Full history and management features are enabled.');
        }
      })
      .catch(() => {
        apiService.clearToken();
        if (mounted) {
          onAuthStateChange?.(false);
          setModeNotice('Guest mode active. Limited free analysis is available without login.');
        }
      })
      .finally(() => {
        if (mounted) {
          setAuthLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [hasToken]);

  const handleAuthSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!authEmail.trim() || !authPassword.trim()) {
      onError('Email and password are required for authentication.');
      return;
    }

    setAuthLoading(true);
    try {
      if (authMode === 'register') {
        await apiService.register({ email: authEmail.trim(), password: authPassword });
      }
      await apiService.login({ email: authEmail.trim(), password: authPassword });
      const user = await apiService.getCurrentUser();
      setAuthUserEmail(user.email);
      onAuthStateChange?.(true);
      setModeNotice('Signed in. Full history and management features are enabled.');
      onError('');
    } catch (error: unknown) {
      if (typeof error === 'object' && error !== null && 'response' in error) {
        const response = (error as { response?: { data?: { detail?: string } } }).response;
        onError(response?.data?.detail || 'Authentication failed.');
      } else {
        onError(error instanceof Error ? error.message : 'Authentication failed.');
      }
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    apiService.clearToken();
    setAuthUserEmail(null);
    onAuthStateChange?.(false);
    setModeNotice('Guest mode active. Limited free analysis is available without login.');
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!errorInput.trim()) {
      onError('Please enter an error message or stack trace.');
      return;
    }

    setSubmitting(true);
    onAnalysisStart();

    try {
      const envMap: Record<string, string> = {};
      if (environment.trim()) {
        environment.split('\n').forEach((line) => {
          const [key, value] = line.split('=').map((segment) => segment.trim());
          if (key && value) {
            envMap[key] = value;
          }
        });
      }

      if (!authUserEmail) {
        const guestResult = await apiService.analyzeErrorFree({
          description: errorInput,
          input_type: inputType,
          environment: envMap,
        });
        onAnalysisComplete(guestResult);
        setModeNotice('Analysis completed in guest mode. Sign in to save and manage history.');
        return;
      }

      const result = await apiService.analyzeError({
        description: errorInput,
        input_type: inputType,
        environment: envMap,
      });
      onAnalysisComplete(result);
    } catch (error: unknown) {
      if (typeof error === 'object' && error !== null && 'response' in error) {
        const response = (error as { response?: { data?: { detail?: string } } }).response;
        const detail = response?.data?.detail;
        onError(detail || 'Analysis failed. Please try again in a moment.');
      } else {
        onError(error instanceof Error ? error.message : 'Failed to analyze error.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="panel reveal">
      <h2 className="card-title" style={{ fontSize: 22 }}>Analyze Error</h2>
      <p style={{ color: 'var(--text-secondary)', marginTop: 0 }}>
        Paste logs or stack traces and get a structured report, root cause analysis, recommendations, and similar incidents.
      </p>

      <div className="auth-box" style={{ marginBottom: 14 }}>
        {!authUserEmail ? (
          <form onSubmit={handleAuthSubmit}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <strong style={{ fontSize: 13 }}>Authentication required</strong>
              <div className="pill-row" style={{ gap: 6 }}>
                <button
                  type="button"
                  className={`pill-btn ${authMode === 'login' ? 'active' : ''}`}
                  onClick={() => setAuthMode('login')}
                >
                  Login
                </button>
                <button
                  type="button"
                  className={`pill-btn ${authMode === 'register' ? 'active' : ''}`}
                  onClick={() => setAuthMode('register')}
                >
                  Register
                </button>
              </div>
            </div>
            <div className="auth-grid">
              <input
                className="auth-input"
                type="email"
                name="email"
                placeholder="you@example.com"
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
                autoComplete="username"
              />
              <input
                className="auth-input"
                type="password"
                name="password"
                placeholder="Password (min 8 chars)"
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
                autoComplete={authMode === 'login' ? 'current-password' : 'new-password'}
              />
            </div>
            <button className="pill-btn" type="submit" disabled={authLoading} style={{ marginTop: 8 }}>
              {authLoading ? 'Authenticating...' : authMode === 'login' ? 'Login' : 'Create account'}
            </button>
            <div style={{ marginTop: 8, fontSize: 12, color: 'var(--text-secondary)' }}>{modeNotice}</div>
          </form>
        ) : (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
              Signed in as <span style={{ color: 'var(--text-primary)' }}>{authUserEmail}</span>
            </div>
            <button className="pill-btn" type="button" onClick={handleLogout}>Logout</button>
            <div style={{ width: '100%', fontSize: 12, color: 'var(--text-secondary)' }}>{modeNotice}</div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit}>
        <div className="pill-row" style={{ marginBottom: 10 }}>
          {(['text', 'stack_trace', 'log', 'json'] as const).map((option) => (
            <button
              key={option}
              type="button"
              className={`pill-btn ${inputType === option ? 'active' : ''}`}
              onClick={() => setInputType(option)}
            >
              {option === 'stack_trace' ? 'Stack Trace' : option.toUpperCase()}
            </button>
          ))}
        </div>

        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 10 }}>
          {inputTypeDescriptions[inputType]}
        </div>

        <textarea
          className="textarea"
          placeholder={exampleInputs[inputType]}
          value={errorInput}
          onChange={(event) => setErrorInput(event.target.value)}
          disabled={submitting}
        />

        <div className="actions-row" style={{ marginTop: 8, marginBottom: 14 }}>
          <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{errorInput.length} characters</span>
          <button
            type="button"
            className="pill-btn"
            onClick={() => setShowEnvironment((open) => !open)}
          >
            {showEnvironment ? 'Hide Environment' : 'Environment'}
          </button>
        </div>

        {showEnvironment && (
          <div style={{ marginBottom: 12 }}>
            <textarea
              className="textarea"
              style={{ minHeight: 110 }}
              placeholder={'OS=Ubuntu 22.04\nPYTHON_VERSION=3.12\nFRAMEWORK=FastAPI'}
              value={environment}
              onChange={(event) => setEnvironment(event.target.value)}
              disabled={submitting}
            />
          </div>
        )}

        <button className={`btn-primary ${submitting ? 'pulse-once' : ''}`} type="submit" disabled={submitting || !errorInput.trim()}>
          {submitting ? 'Analyzing...' : authUserEmail ? 'Analyze Error' : 'Analyze for Free'}
        </button>

        <div style={{ marginTop: 14 }}>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 8 }}>Quick examples</div>
          <div className="pill-row">
            {quickExamples.map((example) => (
              <button key={example.label} type="button" className="pill-btn" onClick={() => setErrorInput(example.value)}>
                {example.label}
              </button>
            ))}
          </div>
        </div>
      </form>
    </section>
  );
};

export default ErrorForm;
