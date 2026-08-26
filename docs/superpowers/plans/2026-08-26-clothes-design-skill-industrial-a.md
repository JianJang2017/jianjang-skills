# Clothes Design Skill Industrial A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden `clothes-design-skill` into a reproducible A-level pattern-maker review package without claiming direct cutting or production readiness.

**Architecture:** Keep the deterministic drafting and costing engines intact, add a concise routing/contract entrypoint, a dedicated industrial-boundary reference, and a single validation runner. Existing user changes are preserved and tests are made independent of the caller's working directory.

**Tech Stack:** Markdown skill instructions, Python 3 standard library, shell validation, JSON behavior evals.

## Global Constraints

- The output is a 1:N technical review package for a professional pattern maker, not a 1:1 production pattern.
- Do not add DXF/PLT, industrial grading, marker making, production BOM, tolerance sheets, or batch QC.
- Preserve all pre-existing uncommitted user changes.
- Unknown or inferred facts must be disclosed; critical uncertainty produces `BLOCKED` and non-critical assumptions produce `CONDITIONAL`.

---

### Task 1: Capture failing industrial-contract behavior

**Files:**
- Create: `clothes-design-skill/tests/test_industrial_contract.py`
- Inspect: `clothes-design-skill/SKILL.md`
- Inspect: `clothes-design-skill/README.md`

**Interfaces:**
- Consumes: skill and README text.
- Produces: executable contract assertions used by the final validation runner.

- [ ] **Step 1: Write failing assertions**

Add a standard-library test that checks required status words (`PASS`, `CONDITIONAL`, `BLOCKED`), the pattern-maker review boundary, required deliverable sections, and absence of statements that send 1:N drawings directly to cutting or production.

- [ ] **Step 2: Run the test to verify RED**

Run: `python3 clothes-design-skill/tests/test_industrial_contract.py`

Expected: non-zero with missing state/contract assertions and conflicting direct-production wording.

- [ ] **Step 3: Record behavioral baseline**

Run an independent evaluator against the current skill using a basic forward request, an unknown-fabric request, and an unsupported-style request. Record whether it overclaims readiness or omits assumptions/status.

### Task 2: Define the A-level delivery contract

**Files:**
- Create: `clothes-design-skill/references/industrial-delivery-contract.md`
- Modify: `clothes-design-skill/SKILL.md`
- Modify: `clothes-design-skill/README.md`

**Interfaces:**
- Consumes: existing CLI commands and the design specification.
- Produces: one routing entrypoint and one authoritative delivery contract.

- [ ] **Step 1: Add the contract reference**

Define required inputs, supported/unsupported capability matrix, `PASS`/`CONDITIONAL`/`BLOCKED` rules, delivery package sections, error/degradation behavior, and handoff wording.

- [ ] **Step 2: Refactor the skill entrypoint**

Replace duplicated long-form material with concise mode routing, input preflight, deterministic execution, delivery gate, exact command examples, and conditional links to existing references.

- [ ] **Step 3: Align README claims**

Remove direct cutting/production implications and state that the output requires pattern-maker verification and 1:1 pattern development.

- [ ] **Step 4: Run contract test to verify GREEN**

Run: `python3 clothes-design-skill/tests/test_industrial_contract.py`

Expected: all contract assertions pass.

### Task 3: Make the regression suite location-independent

**Files:**
- Modify: `clothes-design-skill/tests/test_calculate_garment.py`
- Modify: `clothes-design-skill/tests/test_regressions.py`
- Modify only if required: `clothes-design-skill/tests/test_pattern_drafting.py`

**Interfaces:**
- Consumes: scripts resolved from `Path(__file__).resolve().parents[1]`.
- Produces: tests runnable from repository root or skill directory.

- [ ] **Step 1: Reproduce root-directory failure**

Run: `python3 -m unittest discover -s clothes-design-skill/tests -p 'test_*.py'`

Expected: current tests fail because subprocess paths depend on the caller's working directory.

- [ ] **Step 2: Use absolute script paths and explicit cwd**

Resolve the skill root from each test file and invoke scripts via absolute paths, retaining all existing assertions.

- [ ] **Step 3: Verify both invocation locations**

Run from repository root and from `clothes-design-skill`; both runs must exit zero.

### Task 4: Add a dependency-free industrial validation gate

**Files:**
- Create: `clothes-design-skill/scripts/validate_skill.py`
- Create: `clothes-design-skill/tests/test_validate_skill.py`
- Modify: `clothes-design-skill/README.md`
- Modify: `clothes-design-skill/SKILL.md`

**Interfaces:**
- Produces: `python3 scripts/validate_skill.py`, returning 0 only when structural, contract, calculation, drafting, SVG, and error-path checks pass.

- [ ] **Step 1: Write a failing runner test**

Assert that the runner exists, can be called from both locations, reports named gates, and propagates a child failure as a non-zero exit.

- [ ] **Step 2: Verify RED**

Run: `python3 clothes-design-skill/tests/test_validate_skill.py`

Expected: failure because the runner does not exist.

- [ ] **Step 3: Implement the runner**

Use only Python standard library. Validate frontmatter/name/reference targets directly, then run each regression script with explicit paths and print a final count. Provide an environment-variable test hook naming one gate to fail so failure propagation is observable.

- [ ] **Step 4: Verify GREEN**

Run the runner test and the runner itself; both must exit zero without external packages.

### Task 5: Replace vague behavior evals with machine-checkable criteria

**Files:**
- Modify: `clothes-design-skill/evals/evals.json`

**Interfaces:**
- Produces: valid JSON scenarios with explicit required and forbidden outcome criteria.

- [ ] **Step 1: Add a failing eval-schema assertion to the industrial contract test**

Require each eval to have a unique id, a prompt, `required_behaviors`, and `forbidden_behaviors`; reject ellipses and approximate numeric prose as acceptance criteria.

- [ ] **Step 2: Verify RED**

Run: `python3 clothes-design-skill/tests/test_industrial_contract.py`

Expected: failure on the old eval schema.

- [ ] **Step 3: Rewrite eval cases**

Cover forward design, reverse-image uncertainty, unsupported garment, invalid size, unknown fabric, and validation failure with deterministic behavioral criteria.

- [ ] **Step 4: Verify GREEN**

Run the contract test and parse the JSON with `python3 -m json.tool`.

### Task 6: Final verification and assessment

**Files:**
- Verify all modified files.

**Interfaces:**
- Produces: evidence-backed A-level assessment and a remaining-gap list.

- [ ] **Step 1: Run the complete gate**

Run: `python3 clothes-design-skill/scripts/validate_skill.py`

Expected: every named gate passes, zero failures.

- [ ] **Step 2: Run repository hygiene checks**

Run `git diff --check` for the skill and inspect `git diff` to ensure unrelated user files were not modified by this implementation.

- [ ] **Step 3: Re-run realistic behavioral evaluation with the skill loaded**

Compare with the Task 1 baseline. Confirm correct state selection, assumption disclosure, and prohibition against direct cutting/production claims.

- [ ] **Step 4: Report verdict**

Classify each industrial A criterion as met, conditional, or unmet, and explicitly list B/C-level capabilities that remain outside scope.
