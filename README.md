# simulacao_de_banco
Este repositório contém uma API bancária completa desenvolvida com FastAPI, SQLite e SQLAlchemy, oferecendo funcionalidades de registro de usuários, login com JWT, consulta de saldo, depósitos e transferências via Pix, além de endpoint para logs de ações
FastAPI
SQLAlchemy
. O projeto segue boas práticas de segurança baseadas na OWASP API Security Top 10, incluindo proteção contra injeção SQL, autenticação robusta e registro detalhado de logs de ações
OWASP Foundation
OWASP Foundation
. Inclui testes unitários e de integração utilizando pytest para validar cada endpoint e garantir cobertura contra vulnerabilidades como brute force, mass assignment e autorização em nível de objeto
pytest Documentation
OWASP Foundation
. Este README detalha instruções de instalação, execução, testes e considerações de segurança para facilitar o uso e manutenção
GitHub Docs
.
Features

A API oferece as seguintes funcionalidades principais
GitHub
:

    Registro de usuário

    Autenticação e geração de token JWT

    Consulta de saldo

    Depósito

    Transferência via Pix

    Logs de ações com timestamp

Tech Stack

O projeto utiliza FastAPI como framework web, SQLite como banco de dados relacional, SQLAlchemy como ORM e PyJWT para geração e verificação de tokens JWT
FastAPI
SQLAlchemy
.
Installation

Utilize um ambiente virtual Python e instale as dependências com:

pip install -r requirements.txt

que inclui fastapi, uvicorn[standard], sqlalchemy, passlib[bcrypt] e python-jose
Stack Overflow
Uvicorn
.
O arquivo requirements.txt pode ser gerado com pip freeze > requirements.txt para reproduzir o ambiente
GitHub
.
Usage

Para iniciar o servidor em modo de desenvolvimento:

uvicorn main:app --reload

Uvicorn
FastAPI
.
API Endpoints

Os principais endpoints disponíveis são
FastAPI
:

    POST /register – cria usuário

    POST /login – autentica e retorna JWT

    GET /balance – consulta saldo

    POST /deposit – realiza depósito

    POST /pix – transfere via Pix

    GET /logs – retorna histórico de ações

Testing

Os testes unitários e de integração são implementados com pytest, localizados na pasta tests, e podem ser executados via:

pytest

pytest Documentation
. Eles cobrem registro, login, operações bancárias e verificação de segurança como injeção SQL e brute force
OWASP Foundation
OWASP Foundation
.
Security Considerations

Este projeto segue as recomendações do OWASP API Security Top 10, incluindo tratamento de SQL injection, limitação de tentativas de login e validação de ações do usuário
OWASP Foundation
OWASP Foundation
. Tokens JWT têm expiração configurada por padrão, e recomenda-se armazenar segredos em variáveis de ambiente para maior segurança
PyPI
.
Contributing

Patches, issues e sugestões são bem-vindos. Por favor, abra uma issue ou pull request no GitHub
GitHub Docs
.
License

Este projeto está licenciado sob a MIT License.
