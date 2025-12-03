import pandas as pd
import numpy as np
from jamo import h2j, j2hcj
import copy

korean_list = list("ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㅏㅐㅑㅓㅔㅕㅗㅛㅜㅠㅡㅣ")
double_jamo = {
    "ㄳ": "ㄱㅅ",
    "ㄵ": "ㄴㅈ",
    "ㄶ": "ㄴㅎ",
    "ㄺ": "ㄹㄱ",
    "ㄻ": "ㄹㅁ",
    "ㄼ": "ㄹㅂ",
    "ㄽ": "ㄹㅅ",
    "ㄾ": "ㄹㅌ",
    "ㄿ": "ㄹㅍ",
    "ㅀ": "ㄹㅎ",
    "ㅄ": "ㅂㅅ",
    "ㅘ": "ㅗㅏ",
    "ㅙ": "ㅗㅐ",
    "ㅚ": "ㅗㅣ",
    "ㅝ": "ㅜㅓ",
    "ㅞ": "ㅜㅔ",
    "ㅟ": "ㅜㅣ",
    "ㅢ": "ㅡㅣ",
    "ㄲ": "ㄱ",
    "ㄸ": "ㄷ",
    "ㅃ": "ㅂ",
    "ㅆ": "ㅅ",
    "ㅉ": "ㅈ",
    "ㅒ": "ㅐ",
    "ㅖ": "ㅔ"
}

def preprocess_word(words = pd.DataFrame()):
    words_count = dict() #jamo freq
    raw_weight = dict() #raw dict (이중딕셔너리임, 후행 자모 빈도)

    for i in korean_list:
        words_count[i] = 0

    for i in korean_list:
        raw_weight[i] = copy.deepcopy(words_count)

    for i in words.iterrows(): 
        syllables = list(j2hcj(h2j(i[1]['단어']))) #jamo seperate
        for j, sy in enumerate(syllables):
            if sy in double_jamo.keys(): #이중자모 분리
                syllables.pop(j)
                syllables[j:j] = list(double_jamo[sy])

        for j in enumerate(syllables): #freq
            index, char = j[0], j[1]
            try:
                words_count[char] += i[1]['빈도']
            except KeyError:
                pass

            if index < len(syllables) - 1: #add next 자모!
                try:
                    raw_weight[char][syllables[index + 1]] += i[1]['빈도']
                except KeyError:
                    pass
    return words_count, raw_weight

if __name__ == "__main__":
    high_words = pd.read_csv('datas/word_frequency.csv', encoding='utf-8')
    all_words =pd.read_csv('datas/kor_news_2007_100K-words.txt', 
                sep=r'\s+', 
                header=None, 
                engine='python',
                names=['index', '단어', '빈도']) #10k words from news (txt여서 regex)
    all_words.drop(columns=['index'], inplace=True)
    

    high_result = preprocess_word(high_words)
    all_result = preprocess_word(all_words)

    high_count = pd.DataFrame(list(high_result[0].items()), columns=['단어', '빈도'])
    all_count = pd.DataFrame(list(all_result[0].items()), columns=['단어', '빈도'])

    high_weight = pd.DataFrame(high_result[1], index=korean_list)
    all_weight = pd.DataFrame(all_result[1], index=korean_list)

    #Save csv
    high_count.to_csv("datas/high_count.csv", index=True, encoding='utf-8-sig')
    all_count.to_csv("datas/all_count.csv", index=True, encoding='utf-8-sig')
    high_weight.to_csv("datas/high_raw_weight.csv", index=True, encoding='utf-8-sig')
    all_weight.to_csv("datas/all_raw_weight.csv", index=True, encoding='utf-8-sig')


def load_co_occurrence_matrix(corpus_file: str = None, 
                              csv_weight_file: str = 'datas/all_raw_weight.csv',
                              normalize: bool = True) -> np.ndarray:
    
    if csv_weight_file:
        try:
            weight_df = pd.read_csv(csv_weight_file, index_col=0, encoding='utf-8-sig')
            co_occurrence = weight_df.values.astype(float)

            if normalize:
                row_sum = co_occurrence.sum(axis=1, keepdims=True)
                row_sum[row_sum == 0] = 1
                co_occurrence = co_occurrence / row_sum
            
            return co_occurrence
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return None
    
    elif corpus_file:
        try:
            words = pd.read_csv(corpus_file, 
                              sep=r'\s+', 
                              header=None, 
                              engine='python',
                              names=['index', '단어', '빈도'])
            words.drop(columns=['index'], inplace=True)
            
            result = preprocess_word(words)
            raw_weight = result[1]
            
            co_occurrence = pd.DataFrame(raw_weight, index=korean_list).values.astype(float)
            
            if normalize:
                row_sum = co_occurrence.sum(axis=1, keepdims=True)
                row_sum[row_sum == 0] = 1
                co_occurrence = co_occurrence / row_sum
            
            return co_occurrence
        except Exception as e:
            print(f"Error loading corpus: {e}")
            return None
    
    return None


def symmetrize_matrix(matrix: np.ndarray) -> np.ndarray:
    return (matrix + matrix.T) / 2


def load_combined_cooccurrence(all_csv: str = 'datas/all_raw_weight.csv',
                               high_csv: str = 'datas/high_raw_weight.csv',
                               alpha: float = 0.6,
                               normalize: bool = True) -> np.ndarray:
    try:
        df_all = pd.read_csv(all_csv, index_col=0, encoding='utf-8-sig')
        df_high = pd.read_csv(high_csv, index_col=0, encoding='utf-8-sig')
    except Exception as e:
        print(f"Error loading CSVs for combined co-occurrence: {e}")
        return None
    
    common_idx = df_all.index.intersection(df_high.index)
    df_all = df_all.loc[common_idx, common_idx]
    df_high = df_high.loc[common_idx, common_idx]

    A = df_all.values.astype(float)
    H = df_high.values.astype(float)

    if normalize:
        row_sums_A = A.sum(axis=1, keepdims=True)
        row_sums_H = H.sum(axis=1, keepdims=True)
        row_sums_A[row_sums_A == 0] = 1.0
        row_sums_H[row_sums_H == 0] = 1.0
        A = A / row_sums_A
        H = H / row_sums_H

    W = (1.0 - alpha) * A + alpha * H

    if normalize:
        row_sums = W.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        W = W / row_sums

    return W


def load_combined_frequency(all_count_csv: str = 'datas/all_count.csv',
                            high_count_csv: str = 'datas/high_count.csv',
                            alpha: float = 0.6) -> np.ndarray:
    try:
        df_all = pd.read_csv(all_count_csv, index_col=0, encoding='utf-8-sig')
        df_high = pd.read_csv(high_count_csv, index_col=0, encoding='utf-8-sig')
    except Exception as e:
        print(f"Error loading count CSVs: {e}")
        return None

    common_chars = df_all.index.intersection(df_high.index)

    freq_all = df_all.loc[common_chars, '빈도'].values.astype(float)
    freq_high = df_high.loc[common_chars, '빈도'].values.astype(float)

    freq_all = freq_all / (freq_all.sum() + 1e-9)
    freq_high = freq_high / (freq_high.sum() + 1e-9)

    freq_combined = (1.0 - alpha) * freq_all + alpha * freq_high

    freq_combined = freq_combined / (freq_combined.sum() + 1e-9)

    return freq_combined
