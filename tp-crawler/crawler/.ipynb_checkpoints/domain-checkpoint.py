from datetime import datetime
from collections import OrderedDict

class Domain():
	def __init__(self,nam_domain,int_time_limit_between_requests):
		self.time_last_access = datetime(1970,1,1)
		self.nam_domain = nam_domain
		self.int_time_limit_seconds  = int_time_limit_between_requests

	@property
	def time_since_last_access(self): # Atributo calculado que retorna um objeto TimeDelta com a diferença da data atual e a data do último acesso. Veja os exemplos de uso do TimeDelta na sua documentação
		obj = (datetime.now() - self.time_last_access)
		return obj.total_seconds

	def accessed_now(self): # Método que modifica o último acesso com a data/hora atual usando um objeto datetime
		self.time_last_access = datetime.now() 

	def is_accessible(self): # Método que verdadeiro se o domínio estiver acessível
		if self.time_since_last_access() <= self.int_time_limit_seconds:
			return False
		else:
			return True

	def __hash__(self): # associa um valor de retorno para o objeto
		return hash(self.nam_domain)

	def __eq__(self, domain):
		return domain == self.nam_domain

	def __str__(self): # retorna uma string que representa o objeto
		return self.nam_domain

	def __repr__(self): # chama __str__
		return str(self)
