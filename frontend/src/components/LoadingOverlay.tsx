import React from 'react';
import { Backdrop, CircularProgress, Box, Typography } from '@mui/material';

interface LoadingOverlayProps {
  open: boolean;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ open }) => {
  return (
    <Backdrop
      sx={{
        color: '#fff',
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backdropFilter: 'blur(4px)',
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
      }}
      open={open}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
        <CircularProgress
          size={60}
          sx={{
            color: '#0047ab',
          }}
        />
        <Typography
          variant="h6"
          sx={{
            color: 'white',
            fontWeight: 700,
            textAlign: 'center',
            textShadow: '0 2px 4px rgba(0,0,0,0.3)',
          }}
        >
          🔍 Analyzing Error
        </Typography>
        <Typography
          variant="caption"
          sx={{
            color: 'rgba(255,255,255,0.8)',
            textAlign: 'center',
            maxWidth: 300,
          }}
        >
          Processing input, running RCA, searching similar bugs, and generating recommendations...
        </Typography>
      </Box>
    </Backdrop>
  );
};

export default LoadingOverlay;
