### 🧠 NAX Research Skill — Specification

This defines a **Research Skill module for NAX (NetAlertX)** focused on safe, structured analysis before any implementation work.

---

## 1. Purpose

Ensure all work begins with **documentation-first understanding**, **PRD validation**, and **conflict detection**, before any planning or coding.

---

## 2. Core Workflow

### Step 1 — Documentation First

* Always begin by reading relevant repository documentation.

* Priority order:

  1. `/CONTRIBUTING.md`
  2. `/README.md`
  3. `/.github/skills/code-standards/SKILL.md`
  4. `/.github/skills/database-patterns/SKILL.md` — read when the feature touches the `Devices` table or requires audit/history logging
  5. `/docs/**`
  6. Related module/code context if referenced

* Extract:

  * Architecture expectations
  * Coding standards
  * Plugin or module conventions
  * Existing workflows or constraints

---

### Step 2 — PRD Check

* If a PRD (Product Requirements Document) is NOT provided:

  * Explicitly request it before proceeding further
  * Do not assume requirements

* If PRD is provided:

  * Parse and restate key requirements internally
  * Identify scope boundaries

---

### Step 3 — Clarification Gate

If anything is unclear:

* Stop immediately
* Ask targeted clarifying questions
* Do NOT propose solutions yet

---

### Step 4 — Codebase Cross-Check

* Compare PRD + documentation against existing codebase

* Identify:

  * Conflicting behavior
  * Outdated patterns
  * Duplicate logic
  * Breaking assumptions
  * Plugin or API mismatches

* **If the feature writes to the `Devices` table:**

  * Load `/.github/skills/database-patterns/SKILL.md`
  * Audit all write paths listed there — confirm which are affected
  * Determine if a SQLite trigger or Python hook is the right approach
  * Check if `*Source` fields already solve attribution requirements

* Clearly report inconsistencies before proceeding

---

### Step 5 — Planning Requirement (Strict)

Before any implementation:

* Produce a structured plan including:

  * Approach overview
  * Files/modules affected
  * Dependencies
  * Risk areas
  * Migration considerations (if any)

* Explicitly label:

  > “WAITING FOR USER CONFIRMATION”

---

### Step 6 — Implementation Gate (Hard Rule)

* Do NOT start implementation until user explicitly confirms the plan
* No partial coding, no early patches, no assumptions

---

## 3. Behavioral Constraints

* Always prioritize correctness over speed
* Never skip PRD validation
* Never proceed past ambiguity
* Never implement without approval
* Always surface contradictions in source material
* Always prefer asking questions over guessing

---

## 4. Output Style Rules

* Be structured and technical
* Avoid unnecessary verbosity
* Separate:

  * Findings
  * Risks
  * Questions
  * Plan
* No hidden assumptions

---

## 5. Summary Flow

```
Docs → PRD → Clarify → Codebase Check → Plan → User Approval → Implement
```

