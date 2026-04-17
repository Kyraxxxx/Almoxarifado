#!/usr/bin/env python3
import urllib.request
import json
import sys
import time
from datetime import datetime
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- CONFIGURAÇÃO ---
FIREBASE_URL = "https://almoxarifado-dacbe-default-rtdb.firebaseio.com"

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
        print(f"\n❌ Erro na conexão: {e}")
        return None

def show_menu():
    while True:
        settings = fb_request("settings") or {}
        m_mode = settings.get("maintenanceMode", False)
        o_mode = settings.get("outOfOrderMode", False)
        
        if o_mode:
            status = "🤷 SITE FORA DE FUNCIONAMENTO"
        elif m_mode:
            status = "🛠️  MANUTENÇÃO ATIVA"
        else:
            status = "✅ SITE ONLINE"

        print("\n" + "="*40)
        print("     METAL PRINT - CONTROLE DE SITE")
        print("="*40)
        print(f" STATUS ATUAL: {status}")
        print("-"*40)
        print(" 1. ATIVAR MODO MANUTENÇÃO")
        print(" 2. DESATIVAR MODO MANUTENÇÃO")
        print(" 3. ATIVAR SITE FORA DE FUNCIONAMENTO (🤷)")
        print(" 4. DESATIVAR SITE FORA DE FUNCIONAMENTO")
        print(" 5. SAIR")
        print("-"*40)
        
        choice = input(" Escolha uma opção: ")
        
        if choice == '1':
            fb_request("settings", "PATCH", {"maintenanceMode": True, "outOfOrderMode": False})
            print("\n✅ MODO MANUTENÇÃO ATIVADO!")
        elif choice == '2':
            fb_request("settings", "PATCH", {"maintenanceMode": False})
            print("\n✅ MODO MANUTENÇÃO DESATIVADO!")
        elif choice == '3':
            fb_request("settings", "PATCH", {"maintenanceMode": False, "outOfOrderMode": True})
            print("\n✅ SITE FORA DE FUNCIONAMENTO ATIVADO!")
        elif choice == '4':
            fb_request("settings", "PATCH", {"outOfOrderMode": False})
            print("\n✅ SITE FORA DE FUNCIONAMENTO DESATIVADO!")
        elif choice == '5':
            print("\nSaindo... Metal Print agradece.")
            break
        else:
            print("\n❌ Opção inválida!")
        
        time.sleep(1)

if __name__ == "__main__":
    try:
        show_menu()
    except KeyboardInterrupt:
        print("\n\nSaindo...")
