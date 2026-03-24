import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Collapse,
  IconButton,
  Chip,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { RCAResult } from '../types';

interface RCAResultsPanelProps {
  rca: RCAResult;
}

const RCAResultsPanel: React.FC<RCAResultsPanelProps> = ({ rca }) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);
  const probableCauses = Array.isArray(rca?.probable_causes) ? rca.probable_causes : [];

  const toggleExpand = (idx: number) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return '#942911';
      case 'high':
        return '#e81123';
      case 'medium':
        return '#ffc715';
      case 'low':
        return '#107c10';
      default:
        return '#0047ab';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#107c10';
    if (confidence >= 0.6) return '#ffc715';
    return '#e81123';
  };

  return (
    <Box sx={{ gridColumn: { xs: '1', md: '1' } }}>
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>
        Root Cause Analysis
      </Typography>

      {/* Error Type and Severity Summary */}
      <Paper
        sx={{
          p: 2,
          mb: 2,
          bgcolor: '#f0f8ff',
          borderLeft: '4px solid #0047ab',
        }}
      >
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
          Error Type
        </Typography>
        <Typography variant="body2" sx={{ mb: 1.5, fontFamily: 'monospace' }}>
          {rca.error_type || 'Unknown'}
        </Typography>

        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
          Severity
        </Typography>
        <Chip
          label={rca.severity || 'Unknown'}
          sx={{
            bgcolor: getSeverityColor(rca.severity),
            color: 'white',
            fontWeight: 600,
          }}
        />
      </Paper>

      {/* Probable Causes */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {probableCauses.length === 0 && (
          <Paper sx={{ p: 2, bgcolor: '#fff8e1', borderLeft: '4px solid #ffc715' }}>
            <Typography variant="body2" sx={{ color: '#5f370e' }}>
              No probable causes available for this input.
            </Typography>
          </Paper>
        )}
        {probableCauses.map((cause, idx) => (
          <Card
            key={idx}
            sx={{
              border: `1px solid ${getConfidenceColor(cause.confidence)}`,
              borderRadius: 1,
            }}
          >
            <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  mb: 1.5,
                  cursor: 'pointer',
                }}
                onClick={() => toggleExpand(idx)}
                role="button"
                tabIndex={0}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    toggleExpand(idx);
                  }
                }}
              >
                <Box>
                  <Typography
                    variant="subtitle2"
                    sx={{
                      fontWeight: 700,
                      color: '#333',
                      mb: 0.5,
                    }}
                  >
                    #{idx + 1} {cause.cause}
                  </Typography>

                  {/* Confidence Bar */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Box sx={{ flex: 1, maxWidth: 150 }}>
                      <LinearProgress
                        variant="determinate"
                        value={cause.confidence * 100}
                        sx={{
                          height: 6,
                          borderRadius: 3,
                          backgroundColor: '#e0e0e0',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: getConfidenceColor(cause.confidence),
                          },
                        }}
                      />
                    </Box>
                    <Typography
                      variant="caption"
                      sx={{
                        fontWeight: 700,
                        color: getConfidenceColor(cause.confidence),
                        minWidth: '50px',
                      }}
                    >
                      {Math.round(cause.confidence * 100)}% confidence
                    </Typography>
                  </Box>
                </Box>

                <IconButton
                  size="small"
                  sx={{
                    transform: expandedIndex === idx ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 0.2s',
                  }}
                >
                  <ExpandMoreIcon />
                </IconButton>
              </Box>

              <Collapse in={expandedIndex === idx} timeout="auto" unmountOnExit>
                <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #e0e0e0' }}>
                  {/* Recommendation */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" sx={{ fontWeight: 600, color: '#666', display: 'block', mb: 0.5 }}>
                      Recommendation
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#333' }}>
                      {cause.recommendation}
                    </Typography>
                  </Box>

                  {/* Code Example */}
                  {cause.code_example && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="caption" sx={{ fontWeight: 600, color: '#666', display: 'block', mb: 0.5 }}>
                        Code Example
                      </Typography>
                      <Box
                        sx={{
                          bgcolor: '#1e1e1e',
                          color: '#d4d4d4',
                          p: 1.5,
                          borderRadius: 1,
                          overflow: 'auto',
                          fontSize: '0.75rem',
                          fontFamily: 'monospace',
                          lineHeight: 1.4,
                        }}
                      >
                        {cause.code_example}
                      </Box>
                    </Box>
                  )}

                  {/* Evidence */}
                  {cause.evidence && cause.evidence.length > 0 && (
                    <Box>
                      <Typography variant="caption" sx={{ fontWeight: 600, color: '#666', display: 'block', mb: 0.75 }}>
                        Evidence
                      </Typography>
                      <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                        {cause.evidence.map((ev, evIdx) => (
                          <li key={evIdx} style={{ marginBottom: '0.5rem' }}>
                            <Typography variant="caption" sx={{ color: '#555' }}>
                              {ev}
                            </Typography>
                          </li>
                        ))}
                      </ul>
                    </Box>
                  )}
                </Box>
              </Collapse>
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  );
};

export default RCAResultsPanel;
