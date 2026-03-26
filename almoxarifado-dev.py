#!/usr/bin/env python3
import json
import urllib.request
import os
import sys
import time
import csv
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO FIREBASE ---
FIREBASE_URL = "https://almoxarifado-dacbe-default-rtdb.firebaseio.com"

# --- CORES ANSI ---
CLEAR = "\033[2J\033[H"
BOLD = "\033[1m"
GREEN = "\033[32m"
BLUE = "\033[34m"
RED = "\033[31m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RESET = "\033[0m"

# --- ESTADO GLOBAL ---
CONFIG = {"LOW_STOCK_THRESHOLD": 5, "PASSWORD": "jonas"}

# --- UTILITÁRIOS DB ---
def fb_request(path, method="GET", data=None):
    url = f"{FIREBASE_URL}/{path}.json"
    req = urllib.request.Request(url, method=method)
    if data is not None:
        req.add_header('Content-Type', 'application/json')
        data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req, data=data) as response:
            res = response.read().decode('utf-8')
            return json.loads(res) if res else None
    except Exception as e:
        print(f"\n{RED}[ERRO] {e}{RESET}")
        return None

def get_products(): return [{"id": k, **v} for k, v in (fb_request("products") or {}).items()]
def get_employees(): return [{"id": k, **v} for k, v in (fb_request("employees") or {}).items()]
def get_transactions(): return [{"id": k, **v} for k, v in (fb_request("transactions") or {}).items()]

# --- INTERFACE ---
def header():
    print(CLEAR)
    print(BOLD + BLUE + r"""
    ___    __                                  _ ____            __            ____            
   /   |  / /___ ___  ____  _  ______ ______ _/ / __/___ ______ / /___         / __ \___ _   __ 
  / /| | / / __ `__ \/ __ \| |/_/ __ `/ ___/ / / /_/ __ `/ ___// / __ \______/ / / / _ \ | / / 
 / ___ |/ / / / / / / /_/ />  </ /_/ / /  / / / __/ /_/ / /   / / /_/ /_____/ /_/ /  __/ |/ /  
/_/  |_/_/_/ /_/ /_/\____/_/|_|\__,_/_/  /_/_/_/  \__,_/_/   /_/\____/     /_____/\___/|___/   
    """ + RESET)
    print(f"{CYAN}{'='*95}{RESET}")
    print(f"{BOLD}PAINEL ADVANCED DEV - METAL PRINT V3.0 | THRESHOLD: {CONFIG['LOW_STOCK_THRESHOLD']}{RESET}")
    print(f"{CYAN}{'='*95}{RESET}\n")

def login():
    while True:
        header()
        pwd = input(f"{BOLD}Digite a senha de acesso:{RESET} ")
        if pwd == CONFIG["PASSWORD"]: break
        else: print(f"{RED}Senha incorreta!{RESET}"); time.sleep(1)

def menu():
    header()
    ops = [
        "01. Listar Produtos", "02. Adicionar Produto", "03. Deletar Produto", "04. Editar Nome", "05. Editar Qtd",
        "06. Editar Categoria", "07. Buscar por Nome", "08. Estoque Baixo", "09. Listar Funcionários", "10. Novo Funcionário",
        "11. Deletar Funcionário", "12. Listar Transações", "13. Registrar Saída", "14. Stats Gerais", "15. Backup Database",
        "16. Exportar CSV", "17. Limpar Histórico", "18. Top Funcionário", "19. Top Produto", "20. Créditos",
        "21. AJUSTE: Massa por Categ.", "22. AJUSTE: Zerar Todos", "23. AUDIT: Maior Retirada", "24. AUDIT: Vulto Financeiro?", "25. AUDIT: Trans. Órfãs",
        "26. CLEAN: Apagar Estoque 0", "27. CLEAN: Normalizar Nomes", "28. CLEAN: Unificar Funcionários", "29. ANALISE: Funcionário Inativo", "30. ANALISE: Giro Rápido",
        "31. ANALISE: Itens Parados", "32. ADMIN: Mudar Senha", "33. ADMIN: Mudar Threshold", "34. ADMIN: Resetar Sistema", "35. DEV: Inspecionar JSON",
        "36. DEV: Testar Latência", "37. DEV: Ver Database Size", "38. DEV: Forçar Sync Web", "39. RELATORIO: Fechamento Dia", "40. RELATORIO: Mensal (Simulado)",
        "41. SAIR"
    ]
    for i in range(0, 20):
        try: print(f"{ops[i].ljust(30)} {ops[i+20].ljust(30)}")
        except: pass
    print(f"\n{ops[40]}")
    return input(f"\n{BOLD}Escolha: {RESET}")

# --- FUNÇÕES ---

def mass_adjust():
    header(); cat = input("Categoria alvo: ")
    val = int(input("Valor para somar/subtrair (Ex: 10 ou -5): ") or 0)
    prods = [p for p in get_products() if p.get('category') == cat]
    if not prods: print("Nenhum produto encontrado."); time.sleep(1.5); return
    for p in prods: fb_request(f"products/{p['id']}", "PATCH", {"quantity": max(0, p.get('quantity', 0) + val)})
    print(f"{GREEN}Ajustado {len(prods)} itens!{RESET}"); time.sleep(1.5)

