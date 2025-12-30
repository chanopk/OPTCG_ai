# Project Specification: OPTCG AI Service

เอกสารนี้ระบุรายละเอียดทางเทคนิคและแผนการพัฒนาสำหรับโปรเจค OPTCG AI Service ซึ่งเป็น AI Agent สำหรับวิเคราะห์และให้ข้อมูลเกี่ยวกับ One Piece Card Game

## 1. Project Overview (ภาพรวมโครงการ)
**Goal:** สร้าง AI Service ที่สามารถตอบคำถาม, วิเคราะห์ข้อมูล Deck, และจำลองสถานการณ์การเล่น (Simulation) ของ One Piece Card Game ได้ โดยใช้เทคโนโลยี AI Agent
**Purpose:** เพื่อเป็นโปรเจคศึกษา (Educational Project) ด้านการพัฒนา AI Agent, Multi-Agent Systems และการนำ LLM มาประยุกต์ใช้ในการวิเคราะห์เกม

## 2. Requirements (ความต้องการระบบ)

### Functional Requirements
1.  **Card Knowledge Analysis:** เข้าใจข้อมูลการ์ด Model, Effect, Trigger และ Attribute ต่างๆ
2.  **Rule Understanding:** เข้าใจกติกาพื้นฐานและ Flow ของเกม (Implemented via **Direct Context Injection** of Official Rules)
3.  **Deck & Meta Analysis:**
    *   วิเคราะห์ Deck list
    *   ดูสถิติการใช้งาน (Meta trends)
    *   แนะนำ card (การ์ดแก้ทาง)
4.  **Simulation:** จำลองการต่อสู้ (Battle) ระหว่าง Deck เพื่อหา Win Rate
5.  **Competitive Gameplay AI:** (Highlight) สร้าง AI ที่สามารถเล่นเกมได้จริง มีการตัดสินใจที่ถูกต้อง (Decision Making) เพื่อเอาชนะคู่ต่อสู้ได้ ไม่ใช่แค่สุ่มเล่น

### Agent Services Breakdown
เพื่อให้รองรับ Requirements ข้างต้น และง่ายต่อการขยายระบบ (Microservices capable) เราจะแบ่ง AI Agents ออกเป็น 3 ตัวหลัก ที่สามารถทำงานแยกกันได้ (Separate FastAPI Services):

1.  **Card Knowledge Agent** (รับผิดชอบ Reqs ข้อ 1, 2)
    *   **หน้าที่:** ผู้เชี่ยวชาญด้านข้อมูลการ์ดและกติกา
    *   **Core Capabilities:** RAG, Vector Search, Rule Interpretation
    *   **Input:** คำถามเกี่ยวกับ Text, Effect, Q&A
    
2.  **Deck & Meta Agent** (รับผิดชอบ Reqs ข้อ 3)
    *   **หน้าที่:** นักวิเคราะห์ข้อมูล Comunity และ Meta Game
    *   **Core Capabilities:** Data Analytics, Statistics Query, Trend Analysis
    *   **Input:** Deck Lists, Win Rate Query, "แก้ทาง Deck นี้ยังไง"

3.  **Gameplay & Simulation Agent** (รับผิดชอบ Reqs ข้อ 4, 5)
    *   **หน้าที่:** ผู้เล่นมือโปร (Pro Player AI)
    *   **Core Capabilities:** Game State Management, Decision Making, Minimax/Search Algorithms
    *   **Input:** Game State ปัจจุบัน, Action ที่ต้องการตัดสินใจ


### Non-Functional Requirements
1.  **Modularity:** แยกส่วนประกอบชัดเจน (API, Agent, Engine, Data) เพื่อการดูแลรักษา
2.  **Extensibility:** รองรับฟีเจอร์ AIOps (Evaluation, Tracing) ในอนาคต
3.  **Observability:** มีระบบ Tracing/Logging เพื่อตรวจสอบกระบวนการคิดของ Agent (Langfuse)
4.  **Reliability:** มี Guardrails ป้องกันการทำผิดกติกา (Illegal Moves)
5.  **Simplicity:** โค้ดเข้าใจง่าย ไม่ซับซ้อนจนเกินไป เหมาะแก่การเรียนรู้

