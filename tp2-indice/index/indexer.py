from nltk.stem.snowball import SnowballStemmer
from bs4 import BeautifulSoup
import string
from nltk.tokenize import word_tokenize
from collections import Counter
import nltk
import os
from index.structure import *

class Cleaner:
    def __init__(self,stop_words_file:str,language:str,
                        perform_stop_words_removal:bool,perform_accents_removal:bool,
                        perform_stemming:bool):
        self.set_stop_words = self.read_stop_words(stop_words_file)

        self.stemmer = SnowballStemmer(language)
        in_table =  "áéíóúâêôçãẽõü"
        out_table = "aeiouaeocaeou"
        #altere a linha abaixo para remoção de acentos (Atividade 11)
        self.accents_translation_table = str.maketrans(in_table, out_table)
        self.set_punctuation = set(string.punctuation)

        #flags
        self.perform_stop_words_removal = perform_stop_words_removal
        self.perform_accents_removal = perform_accents_removal
        self.perform_stemming = perform_stemming

    def html_to_plain_text(self,html_doc:str) ->str:
        soup = BeautifulSoup(html_doc,"html.parser")
        text = soup.get_text()
        return text

    def read_stop_words(self,str_file):
        set_stop_words = set()
        with open(str_file, "r") as stop_words_file:
            for line in stop_words_file:
                arr_words = line.split(",")
                [set_stop_words.add(word) for word in arr_words]
        return set_stop_words
    
    def is_stop_word(self,term:str):
        if (term in self.set_stop_words):
            return True
        else:
            return False
        
    def word_stem(self,term:str):
        return self.stemmer.stem(term)


    def remove_accents(self,term:str) ->str:
        aux = []
        for i,j in enumerate(term): 
            # ord pega a referência de uma letra na tabela ASCII em python
            # e chr pega a referência retornada em ASCII e converte pra char
            if ord(j) in self.accents_translation_table.keys():
                key =  ord(j)
                value = chr(self.accents_translation_table[key])
                aux.append(value)
            else:
                aux.append(j)
        newTerm = ''.join(aux)
        return newTerm


    def preprocess_word(self,term:str) -> str:
        # Se não for pontuação e não for stopword
        '''Agora você irá fazer o método `preprocess_word` ele irá receber como parametro uma palavra e irá verificar se é uma palavra válida de ser indexada. Caso não seja, retornará None. Caso contrário, irá retornar a palvra preprocessada. Uma palavra válida a ser indexada é aquela que não é pontuação e não é stopword (caso `perform_stop_words_removal = True`). Para que seja feito o preprocessamento você deverá: transformar o texto para minúsculas, remover acento (se `perform_accents_removal=True`), fazer o stemming (se `perform_stemming = True`).'''
        if term not in self.set_punctuation and not self.is_stop_word(term):
            # Será indexada após remover fazer pre processamento
            toLower = term.lower()
            removed = self.remove_accents(toLower)
            return self.word_stem(removed)
        else:
            return None
    



class HTMLIndexer:
    cleaner = Cleaner(stop_words_file="stopwords.txt",
                        language="portuguese",
                        perform_stop_words_removal=True,
                        perform_accents_removal=True,
                        perform_stemming=True)
    def __init__(self,index):
        self.index = index

    def text_word_count(self,plain_text:str):
        nltk.download('punkt')
        words = word_tokenize(plain_text)
        new_word_array = []
        for term in words:
            new_term = self.cleaner.preprocess_word(term)
            if new_term != None:
                 new_word_array.append(new_term)
        dic_word_count = Counter(new_word_array)
        return dic_word_count
    
    def index_text(self,doc_id:int, text_html:str):
        '''
        **Atividade 13 - método index_text: ** Implemente o método `index_text` que deverá (1) converter o HTML para texto simples usando `HTMLIndexer.cleaner`; (2) converter o texto em um dicionário de ocorrencias de palavras com sua frequencia (metodo da atividade 12); e (3) indexar cada palavra deste dicionário.
        '''
        # Passo 1: Converter o HTML para um texto simples
        
        plain_text = self.cleaner.html_to_plain_text(text_html)
        
        # Passo 2: Converter o texto em um dicionário de ocorrências
        
        dict_word_count = self.text_word_count(plain_text)
        
        # Passo 3: Indexar cada palavra
        for key, freq in dict_word_count.items():
            self.index.index(key, doc_id, freq)

    def index_text_dir(self,path:str):

        for str_sub_dir in os.listdir(path):
            path_sub_dir = f"{path}/{str_sub_dir}"
