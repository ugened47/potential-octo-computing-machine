# Claude Code Setup Guide for AI Video Editor

This guide explains the Claude Code development environment setup for efficient development of the AI Video Editor project.

## Table of Contents

- [Overview](#overview)
- [Slash Commands](#slash-commands)
- [Skills](#skills)
- [Task Tracking](#task-tracking)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

Your development environment now includes:

### 📁 Directory Structure

```
.claude/
├── CLAUDE.md              # Main development guide (project instructions)
├── SETUP-GUIDE.md         # This file
├── TASKS.md               # Project task tracking
├── commands/              # Slash commands (8 commands)
│   ├── api.md            # Create FastAPI endpoints
│   ├── component.md      # Create React components
│   ├── migration.md      # Database migrations
│   ├── test.md           # Run tests
│   ├── quality.md        # Code quality checks
│   ├── feature.md        # Full-stack feature implementation
│   ├── docker.md         # Docker operations
│   └── setup.md          # Development environment setup
└── skills/               # Claude skills (6 skills)
    ├── video-processing/
    ├── database-design/
    ├── api-design/
    ├── security-review/
    ├── frontend-architecture/
    └── performance-optimization/
```

---

## Slash Commands

Slash commands are project-specific automation commands you can invoke with `/command-name`.

### Available Commands

#### 1. `/api [endpoint-name]`
**Purpose:** Create a new FastAPI endpoint with tests

**Example:**
```
/api videos
```

**What it does:**
- Reads existing routes for patterns
- Creates service layer in `backend/app/services/`
- Creates API route in `backend/app/api/routes/`
- Generates tests in `backend/tests/`
- Runs type checking and linting

**When to use:** Creating new API endpoints for the backend

---

#### 2. `/component [component-name]`
**Purpose:** Create a new React component with Shadcn UI

**Example:**
```
/component VideoUploader
```

**What it does:**
- Checks existing component patterns
- Creates component file in appropriate directory
- Sets up TypeScript types
- Generates component tests
- Runs type checking and linting

**When to use:** Building new UI components

---

#### 3. `/migration [description]`
**Purpose:** Create database migration

**Example:**
```
/migration "Add video processing status enum"
```

**What it does:**
- Guides through database schema changes
- Updates SQLModel models
- Generates Alembic migration
- Tests migration up/down
- Updates related tests

**When to use:** Changing database schema

---

#### 4. `/test [backend|frontend|all]`
**Purpose:** Run tests for backend, frontend, or both

**Examples:**
```
/test backend
/test frontend
/test all
```

**What it does:**
- Runs pytest for backend with coverage
- Runs npm test for frontend
- Runs E2E tests (if "all")
- Reports test failures and coverage

**When to use:** Verifying code changes, before commits

---

#### 5. `/quality`
**Purpose:** Run all code quality checks

**What it does:**
- Formats code (ruff, prettier)
- Runs linters (ruff, eslint)
- Runs type checkers (mypy, tsc)
- Auto-fixes issues where possible

**When to use:** Before committing, before PRs

---

#### 6. `/feature [feature-name]`
**Purpose:** Implement a full-stack feature end-to-end

**Example:**
```
/feature "Video upload with progress tracking"
```

**What it does:**
- Creates implementation plan with TodoWrite
- Guides through: database → backend → frontend → tests
- Ensures quality standards at each step
- Follows the complete development workflow

**When to use:** Implementing features from TASKS.md

---

#### 7. `/docker [up|down|restart|logs|build|reset]`
**Purpose:** Docker operations for the project

**Examples:**
```
/docker up        # Start all services
/docker logs      # View logs
/docker reset     # Full reset (deletes data!)
```

**What it does:**
- Manages Docker Compose services
- Shows logs for debugging
- Rebuilds containers
- Resets environment

**When to use:** Development environment management

---

#### 8. `/setup`
**Purpose:** Set up complete development environment

**What it does:**
- Checks prerequisites
- Creates .env file
- Installs dependencies
- Sets up database
- Runs initial migrations
- Verifies installation

**When to use:** First-time setup, onboarding new developers

---

## Skills

Skills are specialized AI agents that activate automatically based on the task context. You can also explicitly invoke them.

### Available Skills

#### 1. `video-processing`
**Triggers:** Working with video files, FFmpeg, PyAV, video slicing, silence removal, scene detection

**Expertise:**
- FFmpeg command optimization
- PyAV usage patterns
- Video codec selection
- Audio processing strategies
- Performance optimization for video

**Allowed Tools:** Read, Grep, Glob, WebFetch (read-only for research)

**Use cases:**
- Implementing video processing features
- Optimizing encoding parameters
- Debugging video-related issues
- Choosing between FFmpeg and PyAV

---

#### 2. `database-design`
**Triggers:** Creating models, planning migrations, optimizing queries, database schema design

**Expertise:**
- PostgreSQL schema design
- SQLModel relationships
- Alembic migrations
- Query optimization
- Indexing strategies

**Allowed Tools:** Read, Grep, Glob

**Use cases:**
- Designing new database tables
- Creating relationships between models
- Optimizing slow queries
- Planning data migrations

---

#### 3. `api-design`
**Triggers:** Creating endpoints, reviewing API design, implementing auth

**Expertise:**
- REST API best practices
- FastAPI patterns
- Pydantic validation
- JWT authentication
- API documentation

**Allowed Tools:** Read, Grep, Glob

**Use cases:**
- Designing new API endpoints
- Implementing authentication
- Creating request/response schemas
- Following REST conventions

---

#### 4. `security-review`
**Triggers:** Implementing auth, handling user input, security-critical code

**Expertise:**
- OWASP Top 10 vulnerabilities
- Input validation
- Authentication/authorization
- SQL injection prevention
- XSS prevention

**Allowed Tools:** Read, Grep, Glob

**Use cases:**
- Reviewing code for security issues
- Implementing secure authentication
- Validating user inputs
- Preventing common vulnerabilities

---

#### 5. `frontend-architecture`
**Triggers:** Building pages, optimizing React, implementing complex UI, using Shadcn UI

**Expertise:**
- Next.js 14 App Router
- Server vs Client Components
- React performance optimization
- Shadcn UI patterns
- State management

**Allowed Tools:** Read, Grep, Glob, WebFetch

**Use cases:**
- Structuring Next.js apps
- Optimizing React performance
- Implementing complex UI features
- Using Shadcn UI effectively

---

#### 6. `performance-optimization`
**Triggers:** Investigating slow endpoints, optimizing queries, improving frontend render performance

**Expertise:**
- Backend async patterns
- Database optimization
- React rendering optimization
- Caching strategies
- Video processing performance

**Allowed Tools:** Read, Grep, Glob

**Use cases:**
- Finding performance bottlenecks
- Optimizing slow queries
- Reducing React re-renders
- Implementing caching

---

## Task Tracking

### TASKS.md

The `TASKS.md` file tracks all features from the PRD with implementation status.

**Status Icons:**
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Completed
- ⚪ Blocked

**Usage:**

1. **Check current status:**
   ```
   Open .claude/TASKS.md
   ```

2. **Start working on a feature:**
   ```
   /feature "Feature name from TASKS.md"
   ```

3. **Update status manually:**
   Edit TASKS.md and change the emoji

**Structure:**
- MVP Phase (MUST HAVE) - Features 1-9
- Post-MVP Phase (SHOULD HAVE) - Features 10-15
- Future Features (COULD HAVE) - Features 16-19
- Cross-Cutting Concerns (Security, Performance, etc.)

---

## Best Practices

### 1. Token Usage Optimization

**DO:**
- ✅ Use `/feature` for complex, multi-step tasks
- ✅ Reference specific files with `@filename` when you know what you need
- ✅ Use slash commands for common workflows
- ✅ Let skills activate automatically based on context

**DON'T:**
- ❌ Ask Claude to explore the entire codebase at once
- ❌ Read files unnecessarily
- ❌ Repeat information already in CLAUDE.md
- ❌ Run tools that aren't needed for the task

### 2. Development Workflow

**Standard flow for any feature:**

1. **Check TASKS.md** - Find the feature and its dependencies
2. **Read relevant code** - Understand existing patterns
3. **Use `/feature [name]`** - Let Claude guide through implementation
4. **Use TodoWrite** - Track progress on complex tasks
5. **Run `/quality`** - Before committing
6. **Run `/test all`** - Verify everything works
7. **Update TASKS.md** - Mark feature as completed

### 3. Using Skills Effectively

**Automatic activation:**
Skills activate automatically based on your query. Just describe what you need:

```
"I need to optimize the video transcription query that's taking 5 seconds"
→ database-design and performance-optimization skills activate
```

**Manual invocation:**
If a skill doesn't activate automatically, mention it explicitly:

```
"Use the security-review skill to check this authentication code"
```

### 4. Combining Tools

**Example: Implementing a new API endpoint**

```
# 1. Use the api command to scaffold
/api video-upload

# 2. Skills automatically activate:
#    - api-design (for REST patterns)
#    - security-review (for input validation)
#    - database-design (if new models needed)

# 3. Run quality checks
/quality

# 4. Run tests
/test backend
```

### 5. Project Context

**CLAUDE.md is your source of truth:**
- Development patterns
- Tech stack details
- Common commands
- Troubleshooting

**Always refer to:**
- `CLAUDE.md` for how to do things
- `PRD.md` for what to build
- `TASKS.md` for what's done/todo

---

## Troubleshooting

### Skills not activating

**Problem:** A skill isn't being used when you expect it

**Solution:**
1. Mention the skill explicitly: "Use the [skill-name] skill to..."
2. Check that your query matches the skill description
3. Verify skill files exist in `.claude/skills/[skill-name]/SKILL.md`

### Slash command not found

**Problem:** `/command` not recognized

**Solution:**
1. Check command exists: `ls .claude/commands/`
2. Verify filename matches: `/command` → `command.md`
3. Check frontmatter has valid YAML

### Task tracking out of sync

**Problem:** TASKS.md doesn't reflect current state

**Solution:**
1. Manually update status icons in TASKS.md
2. Review with team weekly
3. Update after each feature completion

### Performance issues

**Problem:** Claude taking too long or using too many tokens

**Solution:**
1. Use specific slash commands instead of general questions
2. Reference files explicitly with `@` symbol
3. Use skills for specialized tasks
4. Break large features into smaller tasks with TodoWrite

### Need to add a new command

**Create:** `.claude/commands/new-command.md`

```markdown
---
description: Brief description of what it does
argument-hint: [optional-args]
allowed-tools: Tool1, Tool2
---

Command instructions here.
Use $1, $2 for arguments.
Use $ARGUMENTS for all arguments.
```

### Need to add a new skill

**Create:** `.claude/skills/new-skill/SKILL.md`

```markdown
---
name: new-skill
description: When to use this skill (be specific with triggers)
allowed-tools: Read, Grep, Glob
---

# Skill Name

Expertise and instructions here.
```

---

## Quick Reference

### Common Workflows

**Implement a feature:**
```bash
/feature "Feature name"
# Follow the guided workflow
/quality
/test all
```

**Create an API endpoint:**
```bash
/api endpoint-name
```

**Create a React component:**
```bash
/component ComponentName
```

**Database changes:**
```bash
/migration "Description"
```

**Before committing:**
```bash
/quality
/test all
```

**Development environment:**
```bash
/docker up      # Start
/docker logs    # Debug
/docker down    # Stop
```

### Keyboard Shortcuts (in Claude Code)

- `/` - Show slash commands
- `@` - Reference files
- `Cmd/Ctrl + K` - Quick command

---

## Getting Help

1. **Check CLAUDE.md** - Development guidelines
2. **Check this file** - Setup and usage
3. **Check TASKS.md** - Feature status
4. **Ask Claude** - With specific context

**Example questions:**
- "How do I implement video transcription? Use the video-processing skill"
- "Show me how to create a new database model following project patterns"
- "What's the status of the Video Upload feature in TASKS.md?"

---

## Summary

You now have:

✅ **8 slash commands** for common workflows
✅ **6 specialized skills** for domain expertise
✅ **Comprehensive task tracking** (TASKS.md)
✅ **Best practices** for token-efficient development
✅ **This guide** for reference

**Next steps:**

1. Review CLAUDE.md for project specifics
2. Check TASKS.md to see what's ready to implement
3. Run `/setup` to initialize your development environment
4. Start with `/feature "User Authentication"` (first MVP feature)

Happy coding!
