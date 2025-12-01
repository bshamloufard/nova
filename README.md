# Nova - Clinician Transcription Tool

An intelligent medical transcription tool that goes beyond standard speech-to-text by implementing a **Multi-Model Orchestration System** for handling uncertain audio segments.

## Features

- **Multi-Model Transcription**: Uses 3 speech-to-text APIs (Deepgram, AssemblyAI, OpenAI Whisper) with word-level confidence scores
- **Low Confidence Detection**: Identifies segments where confidence falls below threshold
- **Orchestrator Council**: When confidence is low, invokes all 3 models for that segment
- **LLM Judge**: Uses GPT-4 to evaluate which transcription fits best contextually
- **Clinical Intelligence Extraction**: Identifies action items, numerical values (vitals, labs, dosages), and important clinical information
- **Interactive Timeline**: Visual scrubbing with synchronized audio playback and karaoke-style text highlighting

## Project Structure

```
nova/
├── backend/                 # Python FastAPI backend
│   ├── api/                # API routes
│   ├── core/               # Orchestrator, confidence analyzer, LLM judge
│   ├── models/             # Pydantic models
│   ├── services/           # Transcription services, clinical extractor
│   └── main.py             # FastAPI entry point
│
├── frontend/               # React + TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── stores/         # Zustand state management
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript definitions
│   └── package.json
│
└── api.md                  # API keys configuration
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- API keys for:
  - Deepgram
  - AssemblyAI
  - OpenAI

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

The backend will start at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will start at `http://localhost:5173`

### API Keys Configuration

Create an `api.md` file in the project root with your API keys:

```
deepgram = your_deepgram_api_key
AssemblyAI = your_assemblyai_api_key
OpenAI = your_openai_api_key
```

Or set environment variables (copy `.env.example` to `.env` in the backend folder).

## How It Works

### Multi-Model Orchestration Flow

1. **Primary Transcription**: Audio is first transcribed using Deepgram Nova-3 (fastest, most accurate)

2. **Confidence Analysis**: The system scans for words with confidence below threshold (default: 0.75)

3. **Orchestrator Council**: For uncertain segments:
   - Extract the audio segment with context padding
   - Send to all 3 transcription models concurrently
   - Collect all transcriptions with confidence scores

4. **LLM Judge**: GPT-4 evaluates candidates and:
   - **SELECTS** the best existing transcription (strongly preferred)
   - **SYNTHESIZES** only as a last resort if all candidates are clearly wrong

5. **Clinical Extraction**: From the final transcript:
   - Action items (prescriptions, follow-ups, referrals, tests)
   - Numerical values (vitals, labs, dosages)
   - Medical terminology

6. **Timeline Generation**: Creates interactive timeline with:
   - Word-level timestamps for karaoke sync
   - Color-coded markers for different content types

## Tech Stack

### Backend
- FastAPI
- Pydantic for validation
- aiohttp for async HTTP
- pydub for audio processing

### Frontend
- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS with pastel color palette
- WaveSurfer.js for audio visualization
- Zustand for state management

## API Endpoints

- `POST /api/transcribe` - Upload audio file, returns job ID
- `GET /api/transcription/{job_id}/status` - Check processing status
- `GET /api/transcription/{job_id}` - Get full transcription result
- `GET /api/audio/{job_id}` - Stream audio file
- `GET /api/health` - Health check

## License

MIT

