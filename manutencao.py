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

def generate_pdf():
    print("\n⏳ Coletando dados para o PDF...")
    products = fb_request("products") or {}
    
    if not products:
        print("❌ Nenhum produto encontrado no estoque!")
        return

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, txt="METAL PRINT - RELATÓRIO DE ESTOQUE", ln=True, align='C')
        pdf.set_font("Arial", "", 10)
        pdf.cell(200, 10, txt=f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align='C')
        pdf.ln(10)

        # Header da Tabela
        pdf.set_fill_color(200, 220, 255)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(100, 10, "Material", 1, 0, 'L', True)
        pdf.cell(60, 10, "Categoria", 1, 0, 'L', True)
        pdf.cell(30, 10, "Qtd", 1, 1, 'C', True)

        # Dados
        pdf.set_font("Arial", "", 10)
        for pid, p in products.items():
            pdf.cell(100, 8, str(p.get("name", "N/A")), 1)
            pdf.cell(60, 8, str(p.get("category", "N/A")), 1)
            pdf.cell(30, 8, str(p.get("quantity", 0)), 1, 1, 'C')

        filename = f"relatorio_estoque_{int(time.time())}.pdf"
        pdf.output(filename)
        print(f"\n✅ Relatório gerado com sucesso: {filename}")
    except Exception as e:
        print(f"\n❌ Erro ao gerar PDF: {e}")

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
        print(" 3. GERAR RELATÓRIO DE ESTOQUE (PDF)")
        print(" 4. SAIR")
        print("-"*40)
        
        choice = input(" Escolha uma opção: ")
        
        if choice == '1':
            fb_request("settings", "PATCH", {"maintenanceMode": True})
            print("\n✅ MODO MANUTENÇÃO ATIVADO!")
        elif choice == '2':
            fb_request("settings", "PATCH", {"maintenanceMode": False})
            print("\n✅ SITE VOLTOU A FICAR ONLINE!")
        elif choice == '3':
            generate_pdf()
        elif choice == '4':
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