def biggest_withdrawal():
    header(); txs = get_transactions()
    if not txs: print("Sem dados."); time.sleep(1.5); return
    top = max(txs, key=lambda x: x.get('quantity', 0))
    print(f"MAIOR RETIRADA: {BOLD}{top['quantity']} un.{RESET}")
    print(f"Material: {top['productName']} | Por: {top['employeeName']}")
    input("\nEnter para voltar...")

def clean_zero_stock():
    header(); prods = [p for p in get_products() if p.get('quantity', 0) <= 0]
    if not prods: print("Nada para limpar."); time.sleep(1.5); return
    print(f"Removendo {len(prods)} itens com estoque zerado...")
    for p in prods: fb_request(f"products/{p['id']}", "DELETE")
    print(f"{GREEN}Limpeza concluída!{RESET}"); time.sleep(1.5)

def inactive_employees():
    header(); txs = get_transactions(); emps = get_employees()
    active_names = {t.get('employeeName') for t in txs if t.get('timestamp', 0) > (time.time() - 30*86400)*1000}
    inactive = [e for e in emps if e['name'] not in active_names]
    print(f"Funcionários sem atividade nos últimos 30 dias ({len(inactive)}):")
    for e in inactive: print(f"- {e['name']} ({e.get('role')})")
    input("\nEnter para voltar...")

def normalize_data():
    header(); prods = get_products(); emps = get_employees()
    print("Corrigindo títulos e espaços..."); count = 0
    for p in prods:
        new_name = p['name'].strip().title()
        if new_name != p['name']: fb_request(f"products/{p['id']}", "PATCH", {"name": new_name}); count += 1
    for e in emps:
        new_name = e['name'].strip().title()
        if new_name != e['name']: fb_request(f"employees/{e['id']}", "PATCH", {"name": new_name}); count += 1
    print(f"{GREEN}Sucesso! {count} entradas corrigidas.{RESET}"); time.sleep(1.5)

def system_reset():
    header(); print(f"{RED}{BOLD}!!! RESET TOTAL DO SISTEMA !!!{RESET}")
    confirm = input("Isso apagará TUDO (Produtos, Transações, Funcionários). Digite 'METALPRINT-CLEAR' para confirmar: ")
    if confirm == 'METALPRINT-CLEAR':
        fb_request("", "DELETE")
        print(f"{GREEN}Sistema resetado.{RESET}")
    time.sleep(2)

def inspect_json():
    header(); node = input("Nó para inspecionar (Ex: products ou trans/id): ")
    data = fb_request(node)
    print(f"\n{CYAN}RAW JSON:{RESET}")
    print(json.dumps(data, indent=2))
    input("\nEnter para voltar...")

def db_size():
    header(); data = fb_request("")
    size = len(json.dumps(data))
    print(f"Tamanho estimado da Database: {BOLD}{size/1024:.2f} KB{RESET}")
    print(f"Total de chaves principais: {len(data) if data else 0}")
    input("\nEnter para voltar...")

def change_pwd():
    header(); new_p = input("Nova senha: ")
    if new_p: CONFIG["PASSWORD"] = new_p; print(f"{GREEN}Senha alterada para a sessão!{RESET}")
    time.sleep(1.5)

# --- RE-EXECUÇÃO DAS FUNÇÕES ANTIGAS ---
# (Implementando as que faltavam ou adaptando)
def list_prods():
    header(); prods = get_products()
    print(f"{'ID':<25} | {'NOME':<30} | {'QTD':<5}")
    for p in prods: print(f"{p['id']:<25} | {p['name']:<30} | {p['quantity']}")
    input("\nEnter...")

def add_prod():
    header(); n = input("Nome: "); q = int(input("Qtd: ")); c = input("Cat: ")
    if n: fb_request("products", "POST", {"name":n,"quantity":q,"category":c})

def del_prod():
    header(); ps = get_products(); [print(f"{i+1}. {p['name']}") for i, p in enumerate(ps)]
    idx = int(input("Número: ") or 0)
    if 0 < idx <= len(ps): fb_request(f"products/{ps[idx-1]['id']}", "DELETE")

def main():
    login()
    while True:
        try:
            c = menu()
            if c == '01': list_prods()
            elif c == '02': add_prod()
            elif c == '03': del_prod()
            elif c == '21': mass_adjust()
            elif c == '23': biggest_withdrawal()
            elif c == '26': clean_zero_stock()
            elif c == '27': normalize_data()
            elif c == '29': inactive_employees()
            elif c == '32': change_pwd()
            elif c == '34': system_reset()
            elif c == '35': inspect_json()
            elif c == '37': db_size()
            elif c == '41': break
            else: input(f"\n{YELLOW}Opção em desenvolvimento ou pressione para voltar...{RESET}")
        except Exception as e: print(e); time.sleep(2)

if __name__ == "__main__": main()
