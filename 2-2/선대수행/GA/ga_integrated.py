"""
통합 GA - 2D 키보드 배열 + Laplacian + 피로도 모델
실제 models와 CSV 데이터를 활용한 완전한 구현
"""

import numpy as np
import pandas as pd
from typing import List, Tuple
import sys
from pathlib import Path

parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

from models.keyboard_layout_corrected import KeyboardLayout
from models.fatigue_corrected import FatigueModel
from models.rw_laplacian import laplacian_spectral


class Individual2D_Full:
    """
    완전한 2D 키보드 배열 개체
    - Laplacian 스펙트럼
    - 피로도 모델 (f1~f4)
    - 실제 키보드 레이아웃
    - 개별 자모 빈도 비용
    """
    
    def __init__(self, 
                 layout_2d: np.ndarray,
                 keyboard: KeyboardLayout,
                 fatigue_model_obj: FatigueModel,
                 co_occurrence: np.ndarray,
                 frequency_vec: np.ndarray = None,
                 laplacian_spectral_obj: laplacian_spectral = None,
                 lap_weight: float = 0.3,
                 freq_weight: float = 1.0):
        """
        Args:
            layout_2d: (행, 열) 글자 배열
            keyboard: Keyboard 객체 (거리 계산)
            fatigue_model_obj: fatigue_model 객체 (f1~f4)
            co_occurrence: 공기 행렬 W (자모 쌍)
            frequency_vec: 개별 자모 출현 빈도 벡터 (26,)
            laplacian_spectral_obj: 라플라시안 스펙트럼
            lap_weight: 라플라시안 페널티 가중치
            freq_weight: 개별 자모 빈도 비용 가중치
        """
        self.layout_2d = np.array(layout_2d, dtype=int)
        self.shape = self.layout_2d.shape
        self.keyboard = keyboard
        self.fatigue_model = fatigue_model_obj
        self.co_occurrence = co_occurrence
        self.frequency_vec = frequency_vec if frequency_vec is not None else np.ones(26) / 26
        self.laplacian_spectral = laplacian_spectral_obj
        self.lap_weight = lap_weight
        self.freq_weight = freq_weight
        
        self._fitness = None
        self._fatigue_total = None
        self._fatigue_lap = None
        self._freq_cost = None
    
    def get_position_in_keyboard(self, char_idx: int) -> Tuple[int, int]:
        """2D 배열에서 글자의 위치 반환"""
        positions = np.where(self.layout_2d == char_idx)
        if len(positions[0]) > 0:
            return (positions[0][0], positions[1][0])
        return None
    
    def get_keyboard_position(self, row: int, col: int) -> Tuple[int, int]:
        """2D 배열의 (row, col) → 실제 키보드 위치"""
        # layout_2d[row, col]이 실제 키보드의 어디인지 매핑
        # 예: (0,0) → 인덱스 0, (0,1) → 인덱스 1, (1,0) → 인덱스 10 등
        flat_idx = row * self.layout_2d.shape[1] + col
        return flat_idx
    
    def distance_in_keyboard(self, char_i: int, char_j: int) -> float:
        """
        두 글자 사이의 실제 키보드 거리 (Keyboard.distance 사용)
        """
        pos_i = self.get_position_in_keyboard(char_i)
        pos_j = self.get_position_in_keyboard(char_j)
        
        if pos_i is None or pos_j is None:
            return 0.0
        
        # 2D 배열 위치를 일차원 인덱스로 변환
        idx_i = self.get_keyboard_position(pos_i[0], pos_i[1])
        idx_j = self.get_keyboard_position(pos_j[0], pos_j[1])
        
        # Convert flat idx to (row,col) using keyboard position table
        # Our KeyboardLayout.distance expects (row,col) tuples, so call with positions
        try:
            kb_pos_i = (pos_i[0], pos_i[1])
            kb_pos_j = (pos_j[0], pos_j[1])
            dist = self.keyboard.distance(kb_pos_i, kb_pos_j)
        except Exception:
            dist = np.sqrt((pos_i[0] - pos_j[0])**2 + (pos_i[1] - pos_j[1])**2)
        
        return dist
    
    def evaluate(self) -> float:
        """적합도 = 1 / (피로도 + ε)"""
        if self._fitness is None:
            self._freq_cost = self._calc_freq_cost()
            self._fatigue_total = self._calc_fatigue_total()
            self._fatigue_lap = self._calc_fatigue_laplacian()
            total_cost = (self.freq_weight * self._freq_cost + 
                         self._fatigue_total + 
                         self.lap_weight * self._fatigue_lap)
            self._fitness = 1.0 / (total_cost + 1e-6)
        return self._fitness
    
    def _calc_freq_cost(self) -> float:
        """
        개별 자모 빈도 비용 = Σ freq[i] · position_cost[i]
        자주 나타나는 자모가 피로가 많은 위치에 있으면 페널티
        """
        freq_cost = 0.0
        for char_idx in range(26):
            if self.frequency_vec[char_idx] <= 0:
                continue
            
            pos = self.get_position_in_keyboard(char_idx)
            if pos is None:
                continue
            
            # 키보드의 중심(row=1, col=4.5)으로부터의 거리 제곱을 위치 비용으로 사용
            # 중심에서 멀수록 높은 비용
            center_row, center_col = 1.0, 4.5
            position_cost = ((pos[0] - center_row) ** 2 + (pos[1] - center_col) ** 2)
            freq_cost += self.frequency_vec[char_idx] * position_cost
        
        return freq_cost
    
    def _calc_fatigue_total(self) -> float:
        """
        총 피로도 = Σ W_ij · f_step(i,j)
        f_step = distance × f2 × f3 × f4
        """
        W = self.co_occurrence
        total_fatigue = 0.0

        n_chars = min(26, W.shape[0])
        # Full pairwise computation over the 26 characters (or available size)
        for i in range(n_chars):
            for j in range(n_chars):
                w_ij = W[i, j]
                if w_ij <= 0:
                    continue

                # positions in layout
                pos_i = self.get_position_in_keyboard(i)
                pos_j = self.get_position_in_keyboard(j)
                if pos_i is None or pos_j is None:
                    continue

                # distance (KeyboardLayout.distance takes (row,col) tuples)
                dist = self.distance_in_keyboard(i, j)

                # finger/hand info via keyboard model
                pos_i_idx = self.get_keyboard_position(pos_i[0], pos_i[1])
                pos_j_idx = self.get_keyboard_position(pos_j[0], pos_j[1])
                hand_i, finger_i = self.keyboard.get_hand_finger(pos_i_idx)
                hand_j, finger_j = self.keyboard.get_hand_finger(pos_j_idx)

                # f2, f3, f4 via fatigue model
                try:
                    f2 = self.fatigue_model.get_f2_cost(finger_i, finger_j)
                except Exception:
                    f2 = 1.0
                try:
                    f3 = self.fatigue_model.get_f3_cost(hand_i, hand_j, pos_i[0], pos_j[0])
                except Exception:
                    f3 = 1.0
                try:
                    f4 = self.fatigue_model.get_f4_cost(finger_i, finger_j)
                except Exception:
                    f4 = 1.0

                f_step = dist * f2 * f3 * f4
                total_fatigue += w_ij * f_step

        return total_fatigue
    
    def _calc_fatigue_laplacian(self) -> float:
        """
        라플라시안 기반 페널티 = x^T L x
        여기서 x는 현재 배치(permutation vector)에 대한 좌표 벡터
        
        자주 함께 쓰이는 글자(높은 W[i,j])가 멀리 떨어져 있으면 높은 페널티
        Laplacian L을 통해 전체 그래프 구조의 smoothness를 평가
        """
        if self.laplacian_spectral is None:
            # fallback to simple grid distance if laplacian not available
            return self._calc_fatigue_laplacian_grid()

        # Compute Laplacian matrix
        L = self.laplacian_spectral.compute_laplacian(normalized=True)
        
        # Create coordinate vector: for each character i, store its (row, col) position
        # We'll use a linear combination of row and col coordinates
        n_chars = 26
        coord_x = np.zeros(n_chars)
        coord_y = np.zeros(n_chars)
        
        for char_idx in range(n_chars):
            pos = self.get_position_in_keyboard(char_idx)
            if pos is not None:
                coord_x[char_idx] = pos[1]  # column
                coord_y[char_idx] = pos[0]  # row
            else:
                # Character not placed; use neutral coordinate
                coord_x[char_idx] = 0
                coord_y[char_idx] = 0
        
        # Compute quadratic form: x^T L x + y^T L y
        # This penalizes arrangements where frequently-co-occurring characters are far apart
        try:
            penalty_x = coord_x @ L @ coord_x
            penalty_y = coord_y @ L @ coord_y
            penalty = penalty_x + penalty_y
        except Exception as e:
            # Fallback to grid distance if Laplacian computation fails
            penalty = self._calc_fatigue_laplacian_grid()
        
        return max(0, penalty)  # Ensure non-negative
    
    def _calc_fatigue_laplacian_grid(self) -> float:
        """
        Fallback: 간단한 grid 거리 기반 라플라시안 페널티
        라플라시안 객체가 없을 때 사용
        """
        W = self.co_occurrence
        penalty = 0.0
        n_chars = min(26, W.shape[0])

        for i in range(n_chars):
            for j in range(n_chars):
                w_ij = W[i, j]
                if w_ij <= 0:
                    continue
                pos_i = self.get_position_in_keyboard(i)
                pos_j = self.get_position_in_keyboard(j)
                if pos_i is None or pos_j is None:
                    continue
                dist_sq = (pos_i[0] - pos_j[0])**2 + (pos_i[1] - pos_j[1])**2
                penalty += w_ij * dist_sq

        return penalty
    
    def copy(self):
        """복사"""
        return Individual2D_Full(
            self.layout_2d.copy(),
            self.keyboard,
            self.fatigue_model,
            self.co_occurrence,
            self.frequency_vec.copy() if self.frequency_vec is not None else None,
            self.laplacian_spectral,
            self.lap_weight,
            self.freq_weight
        )


