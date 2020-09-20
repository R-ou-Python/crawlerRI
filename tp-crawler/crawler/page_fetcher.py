from bs4 import BeautifulSoup
from threading import Thread
import requests
from urllib.parse import urlparse, urlunparse, urljoin

class PageFetcher(Thread):
    def __init__(self, obj_scheduler):
        self.obj_scheduler = obj_scheduler
        self.crawlerName = "Nome do coletor"



    def request_url(self,obj_url):
        """
            Faz a requisição e retorna o conteúdo em binário da URL passada como parametro

            obj_url: Instancia da classe ParseResult com a URL a ser requisitada.
        """
        headers = {'user-agent': self.crawlerName}
        response = requests.get(urlunparse(obj_url), headers=headers)
        
        if 'text/html' in response.headers['Content-Type']:
            return response.content
        
        return None
       
    def discover_links(self,obj_url,int_depth,bin_str_content):
        """
        Retorna os links do conteúdo bin_str_content da página já requisitada obj_url
        """
        soup = BeautifulSoup(bin_str_content,features="lxml")
        for link in soup.select(None):
            obj_new_url = None
            int_new_depth = None

            yield obj_new_url,int_new_depth

    def crawl_new_url(self):
        """
            Coleta uma nova URL, obtendo-a do escalonador
        """
        pass

    def run(self):
        """
            Executa coleta enquanto houver páginas a serem coletadas
        """
        pass
