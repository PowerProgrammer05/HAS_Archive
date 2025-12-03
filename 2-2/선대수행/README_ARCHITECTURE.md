# 📊 최종 정리: 4계층 아키텍처 + 평가 체계 설계

## 🎯 이 프로젝트가 해결하는 문제

**목표:** 고등학생 최적 키보드 배열 찾기

**과정:**
```
고등학생 코퍼스
  ↓ (공기 분석)
글자 빈도 & 연속 사용 패턴
  ↓ (모델링)
거리 + 피로도 (f1~f4 요소 고려)
  ↓ (GA 최적화)
피로도 최소 배열
```

---

## 📁 4계층 구조

### 레이어 1️⃣: 데이터 & 전처리
```
입력:
  - 코퍼스: datas/kor_news_2007_100K-words.txt
  - 결과: W (26×26 공기 행렬)
  
파일:
  - datas/data.py: load_co_occurrence_matrix()
  - datas/all_raw_weight.csv: 실제 데이터

상태: ✅ 완료
```

### 레이어 2️⃣: 그래프·라플라시안 & 피로도 모델
```
입력:
  - W (공기 행렬)
  - 키보드 배치 M

처리:
  1. 라플라시안: L = D - W
  2. 고유분해: L의 고유벡터 → 글자 그룹 정보
  3. 거리 계산: d(i, j) in M
  4. 피로도: f1(거리) × f2(손가락) × f3(방향) × f4(조합)

파일:
  - models/rw_laplacian.py: 라플라시안 계산 ✅
  - models/keyboard_layout_corrected.py: 위치·거리 🆕
  - models/fatigue_corrected.py: f2, f3, f4 테이블 🆕

상태: 🆕 새로 작성됨
```

### 레이어 3️⃣: 유전 알고리즘 (최적화)
```
입력:
  - C_total (비용 함수)

처리:
  1. 초기 population (무작위 배열들)
  2. 각 세대:
     a) 평가: 각 배열의 피로도 계산
     b) 선택: 좋은 배열 선택
     c) 교차: 부모 배열 섞기
     d) 돌연변이: 무작위 변화
  3. 반복 (30세대 등)

파일:
  - GA/ga_integrated.py: 기본 구조 ✅
  - GA/ga_integrated.py: evaluate() 함수 ⚠️ 수정 필요

상태: ⚠️ 평가 함수만 수정하면 완성
```

### 레이어 4️⃣: 실행 & 시각화
```
입력:
  - 최적 배열 M*
  - 피로도 정보

출력:
  - 키보드 배치 시각화
  - 피로도 heatmap
  - 기존 배열과 비교 통계

파일:
  - notebooks/04_visualization.ipynb: 미구현

상태: ⏳ 예정
```

---

## 📚 생성된 문서

### 1. ARCHITECTURE.md
**내용:** 4계층 전체 구조, 각 모듈의 역할, 파일 매핑

```
0. 시스템 전체 흐름
1. 레이어 1: 데이터
2. 레이어 2: 그래프·라플라시안·피로도
3. 레이어 3: GA
4. 레이어 4: 시각화
5. 현재 상태 분석
6. 수정 계획
```

### 2. EVALUATION_SYSTEM.ipynb
**내용:** 평가 함수의 상세 설명 + Python 예제

```
0. 목표
1. 현재 vs 원래 의도 (Before/After)
2. 키보드 구조 & 위치 정의
3. 거리 계산 (f1)
4. 손가락 정보 (f2)
5. 방향 정보 (f3)
6. 손가락 조합 (f4)
7. 통합: 전체 피로도
8. 요약: 평가 구조도
9. 실제 계산 예제 (Python)
```

**실행방법:**
```bash
jupyter notebook EVALUATION_SYSTEM.ipynb
```

### 3. keyboard_layout_corrected.py
**내용:** 올바른 키보드 모델

