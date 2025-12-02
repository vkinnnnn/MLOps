# LoanAI Frontend

Modern React + Vite frontend for the Student Loan Document Extractor Platform.

## Features

- **Document Upload**: Upload PDF and image files with drag & drop
- **Voice Agent**: Talk to your documents using Gemini AI
- **Document CoPilot**: Interactive document analysis
- **Real-time Processing**: Integration with FastAPI backend

## Tech Stack

- **React 19** - UI framework
- **Vite** - Build tool
- **TypeScript** - Type safety
- **Framer Motion** - Animations
- **Lucide React** - Icons
- **Google Gemini AI** - Voice agent

## Setup

### Prerequisites

- Node.js 18+ or 20+
- Backend API running on `http://localhost:8000`

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.local.example .env.local
   ```
   
   Edit `.env.local`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   VITE_API_URL=http://localhost:8000
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Open browser**:
   ```
   http://localhost:3000
   ```

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

### Project Structure

```
frontend/
├── components/          # React components
│   ├── UploadDocuments.tsx
│   ├── TalkToDocuments.tsx
│   ├── DocumentIntegrator.tsx
│   └── Sidebar.tsx
├── services/            # API services
│   ├── api.ts          # Backend API integration
│   ├── gemini.ts       # Gemini AI client
│   └── audioUtils.ts   # Audio utilities
├── types.ts            # TypeScript types
├── App.tsx             # Main app component
└── vite.config.ts      # Vite configuration
```

## Backend Integration

The frontend integrates with the FastAPI backend at `http://localhost:8000`:

- **Document Upload**: `POST /api/v1/documents/upload`
- **Document Extraction**: `POST /api/v1/extract`
- **Chat**: `POST /api/v1/chat/message`
- **Document Retrieval**: `GET /api/v1/documents/{id}`

See `services/api.ts` for the complete API client.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key for voice agent | Required |
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |

## Production Build

```bash
npm run build
```

The build output will be in the `dist/` directory.

## Integration with Backend

This frontend is fully integrated with the Student Loan Document Extractor backend:

1. **Document Upload**: Files are uploaded to `/api/v1/documents/upload`
2. **Extraction**: Documents are processed via `/api/v1/extract`
3. **Chat**: Messages sent to `/api/v1/chat/message`
4. **Storage**: Document metadata stored in PostgreSQL via backend

Make sure the backend is running before using the frontend.
