# GA (Genetic Algorithm) 폴더 완성 가이드

## 📋 개요

`GA/` 폴더는 **유전 알고리즘을 이용한 키보드 배열 최적화**를 구현합니다.

### 핵심 구성 요소

```
GA/
├── __init__.py                  # 모듈 export
└── genetic_algorithm.py         # GA 메인 구현
    ├── Individual              # 개체(해) 표현
    ├── GAOperators             # 선택, 교차, 돌연변이 연산자
    ├── Initializer             # 초기 집단 생성 전략
    └── GARunner                # GA 실행 엔진
```

---

## 🔧 클래스 상세 설명

### 1. `Individual` - 개체(해) 표현

**역할**: 하나의 키보드 배열을 표현

```python
ind = Individual(
    layout=np.array([0, 1, 2, ...]),      # 순열: 위치별 글자 인덱스
    keyboard=keyboard,                     # Keyboard 객체
    fatigue_calc=fatigue_func,            # 피로도 계산 함수
    co_occurrence_matrix=W,               # 공기 행렬
    laplacian_weight=0.5                  # 라플라시안 페널티 가중치
)
```

**주요 메서드**:

| 메서드 | 역할 |
|--------|------|
| `evaluate()` | 적합도 계산 (1 / (피로도 + ε)) |
| `calculate_total_fatigue()` | 전체 피로도: C_total + α·C_lap |
| `_calculate_step_fatigue()` | 단계적 피로도: Σ W_ij · f_step(i,j,M) |
| `_calculate_laplacian_penalty()` | 라플라시안 페널티 |
| `copy()` | 깊은 복사 |

---

### 2. `GAOperators` - 진화 연산자

#### 2.1 선택 (Selection)

```python
# 토너먼트 선택
parent = GAOperators.tournament_selection(population, tournament_size=3)

# 룰렛 휠 선택 (적합도 비례)
parent = GAOperators.roulette_wheel_selection(population)
```

#### 2.2 교차 (Crossover)

**PMX (Partially Matched Crossover)**: 순열 순서 유지
```python
child1, child2 = GAOperators.pmx_crossover(parent1, parent2)
```

**OX (Order Crossover)**: 순서 중심 교차
```python
child1, child2 = GAOperators.ox_crossover(parent1, parent2)
```

#### 2.3 돌연변이 (Mutation)

```python
# 스왑 돌연변이 (위치 교환)
mutated = GAOperators.swap_mutation(individual, mutation_rate=0.1)

# 역순 돌연변이 (구간 반전)
mutated = GAOperators.inversion_mutation(individual, mutation_rate=0.05)

# Lévy flight 돌연변이 (대규모 변화 - 국부 최적해 탈출용)
mutated = GAOperators.levy_flight_mutation(individual, mutation_rate=0.02)
```

---

### 3. `Initializer` - 초기 집단 생성

#### 3.1 무작위 초기화
```python
population = Initializer.random_initialization(
    n_individuals=50,
    n_genes=26,
    keyboard=keyboard,
    fatigue_calc=fatigue_func,
    co_occurrence_matrix=W
)
```

#### 3.2 Seed 기반 초기화
```python
seed_layouts = [
    standard_dubeolsik,  # 기존 두벌식
    np.arange(26)        # Identity
]
population = Initializer.seeded_initialization(
    n_individuals=50,
    n_genes=26,
    keyboard=keyboard,
    fatigue_calc=fatigue_func,
    seed_layouts=seed_layouts,
    co_occurrence_matrix=W
)
```

#### 3.3 스펙트럴 초기화 (⭐ 권장)
```python
population = Initializer.spectral_initialization(
    n_individuals=50,
    n_genes=26,
    keyboard=keyboard,
    fatigue_calc=fatigue_func,
    co_occurrence_matrix=W,
    laplacian_matrix=L,
    n_eigenvectors=3,
    laplacian_weight=0.3
)
```