class GAOperators2D_Full:
    """통합 2D GA 연산자"""
    
    @staticmethod
    def select(population):
        """토너먼트 선택"""
        idx = np.random.choice(len(population), 3, replace=False)
        best_idx = max(idx, key=lambda i: population[i].evaluate())
        return population[best_idx].copy()
    
    @staticmethod
    def crossover_2d(p1: Individual2D_Full, p2: Individual2D_Full) -> Tuple[Individual2D_Full, Individual2D_Full]:
        """2D 교차 - 행 단위 교환"""
        # Preserve uniqueness of characters by performing an order-preserving
        # crossover on the sequence of usable (non -1) cells. This avoids
        # creating duplicates or dropping characters.
        layout1 = p1.layout_2d.copy()
        layout2 = p2.layout_2d.copy()

        # Determine allowed (usable) positions as list of (r,c)
        allowed_pos = [(r, c) for r in range(layout1.shape[0]) for c in range(layout1.shape[1]) if layout1[r, c] != -1]
        n = len(allowed_pos)
        if n <= 1:
            return p1.copy(), p2.copy()

        # Extract sequences of character indices from allowed positions
        seq1 = [int(layout1[r, c]) for (r, c) in allowed_pos]
        seq2 = [int(layout2[r, c]) for (r, c) in allowed_pos]

        # One-point order-preserving crossover (simple OX-like)
        pt = np.random.randint(1, n)

        def ox_child(a, b):
            head = a[:pt]
            tail = [x for x in b if x not in head]
            return head + tail

        child1_seq = ox_child(seq1, seq2)
        child2_seq = ox_child(seq2, seq1)

        # Build child layouts by copying parents and filling allowed positions
        c1_layout = layout1.copy()
        c2_layout = layout2.copy()
        for (r, c), val1, val2 in zip(allowed_pos, child1_seq, child2_seq):
            c1_layout[r, c] = val1
            c2_layout[r, c] = val2

        c1 = p1.copy()
        c1.layout_2d = c1_layout
        c1._fitness = None

        c2 = p2.copy()
        c2.layout_2d = c2_layout
        c2._fitness = None

        return c1, c2
    
    @staticmethod
    def mutate_2d(ind: Individual2D_Full, rate=0.1) -> Individual2D_Full:
        """2D 돌연변이 - 셀 스왑"""
        if np.random.random() < rate:
            layout = ind.layout_2d
            # choose two random usable positions (non -1) to swap
            usable = [(r, c) for r in range(layout.shape[0]) for c in range(layout.shape[1]) if layout[r, c] != -1]
            if len(usable) >= 2:
                (r1, c1), (r2, c2) = tuple(usable[i] for i in np.random.choice(len(usable), 2, replace=False))
                layout[r1, c1], layout[r2, c2] = layout[r2, c2], layout[r1, c1]
                ind._fitness = None

        return ind


