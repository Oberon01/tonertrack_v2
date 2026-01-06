# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-01-06
### Added
- Initial stable release (v1.0.0).
- REST API via FastAPI with endpoints for printer management and polling.
- Web UI (static) and basic dashboard features.
- `start.py` launcher and `main.py` FastAPI server.
- `.env.example`, `VERSION`, `LICENSE` (MIT), and `CHANGELOG.md`.
### Changed
- Aligned docs to use project-local `./data` directory and clarified configuration via `TONERTRACK_DATA_DIR`.
- Set default `AUTO_POLL_INTERVAL` to 5 minutes and fixed related documentation.
- Cleaned repository: updated `.gitignore`, removed generated files from git history (untracked), removed Docker artifacts per local network constraints.
### Security
- Removed local `.env` from tracked files. Any exposed tokens should be rotated.

### Notes
- Docker and compose files were intentionally removed because containerized networking could not reach SNMP devices in this environment. If you need container support, add a `Dockerfile` and `docker-compose.yml` tuned to your network.
