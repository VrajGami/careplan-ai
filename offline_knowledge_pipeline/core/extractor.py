import re
from typing import List, Dict, Any
from pydantic import BaseModel

class KGNode(BaseModel):
    label: str
    properties: Dict[str, Any]

class KGEdge(BaseModel):
    source_label: str
    target_label: str
    relation: str
    properties: Dict[str, Any]

class StructuredExtractor:
    def __init__(self):
        self.patterns = {

            "environment_action": [
                r"install (.*) in (.*)",
                r"remove (.*) from (.*)",
                r"lighting (should|must) be (.*)",
                r"ensure (.*) is (.*)"
            ],
            "assessment_logic": [
                r"if (.*) score (.*) (.*) then (.*)",
                r"evaluate (.*) using (.*)",
                r"cutoff (of|at) (.*) indicates (.*)",
                r"threshold (is|exceeds) (.*)"
            ],
            "care_task": [
                r"assist with (.*)",
                r"monitor (.*) every (.*)",
                r"supervise (.*) during (.*)",
                r"remind (patient|resident) to (.*)"
            ],
            "medication_safety": [
                r"avoid (.*) in (.*)",
                r"dosage (should|must) (.*)",
                r"monitor for (.*) side effects"
            ]
        }

    def extract(self, text: str) -> List[Dict[str, Any]]:
        extracted_data = []
        text_lower = text.lower()
        
        if "tug" in text_lower or "timed up and go" in text_lower:

            match = re.search(r"(\d+(\.\d+)?) seconds?", text_lower)
            if match:
                extracted_data.append({
                    "type": "ScoringRule",
                    "node": KGNode(label="ScoringRule", properties={
                        "assessment": "TUG",
                        "threshold": match.group(1),
                        "logic": f"Cutoff at {match.group(1)} seconds for fall risk"
                    })
                })
        
        if "beers criteria" in text_lower or "inappropriate medication" in text_lower:

            extracted_data.append({
                "type": "MedicationRule",
                "node": KGNode(label="MedicationRule", properties={
                    "type": "SafetyAlert",
                    "description": "Potentially Inappropriate Medication for Older Adults"
                })
            })

        if any(adl in text_lower for adl in ["bathing", "dressing", "toileting", "feeding", "transferring"]):

             extracted_data.append({
                "type": "CareTask",
                "node": KGNode(label="CareTask", properties={
                    "domain": "ADL Assistance",
                    "instruction": text[:500]
                })
            })

        if any(term in text_lower for term in ["grab bar", "lighting", "flooring", "rugs", "hazard"]):

            extracted_data.append({
                "type": "EnvironmentAction",
                "node": KGNode(label="EnvironmentAction", properties={
                    "category": "Home Safety",
                    "instruction": text[:500]
                })
            })

        if any(term in text_lower for term in ["warning sign", "red flag", "report", "worsen", "escalate"]):

             extracted_data.append({
                "type": "ObservationTask",
                "node": KGNode(label="ObservationTask", properties={
                    "name": "Clinical Red Flags",
                    "trigger": text[:500]
                })
            })

        questions = re.findall(r"(\?|^Do|^Have|^Can).*\?", text)

        for q in questions:
             extracted_data.append({
                "type": "AssessmentQuestion",
                "node": KGNode(label="AssessmentQuestion", properties={
                    "question": q,
                    "context": "Clinical Screening"
                })
            })

        if not extracted_data and len(text) > 100:
            clean_text = " ".join(text.split())
            
            topic = "GeneralCare"

            if any(w in text_lower for w in ["diet", "food", "nutrition", "eat", "drink"]): topic = "Nutrition"
            if any(w in text_lower for w in ["exercise", "walk", "move", "strength"]): topic = "PhysicalActivity"
            if any(w in text_lower for w in ["social", "family", "friend", "lonely"]): topic = "SocialWellbeing"
            if any(w in text_lower for w in ["money", "finance", "pay", "cost"]): topic = "FinancialLegal"
            
            extracted_data.append({
                "type": "KnowledgeChunk",
                "node": KGNode(label="KnowledgeChunk", properties={
                    "text": clean_text[:300] + "...",

                    "full_text": clean_text,
                    "topic": topic,
                    "source_type": "GuidelineText"
                })
            })

        for category, regexes in self.patterns.items():

            for pattern in regexes:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for m in matches:
                    extracted_data.append({
                        "type": category.title().replace("_", ""),
                        "node": KGNode(label=category.title().replace("_", ""), properties={
                            "matched_text": m.group(0),
                            "context": text[max(0, m.start()-50):min(len(text), m.end()+50)]
                        })
                    })

        return extracted_data
