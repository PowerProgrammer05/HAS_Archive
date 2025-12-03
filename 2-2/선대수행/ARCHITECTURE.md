# 4계층 아키텍처: 키보드 배열 최적화 시스템

## 0. 시스템 전체 흐름 (한 줄)

```
입력 (코퍼스, 키보드형, 피로도파라미터)
  ↓ [레이어1: 데이터]
공기 행렬 W, 글자 빈도 f
  ↓ [레이어2: 그래프·라플라시안·피로도]
라플라시안 L, 고유벡터, 거리행렬 D(M), 피로도 C_total(M)
  ↓ [레이어3: GA]
초기집단 → 선택·교차·돌연변이 → 최적 배열 M*
  ↓ [레이어4: 시각화]
결과 보고 (피로도, heatmap, 비교)
```

---

## 1. 레이어 1: 데이터 & 전처리

### 1.1 입력 데이터

| 요소 | 설명 | 현재 위치 |
|------|------|---------|
| **텍스트 코퍼스** | 고등학생 실제 텍스트 | `datas/kor_news_2007_100K-words.txt` |
| **공기 행렬** | W_ij = bigram(i→j) 빈도 | `datas/all_raw_weight.csv` |
| **글자 목록** | Σ = {ㄱ, ㄴ, ..., ㅡ} (26개) | `datas/data.py::korean_list` |
| **키보드 형태** | 3행 × 10열 배치 | `models/keyboard_layout.py` |
| **피로도 파라미터** | f2, f3, f4 테이블 | `models/fatigue.py` |

### 1.2 키보드 배치 (26개 자모)

```
행 0:  1(ㅂ)  2(ㅈ)  3(ㄷ)  4(ㄱ)  5(ㅅ)  6(ㅛ)  7(ㅕ)  8(ㅑ)  9(ㅐ) 10(ㅔ)
행 1: 11(ㅁ) 12(ㄴ) 13(ㅇ) 14(ㄹ) 15(ㅎ) 16(ㅗ) 17(ㅓ) 18(ㅏ) 19(ㅣ)  -
행 2: 20(ㅋ) 21(ㅌ) 22(ㅊ) 23(ㅍ) 24(ㅠ) 25(ㅜ) 26(ㅡ)   -     -     -
```

각 위치 = (행, 열, 손, 손가락)

### 1.3 전처리 모듈 (현재 상태)

| 모듈 | 역할 | 파일 | 상태 |
|------|------|------|------|
| `corpus_preprocessor.py` | W_raw 계산 | `datas/data.py` | ✓ 완료 |
| `char_to_idx_map()` | 자모 → 인덱스 | `datas/data.py` | ✓ 완료 |
| `load_co_occurrence_matrix()` | W 로드 | `datas/data.py` | ✓ 완료 |

---

## 2. 레이어 2: 그래프·라플라시안 & 피로도 모델

### 2.1 그래프 & 라플라시안

```
입력: W (26×26 공기 행렬)
  ↓
대칭화: W_sym = (W + W^T) / 2
  ↓
차수 행렬: D_ii = Σ_j W_sym_ij
  ↓
라플라시안: L = D - W_sym
  ↓
고유분해: L w_i = λ_i w_i
```

**의미**: 
- λ_0 = 0 (trivial)
- λ_1, λ_2 (저주파): 자주 함께 쓰이는 글자군 정보
- 고유벡터 w_i: 각 글자의 "그룹 임베딩"

| 모듈 | 역할 | 파일 | 상태 |
|------|------|------|------|
| `graph_builder.py` | L 구성 | `models/rw_laplacian.py` | ✓ 완료 |
| `laplacian_spectral.py` | 고유분해 | `models/rw_laplacian.py` | ✓ 완료 |

### 2.2 키보드 레이아웃 & 거리 계산

```python
# 위치 정보 구조
position = {
    'index': int (0~29, 26~29는 미사용),
    'row': int,
    'col': int,
    'hand': str ('Left' or 'Right'),
    'finger': str ('Index', 'Middle', 'Ring', 'Little')
}

# 거리 행렬
D(M)[i, j] = keyboard.distance(
    pos_of_char_i_in_layout_M,
    pos_of_char_j_in_layout_M
)
```

| 모듈 | 역할 | 파일 | 상태 |
|------|------|------|------|
| `layout_model.py` | 위치↔손가락 매핑 | `models/keyboard_layout.py` | ⚠️ 부분 완료 |
| `distance()` | 두 위치 사이 거리 | `models/keyboard_layout.py` | ⚠️ 오류 있음 |

### 2.3 피로도 모델: 평가 함수

**최종 비용 함수:**

$$C_{\text{total}}^*(M) = C_{\text{fatigue}}(M) + \alpha \cdot C_{\text{lap}}(M)$$

#### 2.3.1 피로도 비용: $C_{\text{fatigue}}(M)$

```
C_fatigue(M) = Σ_{i,j} W[i,j] × f_step(i, j, M)

여기서:
f_step(i, j, M) = dist(pos_i, pos_j) × f2(i,j) × f3(i,j) × f4(i,j)

- dist(pos_i, pos_j): 레이아웃 M에서 글자i→j 이동 거리
- f2(i,j): 손가락 비용 = 0.5 × (f2[finger(i)] + f2[finger(j)])
- f3(i,j): 방향 비용 = f3[hand_direction, row_direction]
- f4(i,j): 손가락조합 비용 = f4[finger(i), finger(j)]
```

