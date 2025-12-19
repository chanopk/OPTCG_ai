# วิธีสร้าง Key สำหรับ Azure AI Content Safety

ใช่ครับ **Azure AI Foundry** เป็นชื่อแพลตฟอร์มรวม (Unified Platform) ซึ่งบริการที่เราใช้จริงๆ ชื่อว่า **"Azure AI Content Safety"** ครับ

## ขั้นตอนการสร้าง Key (ทีละ Step)

1.  **เข้า Azure Portal**
    *   ไปที่ [https://portal.azure.com](https://portal.azure.com) และ Log in

2.  **ค้นหาบริการ**
    *   ในช่อง Search ด้านบนสุด พิมพ์คำว่า `Content Safety`
    *   เลือกบริการที่ชื่อ **"Content Safety"** (ไอคอนรูปโล่)

3.  **สร้าง Resource (+ Create)**
    *   กดปุ่ม **Create** หรือ **+ Create content safety**
    *   **Subscription:** เลือก Subscription ของคุณ (ต้องมีสถานะ Active)
    *   **Resource Group:** เลือกที่มีอยู่ หรือกด Create new (ตั้งชื่ออะไรก็ได้ เช่น `optcg-rg`)
    *   **Region:** เลือก **"East US"** (แนะนำอันนี้เพราะมี Free Tier และฟีเจอร์ครบที่สุด)
    *   **Name:** ตั้งชื่อ Resource (เช่น `optcg-guardrails`)
    *   **Pricing tier:** เลือก **Free (F0)** ถ้ามี หรือ **Standard (S0)**

4.  **เอา Key มาใช้** แ
    *   เมื่อสร้างเสร็จ ระบบจะบอกว่า "Deployment Succeeded" ให้กด **Go to resource**
    *   มองหาเมนูฝั่งซ้ายชื่อ **"Keys and Endpoint"** (รูปกุญแจ)
    *   Copy ค่า:
        *   **Key 1** (หรือ Key 2 ก็ได้)
        *   **Endpoint** (เช่น `https://optcg-guardrails.cognitiveservices.azure.com/`)

5.  **ใส่ในโปรเจค**
    *   เปิดไฟล์ `.env`
    *   วางค่าลงไป:
        ```env
        GUARDRAILS_PROVIDER="AZURE"
        AZURE_CONTENT_SAFETY_ENDPOINT="<วาง Endpoint ที่นี่>"
        AZURE_CONTENT_SAFETY_KEY="<วาง Key ที่นี่>"
        ```
