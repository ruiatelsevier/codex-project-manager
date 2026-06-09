# Codex Project Management Plugin Spec

Date: 2026-06-08

## Goal

Design a Codex plugin that borrows the useful parts of Hermes Agent's memory, skill, review, and curation ideas, but adapts them to Codex's current model:

- project-level cognition, not global personal knowledge management
- low-noise, user-confirmed capture instead of silent autonomous writes
- repo-native assets instead of a runtime-owned memory store

The plugin should help a user continuously preserve project rules, project knowledge, and project-local skills as work progresses, while keeping those assets organized over time.

## Product Position

This is a project cognition management plugin for Codex.

It is not:

- a second agent runtime
- a general workflow executor
- a replacement for Codex global memories
- a silent background writer that mutates project files without confirmation

It is:

- a capture and curation layer for project knowledge assets
- a structured review assistant for "what should be preserved from this work?"
- a bridge between thread output and durable project artifacts

## Core Principles

The design adopts four principles inspired by Hermes Agent:

1. Separate user preference from project knowledge.
2. Preserve "how to do work" as skills, not as generic notes.
3. Review at stage boundaries, not only at the very end of a project.
4. Curate preserved knowledge over time to prevent fragmentation.

These are hard design constraints, not optional heuristics.

## Scope Boundary

The plugin manages four kinds of long-lived outputs:

1. Project rules
2. Project knowledge
3. Project-local skills
4. Global personal memory candidates

The plugin only directly writes the first three. The fourth is suggestion-only.

## Information Layers

### 1. Project Rules

Destination:

- `AGENTS.md`

Examples:

- verification workflow
- repo-specific working rules
- architectural boundaries
- "do not touch" constraints
- preferred repo workflow

Rules should be short, stable, and behavior-shaping.

### 2. Project Knowledge

Destination:

- `memories/<module>/<topic>.md`

Examples:

- architecture explanations
- workflow overviews
- data flow notes
- design rationale
- common pitfalls and their causes

Knowledge is explanatory, not prescriptive.

### 3. Project-Local Skills

Destination:

- project-local Codex skills

Suggested directory:

```text
.codex/
  skills/
    <skill-name>/
      SKILL.md
```

Examples:

- how to debug the agent loop in this repo
- how to document architecture in this repo
- how to review a certain subsystem in this repo

Skills capture repeatable methods, not system facts.

### 4. Global Personal Memory Candidates

Destination:

- not written automatically

Behavior:

- plugin emits a suggestion that the user may want to save a fact to Codex global memory

Examples:

- user prefers short answers
- user prefers design-first collaboration
- user dislikes broad refactors

These never enter project memory directly.

## Directory Convention

Project knowledge is stored under:

```text
memories/
  agent-core/
    architecture.md
    workflows.md
    pitfalls.md
  tools/
    architecture.md
    workflows.md
    pitfalls.md
  gateway/
    architecture.md
    workflows.md
    pitfalls.md
```

Rules:

- top level is module-oriented
- files inside a module are topic-oriented
- initial topic set is constrained

Recommended initial topic names:

- `architecture`
- `workflows`
- `pitfalls`
- `glossary`
- `decisions`

The plugin should not invent arbitrary topic filenames in v1.

## Plugin Responsibilities

The plugin has four responsibilities:

1. Detect likely stage completion.
2. Extract durable candidate knowledge from recent work.
3. Classify each candidate into the right layer.
4. Present write suggestions and apply confirmed changes.

It also supports a second mode:

5. Review existing preserved assets and suggest cleanup or consolidation.

## Operating Modes

### Mode A: Capture Flow

Used when a work stage appears complete.

Flow:

1. Detect stage completion.
2. Ask whether to run a project review now.
3. Extract candidate assets.
4. Classify candidates.
5. Plan write locations.
6. Show structured suggestions.
7. Apply only confirmed changes.

### Mode B: Curation Flow

Used to review what already exists.

Flow:

1. Scan `AGENTS.md`.
2. Scan `memories/`.
3. Scan project-local skills.
4. Detect duplication, overlap, wrong-layer placement, or stale content.
5. Present cleanup suggestions.
6. Apply only confirmed changes.

The first release should support curation as a manual command, not an autonomous background process.

## Triggering Strategy

The plugin should be semi-automatic.

It does not review on every thread turn. It reviews when it detects a likely stage boundary.

### Strong signals

- explicit user completion language
- explicit request to summarize or wrap up

### Soft signals

- code change appears complete
- a design artifact was just created
- a review concluded with recommendations
- a module analysis reached a stable summary

Soft signals should trigger a prompt, not an automatic review run.

## User Interaction Model

### Step 1: Review Prompt

When stage completion is detected, ask:

- review now
- remind later
- skip

### Step 2: Structured Suggestions

If accepted, present grouped suggestions:

- `AGENTS.md` candidates
- `memories/` candidates
- project skill candidates
- global memory candidates

Each suggestion should include:

- type
- proposed destination
- title
- short summary
- evidence from the thread

### Step 3: Confirmation

