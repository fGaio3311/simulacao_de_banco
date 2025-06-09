
import json
import requests
import statistics
from collections import defaultdict
from datetime import datetime

class LogsExporter:
    """
    Faz uma requisição GET em /logs, extrai todos os eventos e grava em um arquivo JSON-lines.
    """

    def __init__(self, api_base_url: str, token: str, output_path: str):
        self.api_base_url = api_base_url.rstrip("/")      # ex: "http://localhost:8000"
        self.token = token                                # token JWT obtido após login
        self.output_path = output_path                    # caminho do arquivo onde será salvo

    def fetch_all_logs(self):
        """
        Chama GET /logs e retorna a lista de dicionários (cada dicionário é um evento).
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.get(f"{self.api_base_url}/logs", headers=headers)
        resp.raise_for_status()
        return resp.json()  # Ex: [ { "timestamp": "...", "user": "...", "action": "...", ... }, ... ]

    def write_to_file(self):
        """
        Grava cada evento em uma linha JSON no arquivo de saída.
        """
        events = self.fetch_all_logs()
        with open(self.output_path, "w", encoding="utf-8") as f:
            for ev in events:
                # Evita campos que não sejam JSON-serializáveis, se houver
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        print(f"[export_logs] Gravados {len(events)} eventos em {self.output_path}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Uso: python export_logs.py <API_BASE_URL> <TOKEN> <ARQUIVO_SAIDA>")
        sys.exit(1)

    api_url = sys.argv[1]      # ex: "http://localhost:8000"
    token = sys.argv[2]        # JWT retornado pela rota /login
    output_path = sys.argv[3]  # ex: "logs.jsonl"

    exporter = LogsExporter(api_url, token, output_path)
    exporter.write_to_file()

import json
from collections import defaultdict
from datetime import datetime

class DigitalTwin:
    """
    Classe que mantém o estado interno dos usuários e aplica eventos de log,
    atualizando saldos e armazenando estatísticas (número de logins, total depositado etc.).
    """

    def __init__(self):
        # Exemplo de estado por usuário:
        # {
        #   "alice": {
        #       "saldo": 100,
        #       "ultimo_login": datetime(...),
        #       "total_depositado": 150,
        #       "total_pix_env": 30,
        #       "total_pix_rec": 0,
        #       "n_logins": 1,
        #       "n_consultas_saldo": 1,
        #       ...
        #   },
        #   ...
        # }
        self.users = defaultdict(lambda: {
            "saldo": 0,
            "ultimo_login": None,
            "total_depositado": 0,
            "total_pix_enviado": 0,
            "total_pix_recebido": 0,
            "n_logins": 0,
            "n_consultas_saldo": 0,
            "n_depositos": 0,
            "n_pix": 0,
            # você pode adicionar outros campos conforme necessidade
            "pix_amount_enviados": [],
            "pix_amount_recebidos": [],
            "login_timestamps": [],
            "deposit_amounts": [],
            "statistics": [],
        })

    def apply_event(self, event: dict):
        """
        Recebe um dicionário event, com pelo menos as chaves:
        - "timestamp": string ISO (ex: "2025-05-20T12:00:00")
        - "user": nome do usuário que executou a ação (ex: "alice")
        - "action": tipo da ação: "login", "balance", "deposit", "pix"
        - outros campos: "amount", "to_user", etc.
        """

        # Parseia timestamp para datetime (se vier em string ISO)
        ts = event.get("timestamp")
        try:
            timestamp = datetime.fromisoformat(ts)
        except Exception:
            # Se já for datetime ou estiver malformatado, ignora parsing
            timestamp = None

        user = event.get("user")
        action = event.get("action")

        if user not in self.users:
            # Isso dispara o lambda default, já inicializando valores
            _ = self.users[user]

        estado = self.users[user]

        if action == "login":
            estado["ultimo_login"] = timestamp
            estado["n_logins"] += 1
            if timestamp:
                estado["login_timestamps"].append(timestamp)

        elif action == "balance":
            # apenas conta como consulta de saldo
            estado["n_consultas_saldo"] += 1

        elif action == "deposit":
            amount = event.get("amount", 0)
            # atualiza saldo e estatísticas
            try:
                amt = float(amount)
            except (TypeError, ValueError):
                amt = 0
            estado["saldo"] += amt
            estado["total_depositado"] += amt
            estado["n_depositos"] += 1
            estado["deposit_amounts"].append(amt)

        elif action == "pix":
            amount = float(event.get("amount", 0))
            to_user = event.get("to_user") or event.get("destinatario") or event.get("recipient")
            # Atualiza saldo do emitente
            try:
                amt = float(amount)
            except (TypeError, ValueError):
                amt = 0
            estado["saldo"] -= amt
            estado["total_pix_enviado"] += amt
            estado["n_pix"] += 1
            estado["pix_enviado_amounts"].append(amt)

            # Atualiza quem recebeu, se o campo existir
            if to_user:
                if to_user not in self.users:
                    _ = self.users[to_user]
                receiver_state = self.users[to_user]
                receiver_state["saldo"] += amt
                receiver_state["total_pix_recebido"] += amt
                receiver_state["pix_recebido_amounts"].append(amt)

        else:
            # Ação não reconhecida: apenas ignora ou imprime aviso
            print(f"[DigitalTwin] Ação desconhecida: {action}")

    def summary(self):
        """
        Retorna um relatório simples (em forma de dict) com o estado atual de cada usuário.
        """
        report = {}
        for user, estado in self.users.items():
            report[user] = {
                "saldo": estado["saldo"],
                "último_login": estado["ultimo_login"].isoformat() if estado["ultimo_login"] else None,
                "n_logins": estado["n_logins"],
                "n_consultas_saldo": estado["n_consultas_saldo"],
                "total_depositado": estado["total_depositado"],
                "n_depositos": estado["n_depositos"],
                "total_pix_enviado": estado["total_pix_enviado"],
                "total_pix_recebido": estado["total_pix_recebido"],
                "n_pix": estado["n_pix"],
            }
        return report

def compute_statistics(self, user:str):

    estado = self.users[user]

    pix_med_enviado = None

    if estado["n_pix_enviado"] > 0:
        pix_med_enviado = statistic.mean(estado["pix_amounts_enviados"])
    
    pix_med_recebido = None

    if estado["n_pix_recebido"] > 0:
        pix_med_recebido = statistic.mean(estado["pix_amounts_recebidos"])

    deposito_medio = None

    if estado["n_depositos"] > 0:
        deposito_medio = statistic.mean(estado["deposit_amounts"])

    janela_medio = None

    if len(estado["login_timestamps"]) >= 2:
        horas = []
        login_timestamps = estado["login_timestamps"]
        
        for hr in estado["login_timestamps"]:
            hora_decimal = hr.hour + hr.minute/60 + hr.second/3600 
            horas.append(hora_decimal)

    janela_media = statistic.mean(horas)

    estado["statistics"] = {
        "pix_med_enviado": pix_med_enviado,
        "pix_med_recebido": pix_med_recebido,
        "deposito_medio": deposito_medio,
        "janela_media": janela_media,
    # Você pode incluir também desvio-padrão ou quantis:
        "dp_pix_enviado": statistics.pstdev(estado["pix_amounts_enviados"]) if estado["n_pix_enviado"] > 1 else None,
        "dp_deposito": statistics.pstdev(estado["deposit_amounts"]) if estado["n_depositos"] > 1 else None,
    }
        
def process_logs_file(file_path: str, twin: DigitalTwin):
    """
    Abre um arquivo JSON-lines (um JSON por linha), faz json.loads e chama twin.apply_event() para cada.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                print(f"[process_logs_file] Linha {idx} não é JSON válido, pulando.")
                continue
            twin.apply_event(ev)

