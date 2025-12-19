import re
import json
from typing import Optional, Dict, Any

class LocalGuardrailsProvider:
    """
    Local implementation of Guardrails using basic Regex and Keyword matching.
    """

    async def validate_input(self, query: str) -> Dict[str, Any]:
        """
        Runs local input guardrails: PII, Injection, Topic.
        """
        
        # 1. PII Guard (Redaction)
        pii_refined_query = re.sub(r'0\d{1,2}-\d{3}-\d{4}', '<PHONE_REDACTED>', query)
        
        # 2. Injection Guard (Basic Keyword Block)
        forbidden_keywords = ["ignore all instructions", "format c:", "rm -rf", "drop table"]
        for keyword in forbidden_keywords:
            if keyword.lower() in pii_refined_query.lower():
                return {
                    "valid": False, 
                    "error": "Security Alert: พบความพยายามป้อนคำสั่งที่อาจเป็นอันตราย (Prompt Injection Discovered)", 
                    "refined_query": query
                }

        # 3. Topic Guard (Relevance)
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
        Runs local output guardrails: Toxicity, JSON Structure.
        """
        # 1. Toxicity Check (Basic Keywords)
        bad_words = ["damn", "stupid", "idiot", "เลว", "โง่"] 
        for word in bad_words:
            if word in response.lower():
                 return {"valid": False, "error": "Quality Alert: ตรวจพบเนื้อหาที่ไม่เหมาะสมในคำตอบ", "refined_response": None}

        # 2. Structure Check
        if response.strip().startswith("{"):
            try:
                json.loads(response)
            except json.JSONDecodeError:
                 return {"valid": False, "error": "Structure Alert: รูปแบบ JSON ไม่ถูกต้อง", "refined_response": response}

        return {"valid": True, "refined_response": response, "error": None}
