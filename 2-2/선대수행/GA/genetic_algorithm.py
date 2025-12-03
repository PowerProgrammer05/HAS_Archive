import numpy as np
import copy
import scipy.linalg as la
from typing import List, Tuple, Dict, Callable
import sys
from pathlib import Path

# 부모 디렉토리 경로 추가
parent_path = Path(__file__).parent.parent
sys.path.insert(0, str(parent_path))

from models.fatigue import fatigue_model
from models.keyboard_layout import Keyboard
from models.rw_laplacian import laplacian_spectral


class Individual: #유전 알고리즘 개체, array 순열로 표현하고 fatigue 역수가 적합도임 (낮을수록 적합함)
    def __init__(self, layout: np.ndarray, keyboard: Keyboard, fatigue_calc: Callable, 
                 co_occurrence_matrix: np.ndarray = None, laplacian_weight: float = 0.0): 
        
        self.layout = layout.copy()
        self.keyboard = keyboard
        self.fatigue_calc = fatigue_calc
        self.co_occurrence_matrix = co_occurrence_matrix
        self.laplacian_weight = laplacian_weight
        self._fitness = None
        self._fatigue = None
    
    def evaluate(self) -> float:
        if self._fitness is None:
            self._fatigue = self.calculate_total_fatigue()
            epsilon = 1e-6
            self._fitness = 1.0 / (self._fatigue + epsilon)
        return self._fitness
    
    def calculate_total_fatigue(self) -> float: #전체 피로도
        C_total = self._calculate_step_fatigue()
        
        if self.laplacian_weight > 0 and self.co_occurrence_matrix is not None:
            C_lap = self._calculate_laplacian_penalty()
            C_total_star = C_total + self.laplacian_weight * C_lap
        else:
            C_total_star = C_total
        
        return C_total_star
    
    def _calculate_step_fatigue(self) -> float:
        if self.co_occurrence_matrix is None:
            return 0.0
        
        total_fatigue = 0.0
        W = self.co_occurrence_matrix
        
        for i in range(len(self.layout)):
            for j in range(len(self.layout)):
                if W[i, j] > 0:
                    pos_i = np.where(self.layout == i)[0]
                    pos_j = np.where(self.layout == j)[0]
                    
                    if len(pos_i) > 0 and len(pos_j) > 0:
                        pos_i = pos_i[0]
                        pos_j = pos_j[0]

                        f_step = self._calculate_step_cost(pos_i, pos_j)
                        total_fatigue += W[i, j] * f_step
        
        return total_fatigue
    
    def _calculate_step_cost(self, pos_i: int, pos_j: int) -> float: #step 비용
        try:
            dist = self.keyboard.distance(pos_i, pos_j)
        except:
            dist = 1.0
        
        return dist
    
    def _calculate_laplacian_penalty(self) -> float: #라플라시안 페널티
        W = self.co_occurrence_matrix
        penalty = 0.0
        
        grid_shape = self.keyboard._get_key_positions().shape  
        
        for i in range(len(self.layout)):
            for j in range(len(self.layout)):
                if W[i, j] > 0:
                    pos_i = np.where(self.layout == i)[0]
                    pos_j = np.where(self.layout == j)[0]
                    
                    if len(pos_i) > 0 and len(pos_j) > 0:
                        pos_i = pos_i[0]
                        pos_j = pos_j[0]

                        coord_i = np.array([pos_i // grid_shape[1], pos_i % grid_shape[1]], dtype=float)
                        coord_j = np.array([pos_j // grid_shape[1], pos_j % grid_shape[1]], dtype=float)
                        
                        dist_sq = np.sum((coord_i - coord_j) ** 2)
                        penalty += W[i, j] * dist_sq
        
        return penalty
    
    def copy(self) -> 'Individual':
        new_layout = self.layout.copy()
        return Individual(
            new_layout, 
            self.keyboard, 
            self.fatigue_calc,
            self.co_occurrence_matrix,
            self.laplacian_weight
        )


class GAOperators: #GA 연산자
    @staticmethod
    def tournament_selection(population: List[Individual], tournament_size: int = 3) -> Individual:
        candidates = np.random.choice(population, size=tournament_size, replace=False)
        best = max(candidates, key=lambda ind: ind.evaluate())
        return best.copy()
    
    @staticmethod
    def roulette_wheel_selection(population: List[Individual]) -> Individual:
        fitness_values = np.array([ind.evaluate() for ind in population])
        fitness_values = fitness_values - fitness_values.min() + 1e-6  # 모두 양수로
        probabilities = fitness_values / fitness_values.sum()
        selected_idx = np.random.choice(len(population), p=probabilities)
        return population[selected_idx].copy()
    
    @staticmethod
    def pmx_crossover(parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        layout1 = parent1.layout.copy()
        layout2 = parent2.layout.copy()
        n = len(layout1)
        
        point1 = np.random.randint(0, n - 1)
        point2 = np.random.randint(point1 + 1, n)

        child1 = np.zeros(n, dtype=int)
        child2 = np.zeros(n, dtype=int)

        child1[point1:point2] = layout1[point1:point2]
        child2[point1:point2] = layout2[point1:point2]
        
        def fill_pmx(child, parent_from, parent_to, start, end):
            for i in range(n):
                if i < start or i >= end:
                    val = parent_to[i]
                    while val in child:
                        idx = np.where(parent_to == val)[0][0]
                        val = parent_from[idx]
                    child[i] = val
        
        fill_pmx(child1, layout2, layout1, point1, point2)
        fill_pmx(child2, layout1, layout2, point1, point2)
        
        child1_ind = parent1.copy()
        child1_ind.layout = child1
        child1_ind._fitness = None
        
        child2_ind = parent2.copy()
        child2_ind.layout = child2
        child2_ind._fitness = None
        
        return child1_ind, child2_ind
    
    @staticmethod
    def ox_crossover(parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        layout1 = parent1.layout.copy()
        layout2 = parent2.layout.copy()
        n = len(layout1)
        
        point1 = np.random.randint(0, n - 1)
        point2 = np.random.randint(point1 + 1, n)
        
        def ox_fill(child, parent_from, parent_to, start, end):
            child[start:end] = parent_from[start:end]
            used = set(child[start:end])
            pos = end % n
            for val in parent_to[(end) % n:] + list(parent_to[:(end) % n]):
                if val not in used:
                    child[pos] = val
                    pos = (pos + 1) % n
        
        child1 = np.zeros(n, dtype=int)
        child2 = np.zeros(n, dtype=int)
        
        ox_fill(child1, layout1, layout2, point1, point2)
        ox_fill(child2, layout2, layout1, point1, point2)
        
        child1_ind = parent1.copy()
        child1_ind.layout = child1
        child1_ind._fitness = None
        
        child2_ind = parent2.copy()
        child2_ind.layout = child2
        child2_ind._fitness = None
        
        return child1_ind, child2_ind
    
    @staticmethod
    def swap_mutation(individual: Individual, mutation_rate: float = 0.1) -> Individual:
        mutated = individual.copy()
        layout = mutated.layout
        n = len(layout)
        
        for _ in range(max(1, int(n * mutation_rate))):
            if np.random.random() < mutation_rate:
                i, j = np.random.choice(n, size=2, replace=False)
                layout[i], layout[j] = layout[j], layout[i]
        
        mutated._fitness = None
        return mutated
    
    @staticmethod
    def inversion_mutation(individual: Individual, mutation_rate: float = 0.05) -> Individual:
        mutated = individual.copy()
        layout = mutated.layout
        n = len(layout)
        
        if np.random.random() < mutation_rate:
            start = np.random.randint(0, n - 1)
            end = np.random.randint(start + 1, n)
            layout[start:end] = layout[start:end][::-1]
        
        mutated._fitness = None
        return mutated
    
    @staticmethod
    def levy_flight_mutation(individual: Individual, mutation_rate: float = 0.02) -> Individual:
        mutated = individual.copy()
        layout = mutated.layout
        n = len(layout)
        
        if np.random.random() < mutation_rate:
            # Lévy flight 스텝 크기 샘플링 (heavy tail)
            num_swaps = int(n * np.random.pareto(2.0) * 0.1) + 1
            num_swaps = min(num_swaps, n // 2)
            
            for _ in range(num_swaps):
                i, j = np.random.choice(n, size=2, replace=False)
                layout[i], layout[j] = layout[j], layout[i]
        
        mutated._fitness = None
        return mutated


class Initializer:
    """
    초기 집단 생성
    """
    
    @staticmethod
    def random_initialization(n_individuals: int, n_genes: int, keyboard: Keyboard, 
                             fatigue_calc: Callable, co_occurrence_matrix: np.ndarray = None,
                             laplacian_weight: float = 0.0) -> List[Individual]:
        """
        무작위 순열로 초기 집단 생성
        """
        population = []
        for _ in range(n_individuals):
            layout = np.random.permutation(n_genes)
            ind = Individual(layout, keyboard, fatigue_calc, co_occurrence_matrix, laplacian_weight)
            population.append(ind)
        return population
    
    @staticmethod
    def seeded_initialization(n_individuals: int, n_genes: int, keyboard: Keyboard,
                             fatigue_calc: Callable, seed_layouts: List[np.ndarray] = None,
                             co_occurrence_matrix: np.ndarray = None,
                             laplacian_weight: float = 0.0) -> List[Individual]:
        """
        일부는 미리 정의된 레이아웃(두벌식 등)을 seed로, 나머지는 무작위 생성
        """
        population = []
        
        if seed_layouts:
            for layout in seed_layouts:
                ind = Individual(layout.copy(), keyboard, fatigue_calc, co_occurrence_matrix, laplacian_weight)
                population.append(ind)
        
        remaining = n_individuals - len(population)
        for _ in range(remaining):
            layout = np.random.permutation(n_genes)
            ind = Individual(layout, keyboard, fatigue_calc, co_occurrence_matrix, laplacian_weight)
            population.append(ind)
        
        return population
    
    @staticmethod
    def spectral_initialization(n_individuals: int, n_genes: int, keyboard: Keyboard,
                               fatigue_calc: Callable, co_occurrence_matrix: np.ndarray,
                               laplacian_matrix: np.ndarray = None,
                               n_eigenvectors: int = 3,
                               co_occurrence_matrix_for_fitness: np.ndarray = None,
                               laplacian_weight: float = 0.0) -> List[Individual]:
        population = []
        
        if laplacian_matrix is None:
            D = np.diag(co_occurrence_matrix.sum(axis=1))
            laplacian_matrix = D - co_occurrence_matrix
        
        eigenvalues, eigenvectors = la.eigh(laplacian_matrix)
        

        n_use = min(n_eigenvectors, len(eigenvalues))
        spectral_coords = eigenvectors[:, :n_use]  # (n_genes, n_eigenvectors)
        
        sorted_indices = np.argsort(spectral_coords[:, 0])
        

        base_layout = sorted_indices.copy()
        
        ind = Individual(base_layout, keyboard, fatigue_calc, co_occurrence_matrix_for_fitness or co_occurrence_matrix, laplacian_weight)
        population.append(ind)
        
        for _ in range(n_individuals - 1):
            layout = base_layout.copy()
            # 작은 섭동 추가
            for _ in range(int(n_genes * 0.1)):
                i, j = np.random.choice(n_genes, size=2, replace=False)
                layout[i], layout[j] = layout[j], layout[i]
            
            ind = Individual(layout, keyboard, fatigue_calc, co_occurrence_matrix_for_fitness or co_occurrence_matrix, laplacian_weight)
            population.append(ind)
        
        return population


class GARunner:
    
    def __init__(self, 
                 population_size: int = 50,
                 max_generations: int = 100,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8,
                 elite_size: int = 2,
                 selection_type: str = 'tournament',
                 crossover_type: str = 'pmx'):
        
        self.population_size = population_size
        self.max_generations = max_generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size
        self.selection_type = selection_type
        self.crossover_type = crossover_type
        
        self.best_fitness_history = []
        self.avg_fitness_history = []
        self.population_history = []
    
    def run(self, population: List[Individual], #GA 실행
            patience: int = None,
            verbose: bool = True) -> Tuple[Individual, List[Individual]]:
        
        current_population = [ind.copy() for ind in population]
        best_individual = None
        best_fitness = -np.inf
        no_improve_count = 0
        
        for generation in range(self.max_generations):
            # 적합도 평가
            fitness_values = [ind.evaluate() for ind in current_population]

            max_fitness = max(fitness_values)
            avg_fitness = np.mean(fitness_values)
            self.best_fitness_history.append(max_fitness)
            self.avg_fitness_history.append(avg_fitness)
            self.population_history.append([ind.copy() for ind in current_population])

            gen_best_idx = np.argmax(fitness_values)
            if fitness_values[gen_best_idx] > best_fitness:
                best_fitness = fitness_values[gen_best_idx]
                best_individual = current_population[gen_best_idx].copy()
                no_improve_count = 0
            else:
                no_improve_count += 1
            
            if verbose:
                print(f"Generation {generation + 1}: Best={max_fitness:.6f}, Avg={avg_fitness:.6f}")
            
            # 조기 종료
            if patience and no_improve_count >= patience:
                if verbose:
                    print(f"Early stopping at generation {generation + 1}")
                break

            new_population = []
            
            # 엘리트 유지
            elite_indices = np.argsort(fitness_values)[-self.elite_size:]
            for idx in elite_indices:
                new_population.append(current_population[idx].copy())
            
            while len(new_population) < self.population_size:
                # 선택
                if self.selection_type == 'tournament':
                    parent1 = GAOperators.tournament_selection(current_population)
                    parent2 = GAOperators.tournament_selection(current_population)
                else:  
                    parent1 = GAOperators.roulette_wheel_selection(current_population)
                    parent2 = GAOperators.roulette_wheel_selection(current_population)
                
                # 교차
                if np.random.random() < self.crossover_rate:
                    if self.crossover_type == 'pmx':
                        child1, child2 = GAOperators.pmx_crossover(parent1, parent2)
                    else:  # ox
                        child1, child2 = GAOperators.ox_crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()

                if np.random.random() < self.mutation_rate:
                    mutation_choice = np.random.random()
                    if mutation_choice < 0.7:
                        child1 = GAOperators.swap_mutation(child1, self.mutation_rate)
                    elif mutation_choice < 0.9:
                        child1 = GAOperators.inversion_mutation(child1, self.mutation_rate)
                    else:
                        child1 = GAOperators.levy_flight_mutation(child1, self.mutation_rate)
                
                if np.random.random() < self.mutation_rate:
                    mutation_choice = np.random.random()
                    if mutation_choice < 0.7:
                        child2 = GAOperators.swap_mutation(child2, self.mutation_rate)
                    elif mutation_choice < 0.9:
                        child2 = GAOperators.inversion_mutation(child2, self.mutation_rate)
                    else:
                        child2 = GAOperators.levy_flight_mutation(child2, self.mutation_rate)
                
                new_population.append(child1)
                if len(new_population) < self.population_size:
                    new_population.append(child2)
            
            current_population = new_population[:self.population_size]
        
        return best_individual, current_population
    
    def get_statistics(self) -> Dict:
        return {
            'best_fitness_history': self.best_fitness_history,
            'avg_fitness_history': self.avg_fitness_history,
            'final_best_fitness': self.best_fitness_history[-1] if self.best_fitness_history else None,
            'generations_run': len(self.best_fitness_history)
        }

