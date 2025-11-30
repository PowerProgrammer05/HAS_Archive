import pandas as pd
from tabulate import tabulate
high_words = pd.read_csv('word_frequency.csv', encoding='utf-8')
print(tabulate(high_words, headers='keys', tablefmt='psql'))
