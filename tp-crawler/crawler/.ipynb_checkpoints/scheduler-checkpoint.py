from urllib import robotparser
from util.threads import synchronized
from collections import OrderedDict
from crawler.domain import Domain
from urllib.parse import urlparse, urlunparse
import time 
import urllib.robotparser

class Scheduler():
    #tempo (em segundos) entre as requisições
    TIME_LIMIT_BETWEEN_REQUESTS = 20

    def __init__(self,str_usr_agent,int_page_limit,int_depth_limit,arr_urls_seeds):
        """
            Inicializa o escalonador. Atributos:
                - `str_usr_agent`: Nome do `User agent`. Usualmente, é o nome do navegador, em nosso caso,  será o nome do coletor (usualmente, terminado em `bot`)
                - `int_page_limit`: Número de páginas a serem coletadas
                - `int_depth_limit`: Profundidade máxima a ser coletada
                - `int_page_count`: Quantidade de página já coletada
                - `dic_url_per_domain`: Fila de URLs por domínio
                - `set_discovered_urls`: Conjunto de URLs descobertas, ou seja, que foi extraída em algum HTML e já adicionadas na fila - mesmo se já ela foi retirada da fila. A URL armazenada deve ser uma string.
                - `dic_robots_per_domain`: Dicionário armazenando, para cada domínio, o objeto representando as regras obtidas no `robots.txt`
        """
        self.str_usr_agent = str_usr_agent
        self.int_page_limit = int_page_limit
        self.int_depth_limit = int_depth_limit
        self.int_page_count = 0

        self.dic_url_per_domain = OrderedDict()
        self.set_discovered_urls = set()
        self.dic_robots_per_domain = {}
        
        for url in arr_urls_seeds: # cria um url parse para cada posicao do array e adiciona com profundidade de coleta 0 com add_new_page
            urlParse = urlparse(url)
            self.add_new_page(urlParse,0)


    @synchronized
    def count_fetched_page(self):
        """
            Contabiliza o número de paginas já coletadas
        """
        self.int_page_count += 1

    def has_finished_crawl(self):
        """
            Verifica se finalizou a coleta
        """
        if(self.int_page_count > self.int_page_limit):
            return True
        return False


    @synchronized
    def can_add_page(self,obj_url,int_depth):
        """
            Retorna verdadeiro caso  profundade for menor que a maxima
            e a url não foi descoberta ainda
        """

        # verifica se a página não foi descoberta ainda e se a profundidade dela é menor que a profundidade limite
        if obj_url not in self.set_discovered_urls and int_depth <= self.int_depth_limit:
            # se as condicoes sao verdadeiras, retorna True
            return True
        else:
            return False


    @synchronized
    def add_new_page(self,obj_url,int_depth):
        """
            Adiciona uma nova página
            obj_url: Objeto da classe ParseResult com a URL a ser adicionada
            int_depth: Profundidade na qual foi coletada essa URL
        """
        #https://docs.python.org/3/library/urllib.parse.html
        
        # cria um objeto Domain com o netloc do Objeto da classe ParseResult com a URL e com o tempo entre requisicoes
        obj_domain = Domain(obj_url.netloc, self.TIME_LIMIT_BETWEEN_REQUESTS)
        
        # verifica se a pagina pode ser adicionada e retorna false se não puder. Assim, a url nao foi adicionada
        if self.can_add_page(obj_url,int_depth) == False:
            return False

        else: # se puder, adiciona o objeto como key do dicionario de urls por dominio coma profundidade de coleta como value
            if (obj_domain in self.dic_url_per_domain):
                self.dic_url_per_domain[obj_domain].append((obj_url, int_depth))
            else:
                self.dic_url_per_domain[obj_domain] = [(obj_url, int_depth)]
            
            self.set_discovered_urls.add(obj_url) # armazenar que este parseresult já foi descoberto
            return True


    @synchronized
    def get_next_url(self):
        """
        Obtem uma nova URL por meio da fila. Essa URL é removida da fila.
        Logo após, caso o servidor não tenha mais URLs, o mesmo também é removido.
        """
        # pega as keys do dicionario de urls
        domains = list(self.dic_url_per_domain.keys())
        
        while (True):
            for domain in domains: # itera sobre as keys
                if domain.is_accessible() == True: # verifica se o dominio esta acessivel. Se sim, marque como acessado
                    domain.accessed_now()
                    if len(self.dic_url_per_domain[domain]) == 0: # verifica se o value do dominio no dicionario esta vazio
                        self.dic_url_per_domain.pop(domain, None)
                    else:
                        return self.dic_url_per_domain[domain].pop(0) # remove url da fila

            time.sleep(self.TIME_LIMIT_BETWEEN_REQUESTS) # espera  o tempo entre requisicoes
        
        """
        TIME_LIMIT_BETWEEN_REQUESTS não é a melhor métrica de variável para isso.
        Melhor tática possível é implementar exponential backoff
        """
    def can_fetch_page(self,obj_url):
        """
        Verifica, por meio do robots.txt se uma determinada URL pode ser coletada
        """
        
        if (obj_url.netloc in self.dic_robots_per_domain):
            robotFileParser = self.dic_robots_per_domain[obj_url.netloc]
        else:
            robotFileParser = urllib.robotparser.RobotFileParser()
            robotsTxt = obj_url.scheme + '://' + obj_url.netloc + '/robots.txt'
            robotFileParser.set_url(robotsTxt)
            robotFileParser.read()
            self.dic_robots_per_domain[obj_url.netloc] = robotFileParser

        return robotFileParser.can_fetch("*", urlunparse(obj_url))
      