## 3. Technology Stack

*   **Language:** Python 3.10+
*   **Web Framework:** FastAPI (สำหรับสร้าง REST API)
*   **AI Framework:** LangChain / LangGraph (สำหรับทำ Agentic Workflow)
*   **LLM Model:** Google Gemini (ผ่าน Google AI Studio)
*   **Data Source:** JSON Data จาก API `https://tcgcsv.com/tcgplayer/68/{Group ID}/products`
    *   ดึงทุก Group ID แล้วกรองเฉพาะสินค้าที่เป็น **Card**
    *   เก็บแยกไฟล์ JSON ตาม Group ID
*   **Search Strategy:** **Hybrid Search** (สำคัญมาก)
    *   **Vector Search (Semantic):** ใช้ ChromaDB/FAISS สำหรับคำถามเชิงความหมาย
    *   **Structured Search (Exact):** ใช้ SQL/JSON Filtering สำหรับ Stat (Power, Cost, Type, Color)
*   **Vector Database:** ChromaDB (สำหรับ Cards Knowledge Base)
*   **Context Injection:** Comprehensive Rules (สำหรับ Rule Knowledge)
*   **Testing:** Pytest

## 4. System Architecture (สถาปัตยกรรมระบบ)

ระบบจะออกแบบเป็น **Modular Architecture**

```mermaid
graph TD
    User[Clients] --> API[FastAPI Service]
    API --> AgentOrchestrator[LangGraph Orchestrator]
    
    subgraph "Agent Layer"
        AgentOrchestrator --> RouterAgent[Router Node]
        RouterAgent --> KB_Agent[Knowledge Agent (with Rules Context)]
        RouterAgent --> Meta_Agent[Meta/Stats Agent]
        RouterAgent --> Sim_Agent[Simulation Agent]
    end
    
    subgraph "Capabilities / Tools"
        KB_Agent --> |Hybrid Retrieve| SearchModule{Search Engine}
        SearchModule --> |Semantic| VectorDB[(Cards Vector DB)]
        SearchModule --> |Filter| JSON_DB[(Raw Card Data)]
        Meta_Agent --> |Query| StatsDB[(Deck Stats DB)]
        Sim_Agent --> |Run| GameEngine[Game Logic Engine]
    end
    
    subgraph "Data Layer"
        Sources[External Sources] --> |ETL Pipeline| VectorDB
        Sources --> |ETL Pipeline| StatsDB
    end
```

### Module Breakdown
1.  **`app/`**: เก็บ FastAPI related files (main, routers, schemas).
2.  **`agents/`**: เก็บ Code ของ LangGraph nodes, edges และ prompts.
    *   *Knowledge Agent*: เชี่ยวชาญเรื่อง Text ของการ์ด
    *   *Stats Agent*: เชี่ยวชาญเรื่องตัวเลขและ Meta
3.  **`engine/`**: (สำคัญ) Python pure logic ที่จำลองกติกาเกม OPTCG สำหรับใช้ใน Simulation.
4.  **`data/`**: ศูนย์กลางข้อมูล
    *   **`scripts/`**: Utility Scripts (`fetch`, `clean`, `embed`, `query`).
    *   **`chroma_db_gemini/`**: Vector DB (Google GenAI).
    *   **`clean_json/`**: ข้อมูลการ์ดที่ผ่านการ Clean.
5.  **`core/`**: Config, Logger, Utilities.

### Data Retrieval Strategy (Hybrid Search)
เพื่อความแม่นยำ 100% ในบริบทของ Card Game เราจะไม่พึ่งพา Vector Search เพียงอย่างเดียว แต่จะใช้ระบบ Hybrid:
1.  **Retrieve IDs:** ใช้ Vector Search หา ID ของการ์ดที่เกี่ยวข้องจากบริบทคำถาม
2.  **Fetch Data:** ใช้ ID ดึงข้อมูลดิบ (Raw JSON) เพื่อให้ได้ค่า Text และ Stat ที่ถูกต้องแน่นอน
3.  **Generate:** ให้ AI ตอบคำถามจากข้อมูลดิบนั้น

## 5. Development Phases (แผนการพัฒนา)

