# CyberShield AI - System Architecture
**Version:** 1.0  
**Date:** August 23, 2026

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Architecture Goals](#2-architecture-goals)
3. [System Components](#3-system-components)
4. [High-Level Architecture](#4-high-level-architecture)
5. [Cloud Architecture](#5-cloud-architecture)
6. [CyberShield Agent Architecture](#6-cybershield-agent-architecture)
7. [Backend Architecture](#7-backend-architecture)
8. [Frontend Architecture](#8-frontend-architecture)
9. [AI Architecture](#9-ai-architecture)
10. [Database Architecture](#10-database-architecture)
11. [Communication Architecture](#11-communication-architecture)
12. [Data Flow](#12-data-flow)
13. [Security Architecture](#13-security-architecture)
14. [Deployment Architecture](#14-deployment-architecture)
15. [Scalability](#15-scalability)
16. [Failure Handling](#16-failure-handling)
17. [Technology Mapping](#17-technology-mapping)

---

## 1. Architecture Overview

CyberShield AI is a distributed cybersecurity platform that leverages artificial intelligence for threat detection, real-time monitoring, and automated vulnerability scanning. The system follows a microservices-inspired architecture with clear separation of concerns between frontend, backend, AI services, and external agents.

The architecture is designed to be:
- **Modular**: Each component can be developed, deployed, and scaled independently
- **Secure**: End-to-end encryption with defense-in-depth security principles
- **Scalable**: Horizontal scaling capabilities to handle increased load
- **Resilient**: Built-in redundancy and fault tolerance mechanisms
- **Extensible**: Plugin architecture for adding new threat detection capabilities

---

## 2. Architecture Goals

### 2.1 Performance Goals
- **API Response Time**: < 200ms for 95th percentile of requests
- **Dashboard Load Time**: < 3 seconds initial load
- **AI Inference Time**: < 5 seconds for threat analysis
- **Concurrent Users**: Support 1,000+ concurrent users
- **Agent Throughput**: Handle 100+ simultaneous agent connections

### 2.2 Security Goals
- **Encryption**: TLS 1.3 for all communications
- **Authentication**: Multi-factor authentication for users
- **Authorization**: Role-based access control (RBAC)
- **Data Protection**: AES-256 encryption for data at rest
- **Compliance**: GDPR, SOC 2, and ISO 27001 compliance

### 2.3 Availability Goals
- **Uptime**: 99.9% availability (8.76 hours downtime/year)
- **Recovery Time**: < 4 hours RTO (Recovery Time Objective)
- **Recovery Point**: < 1 hour RPO (Recovery Point Objective)
- **Disaster Recovery**: Geographic redundancy

### 2.4 Scalability Goals
- **Horizontal Scaling**: Auto-scaling for backend services
- **Database Scaling**: Read replicas and connection pooling
- **Load Balancing**: Distribute traffic across multiple instances
- **Elastic Resources**: Cloud-native resource management

---

## 3. System Components

### 3.1 Core Components

| Component | Description | Technology |
|-----------|-------------|------------|
| **Nginx Reverse Proxy** | Entry point, SSL termination, load balancing | Nginx 1.18+ |
| **React Frontend** | User interface and dashboard | React 18+, TypeScript, Vite |
| **FastAPI Backend** | REST API server and business logic | FastAPI, Python 3.11+ |
| **PostgreSQL** | Primary data persistence | PostgreSQL 13+ |
| **Qwen AI** | AI model for threat detection | Qwen (Local Model) |
| **Background Tasks** | Asynchronous job processing | Celery, Redis |
| **AI Context Layer** | AI model context management | Custom implementation |

### 3.2 External Components

| Component | Description | Technology |
|-----------|-------------|------------|
| **CyberShield Agents** | Distributed security monitoring agents | Python, HTTPS REST API |
| **Local Networks** | Customer network environments | Customer infrastructure |

---

## 4. High-Level Architecture

```
                         INTERNET
                            │
                            │ HTTPS
                            ▼
                    ┌───────────────┐
                    │     Nginx     │
                    │ Reverse Proxy │
                    └───────┬───────┘
                            │
             ┌──────────────┴──────────────┐
             │                             │
             ▼                             ▼
     ┌─────────────────┐          ┌─────────────────┐
     │ React Frontend  │          │ FastAPI Backend │
     │ TypeScript/Vite │          │    REST API     │
     └─────────────────┘          └───────┬─────────┘
                                            │
                    ┌─────────────────────┼──────────────────┐
                    │                     │                  │
                    ▼                     ▼                  ▼
             ┌────────────┐       ┌──────────────┐   ┌─────────────┐
             │ PostgreSQL │       │ Qwen AI      │   │ Background  │
             │            │       │ Local Model  │   │ Tasks       │
             └────────────┘       └──────────────┘   └─────────────┘
                                         ▲
                                          │
                              AI Context Layer
                                          │
                                          │ 
                    HTTPS REST API         │
                       ▲                   │
                       │                   │
┌──────────────────────┴───────────────────┘
│
│
┌──────────────────────────────────────────────────────┐
│                    CyberShield Agents                 │
├──────────────┬──────────────┬──────────────┬─────────┤
▼              ▼              ▼              ▼         ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────┐
│ CyberShield│ │CyberShield │ │CyberShield │ │  ...   │
│ Agent #1   │ │ Agent #2   │ │ Agent #3   │ │Agent #N│
└─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └───┬────┘
      │               │               │            │
      ▼               ▼               ▼            ▼
   Local         Local          Local         Local
 Network       Network        Network       Network
```

### 4.1 Architecture Layers

**Presentation Layer**
- React Frontend: Single-page application with TypeScript
- Responsive design for desktop, tablet, and mobile
- Real-time updates via WebSocket connections

**Application Layer**
- FastAPI Backend: RESTful API with async support
- Business logic and orchestration
- Authentication and authorization

**Data Layer**
- PostgreSQL: Relational database for structured data
- Connection pooling and query optimization
- Backup and replication strategies

**AI Layer**
- Qwen AI Model: Local deployment for threat analysis
- AI Context Layer: Manages model state and context
- Background processing for AI inference

**Agent Layer**
- CyberShield Agents: Distributed monitoring nodes
- HTTPS REST API communication
- Local network integration

---

## 5. Cloud Architecture

### 5.1 Cloud Provider Strategy

The system is designed for cloud-agnostic deployment with support for:
- **AWS**: Amazon Web Services
- **GCP**: Google Cloud Platform
- **Azure**: Microsoft Azure
- **Self-hosted**: On-premises deployment

### 5.2 Cloud Components

**Compute Resources**
- Virtual machines or container instances for backend services
- Auto-scaling groups for horizontal scaling
- Serverless functions for event-driven tasks

**Storage Resources**
- Managed PostgreSQL instances with automated backups
- Object storage for file uploads and reports
- CDN for static asset delivery

**Networking**
- Virtual Private Cloud (VPC) isolation
- Load balancers for traffic distribution
- CDN for global content delivery

### 5.3 Cloud Security

- **Network Security Groups**: Firewall rules at subnet level
- **IAM Roles**: Least-privilege access control
- **KMS Encryption**: Key management for data encryption
- **Security Monitoring**: Cloud-native security tools

---

## 6. CyberShield Agent Architecture

### 6.1 Agent Overview

CyberShield Agents are lightweight, distributed monitoring components deployed in customer local networks. They collect security data and communicate with the central platform via HTTPS REST API.

### 6.2 Agent Components

```
┌─────────────────────────────────────────┐
│         CyberShield Agent               │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Data Collector│  │ Event Queue  │   │
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Local Cache  │  │ HTTP Client   │   │
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Config Manager│ │ Health Check  │   │
│  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────┘
```

### 6.3 Agent Responsibilities

- **Data Collection**: Gather security metrics, logs, and events
- **Local Processing**: Pre-process data before transmission
- **Secure Communication**: HTTPS with mutual TLS authentication
- **Offline Mode**: Cache data when connectivity is lost
- **Self-Healing**: Automatic recovery from failures
- **Configuration Management**: Remote configuration updates

### 6.4 Agent Communication

**Protocol**: HTTPS REST API  
**Authentication**: Mutual TLS with client certificates  
**Data Format**: JSON  
**Compression**: Gzip for large payloads  
**Retry Logic**: Exponential backoff for failed requests

---

## 7. Backend Architecture

### 7.1 Backend Overview

The FastAPI backend serves as the central API gateway, handling all business logic, data processing, and coordination between components.

### 7.2 Backend Structure

```
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐   │
│  │ API Routes    │  │ Middleware   │   │
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Services     │  │ Models       │   │
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Repositories │  │ Schemas      │   │
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Auth         │  │ Utils        │   │
│  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────┘
```

### 7.3 Backend Modules

**API Routes**
- `/api/v1/auth` - Authentication endpoints
- `/api/v1/threats` - Threat detection and analysis
- `/api/v1/monitoring` - Real-time monitoring data
- `/api/v1/vulnerabilities` - Vulnerability scanning
- `/api/v1/reports` - Report generation
- `/api/v1/agents` - Agent management
- `/api/v1/users` - User management

**Services**
- ThreatDetectionService: AI-powered threat analysis
- MonitoringService: Real-time metrics collection
- VulnerabilityService: Vulnerability scanning
- ReportService: Report generation
- AgentService: Agent communication
- UserService: User management

**Middleware**
- Authentication: JWT token validation
- Rate Limiting: Request throttling
- CORS: Cross-origin resource sharing
- Logging: Request/response logging
- Error Handling: Centralized error processing

### 7.4 Backend Technologies

- **Framework**: FastAPI with async/await
- **ORM**: SQLAlchemy with async support
- **Validation**: Pydantic models
- **Authentication**: JWT with OAuth2
- **Task Queue**: Celery with Redis broker
- **API Documentation**: OpenAPI/Swagger auto-generation

---

## 8. Frontend Architecture

### 8.1 Frontend Overview

The React frontend provides a modern, responsive user interface for interacting with the CyberShield AI platform.

### 8.2 Frontend Structure

```
┌─────────────────────────────────────────┐
│         React Frontend                  │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Pages        │  │ Components  │   │
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Hooks        │  │ Context      │   │
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Services     │  │ Utils        │   │
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ State        │  │ Routing      │   │
│  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────┘
```

### 8.3 Frontend Modules

**Pages**
- Dashboard: Overview and key metrics
- Threats: Threat detection and analysis
- Monitoring: Real-time monitoring views
- Vulnerabilities: Vulnerability reports
- Reports: Report generation and viewing
- Agents: Agent management and status
- Settings: User and system configuration

**Components**
- Charts: Data visualization (Chart.js/D3)
- Tables: Data tables with sorting/filtering
- Forms: Input forms with validation
- Alerts: Notification components
- Modals: Dialog components

**State Management**
- React Context API for global state
- Local component state for UI
- Server state via React Query

### 8.4 Frontend Technologies

- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite for fast development
- **Routing**: React Router
- **State**: React Context + React Query
- **UI Library**: TailwindCSS + shadcn/ui
- **Charts**: Chart.js or Recharts
- **Forms**: React Hook Form
- **HTTP Client**: Axios or Fetch API

---

## 9. AI Architecture

### 9.1 AI Overview

The AI architecture leverages the Qwen model for intelligent threat detection and analysis, with a context layer for managing model state and improving accuracy.

### 9.2 AI Components

```
┌─────────────────────────────────────────┐
│         AI Architecture                 │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Qwen Model   │  │ Context Layer│   │
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Preprocessor │  │ Postprocessor│   │
│  └──────────────┘  └──────────────┘   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Cache        │  │ Monitor      │   │
│  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────┘
```

### 9.3 AI Pipeline

**Input Processing**
1. Data normalization and validation
2. Feature extraction
3. Context preparation

**Model Inference**
1. Load model and context
2. Run inference
3. Generate predictions

**Output Processing**
1. Result validation
2. Confidence scoring
3. Alert generation

### 9.4 AI Context Layer

The AI Context Layer maintains:
- **Historical Context**: Past threat patterns
- **Environmental Context**: System configuration
- **Temporal Context**: Time-based patterns
- **User Context**: User-specific patterns

### 9.5 AI Technologies

- **Model**: Qwen (local deployment)
- **Framework**: PyTorch or TensorFlow
- **Serving**: FastAPI with async inference
- **Caching**: Redis for model cache
- **Monitoring**: Model performance metrics

---

## 10. Database Architecture

### 10.1 Database Overview

PostgreSQL serves as the primary database, providing relational data storage with advanced features for the CyberShield AI platform.

### 10.2 Database Schema

**Core Tables**
- `users`: User accounts and authentication
- `roles`: Role definitions for RBAC
- `permissions`: Permission definitions
- `threats`: Detected threats and analysis
- `vulnerabilities`: Vulnerability scan results
- `agents`: Agent registration and status
- `reports`: Generated reports
- `audit_logs`: System audit trail
- `alerts`: Alert history and status

### 10.3 Database Features

**Performance**
- Indexes on frequently queried columns
- Connection pooling (PgBouncer)
- Query optimization and analysis
- Read replicas for scaling

**Security**
- Row-level security (RLS)
- Encryption at rest
- Role-based access
- Audit logging

**Backup and Recovery**
- Daily automated backups
- Point-in-time recovery
- Geographic replication
- Backup validation

### 10.4 Database Technologies

- **Database**: PostgreSQL 13+
- **Connection Pooling**: PgBouncer
- **ORM**: SQLAlchemy (async)
- **Migrations**: Alembic
- **Monitoring**: pg_stat_statements

---

## 11. Communication Architecture

### 11.1 Communication Protocols

**Client-Server Communication**
- **Protocol**: HTTPS/TLS 1.3
- **Format**: JSON
- **Compression**: Gzip
- **Authentication**: JWT tokens

**Agent-Server Communication**
- **Protocol**: HTTPS with mutual TLS
- **Format**: JSON
- **Authentication**: Client certificates
- **Retry Logic**: Exponential backoff

**Real-time Communication**
- **Protocol**: WebSocket (wss://)
- **Format**: JSON
- **Authentication**: JWT tokens
- **Heartbeat**: Keep-alive messages

### 11.2 API Design

**RESTful Principles**
- Resource-based URLs
- HTTP verbs (GET, POST, PUT, DELETE)
- Status codes for responses
- HATEOAS for navigation

**API Versioning**
- URL-based versioning (/api/v1/)
- Backward compatibility
- Deprecation policy

**Rate Limiting**
- Per-user rate limits
- Per-endpoint limits
- Burst allowance
- Sliding window algorithm

---

## 12. Data Flow

### 12.1 Threat Detection Flow

```
Agent → HTTPS → Backend → AI Context → Qwen AI → Analysis → Database → Frontend
```

1. **Collection**: Agent collects security data
2. **Transmission**: HTTPS POST to backend API
3. **Processing**: Backend validates and processes data
4. **AI Analysis**: Data sent to AI context layer
5. **Inference**: Qwen model analyzes threats
6. **Storage**: Results stored in database
7. **Notification**: Frontend updated via WebSocket

### 12.2 Monitoring Flow

```
System → Agent → HTTPS → Backend → Database → WebSocket → Frontend
```

1. **Collection**: System metrics collected by agent
2. **Transmission**: HTTPS POST to backend
3. **Storage**: Metrics stored in database
4. **Real-time**: WebSocket push to frontend
5. **Visualization**: Dashboard updated

### 12.3 Vulnerability Scanning Flow

```
User Request → Frontend → Backend → Scanner → Analysis → Database → Report
```

1. **Request**: User initiates scan via frontend
2. **Scheduling**: Backend schedules background task
3. **Scanning**: Scanner performs vulnerability check
4. **Analysis**: Results analyzed and prioritized
5. **Storage**: Findings stored in database
6. **Reporting**: Report generated and displayed

---

## 13. Security Architecture

### 13.1 Security Layers

**Network Security**
- TLS 1.3 for all communications
- Firewall rules and network segmentation
- DDoS protection
- IP whitelisting for agents

**Application Security**
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection

**Data Security**
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Key management (KMS)
- Data retention policies

**Identity Security**
- Multi-factor authentication
- Role-based access control
- Session management
- Password policies

### 13.2 Security Controls

**Authentication**
- JWT tokens with short expiration
- Refresh token rotation
- Multi-factor authentication
- OAuth2 integration

**Authorization**
- Role-based access control (RBAC)
- Attribute-based access control (ABAC)
- Least privilege principle
- Regular permission audits

**Audit and Compliance**
- Comprehensive audit logging
- Security event monitoring
- Regular penetration testing
- Compliance reporting (GDPR, SOC 2)

---

## 14. Deployment Architecture

### 14.1 Deployment Strategy

**Environment Stages**
- **Development**: Local development environment
- **Staging**: Pre-production testing environment
- **Production**: Live production environment

**Deployment Methods**
- **Containerization**: Docker for all services
- **Orchestration**: Kubernetes for production
- **CI/CD**: Automated deployment pipeline
- **Infrastructure as Code**: Terraform/Ansible

### 14.2 Deployment Components

**Frontend Deployment**
- Build optimization with Vite
- Static asset CDN delivery
- Progressive Web App (PWA) support
- Service worker for offline capability

**Backend Deployment**
- Containerized FastAPI application
- Horizontal pod autoscaling
- Health checks and readiness probes
- Rolling updates with zero downtime

**Database Deployment**
- Managed PostgreSQL service
- Automated backups
- Read replicas for scaling
- Connection pooling

### 14.3 CI/CD Pipeline

**Stages**
1. **Build**: Compile and package applications
2. **Test**: Run unit and integration tests
3. **Security**: Security scanning and vulnerability checks
4. **Deploy**: Deploy to staging environment
5. **Verify**: Automated smoke tests
6. **Promote**: Deploy to production

---

## 15. Scalability

### 15.1 Horizontal Scaling

**Backend Scaling**
- Stateless API design
- Load balancing across instances
- Auto-scaling based on CPU/memory
- Database connection pooling

**Frontend Scaling**
- Static asset CDN
- Edge caching
- Progressive loading
- Code splitting

**Database Scaling**
- Read replicas for query scaling
- Connection pooling
- Query optimization
- Database sharding (if needed)

### 15.2 Vertical Scaling

**Resource Allocation**
- CPU-optimized instances for AI inference
- Memory-optimized instances for caching
- Storage-optimized instances for database
- GPU instances for AI model training

### 15.3 Caching Strategy

**Application Caching**
- Redis for session storage
- API response caching
- Query result caching
- Static asset caching

**CDN Caching**
- Static files (JS, CSS, images)
- API responses (where appropriate)
- Geographic distribution
- Cache invalidation strategy

---

## 16. Failure Handling

### 16.1 Fault Tolerance

**Component Redundancy**
- Multiple backend instances
- Database replication
- Load balancer redundancy
- Multi-zone deployment

**Graceful Degradation**
- Feature flags for disabling non-critical features
- Fallback mechanisms for AI failures
- Offline mode for agents
- Cached data when services unavailable

### 16.2 Error Handling

**Backend Error Handling**
- Centralized exception handling
- Retry logic with exponential backoff
- Circuit breaker pattern
- Dead letter queues for failed tasks

**Frontend Error Handling**
- Error boundaries for React components
- User-friendly error messages
- Automatic retry for failed requests
- Offline detection and handling

### 16.3 Monitoring and Alerting

**Health Checks**
- Application health endpoints
- Database connectivity checks
- External service availability
- Resource utilization monitoring

**Alerting**
- Critical alerts via multiple channels
- Warning alerts for degraded performance
- Informational alerts for maintenance
- Alert escalation policies

### 16.4 Disaster Recovery

**Backup Strategy**
- Automated daily backups
- Geographic backup replication
- Backup encryption
- Regular backup restoration tests

**Recovery Procedures**
- Documented recovery runbooks
- Recovery time objectives (RTO)
- Recovery point objectives (RPO)
- Regular disaster recovery drills

---

## 17. Technology Mapping

### 17.1 Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | React | 18+ | UI Framework |
| | TypeScript | 5+ | Type Safety |
| | Vite | 5+ | Build Tool |
| | TailwindCSS | 3+ | Styling |
| | shadcn/ui | Latest | UI Components |
| | React Router | 6+ | Routing |
| | React Query | Latest | Server State |
| | Chart.js | 4+ | Data Visualization |
| **Backend** | FastAPI | Latest | API Framework |
| | Python | 3.11+ | Runtime |
| | SQLAlchemy | 2+ | ORM |
| | Pydantic | 2+ | Validation |
| | Celery | 5+ | Task Queue |
| | Redis | 7+ | Cache/Broker |
| | PostgreSQL | 13+ | Database |
| | Alembic | Latest | Migrations |
| **Infrastructure** | Nginx | 1.18+ | Reverse Proxy |
| | Docker | Latest | Containerization |
| | Kubernetes | Latest | Orchestration |
| | Terraform | Latest | IaC |
| | GitHub Actions | Latest | CI/CD |
| **AI/ML** | Qwen | Latest | AI Model |
| | PyTorch | 2+ | ML Framework |
| | Transformers | Latest | NLP Library |
| **Security** | OpenSSL | Latest | TLS/SSL |
| | bcrypt | Latest | Password Hashing |
| | JWT | Latest | Authentication |

### 17.2 External Services

| Service | Purpose | Integration |
|---------|---------|-------------|
| Qwen AI | Threat detection | Local deployment |
| PostgreSQL | Data persistence | Managed service |
| Redis | Caching and queue | Managed service |
| CDN | Static asset delivery | Cloud provider |

### 17.3 Development Tools

| Tool | Purpose |
|------|---------|
| Git | Version control |
| VS Code | IDE |
| pytest | Testing |
| Black | Code formatting |
| ESLint | Linting |
| Prettier | Code formatting |

---

## Appendix A: Architecture Decision Records

### ADR-001: Choice of FastAPI for Backend
**Status**: Accepted  
**Context**: Need for high-performance, async API framework  
**Decision**: Use FastAPI for backend development  
**Consequences**: Improved performance, automatic API documentation, async support

### ADR-002: Local AI Model Deployment
**Status**: Accepted  
**Context**: Data privacy and latency requirements  
**Decision**: Deploy Qwen AI model locally  
**Consequences**: Better privacy, lower latency, higher infrastructure costs

### ADR-003: PostgreSQL as Primary Database
**Status**: Accepted  
**Context**: Need for relational database with advanced features  
**Decision**: Use PostgreSQL as primary database  
**Consequences**: ACID compliance, advanced features, strong ecosystem

---

## Appendix B: Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | August 23, 2026 | Architecture Team | Initial system architecture document |
