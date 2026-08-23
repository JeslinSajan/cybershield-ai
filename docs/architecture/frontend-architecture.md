# CyberShield AI - Frontend Architecture

**Version:** 2.0  
**Phase:** 2 of 27 - System Architecture Design  
**Scope:** Current local-first MVP

## Application Shape

The Frontend is a React + TypeScript + Vite single-page application served locally during development. It renders role-aware views and communicates with the FastAPI Backend through JSON REST requests. It never connects to PostgreSQL or to the Agent directly.

```text
frontend/
  src/
    app/             # app bootstrap, route tree, providers
    components/      # shared tables, charts, forms, notices, dialogs
    features/        # dashboard, agents, devices, scans, alerts, logs...
    layouts/         # authenticated shell and navigation
    pages/           # route-level screens
    services/        # typed REST client and auth transport
    state/           # auth/session and small client UI state
    types/           # API and domain types
```

## Routing

React Router protects authenticated routes and applies role-aware navigation and guards:

- `/login` - public login
- `/dashboard` - summary cards, trends, and recent activity
- `/agents` - Agent status and Administrator enrollment/revocation actions
- `/devices` - discovered device inventory
- `/scans` - authorized discovery and vulnerability scan actions
- `/vulnerabilities` - findings, severity, and recommendations
- `/logs` - normalized log exploration
- `/alerts` - alert investigation and status timeline
- `/threat-intelligence` - local indicator search
- `/reports` - report generation and downloads
- `/users` - Administrator-only user and role management
- `/settings` - Administrator-only system and Agent settings

A Viewer can open read-only views allowed by the SRS. A Security Analyst cannot open user or settings management. The UI must show the authorization notice before discovery or scanning.

## State Management

- **Server state:** Use a query/cache layer such as TanStack Query for Backend data, loading states, errors, invalidation after mutations, and periodic refetch of dashboard/Agent status.
- **Session state:** Keep the authenticated user, role, and JWT lifecycle in an Auth provider/store. Expired or rejected tokens return the user to `/login`.
- **Local UI state:** Keep filters, dialog visibility, form drafts, selected rows, and temporary scan progress local to the owning feature.
- **URL state:** Put shareable filters, pagination, and selected view parameters in query parameters where useful.

The MVP uses REST refetching rather than WebSockets. Optimistic updates are limited to interactions whose outcome can be safely reconciled with the Backend response.

## Feature Boundaries

Each feature owns its API hooks, types, route screen, and focused components. Shared components handle tables, severity labels, risk bands, authorization notices, empty/error/loading states, and report download actions. The AI assistant is presented as the **Local Security Explanation Engine** and requests explanations for a selected alert, vulnerability, or risk score through the Backend AI endpoint.
