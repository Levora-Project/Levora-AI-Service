# Levora AI Service — Python Core Service

The **Python Core Service** is an asynchronous backend service in the Levora platform responsible for automated web scraping, data cleaning, normalization, deduplication, AI-driven opportunity matching, and contextual assistant operations.

---

## 1. Architecture & Interaction Model

Following the Levora High-Level Technical Decisions (v2.0):
* **Source Management & Scheduling:** The Main Service (Node.js) manages source configurations and schedules scraping runs by dispatching source IDs to `POST /api/v1/scrape/run`.
* **Technical Source Metadata:** The Python Service reads detailed scraping configurations (endpoints, pagination, field mappings) from its own database (`sources` table).
* **Asynchronous Processing:** Scrape requests execute in the background and respond immediately with `202 Accepted` and a unique `batch_id`.
* **Completion Notification:** Upon completion of a scraping batch, the Python Service dispatches an HTTP Webhook (`ScrapeCompletePayload`) to the Main Service.
* **Direct Read (SSOT Data Access):** The Main Service directly reads cleaned opportunities (`cleaned_opportunities`) and match results (`match_scores`) via a dedicated read-only PostgreSQL user.

```mermaid
sequenceDiagram
    autonumber
    actor Scheduler as Main Service (Node.js)
    participant API as Python API (FastAPI)
    participant Scraper as Scraper Service & Workers
    participant DB as Python DB (PostgreSQL)
    
    Scheduler->>API: POST /api/v1/scrape/run (source_ids, X-API-Key)
    API-->>Scheduler: 202 Accepted (batch_id)
    API->>Scraper: Execute batch in background
    Scraper->>DB: Fetch source configs (SourceRepository)
    Scraper->>Scraper: Scrape -> Clean -> Normalize -> Deduplicate
    Scraper->>DB: Save raw and cleaned opportunities (OpportunityRepository)
    Scraper->>Scheduler: POST Webhook (batch_id, total_opportunities)
    Scheduler->>DB: SELECT * FROM cleaned_opportunities (Direct Read)
```

---

## 2. Authentication

All private endpoints are secured via **API Key Authentication**.

* **Header Name:** `X-API-Key`
* **Key Storage:** Keys are stored as SHA-256 hashes in the `api_keys` table. The raw key is never stored in plaintext.
* **Key Validation:** Evaluates key presence, active status (`is_active: true`), and expiration (`expires_at > NOW()`). Updates `last_used_at` upon successful verification.

### Generating API Keys
Use the provided CLI script to generate a cryptographically secure key:
```bash
poetry run python scripts/generate_api_key.py "Main Service Production"
```
Output:
```text
API key created.
  name: Main Service Production
  id:   d290f1ee-6c54-4b01-90e6-d701748f0851

  key:  lv_V_7WjL0pQm3xK...

Store this key now. It cannot be recovered later.
```

---

## 3. API Endpoints Reference

### 3.1 Health Check Probe
Checks service liveness and active database connectivity.

* **URL:** `/health`
* **Method:** `GET`
* **Auth Required:** No
* **Responses:**
  * `200 OK`: Database connected and operational.
    ```json
    {
      "status": "ok",
      "database": "connected"
    }
    ```
  * `503 Service Unavailable`: Database query failed.
    ```json
    {
      "status": "degraded",
      "database": "unavailable"
    }
    ```

---

### 3.2 Trigger Scrape Run
Triggers an asynchronous scraping job for specified source IDs.

* **URL:** `/api/v1/scrape/run`
* **Method:** `POST`
* **Auth Required:** Yes (`X-API-Key`)
* **Headers:**
  ```http
  Content-Type: application/json
  X-API-Key: <YOUR_API_KEY>
  ```
* **Request Body:**
  ```json
  {
    "source_ids": [
      "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
      "b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22"
    ]
  }
  ```
