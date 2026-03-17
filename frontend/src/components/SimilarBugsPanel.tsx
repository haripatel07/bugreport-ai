import React from 'react';
import {
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  Link,
  LinearProgress,
} from '@mui/material';
import { SimilarBug } from '../types';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';

interface SimilarBugsPanelProps {
  bugs: SimilarBug[];
}

const SimilarBugsPanel: React.FC<SimilarBugsPanelProps> = ({ bugs }) => {
  const getScoreColor = (score: number) => {
    if (score >= 0.75) return '#107c10';
    if (score >= 0.5) return '#ffc715';
    return '#0047ab';
  };

  const truncateText = (text: string, maxLength: number = 200) => {
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <Box sx={{ gridColumn: { xs: '1', md: '1 / -1' } }}>
      <Typography variant="h5" sx={{ mb: 2, fontWeight: 700 }}>
        🐛 Similar Bugs in Knowledge Base
      </Typography>

      {bugs.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center', bgcolor: '#f5f5f5' }}>
          <Typography variant="body2" sx={{ color: '#666' }}>
            No similar bugs found in the knowledge base.
          </Typography>
        </Paper>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
          {bugs.map((bug, idx) => (
            <Card
              key={idx}
              sx={{
                borderRadius: 1,
                transition: 'all 0.2s',
                '&:hover': {
                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                  transform: 'translateY(-2px)',
                },
              }}
            >
              <CardContent sx={{ p: 2 }}>
                {/* Similarity Score */}
                <Box sx={{ mb: 1.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                    <Typography variant="caption" sx={{ fontWeight: 600, color: '#666' }}>
                      Similarity Match
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{
                        fontWeight: 700,
                        color: getScoreColor(bug.similarity_score),
                      }}
                    >
                      {Math.round(bug.similarity_score * 100)}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={bug.similarity_score * 100}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: '#e0e0e0',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: getScoreColor(bug.similarity_score),
                      },
                    }}
                  />
                </Box>

                {/* Title */}
                <Typography
                  variant="subtitle2"
                  sx={{
                    fontWeight: 700,
                    mb: 1,
                    color: '#0047ab',
                    display: '-webkit-box',
                    WebkitBoxOrient: 'vertical',
                    WebkitLineClamp: 2,
                    overflow: 'hidden',
                  }}
                >
                  {bug.title}
                </Typography>

                {/* Repository */}
                <Typography variant="caption" sx={{ color: '#666', display: 'block', mb: 1 }}>
                  📦 <strong>{bug.repository}</strong>
                </Typography>

                {/* Body / Description */}
                <Typography
                  variant="body2"
                  sx={{
                    color: '#555',
                    mb: 1.5,
                    display: '-webkit-box',
                    WebkitBoxOrient: 'vertical',
                    WebkitLineClamp: 4,
                    overflow: 'hidden',
                    lineHeight: 1.4,
                  }}
                >
                  {truncateText(bug.body, 150)}
                </Typography>

                {/* Labels */}
                {bug.labels && bug.labels.length > 0 && (
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1.5 }}>
                    {bug.labels.slice(0, 3).map((label, labelIdx) => (
                      <Chip
                        key={labelIdx}
                        label={label}
                        size="small"
                        sx={{
                          bgcolor: '#f0f0f0',
                          fontWeight: 500,
                          fontSize: '11px',
                        }}
                      />
                    ))}
                    {bug.labels.length > 3 && (
                      <Chip
                        label={`+${bug.labels.length - 3}`}
                        size="small"
                        sx={{
                          bgcolor: '#f0f0f0',
                          fontWeight: 500,
                          fontSize: '11px',
                        }}
                      />
                    )}
                  </Box>
                )}

                {/* View on GitHub Link */}
                {bug.url && (
                  <Link
                    href={bug.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 0.5,
                      fontSize: '12px',
                      fontWeight: 600,
                      color: '#0047ab',
                      textDecoration: 'none',
                      '&:hover': {
                        textDecoration: 'underline',
                      },
                    }}
                  >
                    View on GitHub <OpenInNewIcon sx={{ fontSize: 12 }} />
                  </Link>
                )}
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
};

export default SimilarBugsPanel;
