import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Box,
} from '@mui/material';
import BugIcon from '@mui/icons-material/BugReport';
import AnalysisPage from './pages/Analysis';

const theme = createTheme({
  palette: {
    primary: {
      main: '#0047ab',
      light: '#1084d7',
      dark: '#003478',
    },
    secondary: {
      main: '#00a8e1',
      light: '#50d4ff',
      dark: '#00769f',
    },
    success: {
      main: '#00b050',
    },
    warning: {
      main: '#ffc715',
    },
    error: {
      main: '#e81123',
    },
    background: {
      default: '#f6f6f6',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Oxygen", "Ubuntu", "Cantarell", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      
      <AppBar position="sticky" sx={{ mb: 0 }}>
        <Toolbar>
          <BugIcon sx={{ mr: 2, fontSize: 28 }} />
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              BugReport AI
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.9 }}>
              Intelligent Bug Analysis & Root Cause Engine
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      <AnalysisPage />
    </ThemeProvider>
  );
}

export default App;
