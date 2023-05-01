import re
import os
import glob
from typing import List

def load_words(path: str) -> List[str]:
    out = []
    for filename in os.listdir(path):
        if filename.endswith('.txt'):
            with open(os.path.join(path, filename), 'r', encoding="utf-8") as f:
                for line in f:
                    out.append(line.strip())
    return out

HEXIE_WORDS = load_words("./mingan")

def hexie(sentence: str) -> str:
    '''
    replace words into ***
    '''
    for word in HEXIE_WORDS:
        # 使用正则表达式匹配单词，并将其替换为相同数量的星号
        sentence = sentence.replace(word, "*" * len(word))
    return sentence