# BugReport AI Frontend

A modern, responsive React dashboard for analyzing software errors and generating intelligent insights.

## Features

- **Error Submission**: Submit errors as text, stack traces, logs, or JSON
- **Bug Report Viewer**: Professional structured bug report display
- **Root Cause Analysis (RCA)**: Visual presentation of probable causes with confidence scores
- **Similar Bugs Search**: Find historically similar bugs from the knowledge base
- **Fix Recommendations**: Get AI-powered fix suggestions

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Material-UI** for polished components
- **Axios** for API communication

## Getting Started

### Prerequisites

- Node.js 16+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

The dev server runs on `http://localhost:3000` and proxies API calls to `http://localhost:8000`.

## Project Structure

```
src/
├── components/          # React components
│   ├── ErrorForm.tsx
│   ├── BugReportViewer.tsx
│   ├── RCAResultsPanel.tsx
│   ├── SimilarBugsPanel.tsx
│   └── LoadingOverlay.tsx
├── services/           # API integration
│   └── api.ts
├── App.tsx            # Main app component
├── main.tsx           # Entry point
└── index.css          # Global styles
```

## API Integration

The frontend communicates with the backend API at `/api`. Ensure the backend is running on `http://localhost:8000` before starting the frontend.

### Key API Endpoints Used

- `POST /api/recommend-fix` - Full pipeline analysis
- `POST /api/search/similar` - Search for similar bugs
- `GET /api/health` - Health check

## UI Components

### ErrorForm
- Supports 4 input types: text, stack_trace, log, json
- Environment variable input
- Quick example buttons

### BugReportViewer
- Displays structured bug report
- Shows severity with visual indicators
- Sections for expected/actual behavior
- Steps to reproduce
- Affected components and environment

### RCAResultsPanel
- Shows error type and severity
- Lists probable causes with confidence scores
- Expandable cause cards with:
  - Recommendations
  - Code examples
  - Evidence list

### SimilarBugsPanel
- Grid of similar bugs with:
  - Similarity score progress bars
  - Repository information
  - Labels/tags
  - Link to GitHub issue

## Development

```bash
# Type checking
npm run lint

# Watch mode (automatic reload)
npm run dev
```

## Styling

The app uses Material-UI's theme system with custom color palette:
- Primary: #0047ab (Blue)
- Secondary: #00a8e1 (Cyan)
- Success: #00b050 (Green)
- Warning: #ffc715 (Yellow)
- Error: #e81123 (Red)

## Deployment

```bash
npm run build
```

This generates an optimized production build in the `dist/` folder.

## License

Same as parent project (BugReport AI)
