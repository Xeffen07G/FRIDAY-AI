# Release Notes - v3-stable

## Features
- Profile memory
- Cross-chat recall
- STT
- WebSocket reconnect limits
- Stream dedup
- Health endpoint
- Render memory cap
- Orb presence states

## Fixes
- Addressed websocket storm issues with reconnect limits
- Stream duplication issues mitigated

## Known limitations
- Dependent on stable network connection for websocket
- Client requires hard refresh upon full system restart

## Performance
- Render memory capped for UI stability
- Stream deduplication prevents frontend lag

## Recovery
- Documented in RECOVERY.md. Basic recovery involves restarting backend/frontend and checking the health endpoint.
