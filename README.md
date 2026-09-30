# 🩺 GitHealer

> **Autonomous Code Review & Self-Healing Agent powered by Google Gemini**

[![Python 3.12](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![AI-Powered](https://img.shields.io/badge/AI-Google%20Gemini%203.8%20Flash-orange.svg)](https://ai.google.dev/)
[![Validation](https://img.shields.io/badge/Schema-Pydantic%20v2-green.svg)](https://docs.pydantic.dev/)
[![Testing](https://img.shields.io/badge/Tested%20with-Pytest-yellow.svg)](https://docs.pytest.org/)

---

## 📌 Overview

**GitHealer** is an intelligent, closed-loop AI agent designed to automate code diagnosis and bug remediation. Instead of just acting as a conversational assistant, GitHealer:

1. **Analyzes** code diffs and failing test traces.
2. **Diagnoses** root causes using structured outputs with strict schemas.
3. **Generates targeted patches** and executes unit tests in an isolated sandbox.
4. **Self-heals** iteratively until all tests pass before proposing a Pull Request.

---

## 🏗️ Architecture & Workflow

```text
       +-----------------------+
       |   Failing Unit Test   |
       +-----------+-----------+
                   |
                   v
       +-----------------------+
       |  Diagnostic Engine    | <--- Powered by Gemini 3.8 Flash
       |  (Structured Output)  |      (Strict Pydantic Schema)
       +-----------+-----------+
                   |
                   v
       +-----------------------+
       | Patch Proposal (Diff) |
       +-----------+-----------+
                   |
                   v
       +-----------------------+
       |  Isolated Test Runner | <--- Pytest Sandbox Execution
       +-----------+-----------+
                   |
         [Tests Pass?]
          /         \
       YES           NO (Feedback Loop)
        /             \
       v               +---> Send failure trace back to Gemini
+--------------+             (Auto-healing loop, max attempts: 3)
| PR / Healing |
|  Completed   |
+--------------+
```

## 🗺️ Project Roadmap & Development Milestones

### 📍 Phase 1: Core AI Foundations & Structured Diagnostics
- [x] **Milestone 1.1: Project Setup & SDK Integration**
  - [x] Isolated Python 3.12 virtual environment & dependency management
  - [x] Secure API key handling (`.env` + `.gitignore` with push protection)
  - [x] Verified connection to Google Gemini 3.8 Flash via official `google-genai` SDK
- [ ] **Milestone 1.2: Structured Diagnostic Engine**
  - [ ] Implement Pydantic schema for type-safe bug diagnosis (`DiagnosticReport`)
  - [ ] Extract root cause, failing line numbers, severity, and remediation strategy
  - [ ] Schema-enforced JSON validation to eliminate model hallucinations

### 📍 Phase 2: Closed-Loop Self-Healing Agent
- [ ] **Milestone 2.1: Automated Patch Generation**
  - [ ] Context-aware prompt design for surgical code patches
  - [ ] File diff generation and automated patch applicator
- [ ] **Milestone 2.2: ReAct Feedback Loop (Test-Driven Healing)**
  - [ ] Programmatic execution of `pytest` test runner
  - [ ] Traceback capture for assertion errors and runtime exceptions
  - [ ] Closed feedback loop: feed test failures back to Gemini until tests pass (max 3 retries)

### 📍 Phase 3: Sandboxing & Safe Code Execution
- [ ] **Milestone 3.1: Containerized Test Sandbox**
  - [ ] Isolate patch verification inside lightweight Docker containers
  - [ ] Restrict CPU, memory, and network access to prevent unsafe code execution
  - [ ] Ephemeral container lifecycles for clean and reproducible test states

### 📍 Phase 4: GitHub Integration & Autonomous PR Bot
- [ ] **Milestone 4.1: Developer CLI Tool**
  - [ ] Build a standalone terminal CLI (`git-healer scan`, `git-healer heal`)
- [ ] **Milestone 4.2: GitHub Action & CI/CD Bot**
  - [ ] Trigger automatically on `pull_request` events or failing CI workflow runs
  - [ ] Post automated review comments explaining diagnosed root causes
  - [ ] Open automated remediation Pull Requests containing verified passing code
