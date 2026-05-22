---
schema_version: 2
id: diagram_0004
type: diagram
title: "Deployment Topology"
status: accepted
section: deployment_view
order: 40
date: "2026-05-21"
diagram_type: "mermaid"
caption: "archledger deployment nodes and their relationships"

related_records:
  - infrastructure_0001
  - infrastructure_0002
  - infrastructure_0003
  - infrastructure_0004
  - infrastructure_0005

tags:
  - deployment
body_format: markdown
created_at: "2026-05-21T19:34:08Z"
updated_at: "2026-05-21T19:38:00Z"
---

archledger has no server component. It runs as a local CLI tool on developer machines and in CI runners. The storage directory is co-located with the source repository.

```mermaid
graph TB
    subgraph "Developer Machine"
        DevEnv["Python 3.10+\nvenv / system"]
        DevCLI["archledger CLI\n(console script)"]
        DevWorkspace["Project Workspace\n.archledger/ + source/"]
        DevOutput["Build Output\nARCHITECTURE.md"]
        DevConverters["Optional Tools\npandoc, asciidoctor"]

        DevCLI --> DevWorkspace
        DevCLI --> DevOutput
        DevCLI -.->|"optional"| DevConverters
    end

    subgraph "CI Runner"
        CIPython["Python 3.10+"]
        CICLI["archledger CLI"]
        CIWorkspace["Checkout\n.archledger/ + source/"]
        CIArtifact["Build Artifacts"]

        CICLI --> CIWorkspace
        CICLI --> CIArtifact
    end

    subgraph "PyPI"
        PyPI["archledger wheel"]
    end

    PyPI -->|"pip install"| DevEnv
    PyPI -->|"pip install"| CIPython

    DevEnv --> DevCLI
    CIPython --> CICLI

    DevWorkspace -->|"git push"| CIWorkspace
    CIArtifact -->|"publish"| Docs["Docs Hosting"]

    style DevCLI fill:#4a9eff,color:#fff
    style CICLI fill:#4a9eff,color:#fff
    style PyPI fill:#fdcb6e
    style DevConverters fill:#f0f0f0,stroke-dasharray: 5 5
    style Docs fill:#00b894,color:#fff
```
