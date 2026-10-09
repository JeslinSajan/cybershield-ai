# CyberShield Agent

The CyberShield Agent is a lightweight host monitoring and security telemetry collector.
It operates within the monitored network or endpoint and communicates outbound over HTTPS with the CyberShield API backend.

## Telemetry Collection
- **Heartbeat & System Metrics**: CPU, memory, and disk usage via `psutil`.
- **Network Discovery & Vulnerability Scans**: Runs scheduled network scans via Nmap.
- **Log Collection**:
  - **Linux**: Reads authentication logs from `/var/log/auth.log` or `/var/log/secure` for SSH login successes and failures.
  - **Windows (Optional)**: Reads the Windows Security Event Log (Event IDs 4624 and 4625) using `pywin32`.
    - `pywin32` is completely optional:
      ```bash
      pip install pywin32
      ```
    - If `pywin32` is not installed, the agent logs an informative warning and continues all other functions normally without errors.

For full installation and setup instructions, refer to [INSTALL.md](INSTALL.md).
