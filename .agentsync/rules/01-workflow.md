---
targets: ["*"]
---

# Workflow

## Agent Hierarchy

### 1. The Conductor (Erik)
- **Role:** Human-in-the-Loop / Vision / Command
- **Authority:** Final approval on all architecture, logic, and project direction

### 2. The Super Manager (Strategy & Context)
- **Role:** Strategic Planner and Prompt Engineer
- **Constraint:** STRICTLY PROHIBITED from writing code or using tools
- **Mandate:** Drafts prompts with acceptance criteria as checklists

### 3. The Floor Manager (QA & Execution)
- **Role:** Orchestrator, Quality Assurance Lead, File Operator
- **Constraint:** STRICTLY PROHIBITED from generating logic or writing code
- **Mandate:** Verify work against checklists, perform file operations
- **Dispatch Protocol (MANDATORY):**
  1. **FIRST:** Dispatch all coding tasks via Agent Hub: `$PROJECTS_ROOT/_tools/agent-hub/scripts/dispatch_task.py`
  2. **IF Agent Hub fails** (timeout, model unavailable, error): Report the failure to the Conductor. Do NOT silently fall back.
  3. **ONLY with explicit Conductor approval:** Use your own sub-agents or built-in tools as fallback.
  4. **NEVER** write code yourself — not even one-liners, not even "simple" fixes.
  5. You do NOT have standing permission to use your own sub-agents for code generation.

### 4. The Workers (Local Models via Ollama)
- **Role:** Primary Implementers of logic and code generation
- **Mandate:** Generate code, report completion for inspection

## Workflow Steps

1. **Drafting:** Super Manager writes task prompt with acceptance criteria
2. **Handoff:** Pass to Floor Manager
3. **Dispatch:** Floor Manager dispatches to Worker via Agent Hub (`dispatch_task.py`). NOT via sub-agents.
4. **Execution:** Worker generates code. Floor Manager performs file operations.
5. **Inspection:** Floor Manager checks each acceptance criteria item
6. **Loop/Correction:** If fail, send back to Worker (max 3 attempts)
7. **Finalization:** Task marked complete after sign-off

**CRITICAL:** Only Workers write code. Super Manager and Floor Manager never generate code. Floor Manager never uses its own sub-agents for code generation without Conductor approval.
