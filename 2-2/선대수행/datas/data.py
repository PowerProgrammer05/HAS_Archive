import pandas as pd
from jamo import h2j, j2hcj
import copy

korean_list = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎㄳㄵㄶㄺㄻㄼㄽㄾㄿㅀㅄㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")

def preprocess_word(words = pd.DataFrame()):
    words_count = dict() #jamo freq
    raw_weight = dict() #raw dict (이중딕셔너리임, 후행 자모 빈도)

    for i in korean_list:
        words_count[i] = 0

    for i in korean_list:
        raw_weight[i] = copy.deepcopy(words_count)

    for i in words.iterrows(): 
        syllables = j2hcj(h2j(i[1]['단어'])) #jamo seperate
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

    print(all_weight)

    #Save csv
    high_count.to_csv("datas/high_count.csv", index=True, encoding='utf-8-sig')
    all_count.to_csv("datas/all_count.csv", index=True, encoding='utf-8-sig')
    high_weight.to_csv("datas/high_raw_weight.csv", index=True, encoding='utf-8-sig')
    all_weight.to_csv("datas/all_raw_weight.csv", index=True, encoding='utf-8-sig')