* **Responses:**
  * `202 Accepted`:
    ```json
    {
      "batch_id": "9f3f9661-8208-4122-a9b8-d2188ff6e4cb",
      "status": "accepted",
      "source_count": 2,
      "message": "Scraping started; a webhook will be sent on completion."
    }
    ```
  * `400 Bad Request`: Validation error (e.g., empty `source_ids` list).
  * `401 Unauthorized`: Missing or invalid API key.

---

### 3.3 Internal Webhook Receiver (Testing & Simulation)
Receives scrape completion notifications (used for internal verification and Main Service mock).

* **URL:** `/api/v1/webhook/scrape-complete`
* **Method:** `POST`
* **Auth Required:** Yes (`X-API-Key`)
* **Request Body:**
  ```json
  {
    "batch_id": "9f3f9661-8208-4122-a9b8-d2188ff6e4cb",
    "total_opportunities": 42,
    "succeeded_sources": ["almin7"],
    "failed_sources": [],
    "completed_at": "2026-09-01T15:30:00Z"
  }
  ```
* **Response:** `200 OK` (`{"status": "received", "batch_id": "..."}`)

---

## 4. Webhook Notification (Python Service → Main Service)

When a batch scrape completes, the Python Service dispatches a webhook to the Main Service URL specified in `MAIN_SERVICE_WEBHOOK_URL`.

### Webhook Headers
```http
Content-Type: application/json
X-Webhook-Secret: <MAIN_SERVICE_WEBHOOK_SECRET>
```

### Webhook Payload Schema
```json
{
  "batch_id": "9f3f9661-8208-4122-a9b8-d2188ff6e4cb",
  "total_opportunities": 42,
  "succeeded_sources": [
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
  ],
  "failed_sources": [],
  "completed_at": "2026-09-01T15:30:00.000Z"
}
```

### Resilience & Retry Policy
* Uses `BaseHttpClient` with `RetryStrategy` (up to 4 attempts with exponential backoff).
* Webhook transmission failures are logged but **do not** fail the scraping execution or database transactions.

---

## 5. Main Service Database Read-Only Access

The Main Service reads opportunities directly from the Python database using a restricted PostgreSQL role.

### Provisioning the Read-Only User
Run the setup script against your PostgreSQL instance:
```bash
psql -U postgres -d levora_python -f scripts/create_readonly_user.sql
```

### SQL Permission Grants (`scripts/create_readonly_user.sql`)
```sql
CREATE ROLE levora_main_service WITH LOGIN PASSWORD 'CHANGE_ME_STRONG_PASSWORD';

GRANT CONNECT ON DATABASE postgres TO levora_main_service;
GRANT USAGE ON SCHEMA public TO levora_main_service;

-- Read-only permissions on clean opportunities and match scores
GRANT SELECT ON TABLE public.cleaned_opportunities TO levora_main_service;
GRANT SELECT ON TABLE public.match_scores TO levora_main_service;

-- Explicitly revoke access to internal tables
REVOKE ALL ON TABLE public.sources FROM levora_main_service;
REVOKE ALL ON TABLE public.raw_opportunities FROM levora_main_service;
REVOKE ALL ON TABLE public.api_keys FROM levora_main_service;

ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM levora_main_service;
```

---

## 6. Local Setup and Development

### Prerequisites
* Python 3.12+
* Poetry
* PostgreSQL 15+

### Installation & Configuration
1. Clone the repository and install dependencies:
   ```bash
   poetry install
   ```
2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your DATABASE_URL and configurations
   ```
3. Generate the Prisma Client:
   ```bash
   poetry run prisma generate
   ```
4. Run database migrations:
   ```bash
   poetry run prisma migrate dev
   ```

### Running the Application
```bash
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

### Running Tests and Linting
* **Run test suite:**
  ```bash
  poetry run pytest -v
  ```
* **Run coverage analysis:**
  ```bash
  poetry run pytest --cov=src --cov-report=term-missing
  ```
* **Run linting & formatting checks:**
  ```bash
  poetry run ruff check .
  poetry run black --check .
  poetry run mypy src
  ```
