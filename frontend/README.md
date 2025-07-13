# Banco Digital com Digital Twin e Dashboard React

Este projeto consiste em um simulador de banco com funcionalidades de registro, autenticação, consulta de saldo, depósito e transferências via PIX, acompanhado de um Digital Twin dos usuários e um dashboard em React para visualização.

## Tecnologias Utilizadas

* **Backend**: FastAPI, Uvicorn
* **Banco de Dados**: PostgreSQL (ou SQLite para desenvolvimento)
* **ORM**: SQLAlchemy
* **Autenticação**: OAuth2 com JWT (python-jose)
* **Mensageria**: MQTT (paho-mqtt, Eclipse Mosquitto)
* **Frontend**: React (Create React App), Nginx para servir estáticos
* **Testes de Carga**: Locust
* **Infraestrutura**: Docker, Docker Compose

## Estrutura de Diretórios

```
/                  # diretório raiz do projeto
├── api/            # código Python da API
│   ├── main.py
│   ├── models.py
│   ├── requirements.txt
│   └── Dockerfile  # definição do container da API
├── frontend/       # dashboard React
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   └── Dockerfile  # build + nginx
├── docker-compose.yml
└── README.md       # você está aqui
```

## Rodando Localmente com Docker Compose

1. Clonar o repositório:

   ```bash
   git clone <seu-repo-url> digital-twin
   cd digital-twin
   ```
2. Subir todos os serviços:

   ```bash
   docker-compose down --remove-orphans
   docker-compose up -d --build
   ```
3. Verificar status:

   ```bash
   docker-compose ps
   ```
4. Testar endpoint de saúde da API:

   ```bash
   curl http://localhost:8000/ping
   # deve retornar {"pong": true}
   ```
5. Abrir o dashboard React:

   * Navegar em [http://localhost:3000](http://localhost:3000)

## Principais Endpoints da API

| Método | Rota                    | Descrição                                              |
| ------ | ----------------------- | ------------------------------------------------------ |
| POST   | `/register`             | Registra usuário (body JSON: `{ username, password }`) |
| POST   | `/token`                | Emite token JWT (form data: `username, password`)      |
| GET    | `/balance`              | Consulta saldo do usuário autenticado                  |
| POST   | `/deposit`              | Faz depósito (body JSON: `{ amount }`)                 |
| POST   | `/pix`                  | Transferência PIX (body JSON: `{ to_user, amount }`)   |
| GET    | `/logs`                 | Lista logs de operações do usuário                     |
| GET    | `/digital-twin/summary` | Estado agregado dos usuários no Digital Twin           |

> **Autenticação**: todas as rotas (exceto `/ping`, `/register` e `/token`) exigem cabeçalho:
> `Authorization: Bearer <access_token>`

## Dashboard React

O frontend é um aplicativo React gerado com Create React App e servido via Nginx. Após o build, ele está disponível em:

```
http://localhost:3000
```

## Testes e Qualidade

### Testes Unitários (pytest)

No diretório da API:

```bash
pip install -r api/requirements.txt
pytest api/tests
```

### Teste de Carga (Locust)

1. Instalar Locust no host:

   ```bash
   pip install locust
   ```
2. Rodar em modo headless:

   ```bash
   locust -f locustfile.py --headless -u 500 -r 50 --run-time 2m --host http://host.docker.internal:8000
   ```

## Implantação (Deployment)

Para subir em produção, ajuste variáveis de ambiente no `docker-compose.yml` ou em um arquivo `.env`:

```yaml
environment:
  - DATABASE_URL=postgresql://user:pass@host:5432/db
  - DB_POOL_SIZE=20
  - DB_MAX_OVERFLOW=30
  - DB_POOL_TIMEOUT=30
```

## Contribuindo

1. Faça um fork deste repositório
2. Crie uma branch com sua feature: `git checkout -b feature/nome`
3. Commit suas mudanças: `git commit -m "feat: descrição da feature"`
4. Envie para o repositório remoto: `git push origin feature/nome`
5. Abra um Pull Request

### Lint e formatação automática

Este projeto usa [pre-commit](https://pre-commit.com/) para:
- corrigir finais de linha e espaços em branco
- validar estilo com flake8
- checar tipagem com mypy
- rodar análises de segurança com bandit

Para instalar localmente (virtualenv ativado):

```bash
py -m pip install pre-commit
py -m pre_commit install
pre-commit run --all-files
