# OPTCG AI Service

โปรเจค **OPTCG AI Service** คือระบบ AI Agent สำหรับวิเคราะห์, ตอบคำถาม, และจำลองสถานการณ์ (Simulation) ของ **One Piece Card Game** โดยมุ่งเน้นการใช้เทคโนโลยี LLM และ Multi-Agent Systems เพื่อการเรียนรู้และพัฒนา

### 🎯 Project Scope & Specification (สรุปย่อ)

เป้าหมายหลักคือการสร้าง AI ที่ "รู้จริง" และ "เล่นเป็น" เกี่ยวกับ OPTCG:

1.  **Card Knowledge**: สามารถตอบคำถามเกี่ยวกับ Effect, Attribute และข้อมูลการ์ดได้อย่างแม่นยำ (โดยใช้ Hybrid Search: Vector + Structured Data).
2.  **Rule Understanding**: เข้าใจ Flow ของเกมและกติกาพื้นฐาน.
3.  **Simulation Engine**: มี Python Logic สำหรับจำลองการต่อสู้ (Battle Simulator) เพื่อหา Win Rate ของ Deck (ในอนาคต).
4.  **Meta Analysis**: วิเคราะห์แนวโน้ม Meta และแนะนำการจัด Deck (ในอนาคต).

---

### ✅ What has been done (สิ่งที่ทำไปแล้ว)

ปัจจุบันอยู่ในช่วง **Phase 1: Foundation & Knowledge Base**

*   **Project Initialization**:
    *   [x] Setup Project Structure และ Environment (`uv`).
    *   [x] add Git Repository.
*   **Data Ingestion Pipeline (Refactored)**:
    *   [x] **Automated Pipeline**: ใช้ `check_for_updates.py` จัดการ Flow (Fetch -> Clean -> Embed) ครบวงจร.
    *   [x] **Data Cleaning**: แปลง Raw JSON ให้เป็น Clean JSON ลดขนาดและตัด field ที่ไม่จำเป็น พร้อม Deduplication.
    *   [x] **Flexible Embeddings**: สลับใช้ `Gemini` หรือ `HuggingFace` ได้ (เก็บ Vector แยก Folder).
*   **Hybrid Search System**:
    *   [x] **Advanced Search**: ค้นหาได้ทั้ง Semantic (ความหมาย) และ Filter (สี, Cost, Type).
    *   [x] **Dynamic Context**: AI Agent สามารถปรับจำนวนผลลัพธ์ (`k`) ได้เองตามความยากของคำถาม.
*   **AI Agent Development**:
    *   [x] **LangGraph Agent:** สร้าง Knowledge Agent ที่ฉลาดขึ้น โดยใช้ Rule Injection ใส่กฎทั้งหมดลงใน Context.
    *   [x] **Rulebook Knowledge Base:** โหลด `comprehensive_rules.txt` เข้าสู่ System Prompt โดยตรงเพื่อให้ตอบคำถามได้แม่นยำที่สุด.
    *   [x] **API Endpoint**: เชื่อมต่อผ่าน FastAPI (`/api/chat`).
*   **Deployment Ready (Phase 1.5)**:
    *   [x] **Containerization**: รองรับ Docker & Docker Compose พร้อมใช้งาน.
*   **Safety & Reliability (Phase 2)**:
    *   [x] **Observability**: Setup **Langfuse** (Tracing) & Implement **Execution Metadata** response.
    *   [x] **Comprehensive Guardrails**: ระบบป้องกัน 2 ชั้น (Input/Output) ครอบคลุม PII, Injection, Toxicity และ Structure Validation (Implemented as Middleware Nodes).
    *   [x] **Azure AI Foundry POC:** Compare and implement Azure Content Safety as an alternative provider.
    *   [x] **Guardrails Dual Provider Support**: Can switch between `LOCAL` (Regex/Keyword) and `AZURE` (AI Content Safety) via `.env`.


### 🚀 Future Plans (สิ่งที่จะทำต่อ)

แผนการพัฒนาเรียงตามลำดับความจำเป็น (Logical Order):

1.  **POC Agent Architecture & Real-time Streaming (Phase 2.5)**: *Better UX*
    *   **Agent Architecture Selection**: Research and implement appropriate patterns (RAG, ReAct, CoT, etc.).
    *   สร้าง Endpoint `/api/chat/stream` (SSE).
    *   แสดง **Thought Process** และ **Streaming Tokens** (เหมือน ChatGPT).


2.  **Game Engine (Phase 3)**: *Core Logic*
    *   เริ่มเขียน Code เกม (Model/Loop).

3.  **Basic Simulation (Phase 4)**: *Validation*
    *   เอา Agent มาวิ่งใน Engine ให้จบเกมได้.

4.  **Competitive AI (Phase 5)**: *Main Goal*
    *   พัฒนาให้ AI เก่งและชนะได้.

5.  **Meta Analysis (Phase 6)**: *Optional*
    *   วิเคราะห์ Deck.


---

### 🛠 Technology Stack
*   **Language**: Python 3.10+
*   **Frameworks**: FastAPI, LangChain / LangGraph
*   **Database**: ChromaDB (Vector)
    *   *Note:* Data Pipeline includes a **Cleaning & Deduplication** step to filter unique card numbers.
*   **Tools**: `uv` (Package Manager)
    *   Virtual Environment Commands
        *   **Windows**: `.venv\Scripts\Activate.ps1` (or simply `.venv\Scripts\python.exe` to run directly)
        *   **macOS / Linux**: `source .venv/bin/activate`

### 🐳 How to Run with Docker

1.  **Environment Setup**:
    Copy `.env.example` to `.env` and fill in your API keys.
    ```bash
    cp .env.example .env
    ```

2.  **Run with Docker Compose**:
    ```bash
    docker-compose -f docker/docker-compose.yml up --build
    ```
    The API will be available at `http://localhost:8000/docs`.

3.  **Data Persistence**:
    The `data` folder is mounted as a volume, so your Vector DB and JSON data persist between restarts.
