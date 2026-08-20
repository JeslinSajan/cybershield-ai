# Initial Architecture

```
                    ┌──────────────────┐
                    │      User        │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ React Dashboard  │
                    └────────┬─────────┘
                             │ HTTPS
                             ▼
                    ┌──────────────────┐
                    │      Nginx       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  FastAPI Backend │
                    └─────┬──────┬─────┘
                          │      │
                 ┌────────┘      └────────┐
                 ▼                        ▼
          ┌─────────────┐          ┌─────────────┐
          │ PostgreSQL  │          │ Qwen / AI   │
          └─────────────┘          └─────────────┘
                          ▲
                          │ HTTPS
                          │
                ┌─────────┴─────────┐
                │ CyberShield Agent │
                └───────────────────┘
```

## Components

- **User**: End users interacting with the system
- **React Dashboard**: Frontend web application for user interface
- **Nginx**: Reverse proxy and load balancer
- **FastAPI Backend**: RESTful API backend server
- **PostgreSQL**: Primary database for data persistence
- **Qwen / AI**: AI model for threat detection and analysis
- **CyberShield Agent**: External agent that communicates with the system via HTTPS
