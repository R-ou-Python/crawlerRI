from bs4 import BeautifulSoup
from threading import Thread
import requests
from urllib.parse import urlparse, urlunparse, urljoin

class PageFetcher(Thread):
    def __init__(self, obj_scheduler):
        self.obj_scheduler = obj_scheduler
        self.crawlerName = "CrawlerBot(nathaclmpaulino.github.io/crawlerRI/infoCrawlerBot)"

    def request_url(self,obj_url):
        """
            Faz a requisição e retorna o conteúdo em binário da URL passada como parametro

            obj_url: Instancia da classe ParseResult com a URL a ser requisitada.
        """
        try:
            headers = {'user-agent': self.crawlerName}
            response = requests.get(urlunparse(obj_url), headers=headers)
            if response != None:
                if response.status_code != 200:
                    return None
                if 'text/html' in response.headers['Content-Type']:
                    print(urlunparse(obj_url))
                    return response.content
    
            return None
        except:
            return None

    def discover_links(self,obj_url,int_depth,bin_str_content):
        """
        Retorna os links do conteúdo bin_str_content da página já requisitada obj_url
        """
        soup = BeautifulSoup(bin_str_content, "html.parser")
        dominio = obj_url.netloc
        
        for link in soup.select('a'):
            
            if link.get('href') == None:
                pass
            else:
                obj_new_url = link.attrs['href']
                urlParse = urlparse(obj_new_url)
            
                # Quando a URL é encurtada
                if urlParse.netloc == '':
                    new_url = obj_url.scheme + '://' + dominio + '/' + urlParse.path
                    urlParse = urlparse(new_url)

                int_new_depth = 0
                if urlParse.netloc == dominio:
                    int_new_depth = int_depth+1
                
                yield(urlParse, int_new_depth)
        
    def crawl_new_url(self):
        """
            Coleta uma nova URL, obtendo-a do escalonador
        """
        url_returned = self.obj_scheduler.get_next_url()
        
        if self.obj_scheduler.can_fetch_page(url_returned[0]):
            print(self.obj_scheduler.can_fetch_page(url_returned[0]))
            print("oi")
            return None
        else:
            binary_content = self.request_url(url_returned[0])
        
            if binary_content != None:
                return self.discover_links(url_returned[0], url_returned[1], binary_content)
            else:
                return None

    def run(self):
        """
            Executa coleta enquanto houver páginas a serem coletadas
        """
        
        # Se não terminou de fazer o crawling
        
        while self.obj_scheduler.has_finished_crawl() == False:
            # Pega todos os conjuntos de tuplas da crawl (retorno da discovery_links
            generator = self.crawl_new_url()
            if generator != None:
                self.obj_scheduler.count_fetched_page()
                # Para cada tupla do conjunto, verificar se é possível adicionar, se é, adiciona no contador.
                for url_discovered,depth_url_discovered in generator: 
                    if self.obj_scheduler.can_add_page(url_discovered, depth_url_discovered):
                        self.obj_scheduler.add_new_page(url_discovered, depth_url_discovered)
                    
