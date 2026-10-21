# CyberShield Agent Service Management & Deployment Guide

This guide describes how to run and manage the CyberShield Agent as a persistent system daemon on **Linux** (systemd) and **Windows** (Task Scheduler or NSSM Windows Service).

---

## 1. Architecture & Security Overview

The CyberShield Agent runs as a standalone endpoint monitoring process on monitored hosts.
It performs:
- Periodic telemetry collection and heartbeats (`POST /api/v1/agents/heartbeat`)
- Task polling and asynchronous scan execution (`GET /api/v1/agents/tasks`)
- Security log collection and transmission (`POST /api/v1/agents/logs`)
- Offline queue buffering (`offline_queue.json`) when network is interrupted

### Security Model
- **Non-Root Execution**: Runs under a dedicated unprivileged user (`cybershield`).
- **File Permissions**: Secret identity tokens (`agent_identity.json`) and offline queue files (`offline_queue.json`) are stored with strict `0600` permissions (owner read/write only).
- **Subprocess Isolation**: Scan commands are executed safely with bounded concurrency and argument termination (`--`) to prevent CLI option injection.

---

## 2. Linux Service Setup (systemd)

### Quick Automated Installation

1. Navigate to the agent source directory:
   ```bash
   cd cybershield-ai/agent
   ```

2. Configure your environment variables in `.env`:
   ```bash
   cp .env.example .env
   nano .env
   # Ensure BACKEND_URL and ENROLLMENT_TOKEN (or existing credentials) are set
   ```

3. Run the automated installer:
   ```bash
   sudo chmod +x install_service.sh
   sudo ./install_service.sh
   ```

4. Start the service:
   ```bash
   sudo systemctl start cybershield-agent
   sudo systemctl status cybershield-agent
   ```

### Manual systemd Installation

If you prefer to configure systemd manually:

1. Copy the unit file:
   ```bash
   sudo cp agent/cybershield-agent.service /etc/systemd/system/cybershield-agent.service
   sudo chmod 644 /etc/systemd/system/cybershield-agent.service
   ```

2. Reload systemd and enable on boot:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable cybershield-agent
   sudo systemctl start cybershield-agent
   ```

3. Monitor logs:
   ```bash
   sudo journalctl -u cybershield-agent -f
   ```

---

## 3. Windows Service Setup

Windows environments can deploy the agent using either **Windows Task Scheduler** (native, no third-party tools) or **NSSM** (Non-Sucking Service Manager).

### Method A: Windows Task Scheduler (Native)

1. Open PowerShell as **Administrator**.
2. Run the registration command to start the agent at system boot with auto-restart on failure:

   ```powershell
   $action = New-ScheduledTaskAction -Execute "C:\cybershield-agent\venv\Scripts\python.exe" `
       -Argument "-m agent.main" `
       -WorkingDirectory "C:\cybershield-agent"

   $trigger = New-ScheduledTaskTrigger -AtStartup
   $settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
       -ExecutionTimeLimit (New-TimeSpan -Days 365) `
       -StartWhenAvailable

   Register-ScheduledTask -TaskName "CyberShieldAgent" `
       -Action $action `
       -Trigger $trigger `
       -Settings $settings `
       -User "NT AUTHORITY\SYSTEM" `
       -RunLevel Highest
   ```

3. Start the task immediately:
   ```powershell
   Start-ScheduledTask -TaskName "CyberShieldAgent"
   Get-ScheduledTask -TaskName "CyberShieldAgent"
   ```

### Method B: NSSM (Non-Sucking Service Manager)

1. Download NSSM from `https://nssm.cc/download`.
2. Install the Windows Service:
   ```powershell
   nssm install CyberShieldAgent "C:\cybershield-agent\venv\Scripts\python.exe" "-m agent.main"
   nssm set CyberShieldAgent AppDirectory "C:\cybershield-agent"
   nssm set CyberShieldAgent Description "CyberShield AI Endpoint Security Agent"
   nssm set CyberShieldAgent Start SERVICE_AUTO_START
   nssm set CyberShieldAgent AppStdout "C:\cybershield-agent\agent.log"
   nssm set CyberShieldAgent AppStderr "C:\cybershield-agent\agent_error.log"
   nssm start CyberShieldAgent
   ```

3. Verify service state:
   ```powershell
   Get-Service -Name CyberShieldAgent
   ```

---

## 4. Verification and Troubleshooting

| Check | Expected Result | Troubleshooting |
|---|---|---|
| **Heartbeat** | Agent status is `ONLINE` in dashboard within 30s | Check `BACKEND_URL` in `.env` and network connectivity |
| **Log Ingestion** | Local auth attempts show up in Logs page | Verify event log collector is reading `auth.log` or Windows Security Log |
| **Scan Execution** | Triggering discovery scan completes and updates status | Verify Nmap is installed on system PATH or fallback ARP succeeds |
| **Offline Recovery** | Disconnect network, generate logs, reconnect | Verify `offline_queue.json` buffers items and drains on reconnect |

---

## 5. Uninstallation

### Linux
```bash
sudo systemctl stop cybershield-agent
sudo systemctl disable cybershield-agent
sudo rm -f /etc/systemd/system/cybershield-agent.service
sudo systemctl daemon-reload
```

### Windows
```powershell
Stop-ScheduledTask -TaskName "CyberShieldAgent"
Unregister-ScheduledTask -TaskName "CyberShieldAgent" -Confirm:$false
```
