import trafilatura
from unstructured.partition.pdf import partition_pdf
import logging

logger = logging.getLogger(__name__)

class ContentCleaner:
    @staticmethod
    def clean_html(html_content: str) -> str:
        """Extracts clean text from HTML using trafilatura."""
        if not html_content:
            return ""
        try:
            return trafilatura.extract(html_content) or ""
        except Exception as e:
            logger.error(f"Error cleaning HTML: {e}")
            return ""

    @staticmethod
    def clean_pdf(pdf_path: str) -> str:
        """Extracts clean text from PDF using unstructured."""
        try:
            elements = partition_pdf(pdf_path)
            relevant_text = []

            for e in elements:
                if e.category in ["Title", "ListItem", "NarrativeText"]:
                    relevant_text.append(e.text)
            return "\n".join(relevant_text)
        except Exception as e:
            logger.error(f"Error cleaning PDF: {e}")
            return ""

    @staticmethod
    def relevance_filter(text: str) -> bool:
        clinical_keywords = [

            "assist", "monitor", "check", "observe", "help with", "supervise", 
            "ensure", "remove hazard", "install", "support", "administer",

            "fall risk", "frailty", "mobility", "cognitive", "dementia",
            "polypharmacy", "medication review", "adl", "iadl", "tug test",
            "balance", "gait", "transfer", "ambulation",

            "recommendation", "guideline", "care plan", "intervention",
            "screening", "scoring", "assessment tool"
        ]
        text_lower = text.lower()
        matches = [k for k in clinical_keywords if k in text_lower]

        return len(matches) >= 2
