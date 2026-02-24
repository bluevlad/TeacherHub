"""
Teacher Name Matcher Service
강사명 매칭 서비스
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """매칭 결과"""
    teacher_id: int
    teacher_name: str
    matched_text: str
    start_pos: int
    end_pos: int
    context: str  # 주변 문맥 (앞뒤 100자)


class TeacherMatcher:
    """강사명 매칭 서비스"""

    # 제외할 일반적인 단어들 (동음이의어 방지)
    EXCLUDE_PATTERNS = [
        r'^\d+$',           # 숫자만
        r'^[가-힣]$',       # 한글 한 글자
        r'^(선생|강사|교수)$',  # 일반 명사
    ]

    def __init__(self, db: Session = None):
        self.db = db
        self._name_map: Dict[str, int] = {}  # name/alias -> teacher_id
        self._teacher_info: Dict[int, Dict] = {}  # teacher_id -> info
        self._patterns: List[Tuple[re.Pattern, int]] = []  # (compiled pattern, teacher_id)

    def load_teachers(self, teachers: List[Dict[str, Any]] = None):
        """
        강사 정보 로드

        Args:
            teachers: List of dict with keys: id, name, aliases, academy_name, subject_name
                     If None, load from database
        """
        if teachers is None and self.db:
            teachers = self._load_from_db()

        if not teachers:
            logger.warning("No teachers to load")
            return

        self._name_map.clear()
        self._teacher_info.clear()
        self._patterns.clear()

        all_names = []

        for teacher in teachers:
            teacher_id = teacher['id']
            name = teacher['name']

            self._teacher_info[teacher_id] = {
                'name': name,
                'academy': teacher.get('academy_name', ''),
                'subject': teacher.get('subject_name', '')
            }

            # 이름 등록
            names_to_register = [name]
            if teacher.get('aliases'):
                names_to_register.extend(teacher['aliases'])

            for n in names_to_register:
                if n and len(n) >= 2:  # 최소 2글자 이상
                    self._name_map[n] = teacher_id
                    all_names.append((n, teacher_id))

        # 긴 이름부터 매칭하도록 정렬 (탐욕적 매칭)
        all_names.sort(key=lambda x: len(x[0]), reverse=True)

        # 정규식 패턴 컴파일
        for name, teacher_id in all_names:
            # 이름 앞뒤에 단어 경계 또는 특수문자가 있어야 함
            # 한글의 경우 단어 경계가 다르게 작동하므로 별도 처리
            pattern_str = self._build_pattern(name)
            try:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                self._patterns.append((pattern, teacher_id, name))
            except re.error as e:
                logger.error(f"Regex error for '{name}': {e}")

        logger.info(f"Loaded {len(self._teacher_info)} teachers, {len(self._name_map)} names/aliases")

    def _load_from_db(self) -> List[Dict[str, Any]]:
        """데이터베이스에서 강사 정보 로드"""
        from ..models import Teacher, Academy, Subject

        teachers = []
        query = self.db.query(Teacher).filter(Teacher.is_active == True)

        for t in query.all():
            teachers.append({
                'id': t.id,
                'name': t.name,
                'aliases': t.aliases or [],
                'academy_name': t.academy.name if t.academy else '',
                'subject_name': t.subject.name if t.subject else ''
            })

        return teachers

    # 이름 뒤에 붙을 수 있는 한글 접미사 (호칭 + 과목명)
    SUFFIX_PATTERN = r'(?:쌤|강사|선생님?|교수님?|국어|영어|수학|한국사|행정법|헌법|행정학|경제학|세법|회계|사회|과학)?'

    def _build_pattern(self, name: str) -> str:
        """이름에 대한 정규식 패턴 생성"""
        # 특수문자 이스케이프
        escaped = re.escape(name)

        # 이름 앞: 한글/영문/숫자가 아닌 문자 또는 문장 시작
        # 이름 뒤: 허용된 접미사(쌤, 강사, 과목명 등) + 한글/영문/숫자가 아닌 문자 또는 문장 끝
        # 예: "이선재 강의" ✓, "이선재국어" ✓, "이선재쌤" ✓, "[이선재]" ✓
        pattern = f'(?:^|[^가-힣a-zA-Z0-9]){escaped}{self.SUFFIX_PATTERN}(?:[^가-힣a-zA-Z0-9]|$)'

        return pattern

    def find_mentions(self, text: str, context_size: int = 100) -> List[MatchResult]:
        """
        텍스트에서 강사 멘션 찾기

        Args:
            text: 검색할 텍스트
            context_size: 주변 문맥 크기 (앞뒤 글자 수)

        Returns:
            List of MatchResult
        """
        if not text or not self._patterns:
            return []

        results = []
        found_positions = set()  # 중복 방지

        for pattern, teacher_id, original_name in self._patterns:
            for match in pattern.finditer(text):
                # 실제 매칭된 위치 조정 (패턴에 앞뒤 문자가 포함되어 있으므로)
                start = match.start()
                end = match.end()

                # 앞뒤 경계 문자 제거
                matched_text = match.group()
                if matched_text and not matched_text[0].isalnum() and matched_text[0] not in '가힣':
                    start += 1
                    matched_text = matched_text[1:]
                if matched_text and not matched_text[-1].isalnum() and matched_text[-1] not in '가힣':
                    end -= 1
                    matched_text = matched_text[:-1]

                # 위치 중복 체크
                pos_key = (start, end)
                if pos_key in found_positions:
                    continue
                found_positions.add(pos_key)

                # 문맥 추출
                context_start = max(0, start - context_size)
                context_end = min(len(text), end + context_size)
                context = text[context_start:context_end]

                teacher_info = self._teacher_info.get(teacher_id, {})

                results.append(MatchResult(
                    teacher_id=teacher_id,
                    teacher_name=teacher_info.get('name', original_name),
                    matched_text=matched_text.strip(),
                    start_pos=start,
                    end_pos=end,
                    context=context
                ))

        # 위치순 정렬
        results.sort(key=lambda x: x.start_pos)

        return results

    def find_in_post(self, title: str, content: str, comments: List[str] = None) -> Dict[str, List[MatchResult]]:
        """
        게시글 전체에서 강사 멘션 찾기

        Args:
            title: 게시글 제목
            content: 게시글 본문
            comments: 댓글 목록

        Returns:
            Dict with keys: 'title', 'content', 'comments'
        """
        results = {
            'title': self.find_mentions(title),
            'content': self.find_mentions(content),
            'comments': []
        }

        if comments:
            for idx, comment in enumerate(comments):
                comment_mentions = self.find_mentions(comment)
                for mention in comment_mentions:
                    # 댓글 인덱스 추가
                    results['comments'].append((idx, mention))

        return results

    def get_teacher_info(self, teacher_id: int) -> Optional[Dict[str, Any]]:
        """강사 정보 조회"""
        return self._teacher_info.get(teacher_id)

    def get_all_teacher_ids(self) -> List[int]:
        """모든 강사 ID 반환"""
        return list(self._teacher_info.keys())
