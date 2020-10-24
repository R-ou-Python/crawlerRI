from IPython.display import clear_output
from typing import List, Set, Union
from abc import abstractmethod
from functools import total_ordering
from os import path
import os
import pickle
import gc

class Index:
    def __init__(self):
        self.dic_index = {}
        self.set_documents = set()

        
    def index(self, term:str, doc_id:int, term_freq:int):
        if term not in self.dic_index:
            int_term_id = len(self.dic_index) + 1
            self.dic_index[term] = self.create_index_entry(int_term_id)
        else:
            int_term_id = self.get_term_id(term)
        
        # Adiciona id do documento na lista de documentos
        self.set_documents.add(doc_id)
        
        # Chama método para adicionar nova ocorrência de um termo
        self.add_index_occur(self.dic_index[term], doc_id, int_term_id, term_freq)

    @property
    def vocabulary(self) -> List:
        # Percorre o dicionário de termos para retornar apenas os termos
        indexList = []
        for index in self.dic_index:
            indexList.append(index)

        return indexList

    @property
    def document_count(self) -> int:
        return len(self.set_documents)

    @abstractmethod
    def get_term_id(self, term:str):
        raise NotImplementedError("Voce deve criar uma subclasse e a mesma deve sobrepor este método")


    @abstractmethod
    def create_index_entry(self, termo_id:int):
        raise NotImplementedError("Voce deve criar uma subclasse e a mesma deve sobrepor este método")

    @abstractmethod
    def add_index_occur(self, entry_dic_index, doc_id:int, term_id:int, freq_termo:int):
        raise NotImplementedError("Voce deve criar uma subclasse e a mesma deve sobrepor este método")

    @abstractmethod
    def get_occurrence_list(self, term:str) -> List:
        raise NotImplementedError("Voce deve criar uma subclasse e a mesma deve sobrepor este método")

    @abstractmethod
    def document_count_with_term(self,term:str) -> int:
         raise NotImplementedError("Voce deve criar uma subclasse e a mesma deve sobrepor este método")

    def finish_indexing(self):
        pass

    def __str__(self):
        arr_index = []
        for str_term in self.vocabulary:
            arr_index.append(f"{str_term} -> {self.get_occurrence_list(str_term)}")

        return "\n".join(arr_index)

    def __repr__(self):
        return str(self)

@total_ordering
class TermOccurrence():
    def __init__(self,doc_id:int,term_id:int, term_freq:int):
        self.doc_id = doc_id
        self.term_id = term_id
        self.term_freq = term_freq

    def write(self, idx_file):
        # salva na ordem certa no arquivo
        with open(idx_file,"wb+") as file:
            print(file.tell())
            file.write(self.term_id.to_bytes(4,byteorder="big"))
            file.write(self.doc_id.to_bytes(4,byteorder="big"))
            file.write(self.term_freq.to_bytes(4,byteorder="big"))
            print(file.tell())


    def __hash__(self):
    	return hash((self.doc_id,self.term_id))

    def __eq__(self,other_occurrence:"TermOccurrence"): #  retorna true se for igual
        if other_occurrence is None:
            return False
        # se o id do termo dela e o id do documento forem iguais
        if (self.doc_id == other_occurrence.doc_id) and (self.term_id == other_occurrence.term_id):
            return True
        else:
            return False


    # Retorna verdadeiro se o objeto corrrente self é menor do que o objeto passado como parametro
    def __lt__(self,other_occurrence:"TermOccurrence"):
        if other_occurrence is None:
            return True

        if (self.term_id < other_occurrence.term_id):
            return True
        elif (self.term_id == other_occurrence.term_id):
            if (self.doc_id < other_occurrence.doc_id): 
                return True
        return False


    def __str__(self):
        return f"(term_id:{self.term_id} doc: {self.doc_id} freq: {self.term_freq})"

    def __repr__(self):
        return str(self)


#HashIndex é subclasse de Index
class HashIndex(Index):
    def get_term_id(self, term:str):
        return self.dic_index[term][0].term_id

    def create_index_entry(self, termo_id:int) -> List:
        return []

    def add_index_occur(self, entry_dic_index:List[TermOccurrence], doc_id:int, term_id:int, term_freq:int):
        entry_dic_index.append(TermOccurrence(doc_id, term_id, term_freq))

    # Retorna a lista de ocorrencias de um determinado termo.
    def get_occurrence_list(self,term: str)->List:
        if term not in self.dic_index: # caso o termo nao exista, retorna vazio
            return []
        else: # se esta la, retorna a lista de ocorrencia
            return self.dic_index[term]
            
    # Retorna a quantidade de documentos que possuem um determinado termo
    def document_count_with_term(self,term:str) -> int:
        occurrence = self.get_occurrence_list(term)
        if len(occurrence) == 0: # Se o retorno for uma lista vazia, não ha documentos relacionados ao termo
            return 0
        else: # Se tiver, retorna a quantidade de docs, que é equivalente ao tam da lista
            return len(occurrence)





