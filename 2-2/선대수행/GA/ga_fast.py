"""
⚡ 최적화된 GA (Genetic Algorithm)
- 무한 루프 제거
- 빠른 교차 연산
- 효율적인 평가
"""

import numpy as np
import scipy.linalg as la
from typing import List, Tuple
import sys
from pathlib import Path

parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

from models.keyboard_layout import Keyboard


class Individual:
    """개체 표현"""
    
    def __init__(self, layout, keyboard, co_occurrence=None, lap_weight=0.0):
        self.layout = np.array(layout, dtype=int)
        self.keyboard = keyboard
        self.co_occurrence = co_occurrence
        self.lap_weight = lap_weight
        self._fitness = None
        self._fatigue = None
    
    def evaluate(self):
        """적합도 = 1 / (피로도 + ε)"""
        if self._fitness is None:
            self._fatigue = self._calc_fatigue()
            self._fitness = 1.0 / (self._fatigue + 1e-6)
        return self._fitness
    
    def _calc_fatigue(self):
        """간단한 피로도: 위치별 거리 합"""
        if self.co_occurrence is None:
            return 1.0
        
        fatigue = 0.0
        W = self.co_occurrence
        
        # 빠른 평가 (모든 쌍이 아닌 top 값만)
        for i in range(min(10, len(W))):
            top_j = np.argsort(W[i])[-3:]  # 상위 3개만
            for j in top_j:
                if W[i, j] > 0:
                    pi = np.where(self.layout == i)[0]
                    pj = np.where(self.layout == j)[0]
                    if len(pi) > 0 and len(pj) > 0:
                        try:
                            dist = self.keyboard.distance(pi[0], pj[0])
                        except:
                            dist = 1.0
                        fatigue += W[i, j] * dist
        
        return fatigue
    
    def copy(self):
        """복사"""
        return Individual(self.layout.copy(), self.keyboard, self.co_occurrence, self.lap_weight)


class GAOperators:
    """GA 연산자"""
    
    @staticmethod
    def select(population):
        """토너먼트 선택"""
        idx = np.random.choice(len(population), 3, replace=False)
        best_idx = max(idx, key=lambda i: population[i].evaluate())
        return population[best_idx].copy()
    
    @staticmethod
    def crossover(p1, p2):
        """단순 교차 - O(n)"""
        n = len(p1.layout)
        point = np.random.randint(1, n)
        
        c1_layout = np.concatenate([p1.layout[:point], p2.layout[point:]])
        c2_layout = np.concatenate([p2.layout[:point], p1.layout[point:]])
        
        c1 = p1.copy()
        c1.layout = c1_layout
        c1._fitness = None
        
        c2 = p2.copy()
        c2.layout = c2_layout
        c2._fitness = None
        
        return c1, c2
    
    @staticmethod
    def mutate(ind, rate=0.1):
        """스왑 돌연변이"""
        if np.random.random() < rate:
            n = len(ind.layout)
            i, j = np.random.choice(n, 2, replace=False)
            ind.layout[i], ind.layout[j] = ind.layout[j], ind.layout[i]
            ind._fitness = None
        return ind


class GARunner:
    """GA 실행기"""
    
    def __init__(self, pop_size=20, generations=50, mut_rate=0.1, cross_rate=0.8):
        self.pop_size = pop_size
        self.generations = generations
        self.mut_rate = mut_rate
        self.cross_rate = cross_rate
        self.history = []
    
    def run(self, population, verbose=False):
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
                p1 = GAOperators.select(pop)
                p2 = GAOperators.select(pop)
                
                if np.random.random() < self.cross_rate:
                    c1, c2 = GAOperators.crossover(p1, p2)
                else:
                    c1, c2 = p1, p2
                
                GAOperators.mutate(c1, self.mut_rate)
                GAOperators.mutate(c2, self.mut_rate)
                
                new_pop.append(c1)
                if len(new_pop) < self.pop_size:
                    new_pop.append(c2)
            
            pop = new_pop[:self.pop_size]
        
        return best_ever, pop
