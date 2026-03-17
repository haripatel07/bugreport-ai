import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  ToggleButton,
  ToggleButtonGroup,
  Grid,
  CircularProgress,
} from '@mui/material';
import { apiService } from '../services/api';
import { AnalysisResult, InputType } from '../types';

interface ErrorFormProps {
  onAnalysisStart: () => void;
  onAnalysisComplete: (result: AnalysisResult) => void;
  onError: (message: string) => void;
}

const inputTypeDescriptions: Record<InputType, string> = {
  text: 'Plain text error description',
  stack_trace: 'Full stack trace (Python, JavaScript, Java, etc.)',
  log: 'Log file content with error messages',
  json: 'Structured JSON error object',
};

const ErrorForm: React.FC<ErrorFormProps> = ({ onAnalysisStart, onAnalysisComplete, onError }) => {
  const [errorInput, setErrorInput] = useState('');
  const [inputType, setInputType] = useState<InputType>('text');
  const [environment, setEnvironment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleInputTypeChange = (_event: React.MouseEvent<HTMLElement>, newType: InputType | null) => {
    if (newType!== null) {
      setInputType(newType);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!errorInput.trim()) {
      onError('Please enter an error message or stack trace');
      return;
    }

    setSubmitting(true);
    onAnalysisStart();

    try {
      const envMap: Record<string, string> = {};
      if (environment.trim()) {
        environment.split('\n').forEach((line) => {
          const [key, value] = line.split('=').map((s) => s.trim());
          if (key && value) {
            envMap[key] = value;
          }
        });
      }

      const result = await apiService.analyzeError({
        description: errorInput,
        input_type: inputType,
        environment: envMap,
      });

      onAnalysisComplete(result);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to analyze error';
      onError(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const exampleInputs: Record<InputType, string> = {
    text: 'NullPointerException in UserController.getUserProfile when accessing user.address.street',
    stack_trace: `Traceback (most recent call last):
  File "/app/main.py", line 45, in process_data
    result = processor.handle(data)
  File "/app/services/processor.py", line 102, in handle
    value = data['key']
KeyError: 'key'`,
    log: `[2024-03-17 14:23:45] ERROR: Connection refused to database at localhost:5432
[2024-03-17 14:23:46] CRITICAL: Failed to establish connection after 3 retries
[2024-03-17 14:23:47] ERROR: Falling back to cached configuration`,
    json: `{
  "error_type": "TypeError",
  "message": "Cannot read property 'map' of undefined",
  "file": "src/components/List.js",
  "line": 42
}`,
  };

  return (
    <Paper sx={{ p: 4, bgcolor: '#white', borderRadius: 2 }}>
      <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Header */}
        <Box>
          <Typography variant="h5" sx={{ mb: 1, fontWeight: 700 }}>
            🐛 Submit an Error
          </Typography>
          <Typography variant="body2" sx={{ color: '#666' }}>
            Paste your error message, stack trace, logs, or structured error data. Our AI will analyze it for root cause
            and suggest fixes.
          </Typography>
        </Box>

        {/* Input Type Selection */}
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
            Error Format
          </Typography>
          <ToggleButtonGroup value={inputType} exclusive onChange={handleInputTypeChange} fullWidth>
            <ToggleButton value="text" aria-label="text">
              📝 Text
            </ToggleButton>
            <ToggleButton value="stack_trace" aria-label="stack_trace">
              📋 Stack Trace
            </ToggleButton>
            <ToggleButton value="log" aria-label="log">
              📊 Log
            </ToggleButton>
            <ToggleButton value="json" aria-label="json">
              {'{}'} JSON
            </ToggleButton>
          </ToggleButtonGroup>
          <Typography variant="caption" sx={{ mt: 1, display: 'block', color: '#888' }}>
            {inputTypeDescriptions[inputType]}
          </Typography>
        </Box>

        {/* Error Input */}
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            Error Details
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={10}
            placeholder={exampleInputs[inputType]}
            value={errorInput}
            onChange={(e) => setErrorInput(e.target.value)}
            variant="outlined"
            sx={{
              bgcolor: '#f5f5f5',
              '& .MuiOutlinedInput-root': {
                fontFamily: 'monospace',
                fontSize: '13px',
              },
            }}
            disabled={submitting}
          />
          <Typography variant="caption" sx={{ mt: 1, display: 'block', color: '#888' }}>
            {errorInput.length} characters
          </Typography>
        </Box>

        {/* Environment Variables (Optional) */}
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            📦 Environment (Optional)
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={4}
            placeholder="KEY=value (one per line)&#10;PYTHON_VERSION=3.11&#10;FRAMEWORK=FastAPI"
            value={environment}
            onChange={(e) => setEnvironment(e.target.value)}
            variant="outlined"
            sx={{
              bgcolor: '#f5f5f5',
              '& .MuiOutlinedInput-root': {
                fontFamily: 'monospace',
                fontSize: '12px',
              },
            }}
            disabled={submitting}
          />
        </Box>

        {/* Submit Button */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={submitting || !errorInput.trim()}
            startIcon={submitting ? <CircularProgress size={20} /> : '🔍'}
            sx={{
              px: 4,
              fontWeight: 600,
            }}
          >
            {submitting ? 'Analyzing...' : 'Analyze Error'}
          </Button>
        </Box>

        {/* Quick Examples */}
        <Box sx={{ bgcolor: '#f0f8ff', p: 2, borderRadius: 1, borderLeft: '4px solid #0047ab' }}>
          <Typography variant="caption" sx={{ fontWeight: 600, color: '#0047ab', display: 'block', mb: 1 }}>
            💡 Examples
          </Typography>
          <Grid container spacing={1}>
            {(['Python Exception', 'JavaScript Error', 'Network Error'] as const).map((example, idx) => (
              <Grid item xs={12} sm={6} key={idx}>
                <Button
                  size="small"
                  variant="outlined"
                  fullWidth
                  sx={{ textTransform: 'none', justifyContent: 'flex-start' }}
                  onClick={() => {
                    const examples = [
                      `AttributeError: 'NoneType' object has no attribute 'split'
File "/app/parser.py", line 42, in parse
    parts = text.strip().split(',')`,
                      `TypeError: Cannot read property 'map' of undefined
at processItems (app.js:45:12)
at Array.forEach (<anonymous>)`,
                      `ConnectionRefusedError: [Errno 111] Connection refused
Failed to connect to 127.0.0.1:5432
Database connection timeout after 30s`,
                    ];
                    setErrorInput(examples[idx]);
                  }}
                >
                  {example}
                </Button>
              </Grid>
            ))}
          </Grid>
        </Box>
      </Box>
    </Paper>
  );
};

export default ErrorForm;
