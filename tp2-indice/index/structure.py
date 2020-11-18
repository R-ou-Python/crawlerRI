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
        idx_file.write(self.term_id.to_bytes(4,byteorder="big"))
        idx_file.write(self.doc_id.to_bytes(4,byteorder="big"))
        idx_file.write(self.term_freq.to_bytes(4,byteorder="big"))

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
        
        self.lst_occurrences_tmp = []
        self.idx_file_counter = 0
        self.str_idx_file_name = None

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
        # Tratar nome de arquivo igual a None (aplicado na primeira iteração do save_tmp_occurrences)
        if(file_idx is None):
            return None
                
        doc_id = int.from_bytes(file_idx.read(4),byteorder='big')
        term_id = int.from_bytes(file_idx.read(4),byteorder='big')
        term_freq = int.from_bytes(file_idx.read(4),byteorder='big')
        
        if doc_id == 0 or term_freq == 0 or term_id == 0:
            return None
        
        return  TermOccurrence(term_id, doc_id, term_freq)   

    
    def save_tmp_occurrences(self):
        
        #ordena pelo term_id, doc_id
        #Para eficiencia, todo o codigo deve ser feito com o garbage collector desabilitado
        gc.disable()
        
        self.lst_occurrences_tmp = sorted(self.lst_occurrences_tmp)
        
        # Gerando o padrão de nomenclatura para o próximo documento
        str_idx_new_file_name = 'occur_index_' + str(self.idx_file_counter)     
        
        with open(str_idx_new_file_name, 'wb') as new_idx_file:
            try:
                idx_file = open(self.str_idx_file_name, 'rb')
            except:
                idx_file = None
            
            # Pegando o primeiro TermOcurrence da lista e do arquivo
            next_list = self.next_from_list()
            next_file = self.next_from_file(idx_file)

            # Ordenação externa
            while(next_list or next_file):
                if next_list <= next_file:
                    next_list.write(new_idx_file)
                    next_list = self.next_from_list()
                else:
                    next_file.write(new_idx_file)
                    next_file = self.next_from_file(idx_file)

            if(idx_file is not None): idx_file.close()
                
        #remove old file
        if self.str_idx_file_name:
            os.remove(self.str_idx_file_name)
        
        # Ataualizar nome do arquivo corrente
        self.str_idx_file_name = str_idx_new_file_name
        
        #Adicionar file_counter
        self.idx_file_counter = self.idx_file_counter + 1
        
        #Zerar lista de ocorrências
        self.lst_occurrences_tmp = []
        
        gc.enable()

    def finish_indexing(self):
        if len(self.lst_occurrences_tmp) > 0:
            self.save_tmp_occurrences()

        #Sugestão: faça a navegação e obetenha um mapeamento 
        # id_termo -> obj_termo armazene-o em dic_ids_por_termo
        dic_ids_por_termo = {}
        
        for str_term, obj_term in self.dic_index.items(): # separa dict em chave, valor
            dic_ids_por_termo[obj_term.term_id] = obj_term # obj do tipo TermFilePosition(term_id,term_file_start_pos, doc_count_with_term)
          
        with open(self.str_idx_file_name,'rb') as idx_file:
            #navega nas ocorrencias para atualizar cada termo em dic_ids_por_termo apropriadamente
            # por atualizar, entende-se colocar um valor diferente do 0 colocado por default
            next_file = self.next_from_file(idx_file)
            position = 0
            while(next_file):
                # Item do dicionário - pega os values da proxima key no dicionario
                item_dic = dic_ids_por_termo[next_file.term_id]
                
                # Adicionando contagem - Quantas vezes o termo aparece no arquivo
                newCount = item_dic.doc_count_with_term
                if newCount is None : newCount = 0
                item_dic.doc_count_with_term = newCount + 1
                
                # Adicionando posição inicial to termo dentro do arquivo final - occur_index_<indice>
                if item_dic.term_file_start_pos is None:
                    item_dic.term_file_start_pos = position * 12
                
                # Salvando atualização no dicionário
                dic_ids_por_termo[next_file.term_id] = item_dic
                
                next_file = self.next_from_file(idx_file)
                position = position + 1
        
        
    def get_occurrence_list(self,term: str)->List:
        occurrence_list = []
        # faz a busca no dicionario e pega os objetos TermFilePosition
        if term not in self.dic_index:
            return occurrence_list
        else:
            obj_TermFilePosition = self.dic_index[term]
            termo_busca = obj_TermFilePosition.term_id
            
            with open(self.str_idx_file_name, 'rb') as idx_file:
                # Posiciona a leitura do arquivo no início da listagem do termo buscado
                idx_file.seek(self.dic_index[term].term_file_start_pos)
                
                # Pegando o primeiro TermOcurrence respectivo ao term buscado
                next_file = self.next_from_file(idx_file)

                # Percorre o arquivo em busca de novas ocorrências de term
                # como o term_id encontra-se agrupado no arquivo, a partir do momento que lemos outro, sai do while
                while(next_file is not None and termo_busca == next_file.term_id):
                    occurrence_list.append(next_file)
                    next_file = self.next_from_file(idx_file)
            return occurrence_list
    
    
    def document_count_with_term(self,term:str) -> int:
        if term in self.dic_index:
            return self.dic_index[term].doc_count_with_term
        return 0