แบ่งออกเป็น 4 Phase ใหญ่ๆ เพื่อให้เห็นผลลัพธ์ทีละขั้น

### Phase 1: Foundation & Knowledge Base (ระบบพื้นฐานและคลังความรู้)
*Focus: ทำให้ AI "รู้จัก" การ์ด One Piece ด้วยระบบ Hybrid Search*
*   [x] **Project Setup:** สร้าง Git, Setup `uv` และ Folder Structure
*   [x] **Data Ingestion Pipeline (Refactored):**
    *   **Architecture:** เก็บ Script ทั้งหมดไว้ที่ `data/scripts/` เพื่อความสะอาด
    *   **Workflow:**
        1.  `fetch_group_id.py`: เช็ค Set ใหม่จาก API
        2.  `fetch_cards.py`: โหลด Raw JSON
        3.  `clean_data.py`: **Data Cleaning** แปลงข้อมูลให้ Flat, Clean และกรอง Deduplication (By Card ID)
        4.  `embed_loader.py`: Index ข้อมูลที่ Clean แล้วลง Vector DB
    *   **Automation:** ใช้ `check_for_updates.py` จัดการ Flow ทั้งหมดอัตโนมัติ
*   [x] **Hybrid Search System:**
    *   **Vector Database:**
        *   แยก Folder ชัดเจนตาม Provider: `data/chroma_db_gemini` และ `data/chroma_db_huggingface`
        *   รองรับการสลับ Model ผ่าน Config (`.env`)
    *   **Search Service:**
        *   รองรับ **Dynamic k** (AI ปรับจำนวนผลลัพธ์ได้เอง)
        *   แสดงผลพร้อม **Clean ID** (e.g., OP01-001)
*   [x] **Basic Knowledge Agent:** สร้าง LangGraph Agent ที่ใช้ Search Tool ตอบคำถามได้
*   [x] **Rule Injection Strategy:** เปลี่ยนจาก RAG เป็นการ Inject `comprehensive_rules.txt` เข้า Context โดยตรงเพื่อความแม่นยำสูงสุด
*   [x] **API:** สร้าง Endpoint `POST /api/chat` ด้วย FastAPI

### Phase 1.5: Containerization (Deployment Ready)
*Focus: เตรียม Environment สำหรับนำ API ไปทดสอบบน Host จริง*
*   [x] **Dockerization:**
    *   สร้าง `Dockerfile` สำหรับ Build Image ของ Service Application
    *   สร้าง `docker-compose.yml` เพื่อทดสอบการรัน Service.
*   [x] **DevOps:**
    *   จัดการ Environment Variables (`.env`) สำหรับ Production.

### Phase 2: Infrastructure & Quality Assurance Foundation
*Focus: ปูพื้นฐานระบบตรวจสอบ (Observability) และความปลอดภัย (Guardrails) ก่อนเริ่มงานยาก*
*   [x] **Observability Setup:**
    *   Setup **Langfuse** Project.
    *   เชื่อมต่อ Tracing เข้ากับ Agent ที่มีอยู่ (Knowledge Agent).
*   [x] **Guardrails Setup (Comprehensive):**
    *   **Layer 1: Input Guards** (Topic Relevance, PII Redaction, Injection Prevention).
    *   **Layer 2: Output Guards** (Toxicity Check, JSON Structure Validation).
    *   **Middleware Architecture:** Refactored Guardrails into LangGraph Nodes (`input_guard`, `output_guard`) for better integration.
*   [x] **Execution Metadata:** เพิ่ม response (trace_id, token usage, cost) เพื่อให้ Client รู้สถานะการทำงาน.


### Phase 2.1: Guardrails POC (Azure vs Local)
*Focus: เปรียบเทียบและทดสอบระบบความปลอดภัยด้วย Azure AI Foundry*
*   [x] **Design & Config:**
    *   เพิ่ม Config `GUARDRAILS_PROVIDER` (Azure/Local) ใน `.env`.
    *   Refactor `guardrails.py` ให้รองรับ Strategy Pattern (Provider Interface).
*   [x] **Azure Integration:**
    *   Implement `AzureGuardrailsProvider` โดยใช้ Azure AI Foundry SDK.
    *   ตรวจสอบ Input (Content Safety).
