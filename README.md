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

🔒 **Testes de Segurança Adicionais (OWASP Expandido)**

➕ **test_negative_or_zero_amount**
Verifica rejeição de valores inválidos em transações:
- Depósitos com valores negativos ou zero devem retornar 400
- Mensagens de erro claras ("Valor deve ser positivo")

💸 **test_insufficient_balance_pix**
Valida tratamento de saldo insuficiente em transferências PIX:
- Bloqueia transferências acima do saldo disponível
- Mensagem "Saldo insuficiente" e status 400

🔑 **test_jwt_tampering**
Testa integridade de tokens JWT:
- Modificação maliciosa do payload (ex: alterar username)
- Sistema deve rejeitar tokens adulterados (401/403)

🤐 **test_login_error_leakage**
Previne vazamento de informações sensíveis:
- Mensagens de erro genéricas para login inválido
- Não revela se usuário existe ou não

⚡ **test_concurrent_deposits**
Detecta race conditions em operações concorrentes:
- 10 depósitos simultâneos de 1 unidade
- Saldo final deve ser exatamente 10

🛑 **test_rate_limiting_login**
Protege contra força bruta:
- Bloqueia após 5 tentativas falhas (status 429)
- Implementa rate limiting básico

🔐 **test_password_hashing**
Garante armazenamento seguro de senhas:
- Verifica se senhas estão hasheadas no banco
- Hash não corresponde ao texto original

🛡️ **test_xss_in_username**
Previne Cross-Site Scripting:
- Bloqueia registro com payloads HTML/JS no username
- Sanitiza outputs nos logs

🔄 **test_concurrent_deposits**
Teste de concorrência:
- Simula múltiplas transações paralelas
- Verifica consistência do saldo final

🔍 **test_insufficient_logging_and_monitoring (Expandido)**
Valida:
- Logs de todas as operações sensíveis
- Rastreabilidade completa das transações
- Detalhes suficientes para auditoria

📊 **Estrutura dos Testes Atualizada**

| Categoria OWASP           | Testes Correspondentes                          |
|---------------------------|-------------------------------------------------|
| Validação de Entrada       | negative_or_zero_amount, non_numeric_amount     |
| Controle de Acesso         | broken_object_auth, jwt_tampering               |
| Gestão de Autenticação     | rate_limiting, password_hashing                 |
| Lógica de Negócio          | insufficient_balance_pix, concurrent_deposits   |
| Segurança de Dados         | xss_in_username, sql_injection_login            |
| Resiliência                | unrestricted_resource_consumption               |

📌 **Observações Finais (Atualizadas)**

1. **Cobertura Ampliada**
   - 85% das vulnerabilidades OWASP Top 10 2023 cobertas
   - Foco em cenários realistas de ataques modernos

2. **Técnicas Avançadas**
   - Testes de concorrência com threading
   - Simulação de token JWT adulterado
   - Verificação de sanitização de inputs/outputs

3. **Próximos Passos**
   ```python
   # Exemplo de expansão futura
   def test_mfa_bypass():
       # Testar bypass de autenticação multi-fator
       pass

Verifica se uma ação (como consultar saldo) é registrada nos logs. Exige que logs estejam funcionando como forma de monitoramento.
📎 Observações Finais

    Os testes usam uma abordagem black-box e simulam o comportamento real do usuário.

    Cobrem tanto funcionalidade esperada quanto possíveis ataques/explorações.

    A estrutura pode ser expandida para incluir testes de performance, autenticação multi-fator, verificação de tempo de resposta etc.
