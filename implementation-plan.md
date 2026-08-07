## `implementation-plan.md` — mm-learning-group-1 (To Do scope only)

### 1) Scope & Source of Truth (Jira = plan authority)
This plan only includes **Jira stories currently in “To Do”** for project **mm-learning-group-1**. Every task below maps directly to one of these Jira IDs:

**Epics**
- **MLG1-16** Async Job Orchestration & Status APIs for long-running operations
- **MLG1-17** Generation Artifact History & Retrieval APIs
- **MLG1-18** API Consistency Improvements (generator_type + script output metadata)
- **MLG1-5**, **MLG1-12** Enhanced Task Metadata (Priority, Assignee, Due Date) *(duplicate epics; see note)*

**Stories**
- **MLG1-19** POST `/generate-tests/jobs` (submit async job)
- **MLG1-20** GET `/jobs/{job_id}` (poll job status)
- **MLG1-21** GET `/jobs/{job_id}/result` (fetch job result)
- **MLG1-22** GET `/artifacts/testcases|framework|testscripts` (list artifacts)
- **MLG1-23** GET `/artifacts/{type}/{artifact_id}` (download artifact)
- **MLG1-24** Honor `generator_type` in `/generate-tests` (deterministic bypasses LLM)
- **MLG1-25** Return generated script output file path from `/generate-test-scripts`
- **MLG1-13** Task Priority (High/Medium/Low with color-coding)
- **MLG1-14** Task Assignment (assign to name/email)
- **MLG1-15** Due Dates (date picker + prevent past dates)

---

### 2) Current System Observations (repo reality check)
Relevant code areas:
- FastAPI routes: `src/endpoints/automation/routes.py`
- Schemas: `src/endpoints/automation/schemas.py`
- Utilities (generation + file saving): `src/endpoints/automation/utility.py`

Notable current behaviors:
- `/generate-tests` exists and accepts `generator_type` in schema, but **route currently always attempts LLM first** and only falls back to deterministic after an exception. This conflicts with **MLG1-24**.
- `/generate-test-scripts` returns `scripts` only and **does not return output file path**, though the utility writes to `outputfolder/testscript/`. This conflicts with **MLG1-25**.
- There is **no existing** `/jobs/*` API nor `/artifacts/*` API. These will be new endpoints.

---

### 3) Dependency Map (what must come before what)
**A. API Consistency (MLG1-18) should come first**
- **MLG1-24** (honor `generator_type`) should be implemented before async jobs, so jobs behave consistently when generating tests.
- **MLG1-25** (return script output path) should be implemented early, because async job “result” should reference saved artifacts/paths cleanly.

**B. Async Jobs (MLG1-16) should come before Artifacts listing**
- **MLG1-19/20/21** define job lifecycle; artifact persistence can be implemented alongside, but listing endpoints (**MLG1-22/23**) are easiest once there’s a stable artifact naming and storage approach.

**C. UI Task Metadata epics (MLG1-5/MLG1-12) are likely separate product area**
- Repo currently appears to be backend-only FastAPI service; these stories look like **task management UI** and may be out-of-repo. They can be planned, but implementation likely requires a different codebase or confirmation of where “Task” entities live.

---

### 4) Milestones & Timeline (proposal)
Assuming 2-week milestones (adjust to team capacity):

#### Milestone 1 (Week 1): API Consistency Improvements (**MLG1-18**)
- **MLG1-24**: Make `/generate-tests` respect `generator_type`:
  - If `deterministic`: skip LLM entirely and run deterministic generator directly.
  - If `llm`: run LLM path, optionally keep fallback if desired (confirm expected behavior).
- **MLG1-25**: Update `/generate-test-scripts` response to include:
  - saved file path (and/or output directory path) for generated script file(s).

**Exit criteria**
- Swagger/OpenAPI shows consistent request/response schemas.
- Deterministic mode is deterministic (no LLM attempt).
- Script generation returns a concrete output reference usable by callers.

#### Milestone 2 (Week 2): Async Job Orchestration APIs (**MLG1-16**)
- **MLG1-19**: Implement job submission endpoint:
  - create `job_id`
  - persist job metadata (in-memory store or file-backed store; decide scope)
  - start background execution (FastAPI `BackgroundTasks` / asyncio task / threadpool; align to deployment model)
- **MLG1-20**: Implement job status polling:
  - states: `queued | running | succeeded | failed`
  - timestamps, progress message, error details if failed
- **MLG1-21**: Implement job result retrieval:
  - if succeeded: return structured result + artifact references (paths/IDs)
  - if running: 202/409-style response (define contract)
  - if failed: return error payload

