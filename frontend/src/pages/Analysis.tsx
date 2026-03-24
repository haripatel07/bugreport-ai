import React, { useState } from 'react';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  Typography,
  Container,
} from '@mui/material';
import { AnalysisResult } from '../types';
import ErrorForm from '../components/ErrorForm';
import BugReportViewer from '../components/BugReportViewer';
import RCAResultsPanel from '../components/RCAResultsPanel';
import LoadingOverlay from '../components/LoadingOverlay';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const AnalysisPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleAnalysisComplete = (result: AnalysisResult) => {
    setAnalysisResult(result);
    setError(null);
    setTabValue(1);
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
    setAnalysisResult(null);
  };

  const handleNewAnalysis = () => {
    setTabValue(0);
    setAnalysisResult(null);
    setError(null);
  };

  return (
    <>
      <LoadingOverlay open={loading} />

      <Container maxWidth="xl" sx={{ py: 4 }}>
        {error && (
          <Paper
            sx={{
              p: 2,
              mb: 3,
              bgcolor: '#fde7e6',
              border: '1px solid #fcc3bf',
              borderRadius: 1,
              color: '#c5192d',
            }}
          >
            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
              Error occurred:
            </Typography>
            <Typography variant="body2">{error}</Typography>
          </Paper>
        )}

        <Paper sx={{ borderRadius: 2, boxShadow: 2 }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="analysis tabs"
            sx={{
              borderBottom: '1px solid #e0e0e0',
              bgcolor: '#fafafa',
            }}
          >
            <Tab label="Error Input" id="tab-0" aria-controls="tabpanel-0" />
            <Tab
              label="Analysis Results"
              id="tab-1"
              aria-controls="tabpanel-1"
              disabled={!analysisResult}
            />
          </Tabs>

          <Box sx={{ p: 3 }}>
            <TabPanel value={tabValue} index={0}>
              <ErrorForm
                onAnalysisStart={() => setLoading(true)}
                onAnalysisComplete={(result) => {
                  setLoading(false);
                  handleAnalysisComplete(result);
                }}
                onError={(msg) => {
                  setLoading(false);
                  handleError(msg);
                }}
              />
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              {analysisResult && (
                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 3 }}>
                  <Box sx={{ gridColumn: '1 / -1' }}>
                    <BugReportViewer report={analysisResult.bug_report} />
                  </Box>

                  <RCAResultsPanel rca={analysisResult.root_cause_analysis} />

                  {analysisResult.recommendations && (
                    <Box
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 2,
                      }}
                    >
                      <Typography variant="h5" sx={{ mb: 2 }}>
                        Fix Recommendations
                      </Typography>
                      {analysisResult.recommendations.recommendations.map((rec, idx) => (
                        <Paper key={idx} sx={{ p: 2, bgcolor: '#f0f8ff', borderLeft: '4px solid #0047ab' }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 0.5 }}>
                            {rec.title}
                          </Typography>
                          <Typography variant="body2" sx={{ mb: 1.5, color: '#555' }}>
                            {rec.description}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 2, mb: 1.5 }}>
                            <Typography
                              variant="caption"
                              sx={{
                                px: 1.5,
                                py: 0.5,
                                bgcolor:
                                  rec.difficulty === 'easy'
                                    ? '#dcedde'
                                    : rec.difficulty === 'medium'
                                      ? '#fff3cd'
                                      : '#f8d7da',
                                borderRadius: 1,
                                fontWeight: 600,
                              }}
                            >
                              Difficulty: {rec.difficulty}
                            </Typography>
                          </Box>
                          {rec.implementation_steps && (
                            <Box sx={{ mb: 1.5 }}>
                              <Typography variant="caption" sx={{ fontWeight: 600, display: 'block', mb: 0.5 }}>
                                Steps:
                              </Typography>
                              <ul style={{ margin: '0 0 0 1.5rem', padding: 0 }}>
                                {rec.implementation_steps.map((step, stepIdx) => (
                                  <li key={stepIdx}>
                                    <Typography variant="caption">{step}</Typography>
                                  </li>
                                ))}
                              </ul>
                            </Box>
                          )}
                          {rec.code_example && (
                            <Box
                              sx={{
                                bgcolor: '#1e1e1e',
                                color: '#d4d4d4',
                                p: 1.5,
                                borderRadius: 1,
                                overflow: 'auto',
                                fontSize: '0.75rem',
                                fontFamily: 'monospace',
                              }}
                            >
                              {rec.code_example}
                            </Box>
                          )}
                        </Paper>
                      ))}
                    </Box>
                  )}

                </Box>
              )}
            </TabPanel>
          </Box>
        </Paper>

        {analysisResult && (
          <Box sx={{ textAlign: 'center', mt: 4 }}>
            <button
              onClick={handleNewAnalysis}
              style={{
                padding: '10px 24px',
                fontSize: '16px',
                fontWeight: 600,
                color: 'white',
                backgroundColor: '#0047ab',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'background-color 0.2s',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.backgroundColor = '#003478';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.backgroundColor = '#0047ab';
              }}
            >
              ➕ Analyze Another Error
            </button>
          </Box>
        )}
      </Container>
    </>
  );
};

export default AnalysisPage;
