from textblob import TextBlob
import random

class SentimentAnalyzer:
    def __init__(self):
        # In a real scenario, we would load a KoELECTRA model here.
        # For this sample, we will use a simple rule-based approach + random factors 
        # to simulate AI score since we cannot easily download 500MB+ models in this specific env.
        self.positive_keywords = ['추천', '좋아요', '감사', '합격', '최고', '도움', '굿', '명강의', '이해']
        self.negative_keywords = ['비추', '별로', '어렵', '실망', '환불', '답답', '부족', '아쉽']

    def analyze(self, text):
        score = 0
        
        # Simple Keyword Scoring
        for kw in self.positive_keywords:
            if kw in text: score += 1
            
        for kw in self.negative_keywords:
            if kw in text: score -= 1
            
        # Mocking "Deep Learning" probability
        # Normalize score to 0.0 ~ 1.0 roughly
        # This is strictly for DEMONSTRATION purposes as requested ("sample")
        base_score = 0.5 + (score * 0.1)
        
        # Add some variation
        final_score = max(0.0, min(1.0, base_score))
        
        if final_score > 0.6:
            label = "POSITIVE"
        elif final_score < 0.4:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"
            
        return {
            "label": label,
            "score": round(final_score, 2),
            "text_snippet": text[:50]
        }
