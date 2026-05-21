import sys
import os
import logging

logger = logging.getLogger("NLP_Classifier")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - [NLP] - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRAWLER_PATH = os.path.join(BASE_DIR, 'crawler')
if CRAWLER_PATH not in sys.path:
    sys.path.insert(0, CRAWLER_PATH)

from db.session import SessionLocal
from db.models import Document

def extract_features_and_difficulty(text_content):
    if not text_content or len(text_content.strip()) < 10:
        return "beginner"
        
    try:
        words = text_content.lower().split()
        word_count = len(words)
        
        adv_terms = {"architecture", "optimization", "asymptotic", "gradient", "neural", "tensor", "distributed", "concurrency"}
        int_terms = {"implementation", "programming", "functions", "database", "pipeline", "application", "intermediate"}
        
        adv_count = sum(1 for w in words if w in adv_terms)
        int_count = sum(1 for w in words if w in int_terms)
        
        if adv_count > 3 or (word_count > 1000 and adv_count >= 1):
            return "advanced"
        elif int_count > 4 or word_count > 500:
            return "intermediate"
        return "beginner"
    except Exception as e:
        logger.warning(f"Error parsing text (applying fallback 'beginner'): {e}")
        return "beginner"

def run_classification_pipeline():
    logger.info("Checking for new unclassified documents in the DB...")
    session = SessionLocal()
    try:
        unclassified_docs = session.query(Document).filter(Document.difficulty.is_(None)).all()
        
        if not unclassified_docs:
            logger.info("No new documents to classify.")
            return

        logger.info(f"Extracting NLP features for {len(unclassified_docs)} documents...")
        for doc in unclassified_docs:
            doc.difficulty = extract_features_and_difficulty(doc.body)
            doc.topic_label = "general education" 
            
        session.commit()
        logger.info(f"SUCCESS: Classified {len(unclassified_docs)} documents.")
        
    except Exception as e:
        logger.error(f"Critical error in NLP classification: {e}", exc_info=True)
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    run_classification_pipeline()