Support:

- accept all
- accept some
- edit then accept
- reject all

No silent writes in v1.

## Internal Components

### 1. Completion Detector

Purpose:

- decide whether a stage completion prompt should appear

Outputs:

- no action
- soft suggestion
- strong suggestion

### 2. Review Extractor

Purpose:

- identify candidate long-term assets from recent work

### 3. Classification Engine

Purpose:

- classify candidates into:
  - rule
  - knowledge
  - project skill
  - global preference candidate

This component enforces the design boundary between project and personal cognition.

### 4. Memory Planner

Purpose:

- map project knowledge into:
  - module
  - topic
  - file path
  - create/append/patch action

### 5. Skill Planner

Purpose:

- decide whether a project-local skill should be created or patched
- decide whether something is only a candidate for later promotion to a personal skill

### 6. Review Presenter / Apply Layer

Purpose:

- render suggestions clearly
- capture user approval
- apply approved changes

## Data Model

### ReviewCandidate

```ts
type ReviewCandidate = {
  id: string
  kind: "rule" | "knowledge" | "project_skill" | "global_preference_candidate"
  title: string
  summary: string
  evidence: string[]
  confidence: "low" | "medium" | "high"
}
```

### MemoryPlan

```ts
type MemoryPlan = {
  module: string
  topic: string
  path: string
  action: "create" | "append" | "patch"
}
```

### SkillPlan

```ts
type SkillPlan = {
  skillName: string
  action: "create" | "patch" | "suggest-promote"
  rationale: string
}
```

No database is required in v1. The repo itself is the source of truth.

## Classification Rules

The classification engine should use simple deterministic rules before any advanced scoring.

### Rule

If the content changes how Codex should work in this repository in future, it is a rule.

Destination:

- `AGENTS.md`

### Knowledge

If the content explains how the project works, but does not prescribe behavior, it is knowledge.

Destination:

- `memories/<module>/<topic>.md`

### Project Skill

If the content is a repeatable way to perform a class of task in this repository, it is a project skill.

Destination:

- `.codex/skills/...`

### Global Preference Candidate

If the content is actually about the user's stable personal preference rather than the project, it is a global memory candidate.

Destination:

- suggestion only

## Write Policy

### `AGENTS.md`

Allowed operations:

- append to an existing section
- create a clear new section
- patch a bounded section

Disallowed in v1:

- rewriting the entire file

### `memories/`

Allowed operations:

- create missing module/topic files
- append a new section
- patch a section in an existing file

Disallowed in v1:

- free-form file sprawl
- auto-inventing arbitrary filenames

### Project Skills

Allowed operations:

- create a new project-local skill
- patch an existing project-local skill

Disallowed in v1:

- autonomous skill merging
- automatic promotion into personal skills

### Global Memory

Allowed:

- suggestion only

Disallowed:

- automatic writes

## Noise Control

The plugin must be conservative.

Rules:

1. Do not prompt when there is no durable value to preserve.
2. Do not prompt at every turn.
3. Do not repeat the same suggestion in the same thread phase.
4. Prefer under-capture to over-capture.
5. Short or ephemeral work should usually not trigger review.

## Conflict Handling

### Wrong-layer content

If explanatory knowledge is headed for `AGENTS.md`, move it to `memories/`.

If operational workflow content is headed for `memories/`, consider skill creation first.

### Existing overlapping content

If similar content already exists:

- prefer patch over duplicate append
- prefer manual user confirmation over automatic consolidation

### Skill overlap

If two skills appear overlapping:

- do not auto-merge in v1
- surface the overlap during curation

## First Release Scope

### Included

- stage completion detection
- review suggestion prompt
- candidate extraction
- candidate classification
- `AGENTS.md` write suggestions
- `memories/` write suggestions
- project-local skill create/patch suggestions
- global memory candidate suggestions
- manual curation review mode

### Excluded

- automatic background curation
- vector indexing or retrieval DB
- silent writes
- personal memory auto-write
- autonomous skill consolidation
- cross-project promotion engine
- complex ranking or scoring systems

## Recommended Delivery Phases

### Phase 1

- review trigger
- candidate classification
- `AGENTS.md` and `memories/` write path

### Phase 2

- project-local skills support
- global memory candidate suggestions

### Phase 3

- manual curation flow
- duplicate, overlap, and wrong-layer cleanup suggestions

## Success Criteria

The plugin is successful if:

- it helps preserve project knowledge without requiring constant manual note-taking
- it keeps project rules, knowledge, skills, and personal preference candidates clearly separated
- it reduces repeated re-explanation in future Codex threads
- it does not become noisy or intrusive
- it makes preserved project knowledge easier to curate than ad hoc notes

## Open Design Decision Resolved

This spec intentionally chooses:

- project-only memory management
- repo-native file storage
- semi-automatic prompting
- user-confirmed writes
- module-first memory organization
- explicit separation of rules, knowledge, skills, and personal preference candidates

Those choices keep the first version small, controllable, and aligned with Codex's current public capabilities.
