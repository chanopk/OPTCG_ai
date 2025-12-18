# Implementation Plan - Phase 2: Langfuse Observability Setup (Tracing)

แผนการติดตั้งระบบ **Langfuse** เพื่อทำ Tracing และ Monitoring ให้กับ OPTCG AI Service ตาม Phase 2

## 1. Goal Description (เป้าหมาย)
เราต้องการติดตั้ง "กล้องวงจรปิด" (Tracing) ให้กับระบบ AI Agent ของเรา เพื่อ:
1.  **Debug:** เห็นภาพว่า Agent เดินไป Node ไหนบ้าง ส่ง Prompt หน้าตาเป็นยังไง และได้รับ Tool Output อะไรกลับมา (สำคัญมากสำหรับ LangGraph)
2.  **Monitor:** ดูความเร็ว (Latency) และค่าใช้จ่าย (Token Cost) ของแต่ละ Request
3.  **Optimize:** หาจุดคอขวดของระบบ

## 2. Infrastructure Options (ทางเลือกในการติดตั้ง)
เนื่องจากคุณมี Docker แล้ว เรามี 2 ทางเลือก:

### Option A: Langfuse Cloud (Selected)
*   **วิธีทำ:** สมัคร account ที่ `cloud.langfuse.com` -> เอา API Key มาใส่ `.env`
*   **ข้อดี:** ง่ายที่สุด ไม่กิน resource เครื่อง, มี Free Tier 50k traces/month เพียงพอสำหรับการ dev
*   **ข้อเสีย:** ข้อมูลวิ่งออกไป server นอก (แต่เป็น encrypted)

### Option B: Self-Hosted via Docker (Alternative)
*   **วิธีทำ:** เพิ่ม Service `langfuse-server` และ `postgres` ลงใน `docker-compose.yml`
*   **ข้อดี:** ข้อมูลอยู่ในเครื่องเรา 100%, ไม่จำกัดจำนวน traces
*   **ข้อเสีย:** Setup ยากกว่า, กิน Ram เพิ่มประมาณ 2-4GB (หนัก Database)

**Status:** Selected **Option A**.

## 3. Implementation Steps (ขั้นตอนการทำ)

### Step 1: Dependencies
ติดตั้ง Library ที่จำเป็น
```bash
uv add langfuse
```

### Step 2: Configuration (.env)
เพิ่ม Variable เหล่านี้ใน `.env`
```env
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_HOST="https://cloud.langfuse.com"
```

### Step 3: Code Integration (LangGraph & Callback)
เราจะไปเชื่อมต่อ Langfuse เข้ากับ LangGraph:
1.  **`app/api/routers/chat.py`**:
    *   Inject `LangfuseCallbackHandler`.
    *   ดึง `trace_id` จาก Handler เพื่อส่งกลับให้ User.
    *   ดึง `observation` หรือ `usage` data (ถ้ามี).

### Step 4: Enhanced API Response (Execution Metadata)
*Concept: **"Execution Metadata"** (Execution Trace Exposure)*
เราจะปรับ API Spec ของ `/api/chat` ให้ส่งข้อมูลกลับมามากขึ้น เพื่อให้ Frontend หรือ User รู้ว่าเกิดอะไรขึ้นเบื้องหลัง:

```json
{
  "response": "คำตอบสุดท้าย...",
  "metadata": {
    "trace_id": "ab-cd-12-34",       // เอาไว้เปิดดู Log เต็มๆ ใน Langfuse (Public Link / Deep Link)
    "total_tokens": 150,             // จำนวน Token ที่ใช้
    "cost_usd": 0.0004,              // ค่าใช้จ่าย
    "execution_time": 1.25,          // เวลาที่ใช้ (วินาที)
    "steps": [                       // (Optional) กระบวนการคิด
      {"agent": "Router", "action": "search_cards"},
      {"agent": "Knowledge", "action": "generate_answer"}
    ]
  }
}
```
*   **Trace ID:** สำคัญที่สุด ทำให้ Client สามารถสร้าง Link ไปที่ Langfuse Public Trace ได้ถ้าต้องการ
*   **Steps:** ดึงจาก LangGraph State History (`messages`)

### Step 5: Agent Architecture Research & Selection (Phase 2.5)
*Goal: เลือกโครงสร้างสมอง AI ที่ฉลาดและเหมาะสมกับเกมที่สุด*
เราจะทำการทดลองและเลือก Architecture จากแผนผัง:
1.  **Common Architectures:** Test RAG vs ReAct vs CoT.
2.  **Advanced Patterns:** พิจารณา Planner Executor หรือ Tree-of-Thought ถ้า Logic เกมซับซ้อนมาก.
3.  **Outcome:** อัปเดต `graph.py` ตาม Architecture ที่เลือก (ปัจจุบันเราใช้ Router+Tools ซึ่งคล้าย ReAct/Router).

### Step 6: Streaming API Implementation (Phase 2.5)
*Goal: ลด Latency และแสดงความคิดของ AI แบบ Real-time*
เราจะสร้าง Endpoint ใหม่ `/api/chat/stream` ที่ส่งข้อมูลแบบ **Server-Sent Events (SSE)**:

#### 1. API Endpoint (`FastAPI`):
*   Return `StreamingResponse` with `media_type="text/event-stream"`.

#### 2. Event Generator Logic:
*   ใช้ `graph.astream_events(inputs, version="v1")` เพื่อดักจับทุกอย่างที่เกิดขึ้นใน Graph.
*   **Filter & Format Events:**
    *   `on_chat_model_stream` -> ส่ง **Token** (ตัวหนังสือ).
    *   `on_tool_start` -> ส่ง **Thought** ("กำลังค้นหา...", "กำลังอ่านกติกา...").
    *   `on_chain_end` -> ส่ง **Metadata** (Trace ID, Token Usage) ตอนจบ.

#### 3. Client Output Example (SSE Format):
```text
data: {"type": "thought", "content": "Checking capabilities..."}

data: {"type": "thought", "content": "Searching for: 'Luffy'"}

data: {"type": "token", "content": "Luc"}

data: {"type": "token", "content": "ky"}

data: {"type": "token", "content": " Roo"}
```

## 4. Expected Outcome (ผลลัพธ์ที่จะได้)

เมื่อทำเสร็จแล้ว สิ่งที่คุณจะเห็นใน Langfuse Dashboard คือ:

1.  **Trace View:** เห็น Flow เป็นกิ่งก้านสาขา
    *   User Query -> Guardrails -> Router Agent -> Tool Call (ChromaDB) -> Tool Output -> Generator Agent -> Final Response
2.  **Input/Output Inspection:** กดเข้าไปดูได้เลยว่า Step นี้ Prompt ที่ส่งหา LLM หน้าตาเป็นยังไง (ช่วยเรื่อง Prompt Engineering มาก)
3.  **Cost:** บอกเลยว่า 1 คำถามนี้เสียเงินกี่บาท ($0.00xxx)
4.  **Error Tracking:** ถ้า Error ตรงไหน กราฟจะแดงและบอกจุดที่พังทันที

## 5. Verification
1.  **Test Call:** ยิง Request ไปที่ `/api/chat`.
2.  **Check Response:** ต้องได้ JSON ที่มี field `metadata` พร้อม `trace_id`.
3.  **Check Dashboard:** นำ `trace_id` ไปค้นใน Langfuse ต้องเจอ Log.