**Exit criteria**
- Jobs can be submitted, polled, and retrieved without timeouts.
- Status is stable across API restarts only if persistence is implemented (explicitly documented).

#### Milestone 3 (Week 3): Artifact History & Retrieval APIs (**MLG1-17**)
- **MLG1-22**: List artifacts by type:
  - `testcases`, `framework`, `testscripts`
  - list metadata: `artifact_id`, filename, created_at, size, job_id (if applicable)
- **MLG1-23**: Download/retrieve artifact by `{type}/{artifact_id}`:
  - serve file content (likely `FileResponse`)
  - validate type + prevent path traversal

**Exit criteria**
- Artifacts can be enumerated and downloaded reliably.
- Artifact model aligns with async job results.

#### Milestone 4 (Week 4): Enhanced Task Metadata (**MLG1-5 / MLG1-12**)
Planned work only (unless this repo actually contains “Task” functionality—currently it doesn’t appear to).
- **MLG1-13**: Priority with color coding
- **MLG1-14**: Assignment (name/email)
- **MLG1-15**: Due date + prevent past dates

**Dependency / clarification needed**
- Where are “Tasks” stored and rendered? If not in this backend repo, we should either:
  1) confirm a separate UI repo, or
  2) confirm new backend Task APIs are expected (but there are no To Do Jira tickets for Task APIs in this project).

---

### 5) Per-Ticket Implementation Tasks (roadmap items)

#### **MLG1-24** — Honor generator_type in `/generate-tests`
- Update `src/endpoints/automation/routes.py` `generate_tests()`:
  - Use `request.generator_type` to choose path.
  - Define deterministic generator usage (ensure deterministic generator class exists/imported; current code references `TestCaseGenerator()` but it is not imported in shown snippet—validate in repo).
- Update docs/behavior notes (OpenAPI).

#### **MLG1-25** — Return generated script output file path from `/generate-test-scripts`
- Update `GenerateScriptResponse` in `src/endpoints/automation/schemas.py`:
  - add `output_dir` and/or `generated_file_path` field(s).
- Update route `generate_test_scripts()` to return that path from utility (`generate_test_scripts_util` returns `(scripts_raw, output_dir)`).
- Confirm how many files are generated:
  - current utility may write a combined `test_<name>_<timestamp>.py`; return that file path if available (may require utility adjustment to return exact file path).

#### **MLG1-19** — POST `/generate-tests/jobs`
- Create job store design:
  - Minimal viable: in-memory dict keyed by UUID, storing status/result/error.
  - If persistence required: file-backed JSON in `outputfolder/jobs/` (still simple).
- Add endpoint + request schema for job submission:
  - should include same payload as `/generate-tests` (api_spec, generator_type, review).
- Start background job execution and update job state transitions.

#### **MLG1-20** — GET `/jobs/{job_id}`
- Define job status response schema:
  - `job_id`, `status`, `created_at`, `updated_at`, `message`, `error` (optional)
- Implement lookup + 404 for missing job_id.

#### **MLG1-21** — GET `/jobs/{job_id}/result`
- Define result schema and behavior for each status:
  - `succeeded`: return output (test cases / file paths / artifact IDs)
  - `failed`: return failure details
  - `running/queued`: return “not ready” response contract

#### **MLG1-22** — GET `/artifacts/{type}`
- Define artifact discovery method:
  - scan `outputfolder/testcases`, `outputfolder/framework`, `outputfolder/testscript`
  - map filenames to `artifact_id` (e.g., filename as id, or hash)
- Return paginated list if needed (otherwise simple list).

#### **MLG1-23** — GET `/artifacts/{type}/{artifact_id}`
- Translate `{type}` to folder.
- Validate `artifact_id` resolves to a file inside folder.
- Return file (download or inline).

#### **MLG1-13 / MLG1-14 / MLG1-15** — Enhanced Task Metadata (UI/Product)
- **Blocked pending repo alignment**:
  - If tasks live elsewhere, implement there.
  - If tasks should be introduced here, we need additional Jira stories for Task entity + CRUD APIs; otherwise we can only document assumptions.

---

### 6) Risks / Open Questions (need confirmation)
1) **Task metadata stories (MLG1-13/14/15)**: which repository/component owns them?
2) For **MLG1-24**: should LLM mode still fallback to deterministic on failure, or strictly fail?
3) For async jobs: is **in-memory job store** acceptable, or must jobs survive restarts?
4) For artifacts: should `artifact_id` be filename, UUID, or derived hash?

---

### 7) Deliverables
- `implementation-plan.md` added to repo with the above milestones, dependencies, and ticket mapping.
