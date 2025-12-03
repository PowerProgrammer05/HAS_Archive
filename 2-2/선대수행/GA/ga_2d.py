"""
⚡ 개선된 GA - 2D 키보드 배열 기반
"""

import numpy as np
from typing import List, Tuple

class Individual2D:
    """2D 키보드 배열 기반 개체"""
    
    def __init__(self, layout_2d: np.ndarray, co_occurrence=None, lap_weight=0.0):
        """
        Args:
            layout_2d: (행, 열) 배열 - 각 셀에 글자 인덱스 저장
                      예: [[0,1,2,...], [10,11,12,...], [...]]
            co_occurrence: 공기 행렬 W
        """
        self.layout_2d = np.array(layout_2d, dtype=int)  # 2D 배열
        self.shape = self.layout_2d.shape  # (rows, cols)
        self.co_occurrence = co_occurrence
        self.lap_weight = lap_weight
        self._fitness = None
        self._fatigue = None
    
    def get_position(self, char_idx: int) -> Tuple[int, int]:
        """글자 인덱스의 (row, col) 위치 반환"""
        positions = np.where(self.layout_2d == char_idx)
        if len(positions[0]) > 0:
            return (positions[0][0], positions[1][0])
        return None
    
    def distance(self, char_i: int, char_j: int) -> float:
        """두 글자 사이의 거리 계산"""
        pos_i = self.get_position(char_i)
        pos_j = self.get_position(char_j)
        
        if pos_i is None or pos_j is None:
            return 0.0
        
        # 유클리드 거리
        row_diff = pos_i[0] - pos_j[0]
        col_diff = pos_i[1] - pos_j[1]
        
        # 거리에 가중치 (행 이동이 더 힘들다고 가정)
        dist = np.sqrt(row_diff**2 + (col_diff**2 * 0.8))
        return dist
    
    def evaluate(self):
        """적합도 = 1 / (피로도 + ε)"""
        if self._fitness is None:
            self._fatigue = self._calc_fatigue()
            self._fitness = 1.0 / (self._fatigue + 1e-6)
        return self._fitness
    
    def _calc_fatigue(self) -> float:
        """피로도 계산 - 공기 행렬 기반"""
        if self.co_occurrence is None:
            return 1.0
        
        fatigue = 0.0
        W = self.co_occurrence
        
        # 상위 빈도만 계산 (속도 최적화)
        for i in range(min(10, len(W))):
            top_j_indices = np.argsort(W[i])[-5:]  # 상위 5개
            for j in top_j_indices:
                if W[i, j] > 0:
                    dist = self.distance(i, j)
                    fatigue += W[i, j] * dist
        
        return fatigue
    
    def copy(self):
        """복사"""
        return Individual2D(
            self.layout_2d.copy(), 
            self.co_occurrence, 
            self.lap_weight
        )


class GAOperators2D:
    """2D 배열용 GA 연산자"""
    
    @staticmethod
    def select(population):
        """토너먼트 선택"""
        idx = np.random.choice(len(population), 3, replace=False)
        best_idx = max(idx, key=lambda i: population[i].evaluate())
        return population[best_idx].copy()
    
    @staticmethod
    def crossover_2d(p1: Individual2D, p2: Individual2D) -> Tuple[Individual2D, Individual2D]:
        """
        2D 교차 - 행 단위 교환
        """
        layout1 = p1.layout_2d.copy()
        layout2 = p2.layout_2d.copy()
        n_rows = layout1.shape[0]
        
        # 행 단위 교환점
        point = np.random.randint(1, n_rows)
        
        c1_layout = np.vstack([layout1[:point], layout2[point:]])
        c2_layout = np.vstack([layout2[:point], layout1[point:]])
        
        c1 = p1.copy()
        c1.layout_2d = c1_layout
        c1._fitness = None
        
        c2 = p2.copy()
        c2.layout_2d = c2_layout
        c2._fitness = None
        
        return c1, c2
    
    @staticmethod
    def mutate_2d(ind: Individual2D, rate=0.1) -> Individual2D:
        """
        2D 돌연변이 - 셀 스왑
        """
        if np.random.random() < rate:
            layout = ind.layout_2d
            # 두 위치를 무작위로 선택
            r1, c1 = np.random.randint(0, layout.shape[0]), np.random.randint(0, layout.shape[1])
            r2, c2 = np.random.randint(0, layout.shape[0]), np.random.randint(0, layout.shape[1])
            
            # 스왑
            layout[r1, c1], layout[r2, c2] = layout[r2, c2], layout[r1, c1]
            ind._fitness = None
        
        return ind


class GARunner2D:
    """2D GA 실행기"""
    
    def __init__(self, pop_size=20, generations=50, mut_rate=0.1):
        self.pop_size = pop_size
        self.generations = generations
        self.mut_rate = mut_rate
        self.history = []
    
    def run(self, population: List[Individual2D], verbose=False):
        """GA 실행"""
        pop = [ind.copy() for ind in population]
        best_ever = None
        best_fitness = -np.inf
        
        for gen in range(self.generations):
            # 평가
            fitness = [ind.evaluate() for ind in pop]
            max_fit = max(fitness)
            avg_fit = np.mean(fitness)
            self.history.append({'max': max_fit, 'avg': avg_fit})
            
            if max_fit > best_fitness:
                best_fitness = max_fit
                best_ever = pop[np.argmax(fitness)].copy()
            
            if verbose:
                print(f"Gen {gen+1}: max={max_fit:.4f}, avg={avg_fit:.4f}")
            
            # 새 세대
            new_pop = []
            
            # 엘리트 (상위 2개)
            elite_idx = np.argsort(fitness)[-2:]
            for idx in elite_idx:
                new_pop.append(pop[idx].copy())
            
            # 나머지
            while len(new_pop) < self.pop_size:
                p1 = GAOperators2D.select(pop)
                p2 = GAOperators2D.select(pop)
                
                if np.random.random() < 0.8:  # 교차 확률
                    c1, c2 = GAOperators2D.crossover_2d(p1, p2)
                else:
                    c1, c2 = p1, p2
                
                GAOperators2D.mutate_2d(c1, self.mut_rate)
                GAOperators2D.mutate_2d(c2, self.mut_rate)
                
                new_pop.append(c1)
                if len(new_pop) < self.pop_size:
                    new_pop.append(c2)
            
            pop = new_pop[:self.pop_size]
        
        return best_ever, pop