*   [x] **LangGraph Integration:**
    *   ใช้ Conditional Routes เพื่อเลือก Guardrails Node ที่ถูกต้อง.
*   *   **Comparison Report & Docs:**
        *   สร้าง `docs/azure_setup_guide.md` สอนวิธีสมัคร.
        *   เปรียบเทียบผลลัพธ์ใน `guardrails_comparison.md`.

### Phase 2.2: Thai Language Support & Localization
*Focus: ปรับปรุงประสบการณ์ผู้ใช้ชาวไทยและการจัดการข้อผิดพลาด*
*   [x] **Thai Language Enforcement:**
    *   **Agent Persona:** เพิ่ม System Prompt ให้ Knowledge Agent ตอบเป็นภาษาไทยเสมอ (ยกเว้นศัพท์เทคนิค).
*   [x] **Guardrails Localization:**
    *   **Translation:** แปลข้อความแจ้งเตือนความปลอดภัยของทั้ง Local และ Azure Provider เป็นภาษาไทย.
*   [x] **API UX Improvements:**
    *   **Graceful Error Handling:** ปรับ API ให้คืนค่า `200 OK` พร้อมข้อความแจ้งเตือนจาก Guardrails แทนการโยน `HTTP 400 Error` เพื่อให้ Frontend แสดงผลเป็นข้อความแชทได้ทันที.

### Phase 2.5: POC Agent Architecture & Real-time Streaming & UX (Better Experience) (Optional)

*Focus: ลดความรู้สึกรอนานของผู้ใช้ และแสดงกระบวนการคิดของ AI*
*   [ ] **Agent Architecture Implementation & Selection:**
    *   ศึกษาและเลือก Architecture ที่เหมาะสมที่สุดจากภาพ:
    *   **Common Architectures:** RAG Agent, ReAct (Reason + Act), Chain of Thought (CoT).
    *   **Other Patterns:** Planner Executor, DAG Agents, Tree-of-Thought.
*   [ ] **Streaming API Endpoint (`/api/chat/stream`):**
    *   สร้าง Endpoint ใหม่ที่รองรับ **Server-Sent Events (SSE)**.
    *   ไม่ลบอันเก่า แต่เพิ่มทางเลือกให้ Frontend.
*   [ ] **Thought Process Exposure:**
    *   Stream **"Thinking Events"** (e.g., "Searching Card: Luffy...", "Reading Rules...").
    *   Stream **"Token Generation"** (ตัวหนังสือค่อยๆ พิมพ์ออกมา).
*   [ ] **LangGraph Streaming:** Implement `.astream_events()` เพื่อจับ Event ภายใน Graph.

### Phase 3: Game Engine Implementation (Completed)
*Focus: สร้างระบบเกม (สนามเด็กเล่น) ให้สมบูรณ์*
*   [x] **Core Models:** Designed `Game`, `Player`, `Card`, `CardInstance`, `Field`.
*   [x] **Basic Game Loop:** Implemented Phases (Refresh, Draw, Don, Main, End).
*   [x] **Action System:** Implemented `PlayCard`, `Attack`, `EndPhase` Actions.

### Phase 3.5: Advanced Game Logic (Completed)
*Focus: เพิ่มความลึกของเกม (Effects & Battle Steps)*
*   [x] **Advanced Battle System:**
    *   **State Machine:** Transitioning between `ATTACK` -> `BLOCK` -> `COUNTER` -> `DAMAGE` steps.
    *   **Mechanics:** Implemented `Blocker` interception and `Counter` power buffs.
    *   **Life System:** Correctly handling Life damage and game winning condition.
*   [x] **Effect System Architecture:**
    *   **Effect Parser:** Robust regex-based parser handling:
        *   **Keywords:** `Rush`, `Banish`, `Double Attack`, `Blocker`.
        *   **Actions:** `Draw`, `Trash`, `Return to Hand` (Bounce), `Return to Bottom Deck`, `KO`, `Buff`.
        *   **Costs:** `Don!! -X`, `Don!! xX`.
    *   **Effect Manager:** Resolving `ON_PLAY` effects and modifying game state (Hand, Field, Power, Cost).

