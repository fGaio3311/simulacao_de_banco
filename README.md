📄 Documentação: tests/test_api.py
📌 Objetivo

Este script implementa testes automatizados para uma API bancária baseada em FastAPI. Os testes cobrem:

    Funcionalidades básicas (registro, login, saldo, depósito, PIX, logs)

    Testes de segurança e vulnerabilidades comuns, como:

        Injeção de SQL

        Autenticação quebrada

        Atribuição indevida de atributos

        Uso excessivo de recursos

        Falta de monitoramento/logs

⚙️ Setup e Fixtures
🔧 Banco de Testes com SQLite

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

Usa SQLite em memória para testes rápidos e isolados, sem afetar o banco real.
🔁 client Fixture

@pytest.fixture(scope="module")
def client():

Cria um cliente de teste com TestClient, usando uma versão sobrescrita de get_db() para conectar ao banco de testes.
✅ Testes de Funcionalidades Básicas
🔐 test_register_and_login

Testa:

    Registro de usuário com /register

    Login com /login

    Verifica se o token de autenticação é retornado

💰 test_balance_deposit_and_pix_and_logs

Testa:

    Consulta de saldo inicial

    Depósito de valor

    Transferência via PIX

    Registro de ações no log

Assegura que todas essas ações sejam registradas corretamente.
🔐 Testes de Segurança (Vulnerabilidades OWASP)

🛡️ test_sql_injection_login

Simula injeção SQL no login com:

{"username": "' OR 1=1 --", "password": "x"}

Valida que o sistema rejeita com status 401 (não autorizado).
🚪 test_broken_authentication_bruteforce

Tenta força bruta com várias senhas erradas. Espera que o sistema continue retornando 401 sem bloquear ou limitar requisições (o que seria uma falha de segurança).

🔓 test_broken_object_level_authorization

Testa se um usuário pode acessar dados de outro (/balance/2). Espera-se 401 ou 403, para impedir acesso não autorizado.

🧬 test_mass_assignment_on_register

Tenta manipular atributos protegidos (como balance) durante o registro:

{"username": "eve", "password": "senha789", "balance": 1000000}

Espera que o saldo real de eve seja 0, evitando mass assignment.

⚠️ test_unrestricted_resource_consumption

Simula um depósito com valor extremamente alto:

big_amount = 10**18

Espera que o sistema trate com erro (400) ou aceite com controle.

📋 test_insufficient_logging_and_monitoring

Verifica se uma ação (como consultar saldo) é registrada nos logs. Exige que logs estejam funcionando como forma de monitoramento.
📎 Observações Finais

    Os testes usam uma abordagem black-box e simulam o comportamento real do usuário.

    Cobrem tanto funcionalidade esperada quanto possíveis ataques/explorações.

    A estrutura pode ser expandida para incluir testes de performance, autenticação multi-fator, verificação de tempo de resposta etc.