```python
class KeyboardLayout:
    # 위치 정보: (row, col, hand, finger)
    position_table = {...}
    
    # 메서드:
    get_position_2d(layout, char_idx)  # 글자 위치
    get_hand_finger(pos_idx)           # 손/손가락
    distance(pos1, pos2)               # 거리
    evaluate_layout()                  # 전체 평가
```

**핵심 기능:**
- ✓ 26개 한글 자모 기본 배치
- ✓ 각 위치의 손/손가락 정보 (왼손: ring/middle/index, 오른손: index/middle/ring/little)
- ✓ 두 위치 사이의 거리 계산 (유클리드)
- ✓ 전체 피로도 평가

### 4. fatigue_corrected.py
**내용:** 올바른 피로도 모델

```python
class FatigueModel:
    # 테이블:
    f2_table = {Index: 1.0, Middle: 1.0, Ring: 1.2, Little: 1.5}
    
    f3_table = {
        ('same_hand', 'top_to_bottom'): 1.2,
        ('same_hand', 'bottom_to_top'): 1.0,
        ...
    }
    
    f4_table = [[2.0, 1.0, 1.2, 1.0], ...]  # 4×4 행렬
    
    # 메서드:
    get_f2_cost(finger1, finger2)
    get_f3_cost(hand1, hand2, row1, row2)
    get_f4_cost(finger1, finger2)
```

**테이블 의미:**
- **f2**: 손가락 약점 (검지 강함 1.0 ~ 소지 약함 1.5)
- **f3**: 입력 방향 난이도 (아래→위 쉬움 1.0 ~ 다른손 위→아래 어려움 1.5)
- **f4**: 손가락 조합 (같은 손가락 2.0 ~ 먼 손가락 1.0)

### 5. IMPLEMENTATION_ROADMAP.md
**내용:** 평가 체계 흐름도 + 수정 사항 + 다음 작업

```
- 현재 상태 분석
- 핵심 개념 요약
- 평가 체계 흐름도
- 파일 매핑 테이블
- Before/After 코드 비교
- 다음 작업 순서
- 예상 결과
```

---

## 🔄 Before vs After: 핵심 차이점

### ❌ 현재 (잘못됨)
```python
# GA/ga_integrated.py
def _calc_fatigue_total(self):
    # 1. 상위 15개 글자만 → 나머지 11개 무시
    # 2. 각 글자의 상위 5개 쌍만 → 전체 가중치 손실
    # 3. f2, f3, f4 = 1.0 고정 → 피로도 모델 미사용
    
    for i in range(min(15, len(W))):  # ❌
        top_j_indices = np.argsort(W[i])[-5:]  # ❌
        for j in top_j_indices:
            distance = self.distance_in_keyboard(i, j)
            f_step = distance * 1.0 * 1.0 * 1.0  # ❌
            total_fatigue += W[i, j] * f_step
```

**결과:** 
- 거리 기반 평가만 함 (f1만)
- 손가락, 방향, 조합 정보 무시
- 부정확한 최적화

### ✅ 수정 후 (올바름)
```python
# GA/ga_integrated_corrected.py
def evaluate_fatigue(self):
    # 1. 모든 26개 글자
    # 2. 모든 26×26 글자쌍
    # 3. 실제 f2, f3, f4 값 사용
    
    for i in range(26):  # ✓
        for j in range(26):  # ✓
            if self.W[i, j] > 0:
                pos_i = self.keyboard.get_position_2d(self.layout, i)
                pos_j = self.keyboard.get_position_2d(self.layout, j)
                
                d = self.keyboard.distance(pos_i, pos_j)  # 거리
                f2 = self.fatigue.get_f2_cost(finger_i, finger_j)  # 손가락
                f3 = self.fatigue.get_f3_cost(hand_i, hand_j, ...)  # 방향
                f4 = self.fatigue.get_f4_cost(finger_i, finger_j)  # 조합
                
                f_step = d * f2 * f3 * f4
                C_fatigue += self.W[i, j] * f_step
```

**결과:**
- f1 (거리) + f2 (손가락) + f3 (방향) + f4 (조합) 모두 사용
- 현실성 있는 피로도 평가
- 정확한 최적화

