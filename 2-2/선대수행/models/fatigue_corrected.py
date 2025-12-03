
import numpy as np


class FatigueModel: #total 피로도 = f1*f2*f3*f4
    def __init__(self):
        self._init_f2_table()
        self._init_f3_table()
        self._init_f4_table()
    
    def _init_f2_table(self):
        self.f2_table = {
            'Index': 1.0,
            'Middle': 1.0,
            'Ring': 1.2,
            'Little': 1.5
        }
    
    def _init_f3_table(self):
        self.f3_table = {
            ('same_hand', 'top_to_bottom'): 1.2,
            ('same_hand', 'bottom_to_top'): 1.0,
            ('same_hand', 'same_row'): 1.0,

            ('diff_hand', 'top_to_bottom'): 1.5,
            ('diff_hand', 'bottom_to_top'): 1.2,
            ('diff_hand', 'same_row'): 1.0,
        }
    
    def _init_f4_table(self):
        self.f4_table = np.array([
            [2.0, 1.0, 1.2, 1.0],  # Index | [Index, Middle, Ring, Little]
            [1.0, 2.0, 1.5, 1.2],  # Middle →|[Index, Middle, Ring, Little]
            [1.2, 1.5, 2.0, 1.5],  # Ring | [Index, Middle, Ring, Little]
            [1.0, 1.2, 1.5, 2.0],  # Little | [Index, Middle, Ring, Little]
        ])
    
    def get_f2_cost(self, finger1, finger2):
        if finger1 not in self.f2_table or finger2 not in self.f2_table:
            return 1.0
        
        f2_1 = self.f2_table[finger1]
        f2_2 = self.f2_table[finger2]
        return (f2_1 + f2_2) / 2
    
    def get_f3_cost(self, hand1, hand2, row1, row2):
        same_hand = (hand1 == hand2)
        if row2 > row1:
            row_direction = 'top_to_bottom'
        elif row2 < row1:
            row_direction = 'bottom_to_top'
        else:
            row_direction = 'same_row'
        key = ('same_hand' if same_hand else 'diff_hand', row_direction)
        return self.f3_table.get(key, 1.0)
    
    def get_f4_cost(self, finger1, finger2):
        finger_map = {
            'Index': 0,
            'Middle': 1,
            'Ring': 2,
            'Little': 3
        }
        
        if finger1 not in finger_map or finger2 not in finger_map:
            return 1.0
        
        idx1 = finger_map[finger1]
        idx2 = finger_map[finger2]
        return self.f4_table[idx1, idx2]
    
    def get_all_tables(self):
        return self.f2_table, self.f3_table, self.f4_table
    
    def summary(self):
        print("=" * 60)
        print("피로도")
        print("=" * 60)
        
        print("\nf2: 손가락 종류별 피로도")
        print("-" * 40)
        for finger, cost in self.f2_table.items():
            print(f"  {finger:8s}: {cost:.1f}")
        
        print("\nf3: 입력 방향별 피로도")
        print("-" * 40)
        print("Same hand:")
        print(f"    위 -> 아래: {self.f3_table[('same_hand', 'top_to_bottom')]:.1f}")
        print(f"    아래 -> 위: {self.f3_table[('same_hand', 'bottom_to_top')]:.1f}")
        print(f"    같은 줄:   {self.f3_table[('same_hand', 'same_row')]:.1f}")
        print("Different hand:")
        print(f"    위 -> 아래: {self.f3_table[('diff_hand', 'top_to_bottom')]:.1f}")
        print(f"    아래 -> 위: {self.f3_table[('diff_hand', 'bottom_to_top')]:.1f}")
        print(f"    같은 줄:   {self.f3_table[('diff_hand', 'same_row')]:.1f}")
        
        print("\nf4: 손가락 조합별 피로도")
        print("-" * 40)
        finger_names = ['Index', 'Middle', 'Ring', 'Little']
        print("     ", " ".join(f"{name:8s}" for name in finger_names))
        for i, from_finger in enumerate(finger_names):
            row_str = f"{from_finger:5s}"
            for j, to_finger in enumerate(finger_names):
                row_str += f" {self.f4_table[i, j]:8.1f}"
            print(row_str)
        
        print("\n" + "=" * 60)
    print("\n" + "=" * 60)