if __name__ == "__main__":
    """
    Exemplo de uso:

    1. Primeiro, execute o export_logs.py para gerar logs.jsonl:
       python export_logs.py http://localhost:8000 <TOKEN_JWT> logs.jsonl

    2. Depois, rode este módulo para processar:
       python digital_twin.py logs.jsonl

    Isso vai imprimir, ao final, um sumário do estado de cada usuário.
    """
    import sys

    if len(sys.argv) != 2:
        print("Uso: python digital_twin.py <CAMINHO_PARA_logs.jsonl>")
        sys.exit(1)

    caminho = sys.argv[1]
    twin = DigitalTwin()
    process_logs_file(caminho, twin)

    # Exibe um resumo formatado
    summary = twin.summary()
    print("=== Resumo do Estado do Digital Twin ===")
    for user, st in summary.items():
        print(f"- Usuário: {user}")
        print(f"    Saldo atual: {st['saldo']}")
        print(f"    Último login: {st['último_login']}")
        print(f"    Nº logins: {st['n_logins']}")
        print(f"    Nº consultas de saldo: {st['n_consultas_saldo']}")
        print(f"    Total depositado: {st['total_depositado']}")
        print(f"    Nº depósitos: {st['n_depositos']}")
        print(f"    Total PIX enviado: {st['total_pix_enviado']}")
        print(f"    Total PIX recebido: {st['total_pix_recebido']}")
        print(f"    Nº total de PIX: {st['n_pix']}")
        print("----------------------------------------")
