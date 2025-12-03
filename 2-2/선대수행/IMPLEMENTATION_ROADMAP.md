# 4계층 아키텍처 + 평가 체계 정리

## 📋 현재 상태

### ✅ 완료된 것
- [x] **ARCHITECTURE.md**: 4계층 구조 전체 설명
- [x] **EVALUATION_SYSTEM.ipynb**: 평가 함수 상세 설명 + 예제 코드
- [x] **keyboard_layout_corrected.py**: 올바른 위치 정보 & 거리 계산
- [x] **fatigue_corrected.py**: 올바른 f2, f3, f4 테이블 & 비용 함수

### ⚠️ 다음 할 것
1. **ga_integrated.py 수정**: 새로운 모델 사용하도록 평가 함수 재구현
2. **통합 테스트**: 단위 테스트 + 전체 GA 테스트
3. **결과 검증**: 수렴 곡선, 최적 배열 시각화

---

## 🎯 핵심 개념 요약

### 레이어 1: 데이터
```
입력 → 코퍼스 처리 → W(공기행렬), f(글자빈도)
```
**현황**: ✓ `datas/data.py` 완료

### 레이어 2: 모델
```
W → 라플라시안(L) → 고유벡터
W + 키보드배치 → 거리행렬 D(M) → f1
손가락테이블 → f2, f3, f4
↓
C_fatigue = Σ W[i,j] × d(i,j) × f2(i,j) × f3(i,j) × f4(i,j)
```
**현황**: 
- ✓ 라플라시안: `models/rw_laplacian.py`
- 🔄 피로도: `models/fatigue_corrected.py` (새로움)
- 🔄 거리: `models/keyboard_layout_corrected.py` (새로움)

### 레이어 3: GA (최적화)
```
C_fatigue + C_lap → Fitness
Population → Selection → Crossover → Mutation → 다음 세대
```
**현황**: ⚠️ `GA/ga_integrated.py` 수정 필요

### 레이어 4: 시각화
```
최적 배열 M* → 키보드 그림 + heatmap + 통계
```
**현황**: 미구현

---

## 📊 평가 체계 흐름도

```
레이아웃 M (3×10 배열)
  ↓
[Step 1] 글자 위치 추출
  layout[r, c] = 글자인덱스 (0~25)
  ↓ get_position_2d(layout, i)
  pos_i = (row_i, col_i)
  ↓
[Step 2] 위치별 손/손가락 정보 추출
  pos_idx = row * 10 + col
  (hand_i, finger_i) = position_table[pos_idx]
  ↓
[Step 3] 모든 글자쌍 (i, j)에 대해
  for i in 26:
    for j in 26:
      if W[i, j] > 0:
        ↓
        [3-1] 거리 계산
          d_ij = sqrt(Δcol² + 0.8×Δrow²)
        ↓
        [3-2] f2 계산 (손가락 비용)
          f2_ij = (f2_table[finger_i] + f2_table[finger_j]) / 2
        ↓
        [3-3] f3 계산 (방향 비용)
          hand_same = (hand_i == hand_j)
          row_dir = 'top_to_bottom' or 'bottom_to_top' or 'same_row'
          f3_ij = f3_table[(hand_same, row_dir)]
        ↓
        [3-4] f4 계산 (손가락조합 비용)
          f4_ij = f4_table[finger_i_idx, finger_j_idx]
        ↓
        [3-5] f_step 계산
          f_step = d_ij × f2_ij × f3_ij × f4_ij
        ↓
        [3-6] 피로도 누적
          C_fatigue += W[i,j] × f_step
  ↓
[Step 4] 라플라시안 페널티 계산
  for i, j: W[i,j] > 0
    dist_sq = (row_j - row_i)² + (col_j - col_i)²
    C_lap += W[i,j] × dist_sq
  ↓
[Step 5] 최종 비용
  C_total = C_fatigue + 0.3 × C_lap
  ↓
[Step 6] 적합도
  Fitness = 1 / (C_total + ε)
  ↓
출력: Fitness (높을수록 좋음)
```

---

## 🔧 파일 매핑

| 레이어 | 모듈 | 파일 | 상태 | 설명 |
|--------|------|------|------|------|
| 1 | 데이터 전처리 | `datas/data.py` | ✓ | W 로드, 글자 매핑 |
| 2 | 라플라시안 | `models/rw_laplacian.py` | ✓ | L, 고유분해 |
| 2 | 키보드 모델 | `models/keyboard_layout_corrected.py` | 🆕 | 위치정보, 거리 |
| 2 | 피로도 모델 | `models/fatigue_corrected.py` | 🆕 | f2, f3, f4 테이블 |
| 3 | GA | `GA/ga_integrated.py` | ⚠️ | 평가함수 수정 필요 |
| 4 | 시각화 | `notebooks/04_visualization.ipynb` | 미구현 | 결과 표시 |

---

## 💡 핵심 수정 사항