---

## 🚀 사용 방법

### 1단계: 새 모델 확인
```bash
# keyboard_layout_corrected.py 테스트
python3 models/keyboard_layout_corrected.py

# fatigue_corrected.py 테스트
python3 models/fatigue_corrected.py
```

### 2단계: 평가 체계 이해
```bash
# Jupyter 노트북에서 예제 실행
jupyter notebook EVALUATION_SYSTEM.ipynb
```

### 3단계: 아키텍처 이해
```bash
# 마크다운 문서 읽기
cat ARCHITECTURE.md
cat IMPLEMENTATION_ROADMAP.md
```

### 4단계: GA 수정 (다음)
```python
# GA/ga_integrated_corrected.py 만들기
# 또는 GA/ga_integrated.py 수정
# - Individual.evaluate() 재구현
# - 새로운 KeyboardLayout, FatigueModel 임포트
# - 모든 26×26 글자쌍 처리
```

---

## 📊 정리 테이블

| 항목 | 내용 | 파일 | 상태 |
|------|------|------|------|
| **개념 설명** | 4계층 구조 | ARCHITECTURE.md | ✅ |
| **개념 설명** | 평가 함수 상세 | EVALUATION_SYSTEM.ipynb | ✅ |
| **구현** | 키보드 모델 | keyboard_layout_corrected.py | ✅ |
| **구현** | 피로도 모델 | fatigue_corrected.py | ✅ |
| **구현** | GA 통합 | GA/ga_integrated.py | ⚠️ 수정필요 |
| **로드맵** | 다음 작업 | IMPLEMENTATION_ROADMAP.md | ✅ |

---

## ✨ 핵심 메시지

### 문제
GA가 `models`와 CSV `data.py`를 제대로 사용하지 못함

### 원인
- 손가락·방향·조합 정보가 f2, f3, f4 테이블에 있지만
- GA의 평가 함수에서 모두 1.0으로 고정
- 결과적으로 거리만 고려, 피로도 모델 미사용

### 해결책
1. **KeyboardLayout** (새로움)
   - 위치정보 정확화
   - 거리 계산 정확화
   
2. **FatigueModel** (새로움)
   - f2, f3, f4 테이블 제공
   - 비용 함수 제공
   
3. **GA Individual.evaluate()** (수정)
   - 새 모델 사용
   - 모든 26×26 글자쌍 처리
   - f1×f2×f3×f4 정확 계산

### 기대효과
✓ 모든 데이터 정보 활용
✓ 현실성 있는 배열 생성
✓ 신뢰할 수 있는 최적화 결과

---

## 🎓 학습 경로

1. **EVALUATION_SYSTEM.ipynb** 읽기 (예제 포함)
2. **fatigue_corrected.py** 실행해보기
3. **keyboard_layout_corrected.py** 실행해보기
4. **ARCHITECTURE.md** 전체 구조 이해
5. **IMPLEMENTATION_ROADMAP.md** 다음 단계 확인
6. GA 수정 구현

---

## 📞 핵심 API

### KeyboardLayout
```python
kb = KeyboardLayout()

# 글자 위치 찾기
pos = kb.get_position_2d(layout, char_idx)  # (row, col)

# 손/손가락 정보
hand, finger = kb.get_hand_finger(pos_idx)

# 거리 계산
dist = kb.distance(pos_i, pos_j)

# 전체 평가
result = kb.evaluate_layout(layout, W, f2, f3, f4)
# → {'fatigue': ..., 'laplacian': ..., 'total': ..., 'fitness': ...}
```

### FatigueModel
```python
fatigue = FatigueModel()

# 각 비용 조회
f2 = fatigue.get_f2_cost(finger1, finger2)
f3 = fatigue.get_f3_cost(hand1, hand2, row1, row2)
f4 = fatigue.get_f4_cost(finger1, finger2)

# 테이블 얻기
f2_table, f3_table, f4_table = fatigue.get_all_tables()
```

---

**준비 완료! 🎉 다음은 GA 통합 수정입니다.**
