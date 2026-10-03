# 🩺 GitHealer

> **Autonomous Code Review & Self-Healing Agent powered by Google Gemini**

[![Python 3.12](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![AI-Powered](https://img.shields.io/badge/AI-Google%20Gemini%203.8%20Flash-orange.svg)](https://ai.google.dev/)
[![Validation](https://img.shields.io/badge/Schema-Pydantic%20v2-green.svg)](https://docs.pydantic.dev/)
[![Testing](https://img.shields.io/badge/Tested%20with-Pytest-yellow.svg)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 📌 Overview

**GitHealer** is an intelligent, closed-loop AI agent designed to automate code diagnosis and bug remediation. Unlike traditional conversational assistants that require constant copy-pasting, GitHealer acts with true agency:

1. **Observes:** Programmatically executes test suites (`pytest`, `swift test`, etc.) using background subprocesses.
2. **Diagnoses:** Analyzes failing assertion traces and source code using Google Gemini 3.8 Flash, constrained by strict Pydantic schemas.
3. **Acts:** Surgically patches the broken source files on disk.
4. **Verifies:** Re-executes the test suite in a closed feedback loop (ReAct pattern) until all tests pass before proposing a Pull Request.

---

## 🏗️ Architecture & Closed-Loop Workflow

```text
       +-------------------------------+
       |   Failing Unit Test (Pytest)  |
       +---------------+---------------+
                       |
                       v
       +-------------------------------+
       |       Diagnostic Engine       | <--- Powered by Gemini 3.8 Flash
       |      (Structured Output)      |      (Strict Pydantic Schema)
       +---------------+---------------+
                       |
                       v
       +-------------------------------+
       |    Surgical Patch Engine      | <--- Directly updates source file
       +---------------+---------------+
                       |
                       v
       +-------------------------------+
       |    Subprocess Test Runner     | <--- Isolated execution
       +---------------+---------------+
                       |
             [Did All Tests Pass?]
              /                 \
           YES                   NO (Self-Healing Loop)
            /                     \
           v                       +---> Feed new failure trace to Gemini
+----------------------+                 (Up to 3 automatic healing attempts)
|   Healthy Codebase   |
| (Pull Request Ready) |
+----------------------+
```

---

## 🗺️ Project Roadmap & Development Milestones

### 📍 Phase 1: Core AI Foundations & Structured Diagnostics
- [x] **Milestone 1.1: Project Setup & SDK Integration**
  - [x] Isolated Python 3.12 virtual environment & dependency management
  - [x] Secure API key handling (`.env` + `.gitignore` with push protection)
  - [x] Verified connection to Google Gemini 3.8 Flash via official `google-genai` SDK
- [x] **Milestone 1.2: Structured Diagnostic Engine**
  - [x] Implemented Pydantic schema for type-safe bug diagnosis (`DiagnosticReport`)
  - [x] Extracted root cause, failing line numbers, severity, and remediation strategy
  - [x] Schema-enforced JSON validation to eliminate model hallucinations

### 📍 Phase 2: Closed-Loop Self-Healing Agent
- [x] **Milestone 2.1: Automated Patch Generation**
  - [x] Context-aware prompt design for surgical code patches
  - [x] Automated file reading and patch application directly on disk
- [x] **Milestone 2.2: ReAct Feedback Loop (Test-Driven Healing)**
  - [x] Programmatic execution of `pytest` test runner via Python `subprocess`
  - [x] Automatic traceback capture for assertion errors and runtime exceptions
  - [x] Closed feedback loop: re-tests patched code iteratively until all tests pass

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

---

## 🚀 Getting Started

### Prerequisites
* Python 3.12+
* A Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### Installation

1. **Clone the repository:**
   ```bash
   git clone git@github.com:SSPF20/GitHealer.git
   cd GitHealer
   ```

2. **Set up the virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and paste your GEMINI_API_KEY
   ```

5. **Run the Autonomous Self-Healing Agent:**
   ```bash
   python gitHealerAgent.py
   ```

---

## 🛠️ Tech Stack

* **Language:** Python 3.12
* **LLM Engine:** Google Gemini 3.8 Flash (`google-genai` SDK)
* **Data Validation:** Pydantic v2
* **Test Runner:** Pytest (via `subprocess`)
* **Security & Sandboxing:** Docker (Phase 3)

---

## 📄 License
This project is open-source under the MIT License.
