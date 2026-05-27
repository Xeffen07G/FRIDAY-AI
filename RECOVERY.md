# Recovery

## Ports
- **Frontend**: 5174
- **Backend**: 8000

## Start Commands
- **Backend**: `uvicorn main:app --reload --port 8000`
- **Frontend**: `npm run dev`

## Health Endpoint
- `GET /api/health/`

## Known Stable Tag
- `v3-stable`

## Verified Features
- Profile memory
- Cross-chat recall
- STT
- WebSocket reconnect limits
- Stream dedup
- Health endpoint
- Render memory cap
- Orb presence states

## Known Recovery Steps
- Restart backend
- Restart frontend
- Hard refresh browser
- Verify health endpoint
