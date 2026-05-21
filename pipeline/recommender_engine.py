import sys
import os
import math
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("Recommender")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - [RECOMMENDER] - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRAWLER_PATH = os.path.join(BASE_DIR, 'crawler')
if CRAWLER_PATH not in sys.path:
    sys.path.insert(0, CRAWLER_PATH)

from db.session import SessionLocal
from db.models import Document, CrawlRun, CrawlRunDocument

class RecommenderEngine:
    def _get_difficulty_score(self, diff_str):
        mapping = {"beginner": 1, "intermediate": 2, "advanced": 3}
        return mapping.get((diff_str or "beginner").lower(), 1)

    def score_run_documents(self, run_id: int):
        logger.info(f"Starting score calculation (TF-IDF + Soft Match) for run_id={run_id}")
        session = SessionLocal()
        
        try:
            run = session.get(CrawlRun, run_id)
            if not run:
                logger.error(f"CrawlRun with id {run_id} does not exist in the database!")
                return

            run_docs = session.query(CrawlRunDocument).filter_by(crawl_run_id=run_id).all()
            if not run_docs:
                logger.warning(f"No documents extracted for run_id {run_id}.")
                return

            doc_ids = [rd.document_id for rd in run_docs]
            documents = session.query(Document).filter(Document.id.in_(doc_ids)).all()
            doc_map = {d.id: d for d in documents}

            target_topic = run.topic or ""
            if run.learner_goal:
                target_topic += " " + run.learner_goal
                
            learner_diff_val = self._get_difficulty_score(run.learner_level)

            corpus = [target_topic] + [(doc_map[rd.document_id].body or "") for rd in run_docs]
            vectorizer = TfidfVectorizer(stop_words='english')
            
            try:
                tfidf_matrix = vectorizer.fit_transform(corpus)
                similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
                logger.info("TF-IDF matrix generated successfully.")
            except ValueError as ve:
                logger.warning(f"TF-IDF failed (likely due to empty texts). Fallback scores to 0. Error: {ve}")
                similarities = [0.0] * len(run_docs)

            # Update scores in the DB
            for idx, rd in enumerate(run_docs):
                doc = doc_map.get(rd.document_id)
                if not doc:
                    continue

                doc_diff_val = self._get_difficulty_score(doc.difficulty or "beginner")
                difficulty_distance = abs(learner_diff_val - doc_diff_val)
                penalty = 0.25 * difficulty_distance
                
                hybrid_score = similarities[idx] - penalty
                if math.isnan(hybrid_score):
                    hybrid_score = 0.0
                
                hybrid_score = max(0.0, min(1.0, float(hybrid_score)))
                
                rd.relevance_score = round(hybrid_score, 4)

            session.commit()
            logger.info(f"SUCCESS: Scores for {len(run_docs)} documents saved to CrawlRunDocument.")
            
        except Exception as e:
            logger.error(f"General error calculating scores: {e}", exc_info=True)
            session.rollback()
        finally:
            session.close()

if __name__ == "__main__":
    engine = RecommenderEngine()
    engine.score_run_documents(run_id=1)