### Before (현재)
```python
# GA/ga_integrated.py - 평가 함수 (잘못됨)
def _calc_fatigue_total(self):
    W = self.co_occurrence
    total_fatigue = 0.0
    
    for i in range(min(15, len(W))):  # ❌ 상위 15개만
        top_j_indices = np.argsort(W[i])[-5:]  # ❌ 각각 상위 5개만
        for j in top_j_indices:
            if W[i, j] > 0:
                distance = self.distance_in_keyboard(i, j)
                f2, f3, f4 = 1.0, 1.0, 1.0  # ❌ 모두 1.0 고정
                f_step = distance * f2 * f3 * f4
                total_fatigue += W[i, j] * f_step
    
    return total_fatigue
```

### After (올바름)
```python
# GA/ga_integrated_corrected.py - 평가 함수 (수정됨)
def evaluate_fatigue(self):
    """
    C_fatigue = Σ W[i,j] × d(i,j) × f2(i,j) × f3(i,j) × f4(i,j)
    """
    C_fatigue = 0.0
    
    for i in range(26):  # ✓ 모든 글자
        for j in range(26):  # ✓ 모든 글자
            if self.W[i, j] > 0:
                # 위치
                pos_i = self.keyboard.get_position_2d(self.layout, i)
                pos_j = self.keyboard.get_position_2d(self.layout, j)
                
                if pos_i is None or pos_j is None:
                    continue
                
                # 거리
                d = self.keyboard.distance(pos_i, pos_j)
                
                # 손/손가락
                pos_i_idx = self.keyboard.get_position_idx(pos_i[0], pos_i[1])
                pos_j_idx = self.keyboard.get_position_idx(pos_j[0], pos_j[1])
                hand_i, finger_i = self.keyboard.get_hand_finger(pos_i_idx)
                hand_j, finger_j = self.keyboard.get_hand_finger(pos_j_idx)
                
                # f2, f3, f4 ✓ 실제 값 조회
                f2 = self.fatigue.get_f2_cost(finger_i, finger_j)
                f3 = self.fatigue.get_f3_cost(hand_i, hand_j, pos_i[0], pos_j[0])
                f4 = self.fatigue.get_f4_cost(finger_i, finger_j)
                
                # f_step
                f_step = d * f2 * f3 * f4
                C_fatigue += self.W[i, j] * f_step
    
    return C_fatigue
```

---

## 🚀 다음 작업 순서

### Phase 1: 수정 (2시간)
```bash
# 1. 새로운 모델 클래스 생성 완료
# ✓ keyboard_layout_corrected.py
# ✓ fatigue_corrected.py

# 2. GA 통합 (ga_integrated.py 수정)
#   - 새로운 KeyboardLayout, FatigueModel 임포트
#   - Individual.evaluate() 재구현
#   - 테스트
```

### Phase 2: 테스트 (1시간)
```bash
# 1. 단위 테스트
python3 tests/test_keyboard_layout_corrected.py
python3 tests/test_fatigue_corrected.py

# 2. 통합 테스트
python3 ga_runner_final.py

# 3. 결과 확인
# - 적합도 증가 트렌드 확인
# - 피로도 감소 확인
# - 최적 배열 확인
```

### Phase 3: 시각화 (1시간)
```bash
python3 notebooks/04_visualization.ipynb
```

---

## 📈 예상 결과

### 현재 (잘못된 평가)
```
Gen 1: fitness = 0.0106
...
Gen 30: fitness = 0.1823
```
⚠️ 음성 피드백, 비현실적인 배열

### 수정 후 (올바른 평가)
```
Gen 1: fitness = 0.0010 (매우 낮음, 임의 배열)
...
Gen 15: fitness = 0.0050 (개선)
...
Gen 30: fitness = 0.0200 (수렴)
```
✓ 긍정적 피드백, 합리적인 배열 진화

---

## ✨ 핵심 정리

**시스템의 흐름:**
1. 코퍼스 → **공기 행렬 W** (얼마나 자주 함께 나타나는가)
2. 키보드 배치 M → **위치 정보** (어디에 배치되어 있는가)
3. W + M → **피로도 계산** (실제로 치기 얼마나 힘든가)
   - f1: 거리 (손가락 이동 거리)
   - f2: 손가락 (검지 1.0 vs 소지 1.5)
   - f3: 방향 (위↓ 1.2 vs 아래↑ 1.0)
   - f4: 조합 (Index→Index 2.0 vs Index→Middle 1.0)
4. 피로도 → **적합도** (역수: 낮을수록 좋음)
5. GA → **최적 배열 탐색** (적합도 최대)

**현재 문제:** 
- f2, f3, f4를 실제로 사용하지 않음 (모두 1.0)
- → 평가 함수가 실질적으로 거리만 보고 있음
- → 피로도 모델을 제대로 활용하지 못함

**해결책:**
- 새로운 KeyboardLayout, FatigueModel 클래스 사용
- GA Individual.evaluate()에서 정확한 평가
- 모든 f1~f4 요소 활용