### Phase 4: Basic AI & Simulation (Validation)
*Focus: เชื่อมต่อ AI ให้เล่นจนจบเกมได้*
*   [x] เชื่อมต่อ Agent เข้ากับ Game Engine (Implemented `BaseGameAgent`).
*   [x] สร้าง **Random Agent** เพื่อทดสอบ Loop (Completed).
*   [x] สร้าง **Rule-Based Agent (SimpleRuleAgent)** เพื่อทดสอบความฉลาดเบื้องต้น (Heuristic: Play Max Cost, Attack Leader).
*   [x] ตรวจสอบผลการเล่นผ่าน Simulation Script (`scripts/simulation_runner.py`).

### Phase 5: Competitive AI (The Goal) (Completed)
*Focus: สร้าง AI ที่เล่นเพื่อชัยชนะ*
*   [x] **Strategy Agent (Chopper):** Implemented Greedy Algorithm with 1-turn Lookahead Simulation.
    *   **Simulation Thinking:** AI clones the game state and "plays out" actions to see real outcomes (Life damage, Board control).
    *   **Battle Simulation:** Solved "Horizon Effect" by fast-forwarding battles (assuming no counters) to value attacks correctly.
*   [x] **Evaluator Brain:** Implemented Scoring Function:
    *   **Win Condition:** Priority #1 (Score: Infinity).
    *   **Life Lead:** Priority #2.
    *   **Hand Advantage & Board Power:** Secondary heuristics.
*   [x] **Validation:** Validated via `scripts/simulation_runner.py` - Strategy Agent consistently defeats Random Agent (Turn 1/2 KO observed).
*   [x] **Critical Bug Fix:** Fixed shared state memory leak in Player model enabling independent simulations.

### Phase 6: Tournament Mode (Paused)
*Focus: ระบบแข่งขันจริงและการจำลองแมตช์ (พักการพัฒนาชั่วคราว)*

**Status:** Functional but incomplete data/logic coverage.

**Accomplished:**
*   [x] **Tournament Runner:** `scripts/tournament_runner.py` capable of running N games between two deck JSONs.
*   [x] **Deck Loader:** Utility to load decks from JSON and instantiate Card objects.
*   [x] **DON!! System:** Implemented Turn-based Don accumulation (+2/turn), Cost checks, and Active/Rested state.
*   [x] **Game Loop:** Full turn structure (Draw -> Main -> Attack/Play -> End) working for basic interactions.
*   [x] **Strategy Agent:** Can make heuristic-based decisions (Win > Life > Board).

**Pending / Known Limitations:**
1.  **Complex Effects:** The current regex parser handles basic effects (Draw, KO) well, but complex conditional triggers (e.g., "If you have 3 characters, do X") are not fully implemented.
2.  **Missing Card Data:** Database lacks full coverage for sets OP11-OP14, requiring manual entry (`cards_manual.json`) or mocks.
3.  **Battle Steps:** Counter step logic is simplified; specific Counter Event cards are not yet fully playable.
4.  **UI/Visualization:** No visual representation, only text logs (`parse_game_log.py`).

### Phase 7: Meta Analysis (Optional/Future)
*Focus: วิเคราะห์สถิติ*
*   [ ] ระบบแนะนำ Deck.

## 6. Implementation Plan: Starting Point (จุดเริ่มต้น)

สิ่งแรกที่จะเริ่มทำคือ **Phase 1: Foundation & Knowledge Base**

1.  **Project Init:**
    *   Create Git Repository
    *   **uv** + `venv` Setup (Fast Python Package Installer)
2.  **Data Ingestion:**
    *   Download `cards.json`
    *   Process & Embed data to VectorDB.
3.  **LangGraph Setup:**
    *   Simple Graph: Input -> Retrieve -> Generate -> Output.
4.  **API:**
    *   POST `/chat` endpoint.

---
*Note: เป้าหมายสูงสุดของโปรเจคคือการสร้าง "Winning AI" ที่เล่นเกมได้จริง ดังนั้นการพัฒนา Game Engine ให้สมบูรณ์จึงเป็นหัวใจสำคัญ*
