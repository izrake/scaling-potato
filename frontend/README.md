# LinkedIn Enricher - Frontend

React-based frontend for the LinkedIn Enricher Admin Panel.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000` and proxy API requests to `http://localhost:9001`.

## Build

To build for production:
```bash
npm run build
```

The built files will be in the `dist/` directory.

## Environment Variables

Create a `.env` file in the frontend directory:

```
VITE_API_URL=http://localhost:9001
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable components
│   ├── pages/          # Page components
│   ├── utils/          # Utility functions (API, etc.)
│   ├── App.jsx         # Main app component
│   └── main.jsx        # Entry point
├── public/             # Static assets
├── index.html          # HTML template
└── package.json        # Dependencies
```

## Pages

- **Dashboard**: Overview with stats (Leads Uploaded, Leads Enriched)
- **Jobs**: View and manage enrichment jobs
- **Leads**: Browse and manage enriched leads with swipe actions
- **Settings**: Configure AI model, API key, and system prompts

