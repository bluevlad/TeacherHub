"""
Sentiment Analyzer Service
감성/난이도/추천 분석 서비스
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """감성 분석 서비스"""

    # 카테고리별 키워드 (DB에서 로드하기 전 기본값)
    DEFAULT_KEYWORDS = {
        'sentiment_positive': [
            ('추천', 1.5), ('강추', 2.0), ('좋아요', 1.0), ('감사', 1.0),
            ('합격', 1.5), ('최고', 1.5), ('도움', 1.0), ('굿', 1.0),
            ('명강의', 2.0), ('이해', 1.0), ('쉽게', 1.0), ('친절', 1.0),
            ('꼼꼼', 1.0), ('체계적', 1.5), ('효율적', 1.0), ('짱', 1.5),
            ('대박', 1.5), ('완벽', 1.5), ('만족', 1.0), ('감동', 1.5)
        ],
        'sentiment_negative': [
            ('비추', 2.0), ('별로', 1.0), ('어렵', 1.0), ('실망', 1.5),
            ('환불', 2.0), ('답답', 1.0), ('부족', 1.0), ('아쉽', 0.8),
            ('불친절', 1.5), ('졸림', 1.0), ('지루', 1.0), ('돈아까', 2.0),
            ('후회', 1.5), ('최악', 2.0), ('노답', 2.0), ('짜증', 1.0),
            ('불만', 1.0), ('노잼', 1.5)
        ],
        'difficulty_easy': [
            ('쉬움', 1.0), ('쉽게', 1.0), ('기초', 0.8), ('입문', 0.8),
            ('초보', 0.8), ('친절', 0.5), ('이해됨', 1.0), ('이해잘', 1.0),
            ('쉬워요', 1.0), ('쉬운', 1.0)
        ],
        'difficulty_hard': [
            ('어려움', 1.0), ('어렵', 1.0), ('심화', 0.8), ('고급', 0.8),
            ('빡셈', 1.5), ('헬', 1.5), ('멘붕', 1.0), ('어려워', 1.0),
            ('하드', 1.0), ('빡세', 1.5)
        ],
        'recommendation': [
            ('추천', 1.0), ('강추', 1.5), ('들어라', 1.0), ('꼭', 0.5),
            ('필수', 1.0), ('인생강의', 2.0), ('듣자', 0.8), ('추천해요', 1.0),
            ('들으세요', 1.0), ('필청', 1.5)
        ]
    }

    def __init__(self, db: Session = None):
        self.db = db
        self.keywords: Dict[str, List[tuple]] = {}
        self._initialized = False

    def load_keywords(self, from_db: bool = True):
        """키워드 로드"""
        if self._initialized:
            return

        if from_db and self.db:
            self._load_from_db()
        else:
            self.keywords = self.DEFAULT_KEYWORDS.copy()

        self._initialized = True
        logger.info(f"Loaded keywords: {sum(len(v) for v in self.keywords.values())} total")

    def _load_from_db(self):
        """데이터베이스에서 키워드 로드"""
        from ..models import AnalysisKeyword

        try:
            keywords = self.db.query(AnalysisKeyword).filter(
                AnalysisKeyword.is_active == True
            ).all()

            for kw in keywords:
                if kw.category not in self.keywords:
                    self.keywords[kw.category] = []
                self.keywords[kw.category].append((kw.keyword, kw.weight))

        except Exception as e:
            logger.error(f"Failed to load keywords from DB: {e}")
            self.keywords = self.DEFAULT_KEYWORDS.copy()

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        텍스트 분석

        Returns:
            {
                'sentiment': 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL',
                'sentiment_score': float (-1.0 ~ 1.0),
                'difficulty': 'EASY' | 'MEDIUM' | 'HARD' | None,
                'is_recommended': bool
            }
        """
        if not self._initialized:
            self.load_keywords(from_db=False)

        if not text:
            return {
                'sentiment': 'NEUTRAL',
                'sentiment_score': 0.0,
                'difficulty': None,
                'is_recommended': False
            }

        text_lower = text.lower()

        # 감성 점수 계산
        positive_score = self._calculate_score(text_lower, 'sentiment_positive')
        negative_score = self._calculate_score(text_lower, 'sentiment_negative')

        # 정규화된 감성 점수 (-1.0 ~ 1.0)
        total = positive_score + negative_score
        if total > 0:
            sentiment_score = (positive_score - negative_score) / (total + 1)
        else:
            sentiment_score = 0.0

        # 감성 레이블
        if sentiment_score > 0.2:
            sentiment = 'POSITIVE'
        elif sentiment_score < -0.2:
            sentiment = 'NEGATIVE'
        else:
            sentiment = 'NEUTRAL'

        # 난이도 분석
        easy_score = self._calculate_score(text_lower, 'difficulty_easy')
        hard_score = self._calculate_score(text_lower, 'difficulty_hard')

        difficulty = None
        if easy_score > hard_score and easy_score > 0:
            difficulty = 'EASY'
        elif hard_score > easy_score and hard_score > 0:
            difficulty = 'HARD'
        elif easy_score > 0 or hard_score > 0:
            difficulty = 'MEDIUM'

        # 추천 여부
        recommend_score = self._calculate_score(text_lower, 'recommendation')
        is_recommended = recommend_score > 0.5

        return {
            'sentiment': sentiment,
            'sentiment_score': round(sentiment_score, 3),
            'difficulty': difficulty,
            'is_recommended': is_recommended
        }

    def _calculate_score(self, text: str, category: str) -> float:
        """카테고리별 점수 계산"""
        keywords = self.keywords.get(category, [])
        score = 0.0

        for keyword, weight in keywords:
            if keyword in text:
                # 등장 횟수에 따른 가중치 (최대 3회까지)
                count = min(text.count(keyword), 3)
                score += weight * count

        return score

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """여러 텍스트 일괄 분석"""
        return [self.analyze(text) for text in texts]

    def get_keywords_by_category(self, category: str) -> List[tuple]:
        """카테고리별 키워드 반환"""
        return self.keywords.get(category, [])

    def add_keyword(self, category: str, keyword: str, weight: float = 1.0):
        """키워드 추가 (메모리에만)"""
        if category not in self.keywords:
            self.keywords[category] = []
        self.keywords[category].append((keyword, weight))