**장점**:
- 라플라시안 고유벡터로부터 "자주 함께 쓰이는 글자군" 정보 활용
- 비슷한 고유벡터 값을 가진 글자들을 인접하게 배치
- 초기 해의 품질이 높아 수렴 속도 향상

---

### 4. `GARunner` - GA 실행 엔진

```python
runner = GARunner(
    population_size=50,          # 집단 크기
    max_generations=100,         # 최대 세대
    mutation_rate=0.1,           # 돌연변이 확률
    crossover_rate=0.8,          # 교차 확률
    elite_size=5,                # 엘리트 (다음 세대 직접 전달)
    selection_type='tournament', # 'tournament' or 'roulette'
    crossover_type='pmx'         # 'pmx' or 'ox'
)
```

**실행**:
```python
best_individual, final_population = runner.run(
    population=initial_population,
    patience=20,  # 20세대 개선 없으면 조기 종료
    verbose=True
)

# 통계 조회
stats = runner.get_statistics()
# {
#   'best_fitness_history': [...],
#   'avg_fitness_history': [...],
#   'final_best_fitness': 0.00234,
#   'generations_run': 87
# }
```

---

## 📊 사용 예제

### 기본 사용법

```python
from GA.genetic_algorithm import Individual, Initializer, GARunner
from datas.data import load_co_occurrence_matrix
import numpy as np

# 1. 데이터 준비
co_occurrence = load_co_occurrence_matrix(csv_weight_file='datas/all_raw_weight.csv')
D = np.diag(co_occurrence.sum(axis=1))
laplacian = D - co_occurrence

# 2. 초기 집단 생성 (스펙트럴 초기화)
population = Initializer.spectral_initialization(
    n_individuals=50,
    n_genes=26,
    keyboard=keyboard,
    fatigue_calc=fatigue_model().set_f1,
    co_occurrence_matrix=co_occurrence,
    laplacian_matrix=laplacian,
    laplacian_weight=0.5
)

# 3. GA 실행
runner = GARunner(
    population_size=50,
    max_generations=100,
    mutation_rate=0.15
)

best_layout, final_pop = runner.run(population, patience=20, verbose=True)

# 4. 결과
print(f"최적 배열: {best_layout.layout}")
print(f"피로도: {best_layout._fatigue:.4f}")
print(f"적합도: {best_layout.evaluate():.6f}")
```

### 전체 통합 실행

`ga_runner_example.py` 실행:

```bash
python ga_runner_example.py
```

함수 호출:
```python
from ga_runner_example import run_keyboard_optimization, visualize_optimization

best_layout, ga_runner, final_pop = run_keyboard_optimization(
    population_size=50,
    max_generations=100,
    mutation_rate=0.15,
    laplacian_weight=0.5,
    initialization_type='spectral',
    corpus_file=None,
    verbose=True
)

# 시각화
visualize_optimization(ga_runner)
```

---

## 🧬 알고리즘 흐름

```
┌─────────────────────────────────────────┐
│   초기 집단 생성 (50개)                 │
│   - 스펙트럴 기반 정렬                  │
│   - 무작위 섭동으로 다양성 확보         │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────▼──────────┐
        │    세대 t            │
        │   (최대 100)         │
        └──────────┬───────────┘
                   │
        ┌──────────▼──────────────┐
        │  1. 적합도 평가         │
        │  fitness = 1/(C_total*) │
        └──────────┬──────────────┘
                   │
        ┌──────────▼──────────────────────┐
        │  2. 엘리트 보존 (상위 5개)      │
        └──────────┬──────────────────────┘
                   │
        ┌──────────▼──────────────────────────────┐
        │  3. 새로운 개체 생성 (45개)              │
        │    ├─ 토너먼트 선택 (2개 부모)           │
        │    ├─ PMX 교차 (80% 확률)               │
        │    └─ 돌연변이 (15% 확률)               │
        │        ├─ 스왑 (70%)                    │
        │        ├─ 역순 (20%)                    │
        │        └─ Lévy flight (10%)             │
        └──────────┬──────────────────────────────┘
                   │
        ┌──────────▼─────────────────┐
        │  4. 적합도 기록             │
        │  (best, avg)                │
        └──────────┬─────────────────┘
                   │
        ┌──────────▼────────────────────────┐
        │  5. 조기 종료 확인                 │
        │  (20세대 개선 없음?)              │
        │  ├─ Yes: 종료                     │
        │  └─ No: 다음 세대                │
        └──────────┬────────────────────────┘
                   │
                   └──► (반복 또는 종료)
```

