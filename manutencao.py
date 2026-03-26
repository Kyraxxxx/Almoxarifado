#!/usr/bin/env python3
import urllib.request
import json
import sys
import time

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
        
        print("\n" + "="*40)
        print("     METAL PRINT - CONTROLE DE SITE")
        print("="*40)
        print(f" STATUS ATUAL: {'🛠️  MANUTENÇÃO ATIVA' if m_mode else '✅ SITE ONLINE'}")
        print("-"*40)
        print(" 1. ATIVAR MODO MANUTENÇÃO")
        print(" 2. DESATIVAR MODO MANUTENÇÃO")
        print(" 3. SAIR")
        print("-"*40)
        
        choice = input(" Escolha uma opção: ")
        
        if choice == '1':
            fb_request("settings", "PATCH", {"maintenanceMode": True})
            print("\n✅ MODO MANUTENÇÃO ATIVADO!")
        elif choice == '2':
            fb_request("settings", "PATCH", {"maintenanceMode": False})
            print("\n✅ SITE VOLTOU A FICAR ONLINE!")
        elif choice == '3':
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