class GARunner2D_Full:
    """통합 2D GA 실행기"""
    
    def __init__(self, pop_size=20, generations=50, mut_rate=0.1):
        self.pop_size = pop_size
        self.generations = generations
        self.mut_rate = mut_rate
        self.history = []
    
    def run(self, population: List[Individual2D_Full], verbose=False):
        """GA 실행"""
        pop = [ind.copy() for ind in population]
        best_ever = None
        best_fitness = -np.inf
        
        for gen in range(self.generations):
            fitness = [ind.evaluate() for ind in pop]
            max_fit = max(fitness)
            avg_fit = np.mean(fitness)
            self.history.append({'max': max_fit, 'avg': avg_fit})
            
            if max_fit > best_fitness:
                best_fitness = max_fit
                best_ever = pop[np.argmax(fitness)].copy()
            
            if verbose:
                print(f"Gen {gen+1}: max={max_fit:.4f}, avg={avg_fit:.4f}")
            
            new_pop = []
            
            # 엘리트
            elite_idx = np.argsort(fitness)[-2:]
            for idx in elite_idx:
                new_pop.append(pop[idx].copy())
            
            # 나머지
            while len(new_pop) < self.pop_size:
                p1 = GAOperators2D_Full.select(pop)
                p2 = GAOperators2D_Full.select(pop)
                
                if np.random.random() < 0.8:
                    c1, c2 = GAOperators2D_Full.crossover_2d(p1, p2)
                else:
                    c1, c2 = p1, p2
                
                GAOperators2D_Full.mutate_2d(c1, self.mut_rate)
                GAOperators2D_Full.mutate_2d(c2, self.mut_rate)
                
                new_pop.append(c1)
                if len(new_pop) < self.pop_size:
                    new_pop.append(c2)
            
            pop = new_pop[:self.pop_size]
        
        return best_ever, pop
