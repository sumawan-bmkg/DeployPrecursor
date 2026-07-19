# Knowledge Graph — PIMES System Architecture

**Version:** v2.0.0-rc2-freeze

## Data Flow

```mermaid
graph TD
    A[ULF Magnetometer] -->|Raw signal| B[Collector]
    B -->|Files| C[Preprocessing]
    C -->|CWT Scalogram| D[Tensor Builder]
    D -->|Tensor| E[Inference Engine]
    E -->|Prediction| F[Dashboard BOCC]
    F -->|Status| G[OSC — Hourly Snapshots]
    G -->|Evidence| H[CEPSL — SHA256 Chain]
    H -->|Integrity| I[SEOS — Evidence Storage]
    I -->|Audit| J[OSRV — Qualification Reports]
    J -->|Certificate| K[SOQ/CSQ — Scientific Qualification]
    K -->|Accreditation| L[SOAP — Operational Accreditation]
    L -->|Readiness| M[FOAC — Final Acceptance]
    M -->|Release| N[RC2 Transition Package]
```

## Component Dependency

```mermaid
graph LR
    subgraph Data
        A1[Collector] --> A2[Preprocessing]
        A2 --> A3[Tensor Builder]
        A3 --> A4[Inference]
    end
    subgraph Scientific
        B1[Prior Models] --> A4
        B2[RDMC Signatures] --> A1
        B3[Cosmic Features] --> A4
    end
    subgraph Operational
        C1[OSC] --> C2[CEPSL]
        C2 --> C3[SEOS]
        C3 --> C4[OSRV]
    end
    subgraph Governance
        D1[State Machine] --> D2[Actions]
        D2 --> D3[Evidence]
    end
    subgraph Deployment
        E1[PDM] --> E2[Blue-Green]
        E2 --> E3[Health Check]
        E3 --> E4[Rollback]
    end
    A4 --> C1
    C4 --> K1[SOQ]
    C4 --> K2[CSQ]
    K1 --> K3[SOAP]
    K2 --> K3
    K3 --> F1[FOAC]
    E4 --> F1
```

## Validation Chain

| Stage | Input | Output | Evidence |
|-------|-------|--------|----------|
| 1. Collector | Raw ULF | Files | OSC snapshot |
| 2. Preprocessing | Files | CWT scalogram | PSEP dual execution |
| 3. Tensor | Scalogram | Tensor | Golden dataset |
| 4. Inference | Tensor + Prior | Prediction | Runtime log |
| 5. Dashboard | Prediction | Visualization | API endpoints |
| 6. OSC | Dashboard state | Hourly snapshot | Append-only log |
| 7. CEPSL | OSC state | SHA256 lock | Archive hash |
| 8. SEOS | Evidence | Stored | UUID + SHA256 |
| 9. OSRV | Evidence | Reports | 10 qualification reports |
| 10. SOQ/CSQ | Reports | Score | Qualification certificate |
| 11. SOAP | Score | Accreditation | Final certificate |
| 12. FOAC | All above | Acceptance | Conditional GO |
