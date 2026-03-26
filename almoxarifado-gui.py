import tkinter as tk
from tkinter import ttk, messagebox
import json
import urllib.request
import time
import threading
from datetime import datetime

# --- CONFIGURAÇÃO FIREBASE ---
FIREBASE_URL = "https://almoxarifado-dacbe-default-rtdb.firebaseio.com"

# --- TEMA E CORES ---
COLORS = {
    "bg": "#0f172a",
    "sidebar": "#1e293b",
    "accent": "#3b82f6",
    "text": "#f8fafc",
    "muted": "#94a3b8",
    "card": "#1e293b",
    "error": "#ef4444",
    "success": "#10b981",
    "warning": "#f59e0b"
}

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
        print(f"Error: {e}")
        return None

# --- APP CLASS ---
class AlmoxarifadoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Metal Print - Almoxarifado Dev V4.0")
        self.geometry("1100x700")
        self.configure(bg=COLORS["bg"])
        
        self.state = {"products": [], "employees": [], "transactions": []}
        self.current_page = None
        
        self.setup_styles()
        self.show_login()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="#1e293b", foreground="white", fieldbackground="#1e293b", borderwidth=0)
        style.map("Treeview", background=[('selected', COLORS["accent"])])
        style.configure("TButton", padding=6, relief="flat", background=COLORS["accent"], foreground="white")
        style.configure("Sidebar.TFrame", background=COLORS["sidebar"])

    def show_login(self):
        self.login_frame = tk.Frame(self, bg=COLORS["bg"])
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(self.login_frame, text="METAL PRINT", font=("Inter", 24, "bold"), fg=COLORS["accent"], bg=COLORS["bg"]).pack(pady=10)
        tk.Label(self.login_frame, text="ALMOXARIFADO DEV", font=("Inter", 12), fg=COLORS["muted"], bg=COLORS["bg"]).pack(pady=(0, 30))
        
        self.pwd_entry = tk.Entry(self.login_frame, show="*", font=("Inter", 14), width=20, bd=0, bg="#334155", fg="white", insertbackground="white")
        self.pwd_entry.pack(pady=10, ipady=8)
        self.pwd_entry.focus()
        self.pwd_entry.bind("<Return>", lambda e: self.attempt_login())
        
        tk.Button(self.login_frame, text="ENTRAR", command=self.attempt_login, bg=COLORS["accent"], fg="white", font=("Inter", 12, "bold"), bd=0, padx=20, pady=8, cursor="hand2").pack(pady=20)

    def attempt_login(self):
        if self.pwd_entry.get() == "jonas":
            self.login_frame.destroy()
            self.setup_main_ui()
            self.start_sync()
        else:
            messagebox.showerror("Erro", "Senha incorreta!")

    def setup_main_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        tk.Label(self.sidebar, text="Menu", font=("Inter", 10, "bold"), fg=COLORS["muted"], bg=COLORS["sidebar"]).pack(pady=(20, 10), padx=20, anchor="w")
        
        menu_items = [
            ("Dashboard", self.show_dashboard),
            ("Estoque", self.show_inventory),
            ("Funcionários", self.show_employees),
            ("Histórico", self.show_history),
            ("Auditoria", self.show_audit),
            ("Configurações", self.show_admin)
        ]
        
        for name, cmd in menu_items:
            btn = tk.Button(self.sidebar, text=f"  {name}", command=cmd, anchor="w", font=("Inter", 11), bg=COLORS["sidebar"], fg=COLORS["text"], bd=0, padx=20, pady=10, cursor="hand2", activebackground=COLORS["accent"])
            btn.pack(fill="x")

        # Content Area
        self.content = tk.Frame(self, bg=COLORS["bg"])
        self.content.pack(side="right", expand=True, fill="both", padx=30, pady=30)
        
        self.show_dashboard()

    def clear_content(self):
        for widget in self.content.winfo_children(): widget.destroy()

    def show_dashboard(self):
        self.clear_content()
        tk.Label(self.content, text="Dashboard", font=("Inter", 20, "bold"), fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 20))
        
        stats_frame = tk.Frame(self.content, bg=COLORS["bg"])
        stats_frame.pack(fill="x", pady=10)
        
        self.create_stat_card(stats_frame, "PRODUTOS", str(len(self.state["products"])), 0)
        self.create_stat_card(stats_frame, "FUNCIONÁRIOS", str(len(self.state["employees"])), 1)
        self.create_stat_card(stats_frame, "SAÍDAS HOJE", "0", 2) # To update later

    def create_stat_card(self, parent, label, value, col):
        card = tk.Frame(parent, bg=COLORS["card"], padx=20, pady=20, highlightthickness=1, highlightbackground="#334155")
        card.grid(row=0, column=col, padx=10, sticky="nsew")
        tk.Label(card, text=label, font=("Inter", 9, "bold"), fg=COLORS["muted"], bg=COLORS["card"]).pack(anchor="w")
        tk.Label(card, text=value, font=("Inter", 24, "bold"), fg=COLORS["accent"], bg=COLORS["card"]).pack(anchor="w")

    def show_inventory(self):
        self.clear_content()
        header = tk.Frame(self.content, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 10))
        tk.Label(header, text="Estoque", font=("Inter", 18, "bold"), fg=COLORS["text"], bg=COLORS["bg"]).pack(side="left")
        tk.Button(header, text="+ NOVO MATERIAL", command=self.add_product_modal, bg=COLORS["accent"], fg="white", font=("Inter", 10, "bold"), bd=0, padx=15, pady=5).pack(side="right")
        
        columns = ("id", "name", "cat", "qty")
        self.tree = ttk.Treeview(self.content, columns=columns, show="headings", height=15)
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="PRODUTO")
        self.tree.heading("cat", text="CATEGORIA")
        self.tree.heading("qty", text="QTD")
        
        self.tree.column("id", width=150)
        self.tree.column("name", width=300)
        self.tree.column("cat", width=150)
        self.tree.column("qty", width=100)
        
        self.tree.pack(fill="both", expand=True)
        self.refresh_inventory_list()

    def refresh_inventory_list(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for p in self.state["products"]:
            self.tree.insert("", "end", values=(p.get('id'), p.get('name'), p.get('category'), p.get('quantity')))

    def show_employees(self):
        self.clear_content()
        tk.Label(self.content, text="Gerenciar Funcionários", font=("Inter", 18, "bold"), fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 10))
        
        columns = ("id", "name", "role")
        self.emp_tree = ttk.Treeview(self.content, columns=columns, show="headings", height=15)
        self.emp_tree.heading("id", text="ID")
        self.emp_tree.heading("name", text="NOME")
        self.emp_tree.heading("role", text="CARGO")
        self.emp_tree.pack(fill="both", expand=True)
        
        for e in self.state["employees"]:
            self.emp_tree.insert("", "end", values=(e.get('id'), e.get('name'), e.get('role')))

    def show_history(self):
        self.clear_content()
        tk.Label(self.content, text="Histórico de Saídas", font=("Inter", 18, "bold"), fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 10))
        
        columns = ("date", "emp", "prod", "qty")
        self.tx_tree = ttk.Treeview(self.content, columns=columns, show="headings", height=15)
        self.tx_tree.heading("date", text="DATA/HORA")
        self.tx_tree.heading("emp", text="FUNCIONÁRIO")
        self.tx_tree.heading("prod", text="MATERIAL")
        self.tx_tree.heading("qty", text="QTD")
        self.tx_tree.pack(fill="both", expand=True)
        
        for t in reversed(self.state["transactions"][-50:]):
            dt = datetime.fromtimestamp(t.get('timestamp', 0)/1000).strftime('%d/%m/%Y %H:%M')
            self.tx_tree.insert("", "end", values=(dt, t.get('employeeName'), t.get('productName'), t.get('quantity')))

    def show_audit(self):
        self.clear_content()
        tk.Label(self.content, text="Ferramentas & Auditoria", font=("Inter", 18, "bold"), fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 20))
        
        tools = [
            ("Mapear Maior Retirada", self.audit_biggest),
            ("Normalizar Nomes (Caps)", self.audit_normalize),
            ("Limpar Itens Esgotados", self.audit_clean_zero),
            ("Verificar Funcionários Inativos", self.audit_inactive),
            ("Ajuste de Estoque em Massa", self.audit_mass_update)
        ]
        
        for name, cmd in tools:
            tk.Button(self.content, text=name, command=cmd, font=("Inter", 11), bg="#334155", fg="white", bd=0, padx=20, pady=12, width=35, anchor="w", cursor="hand2").pack(pady=5)

    def show_admin(self):
        self.clear_content()
        tk.Label(self.content, text="Configurações do Sistema", font=("Inter", 18, "bold"), fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 20))
        
        # Maintenance Toggle
        m_frame = tk.Frame(self.content, bg=COLORS["card"], padx=20, pady=15, highlightthickness=1, highlightbackground="#334155")
        m_frame.pack(fill="x", pady=5)
        
        tk.Label(m_frame, text="MODO MANUTENÇÃO (SITE)", font=("Inter", 11, "bold"), fg="white", bg=COLORS["card"]).pack(side="left")
        
        m_state = self.state.get("settings", {}).get("maintenanceMode", False)
        btn_text = "DESATIVAR" if m_state else "ATIVAR"
        btn_bg = COLORS["error"] if m_state else COLORS["success"]
        
        def toggle_m():
            new_state = not m_state
            fb_request("settings", "PATCH", {"maintenanceMode": new_state})
            if "settings" not in self.state: self.state["settings"] = {}
            self.state["settings"]["maintenanceMode"] = new_state # Update local state immediately
            messagebox.showinfo("Sucesso", f"Modo Manutenção {'Ativado' if new_state else 'Desativado'}!")
            self.show_admin()

        tk.Button(m_frame, text=btn_text, command=toggle_m, bg=btn_bg, fg="white", bd=0, padx=15, pady=5, font=("Inter", 9, "bold")).pack(side="right")

        tk.Button(self.content, text="FAZER BACKUP COMPLETO (JSON)", command=self.backup_db, bg=COLORS["warning"], fg="white", font=("Inter", 11, "bold"), bd=0, padx=20, pady=12, width=35, anchor="w").pack(pady=(20, 5))
        tk.Button(self.content, text="RESETAR TODO O SISTEMA", command=self.full_reset, bg=COLORS["error"], fg="white", font=("Inter", 11, "bold"), bd=0, padx=20, pady=12, width=35, anchor="w").pack(pady=5)

    # --- MODAIS E AÇÕES ---
    def add_product_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Novo Material")
        modal.geometry("400x350")
        modal.configure(bg=COLORS["bg"])
        
        tk.Label(modal, text="Adicionar Material", font=("Inter", 14, "bold"), fg="white", bg=COLORS["bg"]).pack(pady=20)
        
        tk.Label(modal, text="Nome:", fg=COLORS["muted"], bg=COLORS["bg"]).pack(anchor="w", padx=40)
        name_e = tk.Entry(modal, bg="#334155", fg="white", bd=0); name_e.pack(fill="x", padx=40, pady=5, ipady=5)
        
        tk.Label(modal, text="Qtd Inicial:", fg=COLORS["muted"], bg=COLORS["bg"]).pack(anchor="w", padx=40)
        qty_e = tk.Entry(modal, bg="#334155", fg="white", bd=0); qty_e.pack(fill="x", padx=40, pady=5, ipady=5)
        
        tk.Label(modal, text="Categoria:", fg=COLORS["muted"], bg=COLORS["bg"]).pack(anchor="w", padx=40)
        cat_e = tk.Entry(modal, bg="#334155", fg="white", bd=0); cat_e.pack(fill="x", padx=40, pady=5, ipady=5)
        
        def save():
            n, q, c = name_e.get(), qty_e.get(), cat_e.get()
            if n and q.isdigit():
                fb_request("products", "POST", {"name": n, "quantity": int(q), "category": c})
                modal.destroy()
                messagebox.showinfo("Sucesso", "Produto adicionado!")
        
        tk.Button(modal, text="SALVAR", command=save, bg=COLORS["accent"], fg="white", bd=0, pady=10).pack(fill="x", padx=40, pady=20)

    # --- SYNC ENGINE ---
    def start_sync(self):
        def loop():
            while True:
                try:
                    p = fb_request("products") or {}
                    e = fb_request("employees") or {}
                    t = fb_request("transactions") or {}
                    s = fb_request("settings") or {}
                    self.state["products"] = [{"id": k, **v} for k, v in p.items()]
                    self.state["employees"] = [{"id": k, **v} for k, v in e.items()]
                    self.state["transactions"] = [{"id": k, **v} for k, v in t.items()]
                    self.state["settings"] = s
                except: pass
                time.sleep(10)
        threading.Thread(target=loop, daemon=True).start()

    # --- AUDIT IMPLEMENTATION ---
    def audit_normalize(self):
        count = 0
        for p in self.state["products"]:
            new_n = p['name'].strip().title()
            if new_n != p['name']:
                fb_request(f"products/{p['id']}", "PATCH", {"name": new_n})
                count += 1
        messagebox.showinfo("Auditoria", f"Nomes normalizados: {count}")

    def audit_biggest(self):
        if not self.state["transactions"]: return
        top = max(self.state["transactions"], key=lambda x: x.get('quantity', 0))
        messagebox.showinfo("Maior Retirada", f"Produto: {top['productName']}\nQuantidade: {top['quantity']}\nFuncionário: {top['employeeName']}")

    def audit_clean_zero(self):
        zeros = [p for p in self.state["products"] if p.get('quantity', 0) <= 0]
        if messagebox.askyesno("Limpeza", f"Deseja apagar {len(zeros)} itens com estoque zero?"):
            for p in zeros: fb_request(f"products/{p['id']}", "DELETE")
            messagebox.showinfo("Sucesso", "Limpeza realizada.")

    def audit_inactive(self):
        active = {t.get('employeeName') for t in self.state["transactions"] if t.get('timestamp', 0) > (time.time() - 30*86400)*1000}
        inactive = [e['name'] for e in self.state["employees"] if e['name'] not in active]
        messagebox.showinfo("Inatividade", f"Funcionários inativos (30 dias):\n\n" + "\n".join(inactive))

    def audit_mass_update(self):
        # Implementation of mass update... simplified for demo
        messagebox.showinfo("Info", "Funcionalidade disponível em breve em modo avançado.")

    def backup_db(self):
        data = fb_request("")
        with open("backup_v4.json", "w") as f: json.dump(data, f, indent=4)
        messagebox.showinfo("Backup", "Backup completo salvo como 'backup_v4.json'")

    def full_reset(self):
        if messagebox.askyesno("PERIGO", "Isso apagará TODO o banco de dados. Tem certeza?"):
            fb_request("", "DELETE")
            messagebox.showwarning("Reset", "Banco de dados limpo.")

if __name__ == "__main__":
    app = AlmoxarifadoApp()
    app.mainloop()
