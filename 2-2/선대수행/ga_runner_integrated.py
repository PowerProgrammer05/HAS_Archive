"""
통합 GA 예제 - 실제 모델과 CSV 데이터 사용
"""

import numpy as np
import sys
from pathlib import Path

parent_path = Path(__file__).parent
sys.path.insert(0, str(parent_path))

from GA.ga_integrated import Individual2D_Full, GARunner2D_Full
from datas.data import load_co_occurrence_matrix, load_combined_cooccurrence, load_combined_frequency, korean_list
from models.keyboard_layout_corrected import KeyboardLayout
from models.fatigue_corrected import FatigueModel
from models.rw_laplacian import laplacian_spectral


def create_initial_population(pop_size, n_chars=26, keyboard_rows=3, keyboard_cols=10):
    """초기 모집단 생성"""
    population = []
    total_cells = keyboard_rows * keyboard_cols
    # Define allowed (usable) cell indices where actual keys can go.
    # For the 3x10 layout the user wants the following empty spots:
    # - 2nd row (row index 1) last 1 cell (col 9)
    # - 3rd row (row index 2) last 3 cells (cols 7,8,9)
    # So usable flat indices are: 0-9, 10-18, 20-26 (total 26 cells)
    allowed_positions = list(range(0, 10)) + list(range(10, 19)) + list(range(20, 27))

    for _ in range(pop_size):
        # start with all cells empty (-1)
        layout = np.full((keyboard_rows, keyboard_cols), -1, dtype=int)

        # random assignment of 26 characters (0..25) into allowed positions
        perm_chars = np.random.permutation(n_chars)
        for k, flat_pos in enumerate(allowed_positions):
            r = flat_pos // keyboard_cols
            c = flat_pos % keyboard_cols
            layout[r, c] = int(perm_chars[k])

        population.append(layout)
    return population


def visualize_keyboard(layout_2d, korean_chars=korean_list):
    """한글 자모로 키보드를 시각화하여 출력"""
    print("\n    ╔════════════════════════════════════════╗")
    print("    ║         최적화된 한글 키보드            ║")
    print("    ╚════════════════════════════════════════╝\n")
    
    for row_idx, row in enumerate(layout_2d):
        row_str = "     "
        for col_idx, char_idx in enumerate(row):
            if char_idx == -1:
                row_str += "  ·   "
            else:
                # char_idx is 0-25, map to korean_chars
                if 0 <= char_idx < len(korean_chars):
                    char = korean_chars[int(char_idx)]
                    row_str += f"  {char}   "
                else:
                    row_str += "  ?   "
        print(row_str)
    print()



def run_integrated_ga():
    """통합 GA 실행"""
    
    print("=" * 60)
    print("통합 GA: Laplacian + 피로도 모델 + 키보드 레이아웃")
    print("=" * 60)
    
    # 1. 데이터 로드
    print("\n[1] 데이터 로드...")
    # Combine `all_raw_weight.csv` and `high_raw_weight.csv` giving `high` more influence
    alpha = 0.6  # weight for the `high` dataset; increase toward 1.0 to prioritize high dataset
    print(f"    ✓ combining weights with alpha={alpha} (high dataset weight)")
    
    # Load combined co-occurrence (자모 쌍 빈도)
    co_occurrence = load_combined_cooccurrence('datas/all_raw_weight.csv', 'datas/high_raw_weight.csv', alpha=alpha)
    if co_occurrence is None:
        print("    ✗ combined co-occurrence load failed — falling back to single CSV load")
        try:
            co_occurrence = load_co_occurrence_matrix('datas/all_raw_weight.csv')
        except Exception:
            co_occurrence = None

    if co_occurrence is None:
        print("    ✗ co-occurrence 로드 실패: using random test matrix")
        co_occurrence = np.random.rand(26, 26)
        co_occurrence = (co_occurrence + co_occurrence.T) / 2
        co_occurrence = co_occurrence * 10000
    else:
        print(f"    ✓ Co-occurrence 행렬: {co_occurrence.shape}")
    
    # Load combined frequency (개별 자모 출현 빈도)
    frequency_vec = load_combined_frequency('datas/all_count.csv', 'datas/high_count.csv', alpha=alpha)
    if frequency_vec is None:
        print("    ✗ combined frequency load failed")
        frequency_vec = np.ones(26) / 26
    else:
        print(f"    ✓ 개별 자모 빈도 벡터 로드 완료")
    
    print(f"    ✓ 한글 자모: {len(korean_list)}개")
    
    # 2. 모델 초기화
    print("\n[2] 모델 초기화...")
    keyboard = KeyboardLayout()
    fatigue = FatigueModel()
    laplacian = laplacian_spectral(co_occurrence)
    print("    ✓ Keyboard, fatigue_model, laplacian_spectral 생성 완료")
    
    # 3. 초기 모집단 생성
    print("\n[3] 초기 모집단 생성...")
    layouts = create_initial_population(20, n_chars=26, keyboard_rows=3, keyboard_cols=10)
    
    population = []
    for layout in layouts:
        ind = Individual2D_Full(
            layout_2d=layout,
            keyboard=keyboard,
            fatigue_model_obj=fatigue,
            co_occurrence=co_occurrence,
            frequency_vec=frequency_vec,
            laplacian_spectral_obj=laplacian,
            lap_weight=0.3,
            freq_weight=1.0
        )
        population.append(ind)
    
    print(f"    ✓ 모집단 크기: {len(population)}")
    
    # 4. GA 실행
    print("\n[4] GA 실행...")
    runner = GARunner2D_Full(pop_size=20, generations=30, mut_rate=0.1)
    best_ind, final_pop = runner.run(population, verbose=True)
    
    # 5. 결과 분석
    print("\n[5] 결과 분석...")
    print(f"    최고 적합도: {best_ind.evaluate():.6f}")
    print(f"    개별 자모 빈도 비용: {best_ind._calc_freq_cost():.2f}")
    print(f"    총 피로도 (쌍): {best_ind._calc_fatigue_total():.2f}")
    print(f"    라플라시안 페널티: {best_ind._calc_fatigue_laplacian():.2f}")
    
    print("\n    최적 배열 (숫자 인덱스 1~26):")
    # Pretty-print: show empty cells (value -1) as blanks for clarity
    display = best_ind.layout_2d.copy()
    # Add 1 to display indices as 1~26 (not 0~25)
    display_plus_one = np.where(display == -1, -1, display + 1)
    display_str = np.where(display_plus_one == -1, '  ', display_plus_one.astype(str))
    for row in display_str:
        print('     ' + ' '.join(row))
    
    # 한글 자모로 시각화
    visualize_keyboard(best_ind.layout_2d, korean_list)
    
    print("\n    세대별 진화 (마지막 10세대):")
    for i, data in enumerate(runner.history[-10:]):
        print(f"    Gen {i+21}: max={data['max']:.4f}, avg={data['avg']:.4f}")
    
    return best_ind


if __name__ == "__main__":
    best = run_integrated_ga()