---

## 📈 피로도 계산 구조

```
C_total*(M) = C_total(M) + α·C_lap(M)

C_total(M) = Σ_{i,j} W_ij · f_step(i,j,M)

f_step(i,j,M) = distance(i,j;M) × f2(i,j;M) × f3(i,j;M) × f4(i,j;M)
                ↓              ↓              ↓            ↓
              거리      손가락 피로     방향 피로    조합 피로


C_lap(M) = Σ_{i,j} W_ij · (coord_i - coord_j)²
           └─→ 자주 함께 쓰이는 글자가 멀리 떨어져 있으면 페널티
```

---

## 🎯 주요 특징

### 1. **다양한 선택 전략**
- 토너먼트: 국부 탐색 강화
- 룰렛 휠: 다양성 유지

### 2. **순열 친화적 교차/돌연변이**
- PMX, OX: 순열 유효성 보장
- 스왑, 역순, Lévy flight: 다양한 이웃 탐색

### 3. **라플라시안 활용**
- 초기화: 스펙트럴 정렬로 좋은 시작점
- 평가: 페널티로 연속 사용 글자 인접성 강화

### 4. **적응형 하이퍼파라미터**
```python
runner = GARunner(
    population_size=50,    # ↑ 클수록 다양성 ↑, 수렴 느림
    mutation_rate=0.15,    # ↑ 크면 탐색성 ↑, 수렴성 ↓
    crossover_rate=0.8,    # ↑ 크면 교배 많음
    elite_size=5,          # ↑ 크면 수렴성 ↑, 다양성 ↓
)
```

---

## 🚀 성능 최적화 팁

| 상황 | 추천 설정 |
|------|---------|
| 빠른 수렴 원할 때 | `elite_size↑`, `mutation_rate↓`, `spectral_init` |
| 다양한 해 탐색 | `mutation_rate↑`, `crossover_rate↓`, `random_init` |
| 초기 해 품질 좋을 때 | `seeded_init`, `laplacian_weight↑` |
| 국부 최적해 탈출 | `levy_flight` 활성화, `tournament_size↓` |

---

## 🔗 연관 모듈

- **`models/keyboard_layout.py`**: 키보드 구조, 거리 계산
- **`models/fatigue.py`**: 피로도 모델 (f1~f4)
- **`models/rw_laplacian.py`**: 라플라시안 계산
- **`datas/data.py`**: 공기 행렬 로드

---

## 📝 라이선스 & 참고

이 구현은 다음을 기반으로 합니다:

1. **교차 연산자**: PMX (Goldberg & Lingle, 1985), OX (Davis, 1985)
2. **라플라시안 스펙트럴 방법**: Graph Laplacian 고유분석
3. **Lévy flight**: 강화 탐색을 위한 확률적 기법

---

## 📞 문제 해결

### Q: 적합도가 전혀 개선되지 않음
**A**: 
- `laplacian_weight` 조정 (0.1 ~ 0.5)
- `mutation_rate` 증가
- `population_size` 증가

### Q: 수렴이 너무 느림
**A**:
- `elite_size` 증가
- `mutation_rate` 감소
- `initialization_type='spectral'` 사용

### Q: 메모리 부족
**A**:
- `population_size` 감소
- `max_generations` 감소

