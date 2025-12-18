import re
import json
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

class GuardrailsManager:
    """
    Manager สำหรับจัดการ Guardrails รูปแบบต่างๆ ใน OPTCG AI Service
    (Educational Reference Implementation)

    คลาสนี้แสดงตัวอย่างการทำ Guardrails เพื่อควบคุมคุณภาพและความปลอดภัยของ AI:
    
    1. Input Guards (ตรวจสอบข้อมูลขาเข้า): 
       - PII Guard: ป้องกันข้อมูลส่วนตัวรั่วไหล (เช่น เบอร์โทรศัพท์)
       - Injection Guard: ป้องกันคำสั่งที่อาจเป็นอันตรายต่อระบบ (Prompt Injection)
       - Topic Guard: ป้องกันการถามนอกเรื่อง (Topic Relevance)

    2. Output Guards (ตรวจสอบข้อมูลขาออก): 
       - Quality/Toxicity Guard: ป้องกันคำตอบที่ไม่เหมาะสม
       - Structure Guard: ตรวจสอบรูปแบบข้อมูล (เช่น JSON Check)
    """

    def __init__(self):
        # ในการใช้งานจริง อาจมีการ Initialize Model หรือ Connect กับ External Service ตรงนี้
        pass

    async def validate_input(self, query: str) -> Dict[str, Any]:
        """
        รันระบบตรวจสอบ Input Guardrails ทั้งหมด
        Returns:
            dict: {
                'valid': bool,          # ผลการตรวจสอบ (True = ผ่าน, False = ไม่ผ่าน)
                'refined_query': str,   # Query ที่ถูก Clean แล้ว (เช่น ลบข้อมูลส่วนตัวออก)
                'error': Optional[str]  # ข้อความ Error กรณีไม่ผ่านการตรวจสอบ
            }
        """
        
        # ---------------------------------------------------------
        # 1. PII Guard (Redaction - การปกปิดข้อมูลส่วนตัว)
        # ---------------------------------------------------------
        # ตัวอย่างการใช้ Regex อย่างง่ายเพื่อปิดบังเบอร์โทรศัพท์
        # ในระบบจริงอาจใช้ Library เฉพาะทางเช่น Microsoft Presidio
        pii_refined_query = re.sub(r'0\d{1,2}-\d{3}-\d{4}', '<PHONE_REDACTED>', query)
        
        # ---------------------------------------------------------
        # 2. Injection Guard (Basic Keyword Block)
        # ---------------------------------------------------------
        # ตรวจจับคำสั่งที่มักถูกใช้ในการ Hack หรือ Override AI System
        forbidden_keywords = ["ignore all instructions", "format c:", "rm -rf", "drop table"]
        for keyword in forbidden_keywords:
            if keyword.lower() in pii_refined_query.lower():
                return {
                    "valid": False, 
                    "error": "Security Alert: พบความพยายามป้อนคำสั่งที่อาจเป็นอันตราย (Prompt Injection Discovered)", 
                    "refined_query": query
                }

        # ---------------------------------------------------------
        # 3. Topic Guard (Relevance - ความเกี่ยวข้องของเนื้อหา)
        # ---------------------------------------------------------
        # ตรวจสอบว่าคำถามเกี่ยวข้องกับ "One Piece Card Game" หรือไม่
        # 
        # [Concept: Keyword Matching]
        # Implementation นี้ใช้ "Keyword Matching" แบบง่ายเพื่อกรองคำที่รู้อยู่แล้วว่าเป็นเรื่องอื่น
        # ข้อดี: เร็ว, เข้าใจง่าย
        # ข้อเสีย: ดักจับได้ไม่หมด, อาจ Block ผิดบริบทง่าย (False Positive)
        # 
        # [Recommended: LLM-based Classification]
        # วิธีที่มีประสิทธิภาพที่สุดคือการใช้ Small LLM (เช่น Gemini Flash, GPT-4o-mini)
        # ให้ช่วย Classify ว่าคำถามนี้เกี่ยวกับ "One Piece Card Game" หรือไม่
        # Prompt ตัวอย่าง:
        # "Is the following query related to One Piece Card Game or general greeting? Answer YES or NO."
        # ข้อดี: เข้าใจบริบทภาษาได้ดีที่สุด (Context Awareness) ไม่พลาดง่ายๆ เหมือน Keyword
        # ข้อเสีย: มีค่าใช้จ่ายและ Latency เพิ่มขึ้นเล็กน้อย (แต่คุ้มค่าสำหรับ Production)

        # [Alternative: Vector Similarity Check]
        # อีกวิธีคือใช้ Embedding Model แปลง Query เป็น Vector 
        # แล้วเทียบระยะห่าง (Cosine Similarity) กับ "Topic Concept" ของเรา
        # - ถ้าใกล้เคียง Topic (Score สูง) -> ผ่าน
        # - ถ้าห่างไกล (Score ต่ำ) -> Block
        # *วิธีนี้จะยืดหยุ่นกว่า Keyword แต่อาจไม่เข้าใจบริบทลึกซึ้งเท่า LLM*

        # ตัวอย่าง Keyword สำหรับกรองเรื่องที่ไม่เกี่ยว
        off_topic_keywords = [
            "การเมือง", "เลือกตั้ง", "หุ้น", "crypto", "bitcoin",
            "สูตรอาหาร", "วิธีทำ", "ลดความอ้วน",
            "หวย", "เลขเด็ด", "แทงบอล", "บาคาร่า", "หนังโป๊"
        ]
        
        for keyword in off_topic_keywords:
            if keyword in query.lower():
                 return {
                     "valid": False, 
                     "error": "Topic Alert: ขออภัยครับ ผมเป็น AI สำหรับตอบคำถามเรื่อง One Piece Card Game เท่านั้น", 
                     "refined_query": query
                }
        
        return {"valid": True, "refined_query": pii_refined_query, "error": None}

    async def validate_output(self, response: str) -> Dict[str, Any]:
        """
        รันระบบตรวจสอบ Output Guardrails เพื่อความปลอดภัยก่อนส่งให้ User
        """
        # ---------------------------------------------------------
        # 1. Toxicity Check (ตรวจสอบคำหยาบ/ความเหมาะสม)
        # ---------------------------------------------------------
        # [Recommended: LLM-based Validation]
        # วิธีที่ดีที่สุดคือใช้ LLM ช่วยตรวจสอบ (Self-Reflection / Judge LLM)
        # โดยให้ LLM อีกตัว (หรือตัวเดิม) ตรวจสอบ Response ก่อนส่ง
        # Prompt: "Check if the following response contains any toxic, harmful, or inappropriate content. Answer PASS or FAIL."
        # ข้อดี: เข้าใจบริบท (Context) ได้ดีที่สุด แยกแยะระหว่างคำหยาบจริง vs การยกตัวอย่างคำหยาบได้
        
        # [Alternative: Vector Search]
        # สามารถใช้ Vector Search เทียบกับ Database ของ Toxic Sentences ได้
        # แต่ความแม่นยำอาจสู้ LLM ไม่ได้ในเคสที่ซับซ้อน
        bad_words = ["damn", "stupid", "idiot", "เลว", "โง่"] 
        for word in bad_words:
            if word in response.lower():
                 return {"valid": False, "error": "Quality Alert: ตรวจพบเนื้อหาที่ไม่เหมาะสมในคำตอบ", "refined_response": None}

        # ---------------------------------------------------------
        # 2. Structure Check (ตรวจสอบโครงสร้างข้อมูล)
        # ---------------------------------------------------------
        # กรณีที่คาดหวังผลลัพธ์เป็น JSON (เช่น Tool calling)
        if response.strip().startswith("{"):
            try:
                json.loads(response)
            except json.JSONDecodeError:
                 return {"valid": False, "error": "Structure Alert: รูปแบบ JSON ไม่ถูกต้อง", "refined_response": response}

        return {"valid": True, "refined_response": response, "error": None}

# Singleton instance
guardrails_service = GuardrailsManager()