**f2 테이블 (손가락별 피로):**
| Index | Middle | Ring | Little |
|-------|--------|------|--------|
| 1.0   | 1.0    | 1.2  | 1.5    |

**f3 테이블 (방향별 피로):**
| 방향 | 같은손-위→아래 | 같은손-아래→위 | 같은손-같은줄 | 다른손-위→아래 | 다른손-아래→위 | 다른손-같은줄 |
|------|--------|--------|--------|--------|--------|--------|
| 비용 | 1.2    | 1.0    | 1.0    | 1.5    | 1.2    | 1.0    |

**f4 테이블 (손가락조합 피로):**
```
       Index Middle Ring  Little
Index  2.0   1.0    1.2   1.0
Middle 1.0   2.0    1.5   1.2
Ring   1.2   1.5    2.0   1.5
Little 1.0   1.2    1.5   2.0
```

| 모듈 | 역할 | 파일 | 상태 |
|------|------|------|------|
| `fatigue_model.py` | f1~f4 계산 | `models/fatigue.py` | ⚠️ 부분 완료 |

#### 2.3.2 라플라시안 보조 항: $C_{\text{lap}}(M)$

```
C_lap(M) = Σ_{i,j} W[i,j] × (coord_i - coord_j)²

의미: 자주 함께 쓰이는 글자(W[i,j]크면)가 멀리 떨어져있으면 페널티
```

#### 2.3.3 적합도 함수

$$\text{Fitness}(M) = \frac{1}{C_{\text{total}}^*(M) + \epsilon}$$

- 비용 작을수록 → 적합도 크다 (최대화)

---

## 3. 레이어 3: 유전 알고리즘 (최적화)

### 3.1 개체 표현

```python
class Individual:
    layout: np.array  # 길이 26 순열 (또는 [26, 1] 1D 또는 [3, 10] 2D)
    # layout[26:30]은 미사용 위치 (패딩)
    
    def evaluate(self) -> float:
        return Fitness(self.layout)  # 적합도 계산
```

| 항목 | 설명 |
|------|------|
| **표현** | 길이 30 배열 (26글자 + 4패딩) |
| **의미** | layout[i] = 위치i에 있는 글자 인덱스 |
| **예** | [0, 1, 2, ..., 25, 26, 27, 28, 29] |

### 3.2 GA 연산자

| 연산 | 설명 | 구현 |
|------|------|------|
| **선택** | 토너먼트: 3개 무작위 중 최고 적합도 선택 | `GAOperators.select()` |
| **교차** | OX (Order Crossover) 또는 PMX | `GAOperators.crossover()` |
| **돌연변이** | 두 위치 스왑 | `GAOperators.mutate()` |

### 3.3 실행 루프

```
초기 population 생성 (pop_size=20)
  ↓
for gen in range(max_gen):
    1. 모든 개체 evaluate()
    2. select() → parents
    3. crossover(parent1, parent2) → children
    4. mutate(child) → new_child
    5. replace population
  ↓
return best_individual
```

| 모듈 | 역할 | 파일 | 상태 |
|------|------|------|------|
| `ga_core.py` | Individual, Operators | `GA/ga_integrated.py` | ⚠️ 평가 함수 오류 |
| `ga_runner.py` | 실행 루프 | `GA/ga_integrated.py` | ✓ 완료 |

---

## 4. 레이어 4: 실행 & 시각화

| 모듈 | 역할 |
|------|------|
| `experiment.py` | config 로드, 여러 실험 자동 실행 |
| `visualize.py` | 키보드 배치 시각화, heatmap |

---

## 5. 현재 구현 상태 분석

### ✓ 완료된 것
- ✓ W (공기 행렬) 로드
- ✓ L (라플라시안) 계산
- ✓ GA 기본 루프
- ✓ 초기 population 생성

### ⚠️ 문제점 (설계와 불일치)

| 문제 | 현재 | 원래 의도 | 파일 |
|------|------|---------|------|
| **distance() 메서드** | 인덱스 오류 | 2D 좌표→거리 | `models/keyboard_layout.py` |
| **손가락 정보** | 미사용 | hand, finger 활용 | `models/keyboard_layout.py` |
| **f2, f3, f4** | 1.0으로 고정 | 실제 테이블 조회 | `GA/ga_integrated.py` |
| **위치↔글자 매핑** | 혼동 | layout[pos]=char명확화 | `GA/ga_integrated.py` |

---

## 6. 수정 계획

### Phase 1: 기초 모델 수정
1. `keyboard_layout.py`: distance() 메서드 완정
2. `keyboard_layout.py`: 위치 정보 구조화 (row, col, hand, finger)

### Phase 2: 피로도 평가 함수
1. `fatigue.py`: f2, f3, f4 테이블 정의
2. `GA/ga_integrated.py`: evaluate() 함수 재구현
   - f_step 정확한 계산
   - 모든 글자쌍 iteration
   - C_fatigue + C_lap 합산

### Phase 3: GA 평가 정확성
1. 초기 배치 검증
2. 적합도 정렬 테스트
3. 수렴 곡선 확인

### Phase 4: 시각화 & 분석
1. 최적 배치 시각화
2. 피로도 heatmap
3. 기존 배열과 비교

---

## 7. 실행 명령

```bash
# 1단계: 모델 수정 검증
python3 tests/test_keyboard_layout.py

# 2단계: 피로도 함수 검증
python3 tests/test_fatigue_model.py

# 3단계: GA 실행
python3 ga_runner_corrected.py

# 4단계: 결과 시각화
python3 notebooks/04_results_visualization.ipynb
```
