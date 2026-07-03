# Agent Framework: Repository Structure & Development Roadmap

**Recent updates**

- Fixed several backend issues that caused test failures:
  - `agent_framework/guardrails/content_filter.py` — restored proper PII/profanity detection API
  - `agent_framework/core/layers/03_reasoning.py` — support LLMs that return (text, meta) tuples
  - `agent_framework/memory/semantic.py` — added `store_pattern` / retrieval helpers
  - `agent_framework/tools/validator.py` — added `SchemaValidator.validate_params`
  - `agent_framework/core/agent.py` — improved async event-loop handling during synchronous runs
- Created PR [fix/backend-tests-impl](https://github.com/pristley/anatomy/pull/1) with these fixes; backend tests pass locally (`pytest`: 23 passed).
 - Created PR [fix/backend-tests-impl](https://github.com/pristley/anatomy/pull/2) with these fixes; backend tests pass locally (`pytest`: agent-framework: 23 passed; backend: all tests passed).

- Branch `fix/backend-tests-impl` (this branch):
  - Migrated `Agent` and `Message` persistence to SQLAlchemy models and ensured automatic table creation for local setups.
  - Replaced several in-memory services with DB-backed flows (agents, chat persistence) with in-memory fallbacks maintained for quick dev.
  - Added `agent_framework/tools/builtin/api_call.py` hardened implementation to block private IPs and validate domains; TLS verification enforced by default.
  - Added `backend/agent_framework/memory/retrieval.py` OpenAI embeddings adapter (uses `OPENAI_API_KEY` when present) and improved `SemanticRetrieval` behavior.
  - Added `backend/api/routes/*` endpoints for agents, chat, memory and tools with optional DB integration and streaming/WebSocket support.
  - Added GitHub Actions workflow `.github/workflows/ci.yml` to run both backend test suites in separate jobs (Python 3.11/3.12 matrix).
  - Verified locally: `pytest` for both `backend` and `agent-framework/backend` test suites passed (agent-framework: 23 passed; backend: tests passed).

## 📁 Complete Folder Structure

```
agent-framework/
│
├── README.md                          # Main documentation
├── ARCHITECTURE.md                    # Architecture reference
├── ROADMAP.md                         # Development roadmap
├── LICENSE                            # MIT License
├── .gitignore
├── .env.example
├── docker-compose.yml                 # Local dev environment
├── Makefile                           # Common tasks
│
├── /backend/                          # Core agent framework
│   ├── pyproject.toml                # Python project config
│   ├── requirements.txt               # Python dependencies
│   ├── Dockerfile                     # Backend container
│   ├── .dockerignore
│   │
│   ├── /agent_framework/              # Main package
│   │   ├── __init__.py
│   │   ├── version.py
│   │   │
│   │   ├── /core/                     # Agent core (11 layers)
│   │   │   ├── __init__.py
│   │   │   ├── agent.py               # Main Agent class orchestrating layers
│   │   │   ├── types.py               # Type definitions (AgentState, AgentInput, etc)
│   │   │   ├── config.py              # Configuration management
│   │   │   │
│   │   │   ├── /layers/               # The 11 layers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── 01_input.py        # Layer 1: Input normalization
│   │   │   │   ├── 02_understanding.py # Layer 2: Perception + knowledge retrieval
│   │   │   │   ├── 03_reasoning.py    # Layer 3: Reasoning core (LLM interface)
│   │   │   │   ├── 04_planning.py     # Layer 4: Planning & decomposition
│   │   │   │   ├── 05_state.py        # Layer 5: State management
│   │   │   │   ├── 06_decision.py     # Layer 6: Decision engine
│   │   │   │   ├── 07_execution.py    # Layer 7: Execution engine
│   │   │   │   ├── 08_resilience.py   # Layer 8: Resilience & error recovery
│   │   │   │   ├── 09_evaluation.py   # Layer 9: Evaluation & optimization
│   │   │   │   ├── 10_observability.py# Layer 10: Observability & logging
│   │   │   │   └── 11_infrastructure.py# Layer 11: Cost tracking & budgets
│   │   │   │
│   │   │   └── /interfaces/
│   │   │       ├── __init__.py
│   │   │       ├── llm_interface.py   # Abstract LLM interface
│   │   │       ├── claude_client.py   # Claude-specific implementation
│   │   │       └── tool_interface.py  # Tool execution interface
│   │   │
│   │   ├── /memory/                   # Memory systems
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # Abstract memory base classes
│   │   │   ├── episodic.py            # Episodic memory (experiences)
│   │   │   ├── semantic.py            # Semantic memory (patterns, facts)
│   │   │   ├── retrieval.py           # RAG/similarity search
│   │   │   │
│   │   │   ├── /backends/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── in_memory.py       # Dev: simple dict-based
│   │   │   │   ├── sqlite.py          # SQLite for small deployments
│   │   │   │   ├── postgres.py        # PostgreSQL for production
│   │   │   │   ├── chroma.py          # Chroma vector DB
│   │   │   │   ├── pinecone.py        # Pinecone vector DB
│   │   │   │   └── weaviate.py        # Weaviate vector DB
│   │   │   │
│   │   │   └── /embeddings/
│   │   │       ├── __init__.py
│   │   │       ├── base.py            # Abstract embeddings interface
│   │   │       ├── openai.py          # OpenAI embeddings
│   │   │       ├── cohere.py          # Cohere embeddings
│   │   │       └── huggingface.py     # HuggingFace embeddings
│   │   │
│   │   ├── /tools/                    # Tool registry & execution
│   │   │   ├── __init__.py
│   │   │   ├── registry.py            # Tool registry
│   │   │   ├── executor.py            # Execution engine
│   │   │   ├── validator.py           # Schema validation
│   │   │   │
│   │   │   ├── /builtin/              # Built-in tools
│   │   │   │   ├── __init__.py
│   │   │   │   ├── web_search.py      # Search the web
│   │   │   │   ├── database.py        # Query databases
│   │   │   │   ├── file_ops.py        # File operations
│   │   │   │   ├── math_eval.py       # Math evaluation
│   │   │   │   ├── code_exec.py       # Code execution (sandboxed)
│   │   │   │   └── api_call.py        # Generic REST API calls
│   │   │   │
│   │   │   └── /examples/
│   │   │       ├── __init__.py
│   │   │       ├── inventory_api.py
│   │   │       ├── slack_integration.py
│   │   │       └── email_sender.py
│   │   │
│   │   ├── /guardrails/               # Safety & compliance
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # Abstract guardrail
│   │   │   ├── policy_enforcer.py     # Policy enforcement
│   │   │   ├── content_filter.py      # Content filtering (PII, profanity)
│   │   │   ├── bias_detector.py       # Bias detection
│   │   │   ├── cost_limiter.py        # Budget enforcement
│   │   │   └── rate_limiter.py        # Rate limiting per user
│   │   │
│   │   ├── /observability/            # Logging & monitoring
│   │   │   ├── __init__.py
│   │   │   ├── logger.py              # Structured logging
│   │   │   ├── tracer.py              # Distributed tracing
│   │   │   ├── metrics.py             # Prometheus metrics
│   │   │   └── events.py              # Event stream (for real-time updates)
│   │   │
│   │   └── /meta_agent/               # Meta-agent system
│   │       ├── __init__.py
│   │       ├── orchestrator.py        # Meta-agent orchestrator
│   │       ├── factory.py             # Agent factory (create instances)
│   │       ├── router.py              # Route requests to appropriate agent
│   │       ├── pool.py                # Agent pool & lifecycle management
│   │       └── config_store.py        # Store & load agent configs
│   │
│   ├── /api/                          # FastAPI server
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app setup
│   │   ├── middleware.py              # Auth, logging, error handling
│   │   │
│   │   ├── /routes/
│   │   │   ├── __init__.py
│   │   │   ├── agents.py              # Agent CRUD operations
│   │   │   ├── chat.py                # Chat/message endpoints
│   │   │   ├── tools.py               # Tool management
│   │   │   ├── memory.py              # Memory queries
│   │   │   ├── monitoring.py          # Observability endpoints
│   │   │   └── meta.py                # Meta-agent operations
│   │   │
│   │   └── /schemas/
│   │       ├── __init__.py
│   │       ├── agent.py               # Agent request/response schemas
│   │       ├── chat.py                # Chat schemas
│   │       └── tools.py               # Tool schemas
│   │
│   ├── /database/                     # Database models & migrations
│   │   ├── __init__.py
│   │   ├── base.py                    # SQLAlchemy base
│   │   ├── models.py                  # ORM models
│   │   ├── session.py                 # Database session management
│   │   │
│   │   └── /migrations/
│   │       ├── env.py
│   │       ├── script.py.mako
│   │       └── /versions/
│   │           └── 001_initial.py
│   │
│   ├── /tests/                        # Backend tests
│   │   ├── __init__.py
│   │   ├── conftest.py                # Pytest fixtures
│   │   ├── test_layers.py             # Unit tests for each layer
│   │   ├── test_memory.py             # Memory system tests
│   │   ├── test_tools.py              # Tool registry tests
│   │   ├── test_meta_agent.py         # Meta-agent tests
│   │   ├── test_api.py                # API endpoint tests
│   │   └── /fixtures/
│   │       ├── sample_agents.py
│   │       └── sample_tools.py
│   │
│   └── /scripts/
│       ├── __init__.py
│       ├── setup_db.py                # Initialize database
│       ├── seed_tools.py              # Seed tool registry
│       └── benchmark.py               # Performance benchmarking
│
├── /frontend/                         # React/Vue frontend
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts                 # Vite build config
│   ├── index.html
│   ├── Dockerfile
│   ├── .dockerignore
│   │
│   ├── /public/
│   │   ├── favicon.ico
│   │   └── manifest.json
│   │
│   ├── /src/
│   │   ├── index.css                  # Global styles
│   │   ├── App.tsx                    # Root component
│   │   │
│   │   ├── /pages/                    # Page-level components
│   │   │   ├── Dashboard.tsx          # Main dashboard
│   │   │   ├── AgentCreate.tsx        # Create new agent
│   │   │   ├── AgentDetail.tsx        # View single agent
│   │   │   ├── Chat.tsx               # Chat interface
│   │   │   ├── Monitoring.tsx         # Real-time monitoring
│   │   │   ├── MemoryExplorer.tsx     # Browse agent memory
│   │   │   ├── ToolsManagement.tsx    # Manage tools
│   │   │   └── Analytics.tsx          # Analytics & metrics
│   │   │
│   │   ├── /components/
│   │   │   ├── /layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── Layout.tsx
│   │   │   │
│   │   │   ├── /agent/
│   │   │   │   ├── AgentCard.tsx      # Display agent status
│   │   │   │   ├── AgentForm.tsx      # Create/edit agent
│   │   │   │   ├── AgentSelector.tsx  # Dropdown selector
│   │   │   │   └── AgentList.tsx      # List of agents
│   │   │   │
│   │   │   ├── /chat/
│   │   │   │   ├── ChatWindow.tsx     # Main chat area
│   │   │   │   ├── MessageList.tsx    # Scrollable messages
│   │   │   │   ├── InputBar.tsx       # User input
│   │   │   │   ├── Message.tsx        # Single message
│   │   │   │   └── StreamingMessage.tsx # Streaming response
│   │   │   │
│   │   │   ├── /monitoring/
│   │   │   │   ├── MetricsChart.tsx   # Real-time metrics
│   │   │   │   ├── ExecutionTimeline.tsx # Layer execution timeline
│   │   │   │   ├── ToolExecutionLog.tsx  # Tool calls log
│   │   │   │   └── StateViewer.tsx    # Current agent state
│   │   │   │
│   │   │   ├── /memory/
│   │   │   │   ├── EpisodicMemory.tsx # View past experiences
│   │   │   │   ├── SemanticMemory.tsx # View learned patterns
│   │   │   │   ├── RetrievalSearch.tsx # Search memory
│   │   │   │   └── MemoryStats.tsx    # Memory usage stats
│   │   │   │
│   │   │   ├── /tools/
│   │   │   │   ├── ToolRegistry.tsx   # View available tools
│   │   │   │   ├── ToolDetail.tsx     # Tool info & schema
│   │   │   │   ├── ToolTester.tsx     # Test tool manually
│   │   │   │   └── ToolForm.tsx       # Create/edit tool
│   │   │   │
│   │   │   └── /common/
│   │   │       ├── Button.tsx
│   │   │       ├── Input.tsx
│   │   │       ├── Select.tsx
│   │   │       ├── Modal.tsx
│   │   │       ├── Tabs.tsx
│   │   │       ├── Spinner.tsx
│   │   │       └── Badge.tsx
│   │   │
│   │   ├── /hooks/
│   │   │   ├── useAgent.ts            # Agent state management
│   │   │   ├── useChat.ts             # Chat message handling
│   │   │   ├── useWebSocket.ts        # WebSocket connection
│   │   │   ├── useMetrics.ts          # Real-time metrics
│   │   │   └── useLocalStorage.ts     # Persistent storage
│   │   │
│   │   ├── /services/
│   │   │   ├── api.ts                 # REST API client
│   │   │   ├── websocket.ts           # WebSocket client
│   │   │   ├── agent.ts               # Agent operations
│   │   │   ├── chat.ts                # Chat operations
│   │   │   └── memory.ts              # Memory queries
│   │   │
│   │   ├── /store/                    # State management (Redux/Zustand)
│   │   │   ├── index.ts
│   │   │   ├── agentSlice.ts          # Agent state
│   │   │   ├── chatSlice.ts           # Chat messages
│   │   │   ├── monitoringSlice.ts     # Real-time monitoring
│   │   │   └── uiSlice.ts             # UI state
│   │   │
│   │   ├── /types/
│   │   │   ├── agent.ts
│   │   │   ├── chat.ts
│   │   │   ├── tools.ts
│   │   │   └── api.ts
│   │   │
│   │   └── /utils/
│   │       ├── formatters.ts
│   │       ├── validators.ts
│   │       └── helpers.ts
│   │
│   └── /tests/
│       ├── components.test.tsx
│       ├── pages.test.tsx
│       └── services.test.ts
│
├── /docs/                             # Comprehensive documentation
│   ├── README.md
│   ├── GETTING_STARTED.md             # Setup & installation
│   ├── ARCHITECTURE.md                # Architecture deep dive
│   ├── API.md                         # API reference
│   ├── /guides/
│   │   ├── building_agents.md         # How to build agents
│   │   ├── custom_tools.md            # Creating custom tools
│   │   ├── memory_management.md       # Working with memory
│   │   ├── guardrails.md              # Setting up safety
│   │   ├── deployment.md              # Production deployment
│   │   └── troubleshooting.md         # Common issues
│   └── /tutorials/
│       ├── 01_hello_world.md          # Simple hello world agent
│       ├── 02_customer_support.md     # Support bot tutorial
│       ├── 03_data_analysis.md        # Analysis agent tutorial
│       └── 04_meta_agents.md          # Meta-agent system
│
├── /examples/                         # Example agents & configs
│   ├── README.md
│   ├── /configs/
│   │   ├── support_agent.yaml         # Customer support config
│   │   ├── analyst_agent.yaml         # Data analyst config
│   │   ├── researcher_agent.yaml      # Research agent config
│   │   └── coordinator_agent.yaml     # Coordinator meta-agent
│   ├── /agents/
│   │   ├── customer_support.py
│   │   ├── data_analyst.py
│   │   ├── code_reviewer.py
│   │   └── research_agent.py
│   └── /meta_agents/
│       ├── agent_dispatcher.py        # Routes to best agent
│       ├── team_coordinator.py        # Coordinates multiple agents
│       └── learning_meta_agent.py     # Learns & improves agents
│
├── /infrastructure/                   # DevOps & deployment
│   ├── docker-compose.prod.yml
│   ├── kubernetes/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── secrets.yaml
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── /scripts/
│   │   ├── deploy.sh
│   │   ├── rollback.sh
│   │   └── health_check.sh
│   └── monitoring/
│       ├── prometheus.yml
│       ├── grafana-dashboard.json
│       └── alerts.yml
│
└── /.github/                          # GitHub configuration
    ├── workflows/
    │   ├── test.yml                   # Run tests on PR
    │   ├── build.yml                  # Build & push Docker
    │   └── deploy.yml                 # Deploy to staging
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    └── pull_request_template.md
```

---

## 📋 Development Roadmap

### Phase 1: Core Framework (Weeks 1-4)

#### Task P1.1: Project Setup
- [x] Initialize repository structure (verified)
- [x] Set up Python package with pyproject.toml (verified)
- [x] Configure logging & basic infrastructure (logger module and docker-compose present)
- [x] Create git workflows for CI/CD (GitHub Actions workflows present)

**Deliverable:** Runnable skeleton project

#### Task P1.2: Implement Core Agent Architecture (Layers 1-6)
- [x] Implement Layer 1: InputLayer class with schema validation (agent_framework/core/layers/01_input.py)
- [x] Implement Layer 2: UnderstandingLayer (perception engine, KB retrieval) (agent_framework/core/layers/02_understanding.py)
- [x] Implement Layer 3: ReasoningCore (LLM interface, streaming) (agent_framework/core/layers/03_reasoning.py)
- [x] Implement Layer 4: PlanningDecomposition (task DAG generation) (agent_framework/core/layers/04_planning.py)
- [x] Implement Layer 5: StateManager (immutable state snapshots) (agent_framework/core/layers/05_state.py)
- [x] Implement Layer 6: DecisionEngine (heuristic-based action selection) (agent_framework/core/layers/06_decision.py)

**Deliverable:** Agent can execute 1 complete cycle

**Testing:**
- Unit test for each layer
- Integration test for full cycle
- Example: simple inquiry → response

#### Task P1.3: Implement Remaining Layers (7-11)
- [x] Implement Layer 7: ExecutionEngine (tool registry + safe execution) (agent_framework/core/layers/07_execution.py)
- [x] Implement Layer 8: ResilienceLayer (retry logic, fallbacks, backoff) (agent_framework/core/layers/08_resilience.py)
- [x] Implement Layer 9: EvaluationEngine (outcome scoring, metrics) (agent_framework/core/layers/09_evaluation.py)
- [x] Implement Layer 10: ObservabilityLayer (structured logging, tracing) (agent_framework/core/layers/10_observability.py)
- [x] Implement Layer 11: InfrastructureLayer (cost tracking & budgets) (agent_framework/core/layers/11_infrastructure.py)

**Deliverable:** Complete 11-layer agent system

#### Task P1.4: FastAPI Server Setup
- [x] Create FastAPI app skeleton (backend/api/main.py)
- [ ] Set up basic middleware (auth, logging, error handling)
- [ ] Implement health check endpoint
- [ ] Configure CORS & security headers

 - [x] Set up basic middleware (auth, logging, error handling)
 - [x] Implement health check endpoint
 - [x] Configure CORS & security headers

**Deliverable:** Running API server on localhost:8000

**Estimated Time:** 4 weeks  
**Team:** 2 backend engineers

---

### Phase 2: Memory & Tools (Weeks 5-7)

#### Task P2.1: Memory System Implementation
- [x] Abstract base classes (base.py present in agent_framework/memory)
- [x] In-memory backend (agent_framework/memory/backends/in_memory.py)
- [x] SQLite backend (agent_framework/memory/backends/sqlite.py)
- [x] Embedding generation (OpenAI embedding helper present in agent_framework/memory/embeddings/openai.py)
- [ ] Retrieval/RAG (similarity search not implemented / retrieval.py missing)

 - [x] Retrieval/RAG (similarity search implemented in `memory/retrieval.py`; OpenAI adapter present)

**Deliverable:** Agents can store and retrieve experiences

**Tests:**
- Store episodic experience, retrieve with similarity
- Semantic patterns are correctly indexed
- Memory size limits enforced

#### Task P2.2: Tool Registry & Execution
- [x] Tool definition schema / basic validator (agent_framework/tools/validator.py)
- [x] Tool registry (agent_framework/tools/registry.py)
- [x] Execution sandbox / executor (agent_framework/tools/executor.py)
- [x] Schema validation (validator present, basic implementation)
- [x] Implemented built-in tools (partial):
  - [x] Web search (agent_framework/tools/builtin/web_search.py)
  - [x] Database query (agent_framework/tools/builtin/database.py)
  - [x] File operations (agent_framework/tools/builtin/file_ops.py)
  - [x] Math evaluation (agent_framework/tools/builtin/math_eval.py)
  - [ ] API calls (generic) (not present)

   - [x] API calls (generic) implemented and hardened (`tools/builtin/api_call.py`)

**Deliverable:** Agent can call tools safely with validation

**Tests:**
- Tool registration and retrieval
- Parameter validation
- Execution with timeout handling
- Error capture

#### Task P2.3: API Endpoints (Agents, Chat, Tools)
- [ ] POST /agents - Create agent
- [x] GET /agents - List agents (backend/api/routes/agents.py)
- [ ] GET /agents/{id} - Get agent details
- [ ] DELETE /agents/{id} - Delete agent
- [ ] POST /agents/{id}/messages - Send message
- [ ] GET /agents/{id}/memory - Query memory
- [ ] GET /tools - List available tools
- [ ] POST /tools - Create custom tool

 - [x] POST /agents - Create agent
 - [x] GET /agents - List agents (backend/api/routes/agents.py)
 - [x] GET /agents/{id} - Get agent details
 - [x] DELETE /agents/{id} - Delete agent
 - [x] POST /agents/{id}/messages - Send message (chat endpoints persist to DB when available)
 - [x] GET /agents/{id}/memory - Query memory (basic retrieval wired)
 - [x] GET /tools - List available tools
 - [x] POST /tools - Create custom tool

**Deliverable:** Full CRUD API for agents

**Estimated Time:** 3 weeks  
**Team:** 1-2 backend engineers

---

### Phase 3: Safety & Observability (Weeks 8-9)

#### Task P3.1: Guardrails Implementation
- [x] Policy enforcer (agent_framework/guardrails/policy_enforcer.py)
- [x] Content filter (agent_framework/guardrails/content_filter.py)
- [ ] Bias detector (not implemented)
- [ ] Cost limiter (not implemented)
- [ ] Rate limiter (not implemented)

**Deliverable:** Agent respects safety constraints

**Tests:**
- Dangerous actions are blocked
- PII is redacted
- Budget exceeded → action rejected

#### Task P3.2: Observability & Monitoring
- [x] Structured logging (basic logger present at agent_framework/observability/logger.py)
- [ ] Prometheus metrics (not implemented)
- [ ] Distributed tracing (not implemented)
- [ ] Real-time event stream (WebSocket endpoint not implemented)
- [ ] Dashboard metrics endpoint (not implemented)

**Deliverable:** Full visibility into agent execution

**Tests:**
- Metrics recorded correctly
- Events streamed to clients
- Logs parseable and useful

#### Task P3.3: Database Models & Persistence
- [x] SQLAlchemy base (database/base.py present)
- [ ] SQLAlchemy models (models.py missing)
- [ ] Database migrations (Alembic not configured)
- [ ] Session management (session.py missing)
- [ ] Async query support (not configured)

 - [x] SQLAlchemy models (Agent and Message models present and persisted in `database/models.py`)
 - [x] Session management (`database/session.py` present; local `create_all` for convenience)
 - [ ] Database migrations (Alembic not configured)
 - [ ] Async query support (not configured)

**Deliverable:** Data persists across server restarts

**Estimated Time:** 2 weeks  
**Team:** 1 backend engineer

---

### Phase 4: Frontend Development (Weeks 10-13)

#### Task P4.1: React/Vue Setup & Layout
- [x] Vite project setup (scaffolded: frontend/) 
- [x] TypeScript configuration
- [ ] Component library setup (TailwindCSS or Material-UI)
- [ ] Layout components (Sidebar, Footer) (partial: Header implemented at frontend/src/components/layout/Header.tsx)
- [x] Routing (React Router wired in frontend/src/App.tsx)

**Deliverable:** Basic layout with navigation

#### Task P4.2: Core Pages & Components
- [x] Dashboard page (frontend/src/pages/Dashboard.tsx)
- [ ] Agent creation form page
- [x] Chat interface (frontend/src/pages/Chat.tsx)
- [ ] Agent detail page (not implemented)
- [ ] Responsive design for mobile

**Deliverable:** Can create agent and chat with it

**Tests:**
- Form validation works
- Chat messages display correctly
- Responsive on mobile

#### Task P4.3: Real-time Monitoring & Analytics
- [x] WebSocket client/hook (frontend/src/hooks/useWebSocket.ts)
- [x] Metrics visualization (Recharts used in frontend/src/pages/Monitoring.tsx)
- [ ] Message streaming visualization (not implemented)
- [x] Layer execution timeline (Monitoring page renders timeline)
- [x] State viewer (basic placeholder present in Monitoring page)

**Deliverable:** Real-time monitoring of agent execution

#### Task P4.4: Memory & Tools Management UIs
- [ ] Memory explorer (browse episodic, semantic memory)
- [ ] Memory search interface
- [ ] Tool registry viewer
- [ ] Tool tester (manually invoke tools)
- [ ] Tool creation form

**Deliverable:** Full UI for memory & tool management

**Estimated Time:** 4 weeks  
**Team:** 2 frontend engineers

---

### Phase 5: Meta-Agent System (Weeks 14-16)

#### Task P5.1: Agent Factory & Lifecycle Management
- [ ] AgentFactory class (spawn agent instances)
- [ ] Agent pooling (reuse agents vs create new)
- [ ] Config store (save/load agent configurations)
- [ ] Agent naming & discovery
- [ ] Shutdown/cleanup on unused agents

**Deliverable:** Can dynamically create & manage agent instances

**Example:** Create support bot, analyst bot, research bot on demand

#### Task P5.2: Meta-Agent Orchestrator
- [ ] Main orchestrator that spawns agents
- [ ] Router (route user requests to appropriate agent)
- [ ] Resource pooling (shared memory, tools, LLM budget)
- [ ] Coordination (multiple agents working together)
- [ ] Communication between agents (agent-to-agent messages)

**Deliverable:** Meta-agent can spin up specialized agents

**Example:**
```
User: "I need support and analysis"
  ↓
Meta-Agent (orchestrates)
  ├─→ Support Agent (spawned)
  ├─→ Analysis Agent (spawned)
  └─→ Coordinator Agent (synthesizes results)
```

#### Task P5.3: Meta-Agent API & Frontend
- [ ] POST /meta-agents - Create meta-agent config
- [ ] GET /meta-agents/{id}/agents - List spawned agents
- [ ] Meta-agent control dashboard (spawn, pause, terminate agents)
- [ ] Agent resource visualization (memory shared, cost per agent)
- [ ] Agent communication logs

**Deliverable:** Can visualize & control multi-agent system

**Estimated Time:** 3 weeks  
**Team:** 1 backend + 1 frontend engineer

---

### Phase 6: Testing & Documentation (Weeks 17-18)

#### Task P6.1: Comprehensive Testing
- [ ] Unit tests (>90% coverage for core layers)
- [ ] Integration tests (full agent cycles)
- [ ] API endpoint tests (all CRUD operations)
- [ ] Load testing (concurrent agents, memory under load)
- [ ] Security testing (injection, token limit enforcement)

**Deliverable:** >85% test coverage

#### Task P6.2: Documentation
- [ ] Architecture documentation (updated with implementation)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Getting started guide
- [ ] Tutorial walkthroughs (5+ example agents)
- [ ] Troubleshooting guide
- [ ] Contributing guidelines

**Deliverable:** Complete docs (docs/ folder)

#### Task P6.3: Example Agents
- [ ] Customer support agent (working example)
- [ ] Data analysis agent
- [ ] Code review agent
- [ ] Research agent (multi-step)
- [ ] Meta-agent coordinator

**Deliverable:** 5 fully functional example agents

**Estimated Time:** 2 weeks  
**Team:** 1 engineer + 1 tech writer

---

### Phase 7: Deployment & DevOps (Weeks 19-20)

#### Task P7.1: Docker & Containerization
- [ ] Dockerfile for backend (multi-stage build)
- [ ] Dockerfile for frontend
- [ ] docker-compose.yml for local development
- [ ] docker-compose.prod.yml for production

**Deliverable:** Can run `docker-compose up` and have full system

#### Task P7.2: Kubernetes Deployment
- [ ] Deployment manifests
- [ ] Service definitions
- [ ] ConfigMaps for configuration
- [ ] Secrets for API keys
- [ ] Auto-scaling configuration

**Deliverable:** Can deploy to K8s cluster

#### Task P7.3: Monitoring & Alerting
- [ ] Prometheus metrics setup
- [ ] Grafana dashboards
- [ ] Alert rules (high error rate, cost limits, etc.)
- [ ] Log aggregation (ELK or CloudWatch)

**Deliverable:** Production-ready monitoring

#### Task P7.4: Deployment Automation
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Automated testing on PR
- [ ] Build & push Docker on main
- [ ] Automated deployment to staging
- [ ] Manual approval for production

**Deliverable:** Automated deployment workflow

**Estimated Time:** 2 weeks  
**Team:** 1 DevOps engineer

---

## 🎯 Detailed Task List by Component

### Backend Core (Backend Priority)

```
Phase 1: Foundation (4 weeks)
├─ P1.1: Project Setup (2 days)
├─ P1.2: Layers 1-6 Implementation (12 days)
│  ├─ Layer 1: InputLayer
│  ├─ Layer 2: UnderstandingLayer
│  ├─ Layer 3: ReasoningCore (integrate with Claude API)
│  ├─ Layer 4: PlanningDecomposition
│  ├─ Layer 5: StateManager
│  └─ Layer 6: DecisionEngine
├─ P1.3: Layers 7-11 Implementation (8 days)
│  ├─ Layer 7: ExecutionEngine
│  ├─ Layer 8: ResilienceLayer
│  ├─ Layer 9: EvaluationEngine
│  ├─ Layer 10: ObservabilityLayer
│  └─ Layer 11: InfrastructureLayer
└─ P1.4: API Server (2 days)

Phase 2: Extended Systems (3 weeks)
├─ P2.1: Memory System (8 days)
│  ├─ Episodic Memory
│  ├─ Semantic Memory
│  ├─ Multiple backends (in-memory, SQLite, Postgres)
│  └─ Embedding + Retrieval
├─ P2.2: Tool System (5 days)
│  ├─ Tool Registry
│  ├─ 5 Built-in Tools
│  └─ Safe Execution
└─ P2.3: Agent API Endpoints (5 days)
   ├─ CRUD Agent operations
   ├─ Chat endpoints
   └─ Tool management

Phase 3: Safety (2 weeks)
├─ P3.1: Guardrails (6 days)
├─ P3.2: Observability (5 days)
└─ P3.3: Database (4 days)

Phase 5: Meta-Agent (3 weeks)
├─ P5.1: Agent Factory & Lifecycle
├─ P5.2: Meta-Orchestrator
└─ P5.3: Meta-Agent API
```

### Frontend Core (Frontend Priority)

```
Phase 4: Frontend (4 weeks)
├─ P4.1: Setup & Layout (3 days)
├─ P4.2: Core Pages (8 days)
│  ├─ Dashboard
│  ├─ Agent Creation
│  ├─ Chat Interface
│  └─ Responsive Design
├─ P4.3: Real-time Monitoring (6 days)
│  ├─ WebSocket Integration
│  ├─ Metrics Visualization
│  └─ State Viewer
└─ P4.4: Memory & Tools UI (6 days)
   ├─ Memory Explorer
   ├─ Tool Registry
   └─ Tool Tester

Phase 5 (Frontend Part): Meta-Agent UI (2 days)
├─ Agent spawning UI
├─ Resource visualization
└─ Agent communication logs
```

---

## 📊 Resource Planning

### Team Structure

| Role | Count | Responsibilities |
|------|-------|------------------|
| Backend Lead | 1 | Architecture, core layers, API design |
| Backend Engineer | 1 | Memory, tools, meta-agent system |
| Frontend Lead | 1 | UI/UX, component design, state management |
| Frontend Engineer | 1 | Pages, real-time features, monitoring UI |
| DevOps Engineer | 1 | Docker, Kubernetes, CI/CD (part-time until Phase 7) |
| Tech Writer | 0.5 | Documentation, tutorials, examples |

**Total:** ~4.5 FTE

### Timeline

- **Phase 1 (4w):** Core agent works end-to-end
- **Phase 2 (3w):** Agents can learn from experience
- **Phase 3 (2w):** Production safety & monitoring
- **Phase 4 (4w):** Beautiful UI
- **Phase 5 (3w):** Meta-agents work
- **Phase 6 (2w):** Solid testing & docs
- **Phase 7 (2w):** Production ready

**Total: 20 weeks (~5 months)**

---

## 🛠️ Tech Stack

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL (prod), SQLite (dev)
- **Vector DB:** Chroma (dev), Pinecone/Weaviate (prod)
- **Testing:** pytest, pytest-cov
- **Async:** asyncio, httpx
- **Logging:** Python logging, JSON formatter
- **Monitoring:** Prometheus, Jaeger

## ✅ Verification & Validation

- **Branch:** `fix/backend-tests-impl` pushed to origin and used for verification.
- **Pull Request:** Created PR https://github.com/pristley/anatomy/pull/2 summarizing changes.
- **Local tests:** Ran test suites locally:
  - `agent-framework/backend` tests: 23 passed
  - `backend` tests: all tests passed
- **CI:** Added `.github/workflows/ci.yml` to run backend and agent-framework tests in a Python 3.11/3.12 matrix (jobs created in PR).
- **Manual validation highlights:**
  - FastAPI app starts; middleware (request id, auth, logging) is wired.
  - Health endpoint responds on startup.
  - SQLAlchemy `Agent` and `Message` models persist data; `database/session.py` creates tables locally.
  - Memory retrieval module includes OpenAI embeddings adapter and similarity search hooks.
  - `APICallTool` hardened to block private IPs and enforce TLS by default.

If you want, I can (pick next): merge the PR, add Alembic migrations, or convert remaining in-memory components to DB-backed models and tests.

### Frontend
- **Framework:** React 18+ or Vue 3
- **Language:** TypeScript
- **Build Tool:** Vite
- **State Management:** Redux Toolkit or Zustand
- **UI Framework:** TailwindCSS or Material-UI
- **Charts:** Chart.js or Recharts
- **Testing:** Vitest, React Testing Library
- **HTTP:** Axios or fetch with interceptors

### DevOps
- **Containerization:** Docker
- **Orchestration:** Kubernetes (optional, but planned)
- **CI/CD:** GitHub Actions
- **Infrastructure:** Terraform (for cloud resources)
- **Monitoring:** Prometheus + Grafana
- **Logging:** ELK Stack or CloudWatch

---

## 🚀 Quick Start Commands

```bash
# Setup
git clone <repo>
cd agent-framework
python -m venv venv
source venv/bin/activate

# Backend
cd backend
pip install -r requirements.txt
python -m pytest                    # Run tests
python -m uvicorn api.main:app --reload  # Start dev server

# Frontend
cd frontend
npm install
npm run dev                         # Start dev server

# Full stack
docker-compose up                   # All services

# Database
alembic upgrade head                # Run migrations
python scripts/seed_tools.py        # Seed initial data
```

---

## 📈 Success Metrics

### By End of Phase 1
- ✅ Agent can process 1 complete cycle (input → output)
- ✅ All 11 layers tested individually
- ✅ API responds on localhost

### By End of Phase 4
- ✅ Team can create & chat with agents via UI
- ✅ Real-time monitoring visible
- ✅ Mobile responsive

### By End of Phase 5
- ✅ Meta-agent spawns multiple agents dynamically
- ✅ Agents share resources efficiently
- ✅ Agent-to-agent communication works

### By End of Phase 7
- ✅ Deployed to production K8s cluster
- ✅ Monitoring & alerts working
- ✅ Auto-scaling configured

---

## 🔄 Continuous Improvement (Post-MVP)

### Planned Enhancements
- [ ] Multi-agent coordination patterns
- [ ] Tool marketplace (shared custom tools)
- [ ] Plugin system (extend framework)
- [ ] Analytics dashboard (agent performance)
- [ ] Fine-tuning capability (agent adaptation)
- [ ] Streaming responses with token counting
- [ ] A/B testing framework (test agent configs)

---

## 📝 Notes

1. **Iteration is key** - Deliver working features every phase, not "90% complete"
2. **Testing early** - Don't skip tests; they accelerate later phases
3. **Document as you go** - Don't document after; it's 10x harder
4. **DevOps early** - Containers from day 1, not "we'll do it later"
5. **User feedback** - Get real users on Phase 4 delivery; adjust Phase 5 based on feedback