class TermFilePosition:
    def __init__(self,term_id:int,  term_file_start_pos:int=None, doc_count_with_term:int = None):
        self.term_id = term_id

        #a serem definidos após a indexação
        self.term_file_start_pos = term_file_start_pos
        self.doc_count_with_term = doc_count_with_term

    def __str__(self):
        return f"term_id: {self.term_id}, doc_count_with_term: {self.doc_count_with_term}, term_file_start_pos: {self.term_file_start_pos}"
    def __repr__(self):
        return str(self)
    

class FileIndex(Index): # armazena as ocorrencias em arquivo

    TMP_OCCURRENCES_LIMIT = 1000000

    def __init__(self):
        super().__init__()
        self.contador = 0
        self.old_file = ""
        self.destino_file = "new_file_2.idx"
        self.lst_occurrences_tmp = []
        self.idx_file_counter = 0
        self.str_idx_file_name = "occur_idx_file"

    def get_term_id(self, term:str):
        return self.dic_index[term].term_id

    def create_index_entry(self, term_id:int) -> TermFilePosition:
        return  TermFilePosition(term_id)

    def add_index_occur(self, entry_dic_index:TermFilePosition,  doc_id:int, term_id:int, term_freq:int):
        self.lst_occurrences_tmp.append(TermOccurrence(doc_id,term_id,term_freq))

        if len(self.lst_occurrences_tmp) >= FileIndex.TMP_OCCURRENCES_LIMIT:
            self.save_tmp_occurrences()


    def next_from_list(self) -> TermOccurrence:
        if len(self.lst_occurrences_tmp) == 0:
            return None
        else:
            return self.lst_occurrences_tmp.pop(0) #retorna o primeiro termo (removido da lista)


    def next_from_file(self,file_idx) -> TermOccurrence:
            #next_from_file = pickle.load(file_idx)
        
        with open(file_idx, "rb") as file:
            #bytes_doc_id = file_idx.read(4)
            #if not bytes_doc_id:
            #    return None
        
            file.seek(self.contador*4)
                
            doc_id = int.from_bytes(file.read(4),byteorder='big')
            term_id = int.from_bytes(file.read(4),byteorder='big')
            term_freq = int.from_bytes(file.read(4),byteorder='big')
            self.contador = self.contador + 3
            
            if doc_id == 0 or term_freq==0 or term_id==0:
                return None
        #seu código aqui :)

        return TermOccurrence(doc_id, term_id, term_freq)


    def save_tmp_occurrences(self):
        
        #ordena pelo term_id, doc_id
        #Para eficiencia, todo o codigo deve ser feito com o garbage
        #collector desabilitado
        gc.disable()
        
        
        if self.idx_file_counter == 0:
            self.str_idx_file_name = None
            self.str_idx_file_name = "occur_index_0"
            next_list = self.next_from_list()
            tam = len(self.lst_occurrences_tmp)
            for i in range(0,tam):
                next_list.write(self.str_idx_file_name)
                
        else:
            self.old_file = self.str_idx_file_name
            self.idx_file_counter = self.idx_file_counter + 1
            self.str_idx_file_name = "occur_index_" + str(self.idx_file_counter)
            
        
        
            #ordena pelo term_id, doc_id -- Com a sobrescrita dos métodos, a sorted vai ordenar por term_id
            list_sorted = sorted(self.lst_occurrences_tmp)
            self.lst_occurrences_tmp = list_sorted

            ### Abra um arquivo novo faça a ordenação externa: compar sempre a primeira posição
            ### da lista com a primeira posição do arquivo usando os métodos next_from_list e next_from_file
            ### para armazenar no novo indice ordenado
            next_list = self.next_from_list()
            next_file = self.next_from_file(self.old_file)

            while(next_list or next_file):
                if next_list <= next_file: # compara os term_id e pega o menor pra salvar no arquivo
                    next_list.write(self.str_idx_file_name)
                    next_list = self.next_from_list()
                else:
                    next_file.write(self.str_idx_file_name)
                    next_file = self.next_from_file(self.old_file)
        

            #remove old file
            try:
                os.remove(self.old_file)
            except OSError as e:
                print(e)
            else:
                print("File deleted successfully")
        
        gc.enable()
        self.lst_occurrences_tmp = [] # added

    def finish_indexing(self):
        if len(self.lst_occurrences_tmp) > 0:
            self.save_tmp_occurrences()

        #Sugestão: faça a navegação e obetenha um mapeamento 
        # id_termo -> obj_termo armazene-o em dic_ids_por_termo
        dic_ids_por_termo = {}
        for str_term,obj_term in self.dic_index.items():
            pass
        
        with open(self.str_idx_file_name,'rb') as idx_file:
            #navega nas ocorrencias para atualizar cada termo em dic_ids_por_termo 
            #apropriadamente
            pass

    def get_occurrence_list(self,term: str)->List:
        return []
    def document_count_with_term(self,term:str) -> int:
        return 0
