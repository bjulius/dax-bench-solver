# DAX Bench v4 Validation Flow

## Overview

This document describes the complete testing and validation workflow for DAX Bench v4, which uses **mandatory Power BI execution validation** instead of pattern matching.

## Flow Diagram

```mermaid
flowchart TD
    subgraph Setup["🔧 Setup"]
        A[Start Benchmark] --> B{Power BI<br/>Connected?}
        B -->|No| C[❌ Exit with Error]
        B -->|Yes| D[Load Tasks]
        D --> E{Task Filter?}
        E -->|--tasks| F[Filter by IDs]
        E -->|--complexity| G[Filter by Level]
        E -->|None| H[All 30 Tasks]
        F --> I[Task Queue]
        G --> I
        H --> I
    end

    subgraph TaskLoop["🔄 For Each Task"]
        I --> J[Load Task JSON]
        J --> K[Build Prompt]
        K --> L[Set iteration = 1]
    end

    subgraph IterationLoop["🔁 Iteration Loop (max 10)"]
        L --> M[Call OpenRouter API]
        M --> N{API Success?}
        N -->|No| O[Log Error]
        O --> P{iteration < 10?}
        P -->|Yes| Q[iteration++]
        Q --> M
        P -->|No| R[❌ Mark FAILED]

        N -->|Yes| S[Extract DAX from Response]
        S --> T[Parse Measure Name + Expression]
    end

    subgraph Validation["✅ Power BI Validation"]
        T --> U[Create Measure in _Measures]
        U --> V{Syntax Valid?}
        V -->|No| W[Capture Syntax Error]
        W --> X[Generate Feedback]
        X --> Y{iteration < 10?}
        Y -->|Yes| Z[Add to Conversation]
        Z --> Q
        Y -->|No| R

        V -->|Yes| AA[Execute: EVALUATE ROW]
        AA --> AB{Execution<br/>Success?}
        AB -->|No| AC[Capture Exec Error]
        AC --> AD[Delete Failed Measure]
        AD --> X

        AB -->|Yes| AE[✅ Mark SOLVED]
    end

    subgraph Recording["📝 Record Results"]
        AE --> AF[Rename Measure to Final Name]
        AF --> AG[Record Iteration Data]
        R --> AG
        AG --> AH[Write Log File .md]
        AH --> AI[Write JSON Results]
        AI --> AJ{More Tasks?}
        AJ -->|Yes| J
        AJ -->|No| AK[Generate Summary Report]
    end

    subgraph Output["📊 Output"]
        AK --> AL[Per-Task Logs]
        AK --> AM[Summary Report]
        AK --> AN[JSON Results]
        AL --> AO[Done ✅]
        AM --> AO
        AN --> AO
    end

    style A fill:#e1f5fe
    style AE fill:#c8e6c9
    style R fill:#ffcdd2
    style C fill:#ffcdd2
    style AO fill:#c8e6c9
```

## Validation Decision Tree

```mermaid
flowchart LR
    subgraph Input["Model Output"]
        A[Generated DAX]
    end

    subgraph Parse["Parse"]
        A --> B{Can Parse<br/>Name = Expr?}
        B -->|No| C[❌ Parse Error]
        B -->|Yes| D[Measure Name<br/>Expression]
    end

    subgraph CreateMeasure["Create in Power BI"]
        D --> E[manage_measure<br/>operation: create]
        E --> F{Success?}
        F -->|No| G[❌ Syntax Error]
        F -->|Yes| H[Measure Created]
    end

    subgraph Execute["Execute"]
        H --> I[run_dax<br/>EVALUATE ROW]
        I --> J{Returns<br/>Value?}
        J -->|No| K[❌ Execution Error]
        J -->|Yes| L[✅ VALID]
    end

    subgraph Feedback["On Failure"]
        C --> M[Generate Feedback]
        G --> M
        K --> M
        M --> N[Next Iteration]
    end

    style L fill:#c8e6c9
    style C fill:#ffcdd2
    style G fill:#ffcdd2
    style K fill:#ffcdd2
```

## Iteration Feedback Flow

```mermaid
sequenceDiagram
    participant U as User/Task
    participant O as OpenRouter
    participant M as Model (LLM)
    participant P as Power BI

    U->>O: Task prompt + context
    O->>M: Generate DAX
    M->>O: DAX Response
    O->>U: DAX code

    U->>P: Create measure

    alt Syntax Error
        P-->>U: ❌ Error message
        U->>O: Feedback: "Syntax error: {msg}"
        O->>M: Fix the syntax
        M->>O: Corrected DAX
        Note over U,P: Retry validation...
    else Execution Error
        P-->>U: ✅ Created
        U->>P: Execute measure
        P-->>U: ❌ Execution failed
        U->>O: Feedback: "Execution error: {msg}"
        O->>M: Fix the logic
        M->>O: Corrected DAX
        Note over U,P: Retry validation...
    else Success
        P-->>U: ✅ Created
        U->>P: Execute measure
        P-->>U: ✅ Result: {value}
        U->>U: Record SOLVED
    end
```

## Component Architecture

```mermaid
graph TB
    subgraph Claude["Claude Code"]
        CC[Claude Code CLI]
        MCP[MCP Tools]
    end

    subgraph Python["Python Scripts"]
        BM[benchmark_mcp.py]
        V4[run_benchmark_v4.py]
    end

    subgraph External["External Services"]
        OR[OpenRouter API]
        PBI[Power BI Desktop]
    end

    subgraph Storage["Storage"]
        Tasks[tasks/*.json]
        Runs[runs/*.md]
        Measures[_Measures Table]
    end

    CC --> MCP
    MCP --> PBI

    V4 --> BM
    BM --> OR
    BM --> Tasks
    BM --> Runs

    CC --> BM
    MCP --> Measures

    style CC fill:#e3f2fd
    style PBI fill:#fff3e0
    style OR fill:#f3e5f5
```

## Key Files

| File | Purpose |
|------|---------|
| `run_benchmark_v4.py` | CLI entry point with task selection |
| `benchmark_mcp.py` | Core functions for MCP integration |
| `tasks/{level}/task-XXX.json` | Task definitions |
| `runs/YYYY-MM-DD_*_v4.md` | Individual task logs |
| `runs/YYYY-MM-DD_SUMMARY_*_v4.md` | Benchmark summary |

## Validation Guarantees

1. **Syntax Validity**: If measure creation succeeds, DAX syntax is valid
2. **Execution Validity**: If EVALUATE ROW returns a value, the measure executes
3. **No False Positives**: Pattern matching removed - only real execution counts
4. **Iteration Learning**: Models get specific error feedback to improve
