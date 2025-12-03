import numpy as np


class KeyboardLayout:
    
    def __init__(self):
        self.n_rows = 3
        self.n_cols = 10
        self.n_positions = 30
        self.n_chars = 26  

        self.korean_chars = [
            'ㅂ', 'ㅈ', 'ㄷ', 'ㄱ', 'ㅅ', 'ㅛ', 'ㅕ', 'ㅑ', 'ㅐ', 'ㅔ',  # 0~9
            'ㅁ', 'ㄴ', 'ㅇ', 'ㄹ', 'ㅎ', 'ㅗ', 'ㅓ', 'ㅏ', 'ㅣ',           # 10~18
            'ㅋ', 'ㅌ', 'ㅊ', 'ㅍ', 'ㅠ', 'ㅜ', 'ㅡ'                       # 19~25
        ]

        self.default_layout = np.array([
            [0,  1,  2,  3,  4,  5,  6,  7,  8,  9],
            [10, 11, 12, 13, 14, 15, 16, 17, 18, -1],
            [19, 20, 21, 22, 23, 24, 25, -1, -1, -1]
        ], dtype=int)
        
        self._init_position_table()
    
    def _init_position_table(self):
        self.position_table = {}
    
        # 왼손 행 0
        self.position_table[0] = (0, 0, 'Left', 'Ring')      # ㅂ
        self.position_table[1] = (0, 1, 'Left', 'Ring')      # ㅈ
        self.position_table[2] = (0, 2, 'Left', 'Middle')    # ㄷ
        self.position_table[3] = (0, 3, 'Left', 'Index')     # ㄱ
        self.position_table[4] = (0, 4, 'Left', 'Index')     # ㅅ 
        self.position_table[10] = (1, 0, 'Left', 'Ring')     # ㅁ
        self.position_table[11] = (1, 1, 'Left', 'Middle')   # ㄴ
        self.position_table[12] = (1, 2, 'Left', 'Index')    # ㅇ
        self.position_table[13] = (1, 3, 'Left', 'Index')    # ㄹ
        self.position_table[14] = (1, 4, 'Left', 'Index')    # ㅎ
        
        # 행 2
        self.position_table[19] = (2, 0, 'Left', 'Ring')     # ㅋ
        self.position_table[20] = (2, 1, 'Left', 'Middle')   # ㅌ
        self.position_table[21] = (2, 2, 'Left', 'Index')    # ㅊ
        self.position_table[22] = (2, 3, 'Left', 'Index')    # ㅍ 
        
        # 오른손 행 0
        self.position_table[5] = (0, 5, 'Right', 'Index')    # ㅛ
        self.position_table[6] = (0, 6, 'Right', 'Index')    # ㅕ
        self.position_table[7] = (0, 7, 'Right', 'Middle')   # ㅑ
        self.position_table[8] = (0, 8, 'Right', 'Ring')     # ㅐ
        self.position_table[9] = (0, 9, 'Right', 'Ring')     # ㅔ
        
        # 행 1
        self.position_table[15] = (1, 5, 'Right', 'Index')   # ㅗ
        self.position_table[16] = (1, 6, 'Right', 'Index')   # ㅓ
        self.position_table[17] = (1, 7, 'Right', 'Middle')  # ㅏ
        self.position_table[18] = (1, 8, 'Right', 'Ring')    # ㅣ
        
        # 행 2
        self.position_table[23] = (2, 4, 'Right', 'Index')   # ㅠ
        self.position_table[24] = (2, 5, 'Right', 'Middle')  # ㅜ
        self.position_table[25] = (2, 6, 'Right', 'Ring')    # ㅡ
        
        # 미사용 위치 (실제 키보드에서는 ,.; 위치임)
        self.position_table[26] = (2, 7, 'Right', 'Ring')
        self.position_table[27] = (2, 8, 'Right', 'Ring')
        self.position_table[28] = (2, 9, 'Right', 'Ring')
        self.position_table[29] = (-1, -1, 'None', 'None')
    
    def get_position_2d(self, layout, char_idx):
        rows, cols = np.where(layout == char_idx)
        if len(rows) > 0:
            return (rows[0], cols[0])
        return None
    
    def get_position_idx(self, row, col):
        return row * self.n_cols + col
    
    def get_hand_finger(self, pos_idx):
        if pos_idx in self.position_table:
            row, col, hand, finger = self.position_table[pos_idx]
            return (hand, finger)
        return (None, None)
    
    def distance(self, pos1, pos2, weight=0.8):
        if pos1 is None or pos2 is None:
            return float('inf')
        
        row1, col1 = pos1
        row2, col2 = pos2
        
        dist = np.sqrt((col2 - col1)**2 + weight * (row2 - row1)**2) #이거 실제 거리 correction 한거임
        return dist
    
    def get_row_direction(self, row1, row2):
        if row2 > row1:
            return 'top_to_bottom'
        elif row2 < row1:
            return 'bottom_to_top'
        else:
            return 'same_row'
    
    def evaluate_layout(self, layout, W, 
                       f2_table, f3_table, f4_table,
                       lap_weight=0.3):
        C_fatigue = self._calc_fatigue(layout, W, f2_table, f3_table, f4_table)
        C_lap = self._calc_laplacian_penalty(layout, W, lap_weight)
        C_total = C_fatigue + C_lap
        fitness = 1.0 / (C_total + 1e-6)
        
        return {
            'fatigue': C_fatigue,
            'laplacian': C_lap,
            'total': C_total,
            'fitness': fitness
        }
    
    def _calc_fatigue(self, layout, W, f2_table, f3_table, f4_table):
        C_fatigue = 0.0
        
        for i in range(self.n_chars):
            for j in range(self.n_chars):
                if W[i, j] > 0:
                    pos_i = self.get_position_2d(layout, i)
                    pos_j = self.get_position_2d(layout, j)
                    
                    if pos_i is None or pos_j is None:
                        continue
                    
                    dist = self.distance(pos_i, pos_j)

                    pos_i_idx = self.get_position_idx(pos_i[0], pos_i[1])
                    pos_j_idx = self.get_position_idx(pos_j[0], pos_j[1])
                    
                    hand_i, finger_i = self.get_hand_finger(pos_i_idx)
                    hand_j, finger_j = self.get_hand_finger(pos_j_idx)

                    if finger_i and finger_j:
                        f2_i = f2_table.get(finger_i, 1.0)
                        f2_j = f2_table.get(finger_j, 1.0)
                        f2 = (f2_i + f2_j) / 2
                    else:
                        f2 = 1.0
                    
                    if hand_i and hand_j:
                        same_hand = (hand_i == hand_j)
                        row_dir = self.get_row_direction(pos_i[0], pos_j[0])
                        
                        if same_hand:
                            key = ('same_hand', row_dir)
                        else:
                            key = ('diff_hand', row_dir)
                        
                        f3 = f3_table.get(key, 1.0)
                    else:
                        f3 = 1.0
                    
                    if finger_i and finger_j:
                        finger_idx_map = {
                            'Index': 0, 'Middle': 1, 'Ring': 2, 'Little': 3
                        }
                        i_idx = finger_idx_map.get(finger_i, 0)
                        j_idx = finger_idx_map.get(finger_j, 0)
                        f4 = f4_table[i_idx, j_idx]
                    else:
                        f4 = 1.0
                    
                    f_step = dist * f2 * f3 * f4
                    C_fatigue += W[i, j] * f_step
        
        return C_fatigue
    
    def _calc_laplacian_penalty(self, layout, W, weight=0.3): #학습에서 laplacian penalty
        C_lap = 0.0
        
        for i in range(self.n_chars):
            for j in range(self.n_chars):
                if W[i, j] > 0:
                    pos_i = self.get_position_2d(layout, i)
                    pos_j = self.get_position_2d(layout, j)
                    
                    if pos_i is None or pos_j is None:
                        continue
                    dist_sq = (pos_i[0] - pos_j[0])**2 + (pos_i[1] - pos_j[1])**2
                    C_lap += W[i, j] * dist_sq
        
        return weight * C_lap
