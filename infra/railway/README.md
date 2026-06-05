# Railway Deployment

Deploy both services (web + api) on Railway.

## Setup

1. Create a new Railway project
2. Add two services from the same repo:

### Web Service (Next.js)
- **Root Directory**: `apps/web`
- **Build Command**: `pnpm install && pnpm build`
- **Start Command**: `pnpm start`
- **Port**: `3000`

### API Service (FastAPI)
- **Root Directory**: `services/api`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Environment Variables

Set these on the API service:

| Variable | Value |
|----------|-------|
| `B2_ENDPOINT` | Your B2 S3 endpoint |
| `B2_APPLICATION_KEY_ID` | Your B2 application key ID |
| `B2_APPLICATION_KEY` | Your B2 application key |
| `B2_BUCKET_NAME` | Your bucket name |
| `B2_REGION` | Your B2 region (e.g., `us-west-004`) |
| `OPENAI_API_KEY` | OpenAI key — powers both script generation (LLM) and TTS |
| `LLM_MODEL` | (optional) LLM model — defaults to `gpt-4o-mini` |
| `TTS_MODEL` | (optional) TTS model — defaults to `gpt-4o-mini-tts` |
| `TTS_VOICE_HOST_A` | (optional) voice for Host A — defaults to `alloy` |
| `TTS_VOICE_HOST_B` | (optional) voice for Host B — defaults to `verse` |
| `HOST_A_NAME` | (optional) Host A display name — defaults to `Alex` |
| `HOST_B_NAME` | (optional) Host B display name — defaults to `Sam` |
| `API_CORS_ORIGINS` | Your web service URL (e.g., `https://web-production-xxx.up.railway.app`) |

> `B2_APPLICATION_KEY_ID`, `B2_REGION`, and `OPENAI_API_KEY` are required — the API fails fast at startup if any required B2 var is missing or still a placeholder.

Set this on the Web service:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | Your API service URL (e.g., `https://api-production-xxx.up.railway.app`) |
