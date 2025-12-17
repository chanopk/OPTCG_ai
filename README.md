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
    *   [x] สร้าง Git Repository.
*   **Data Ingestion Pipeline**:
    *   [x] พัฒนา Script (`fetch_group_id.py`, `fetch_cards.py`) สำหรับดึงข้อมูลจาก TCGPlayer API.
    *   [x] ระบบ Filter แยกเฉพาะ Card Product และบันทึกเป็น JSON แยกตาม Group ID (Series).
    *   [x] **Data Cleaning**: เพิ่ม step Deduplication กรองการ์ดซ้ำ (Number เดียวกัน) ก่อนนำเข้า DB.
    *   [x] **Multi-Model Embeddings**: รองรับการสลับใช้ `Google Gemini` หรือ `Local HuggingFace` ได้ผ่าน config.
    *   [ ] optimize เพิ่มเติม
    *   [x] มีข้อมูล Raw Data พร้อมสำหรับการทำ Indexing ลง Vector DB.
    *   [x] **Knowledge Base Automation**: สร้าง `check_for_updates.py` เพื่อจัดการ Pipeline (Fetch -> Install -> Index) อัตโนมัติ.
    *   [x] **Hybrid Search System**:
        *   Setup **ChromaDB** พร้อม **Gemini Embeddings**.
        *   สร้าง **Search Engine** ที่รองรับทั้ง Semantic (ความหมาย) และ Structured Filter (สี, Cost, Type).
        *   มี Tool `query_cards.py` สำหรับทดสอบระบบค้นหา.
    *   [x] **Rule Search System**:
        *   เพิ่ม Vector Store สำหรับกฎกติกา (`rules_v1`).
        *   Implement `retrieve_rules` สำหรับค้นหาข้อมูลกฎ.
        *   **Configurable Provider**: สามารถเลือกใช้ Model ได้ตามต้องการ
    *   [x] **Easy-to-Use Tools**: `query_cards.py` สำหรับทดสอบ และ API Endpoint สำหรับ Agent.
    *   [x] **AI Agent Development**:
        *   [x] **LangGraph Agent**:
            *   สร้าง Basic Knowledge Agent ที่รองรับ Multi-tool (Card Search + Rule Search).
            *   เปลี่ยน Embedding Model เป็น `text-embedding-004` เพื่อความแม่นยำสูงสุด.

## Embedding Configuration
สามารถเปลี่ยน Embedding Model ได้ที่ไฟล์ `.env`:
```env
# ใช้ Google Gemini API (ต้องมี Quota)
EMBEDDING_PROVIDER=google_genai
GOOGLE_API_KEY=your_key

# หรือใช้ Local Model (Off-line, ไม่จำกัด Quota)
EMBEDDING_PROVIDER=huggingface
```
ระบบจะแยก Database ให้อัตโนมัติ (`chroma_db_gemini` หรือ `chroma_db_huggingface`) หากเปลี่ยน Provider ต้องทำการ Re-index ข้อมูลใหม่ 1 ครั้งด้วยคำสั่ง `uv run data/embed_loader.py`

---

### 🚀 Future Plans (สิ่งที่จะทำต่อ)

แผนการพัฒนาขั้นต่อไป (เรียงตามลำดับความสำคัญ):

1.  **AI Agent Development (Next Step)**:
    *   [x] พัฒนา **LangGraph** Agent เบื้องต้นที่สามารถใช้ Search Tool ตอบคำถามได้.
    *   [x] สร้าง FastAPI Endpoint (`/api/chat`) สำหรับเชื่อมต่อกับ Frontend หรือ Client อื่นๆ.

2.  **Game Engine (Phase 2)**:
    *   [ ] ออกแบบ Class Design (Game, Player, Card) ในภาษา Python.
    *   [ ] เริ่มเขียน Game Loop พื้นฐาน (Draw, Don!! Phase, Main Phase).

4.  **Simulation & Meta Agent (Phase 3-4)**:
    *   [ ] เชื่อมต่อ Data Deck List.
    *   [ ] ทำระบบ Simulation เพื่อ Run เกมจำนวนมากและเก็บสถิติ.

---

### 🛠 Technology Stack
*   **Language**: Python 3.10+
*   **Frameworks**: FastAPI, LangChain / LangGraph
*   **Database**: ChromaDB (Vector)
    *   *Note:* Data Pipeline includes a **Cleaning & Deduplication** step to filter unique card numbers.
*   **Tools**: `uv` (Package Manager)
