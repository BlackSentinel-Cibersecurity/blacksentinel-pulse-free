# BlackSentinel Pulse — Free / Open-Source Edition

> **This is the free, limited edition.** It's a real, functioning attack
> surface management platform — not a demo — but it is genuinely limited,
> not just flag-disabled: cloud/SaaS/GitHub discovery, threat-intel
> correlation, attack-graph/ML risk scoring, and policy-driven automated
> remediation are **not included in this repository's source at all**,
> and asset inventory is capped at 25 (`backend/app/core/edition.py`). For
> the full platform with those modules and no cap, see
> [blacksentinel.tech](https://blacksentinel.tech).

**AI Autonomous Attack Surface Management Platform**

> Never stops observing. Never stops discovering. Never stops learning.

---

## What is BlackSentinel Pulse?

BlackSentinel Pulse is a next-generation Attack Surface Management platform that
behaves like a living organism - continuously discovering, learning, relating,
predicting, prioritizing, explaining, correcting, and automating your entire
digital attack surface.

### Key Capabilities

- **Autonomous Discovery** - Automatically finds all assets across your infrastructure
- **AI-Powered Risk Scoring** - Multi-factor risk calculation with ML predictions
- **Attack Path Analysis** - Graph-based visualization of attack vectors
- **Real-Time Monitoring** - Continuous pulse of your entire attack surface
- **Threat Intelligence** - Correlation with global threat feeds
- **Automated Remediation** - Policy-driven response and fixing

---

## Quick Start

### Docker (Recommended)
```bash
git clone https://github.com/BlackSentinel-Cibersecurity/blacksentinel-pulse-free.git
cd pulse
bash setup.sh
# Access at http://localhost:3000
```

### Manual
```bash
# Backend
cd backend && pip install poetry && poetry install
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

### Default Credentials
| User | Password | Role |
|------|----------|------|
| `admin` | `admin123` | Super Admin |
| `analyst` | `analyst123` | Analyst |
| `viewer` | `viewer123` | Viewer |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      BLACKSENTINEL PULSE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Frontend    │  │   Backend    │  │   Workers    │          │
│  │  React/TS    │  │   FastAPI    │  │   Celery     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              Discovery Engines                        │       │
│  │  Domain | Network | Cloud | GitHub | Certificate     │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              AI/ML Engines                            │       │
│  │  Risk Scoring | Anomaly Detection | Attack Paths     │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              Data Layer                               │       │
│  │  PostgreSQL | Neo4j (Graph) | Redis (Cache)          │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, TailwindCSS, Recharts, Framer Motion |
| Backend | Python 3.11, FastAPI, SQLAlchemy, Pydantic v2 |
| Database | PostgreSQL 16, Neo4j 5, Redis 7 |
| Task Queue | Celery with Redis broker |
| ML/AI | NumPy, scikit-learn, custom engines |
| Infrastructure | Docker, Kubernetes, Helm |

---

## Deployment Options

| Method | Best For | Time |
|--------|----------|------|
| **Docker Compose** | Single server, POC | 5 min |
| **Kubernetes/Helm** | Enterprise, HA | 1 hour |
| **Cloud Managed** | Production | 1-2 hours |
| **On-Premise** | Regulated industries | 2-4 weeks |

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

**Guia paso a paso completa**: [docs/DEPLOYMENT_STEP_BY_STEP.md](docs/DEPLOYMENT_STEP_BY_STEP.md)

---

## API Documentation

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI spec: `http://localhost:8000/api/openapi.json`

---

## Project Structure

```
blacksentinel-pulse/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/v1/endpoints/   # 16 API endpoint modules
│   │   ├── core/               # Config, DB, Security, Middleware
│   │   ├── models/             # 16 SQLAlchemy models
│   │   └── services/           # Discovery, ML, Threat Intel
│   ├── migrations/             # Alembic migrations
│   └── seed.py                 # Initial data seeding
├── frontend/                   # React TypeScript frontend
│   └── src/
│       ├── pages/              # 13 page components
│       ├── components/         # Layout, common components
│       ├── services/           # API client with auto-refresh
│       └── store/              # Zustand state management
├── deploy/                     # Deployment configs
│   ├── helm/                   # Kubernetes Helm charts
│   └── scripts/                # Deployment scripts
├── docs/                       # Documentation
├── docker-compose.yml          # Development compose
├── docker-compose.prod.yml     # Production compose
└── .github/workflows/          # CI/CD pipeline
```

---

## Features

### Asset Discovery
- Domain & subdomain enumeration
- Port scanning & service detection
- Cloud resource discovery (AWS, Azure, GCP)
- GitHub repository & secret scanning
- Certificate Transparency monitoring
- DNS record enumeration

### Risk Analysis
- 7-factor AI risk scoring
- Attack path visualization
- Blast radius calculation
- Anomaly detection
- Predictive analytics

### Threat Intelligence
- VirusTotal integration
- AbuseIPDB correlation
- Custom threat feeds
- IOC matching

### Integrations
- AWS, Azure, GCP
- GitHub, GitLab
- Okta, Entra ID
- CrowdStrike, SentinelOne
- Jira, ServiceNow
- Slack, Teams, PagerDuty
- Splunk, Microsoft Sentinel

---

## Before you run it

- This is a **technical preview** and the open-source edition of the product. It comes with no warranty and no service-level commitment: try it in a test environment first.
- It is **self-hosted**. BlackSentinel does not host it for you, and paid plans are not on sale.
- Change every default credential and secret before exposing anything to a network. Never deploy with the example values from `.env.example` or `.env.production`.
- Use it only on systems you own or are explicitly authorized to test or monitor. See the [Acceptable Use Policy](https://blacksentinel.tech/acceptable-use/).

## Support

- Bugs and questions: [open an issue](https://github.com/BlackSentinel-Cibersecurity/blacksentinel-pulse-free/issues) in this repository.
- Security reports: follow [security.txt](https://blacksentinel.tech/.well-known/security.txt). Please do not open a public issue for a vulnerability.
- Everything else: BlackSentinel-tech@protonmail.com

## License

MIT. See [LICENSE](LICENSE). The BlackSentinel name and logo are not covered by the licence.
