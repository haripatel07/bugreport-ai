import React from 'react';
import {
  Paper,
  Typography,
  Box,
  Grid,
  Chip,
} from '@mui/material';
import { BugReport } from '../types';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';

interface BugReportViewerProps {
  report: BugReport;
}

const severityConfig = {
  low: { icon: CheckCircleIcon, color: '#107c10', bgcolor: '#dcedde' },
  medium: { icon: WarningIcon, color: '#4a5568', bgcolor: '#fff3cd' },
  high: { icon: ErrorIcon, color: '#e81123', bgcolor: '#f8d7da' },
  critical: { icon: ErrorIcon, color: '#942911', bgcolor: '#f8d7da' },
};

const BugReportViewer: React.FC<BugReportViewerProps> = ({ report }) => {
  const severity = (report.severity || 'medium').toLowerCase() as keyof typeof severityConfig;
  const SeverityIcon = severityConfig[severity]?.icon || severityConfig['medium'].icon;

  return (
    <Paper sx={{ p: 3, bgcolor: 'white', borderRadius: 2, mb: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              bgcolor: severityConfig[severity]?.bgcolor || '#f5f5f5',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <SeverityIcon sx={{ color: severityConfig[severity]?.color || '#666', fontSize: 28 }} />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
              {report.title}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                label={`Severity: ${report.severity || 'Unknown'}`}
                size="small"
                sx={{
                  bgcolor: severityConfig[severity]?.bgcolor || '#f5f5f5',
                  fontWeight: 600,
                }}
              />
              {report.priority && (
                <Chip
                  label={`Priority: ${report.priority}`}
                  size="small"
                  sx={{
                    bgcolor: '#e1f5ff',
                    fontWeight: 600,
                  }}
                />
              )}
            </Box>
          </Box>
        </Box>

        <Typography variant="body1" sx={{ mb: 2, color: '#333', lineHeight: 1.6 }}>
          {report.description}
        </Typography>

        {report.root_cause && (
          <Paper
            sx={{
              p: 2,
              bgcolor: '#fff3cd',
              borderLeft: '4px solid #ffc715',
              mb: 2,
            }}
          >
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5, color: '#664d03' }}>
              🎯 Root Cause
            </Typography>
            <Typography variant="body2" sx={{ color: '#664d03' }}>
              {report.root_cause}
            </Typography>
          </Paper>
        )}
      </Box>

      <Grid container spacing={3}>
        {/* Expected Behavior */}
        <Grid item xs={12} sm={6}>
          <Box>
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 700,
                mb: 1,
                color: '#107c10',
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
              }}
            >
              ✅ Expected Behavior
            </Typography>
            <Paper
              sx={{
                p: 2,
                bgcolor: '#f0f8f0',
                borderLeft: '4px solid #107c10',
              }}
            >
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', color: '#333' }}>
                {report.expected_behavior}
              </Typography>
            </Paper>
          </Box>
        </Grid>

        {/* Actual Behavior */}
        <Grid item xs={12} sm={6}>
          <Box>
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 700,
                mb: 1,
                color: '#e81123',
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
              }}
            >
              ❌ Actual Behavior
            </Typography>
            <Paper
              sx={{
                p: 2,
                bgcolor: '#fff0f0',
                borderLeft: '4px solid #e81123',
              }}
            >
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', color: '#333' }}>
                {report.actual_behavior}
              </Typography>
            </Paper>
          </Box>
        </Grid>

        {/* Steps to Reproduce */}
        <Grid item xs={12}>
          <Box>
            <Typography
              variant="subtitle1"
              sx={{
                fontWeight: 700,
                mb: 1,
                color: '#0047ab',
              }}
            >
              📋 Steps to Reproduce
            </Typography>
            <Paper
              sx={{
                p: 2,
                bgcolor: '#f0f8ff',
                borderLeft: '4px solid #0047ab',
              }}
            >
              <ol style={{ margin: 0, paddingLeft: '1.5rem' }}>
                {report.steps_to_reproduce.map((step, idx) => (
                  <li key={idx} style={{ marginBottom: '0.75rem' }}>
                    <Typography variant="body2" sx={{ color: '#333' }}>
                      {step}
                    </Typography>
                  </li>
                ))}
              </ol>
            </Paper>
          </Box>
        </Grid>

        {/* Affected Components */}
        {report.affected_components && report.affected_components.length > 0 && (
          <Grid item xs={12} sm={6}>
            <Box>
              <Typography
                variant="subtitle1"
                sx={{
                  fontWeight: 700,
                  mb: 1,
                }}
              >
                🔧 Affected Components
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {report.affected_components.map((component, idx) => (
                  <Chip
                    key={idx}
                    label={component}
                    sx={{
                      bgcolor: '#e1f5ff',
                      fontWeight: 500,
                    }}
                  />
                ))}
              </Box>
            </Box>
          </Grid>
        )}

        {/* Environment */}
        {report.environment && Object.keys(report.environment).length > 0 && (
          <Grid item xs={12} sm={6}>
            <Box>
              <Typography
                variant="subtitle1"
                sx={{
                  fontWeight: 700,
                  mb: 1,
                }}
              >
                🌍 Environment
              </Typography>
              <Paper
                sx={{
                  p: 2,
                  bgcolor: '#f5f5f5',
                  borderRadius: 1,
                }}
              >
                {Object.entries(report.environment).map(([key, value]) => (
                  <Typography
                    key={key}
                    variant="caption"
                    sx={{
                      display: 'block',
                      mb: 0.5,
                      fontFamily: 'monospace',
                      fontSize: '11px',
                    }}
                  >
                    <strong>{key}:</strong> {String(value)}
                  </Typography>
                ))}
              </Paper>
            </Box>
          </Grid>
        )}
      </Grid>
    </Paper>
  );
};

export default BugReportViewer;
