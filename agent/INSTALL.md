# CyberShield Agent — Installation Guide

## Requirements
- Python 3.12+
- Nmap (for Phase 11+ scanning — not needed for Phase 9)
  - Linux: `sudo apt install nmap`
  - Windows: https://nmap.org/download.html
  - macOS: `brew install nmap`

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy the example configuration:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and set:
   - `BACKEND_URL` — your CyberShield backend URL
   - `ENROLLMENT_TOKEN` — get this from the CyberShield dashboard (Admin → Agents → Generate Token)
   - `AGENT_NAME` — a recognizable name for this machine

4. Run the agent:
   ```bash
   python -m agent.main
   ```
   Or:
   ```bash
   python main.py
   ```

5. The agent will enroll on first run and save its identity to `agent_identity.json`.
   **Never commit `agent_identity.json` to git.**

## Security Note

- `agent_identity.json` contains the agent credential token. Keep it secure.
- On Linux/macOS the file is created with `chmod 600` (owner-read-only).
- If the token is compromised, revoke it from the dashboard and delete `agent_identity.json`.

## Limitations (MVP)

- Enrollment tokens are stored in backend memory and are lost on backend restart.
  In production, these should be stored in the database or Redis.
- No automatic credential rotation — rotate manually from the Admin dashboard.
