import tkinter as tk
from tkinter import ttk, messagebox
import json
import urllib.request
import time
import threading
from datetime import datetime

# --- CONFIGURAÇÃO FIREBASE ---
FIREBASE_URL = "https://almoxarifado-dacbe-default-rtdb.firebaseio.com"

# --- CONFIGURAÇÕES VISUAIS (HIGH-CONTRAST PREMIUM) ---
COLORS = {
    "bg": "#f1f5f9",        # Slate 100 (Light Gray)
    "sidebar": "#0f172a",   # Navy 900 (Dark)
    "card": "#ffffff",      # White
    "accent": "#2563eb",    # Blue 600
    "text": "#0f172a",      # Slate 900
    "text_muted": "#64748b", # Slate 500
    "border": "#cbd5e1",    # Slate 300 (Visible borders)
    "success": "#10b981",   # Emerald 500
    "error": "#ef4444",     # Red 500
    "warning": "#f59e0b"    # Amber 500
}
RADIUS = 12

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
        self.title("Metal Print - Almoxarifado Dev V4.2")
        self.geometry("1100x700")
        self.configure(bg=COLORS["bg"])
        
        self.state = {"products": [], "employees": [], "transactions": []}
        
        # Main Container to avoid packing/placing on root directly
        self.main_container = tk.Frame(self, bg=COLORS["bg"])
        self.main_container.pack(fill="both", expand=True)
        
        self.setup_styles()
        self.show_login()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # General styles for Treeview
        style.configure("Treeview",
                        background=COLORS["card"],
                        foreground=COLORS["text"],
                        fieldbackground=COLORS["card"],
                        borderwidth=0,
                        rowheight=28)
        style.map("Treeview",
                  background=[('selected', COLORS["accent"])],
                  foreground=[('selected', 'white')])
        
        # Heading style for Treeview
        style.configure("Treeview.Heading",
                        font=("Inter", 10, "bold"),
                        background=COLORS["sidebar"],
                        foreground="white",
                        relief="flat")
        style.map("Treeview.Heading",
                  background=[('active', COLORS["sidebar"])])

        # Scrollbar style
        style.configure("Vertical.TScrollbar",
                        background=COLORS["border"],
                        troughcolor=COLORS["bg"],
                        bordercolor=COLORS["border"],
                        arrowcolor=COLORS["text_muted"])
        
        # Button styles (if using ttk.Button)
        style.configure("TButton",
                        padding=6,
                        relief="flat",
                        background=COLORS["accent"],
                        foreground="white",
                        font=("Inter", 10, "bold"))
        style.map("TButton",
                  background=[('active', COLORS["accent"])])

        # Frame styles
        style.configure("Sidebar.TFrame", background=COLORS["sidebar"])
        style.configure("Content.TFrame", background=COLORS["bg"])


    def show_login(self):
        for widget in self.main_container.winfo_children(): widget.destroy()
        
        self.login_frame = tk.Frame(self.main_container, bg=COLORS["sidebar"], padx=50, pady=50, highlightthickness=1, highlightbackground=COLORS["border"])
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(self.login_frame, text="METAL PRINT", font=("Inter", 24, "bold"), fg="white", bg=COLORS["sidebar"]).pack(pady=10)
        tk.Label(self.login_frame, text="ALMOXARIFADO DEV", font=("Inter", 12), fg="#94a3b8", bg=COLORS["sidebar"]).pack(pady=(0, 30))
        
        self.pwd_entry = tk.Entry(self.login_frame, show="*", font=("Inter", 14), width=20, bd=0, bg="#1e293b", fg="white", insertbackground="white", highlightbackground=COLORS["border"], highlightthickness=1)
        self.pwd_entry.pack(pady=10, ipady=8)
        self.pwd_entry.focus()
        self.pwd_entry.bind("<Return>", lambda e: self.attempt_login())
        
        tk.Button(self.login_frame, text="ENTRAR AGORA", command=self.attempt_login, bg=COLORS["accent"], fg="white", font=("Inter", 12, "bold"), bd=0, padx=20, pady=10, cursor="hand2").pack(pady=20)

    def attempt_login(self):
        if self.pwd_entry.get() == "jonas":
            self.login_frame.destroy()
            self.setup_main_ui()
            self.start_sync()
        else:
            messagebox.showerror("Erro", "Senha incorreta!")

    def setup_main_ui(self):
        for widget in self.main_container.winfo_children(): widget.destroy()
        
        # Sidebar
        self.sidebar = tk.Frame(self.main_container, bg=COLORS["sidebar"], width=240, highlightthickness=1, highlightbackground=COLORS["border"])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="METAL PRINT", font=("Inter", 14, "bold"), fg="white", bg=COLORS["sidebar"]).pack(pady=30)
        
        self.menu_items = [
            ("Dashboard", self.show_dashboard),
            ("Estoque", self.show_inventory),
            ("Saída", self.show_withdraw),
            ("Funcionários", self.show_employees),
            ("Histórico", self.show_history),
            ("Configurações", self.show_admin)
        ]
        
        for name, cmd in self.menu_items:
            # White text for high contrast on Dark Navy
            btn = tk.Button(self.sidebar, text=f"  {name}", command=cmd, font=("Inter", 10, "bold"), 
                           fg="white", bg=COLORS["sidebar"], bd=0, anchor="w", 
                           padx=20, pady=12, cursor="hand2", activebackground="#1e293b", activeforeground="white")
            btn.pack(fill="x")
            # Hover effect
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg=COLORS["accent"], bg="#1e293b"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(fg="white", bg=COLORS["sidebar"]))

        self.content = tk.Frame(self.main_container, bg=COLORS["bg"], padx=40, pady=40)
        self.content.pack(side="right", fill="both", expand=True)
        
        self.show_dashboard()

    def clear_content(self):
        for widget in self.content.winfo_children(): widget.destroy()

    def show_dashboard(self):
        self.clear_content()
        tk.Label(self.content, text="Visão Geral", font=("Inter", 20, "bold"), fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 30))
        
        stats_frame = tk.Frame(self.content, bg=COLORS["bg"])
        stats_frame.pack(fill="x")
        
        def create_stat(parent, label, value, color):
            f = tk.Frame(parent, bg=COLORS["card"], padx=25, pady=20, highlightthickness=1, highlightbackground=COLORS["border"])
            f.pack(side="left", padx=(0, 20), expand=True, fill="both")
            tk.Label(f, text=label, font=("Inter", 9, "bold"), fg=COLORS["text_muted"], bg=COLORS["card"]).pack(anchor="w")
            tk.Label(f, text=value, font=("Inter", 24, "bold"), fg=color, bg=COLORS["card"]).pack(anchor="w", pady=(5, 0))

        create_stat(stats_frame, "TOTAL PRODUTOS", len(self.state.get("products", [])), COLORS["accent"])
        create_stat(stats_frame, "FUNCIONÁRIOS", len(self.state.get("employees", [])), COLORS["text"])
        create_stat(stats_frame, "SAÍDAS (TUDO)", len(self.state.get("transactions", [])), COLORS["success"])

    def show_inventory(self):
        self.clear_content()
        header = tk.Frame(self.content, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 20))
        
        tk.Label(header, text="Estoque de Materiais", font=("Inter", 18, "bold"), fg=COLORS["text"], bg=COLORS["bg"]).pack(side="left")
        tk.Button(header, text="+ NOVO MATERIAL", command=lambda: self.show_modal("add"), bg=COLORS["accent"], fg="white", font=("Inter", 9, "bold"), bd=0, padx=15, pady=8).pack(side="right")
        
        # Search Bar
        search_frame = tk.Frame(self.content, bg=COLORS["card"], padx=15, pady=10, highlightthickness=1, highlightbackground=COLORS["border"])
        search_frame.pack(fill="x", pady=(0, 20))
        tk.Label(search_frame, text="Buscar:", font=("Inter", 9, "bold"), fg=COLORS["text_muted"], bg=COLORS["card"]).pack(side="left", padx=(0, 10))
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Inter", 10), bd=0, bg=COLORS["card"], fg=COLORS["text"], insertbackground=COLORS["text"])
        search_entry.pack(side="left", fill="x", expand=True)
        self.search_var.trace_add("write", lambda *args: self.refresh_inventory_table())

        self.tree_frame = tk.Frame(self.content, bg=COLORS["card"], highlightthickness=1, highlightbackground=COLORS["border"])
        self.tree_frame.pack(fill="both", expand=True)
        
        self.tree = ttk.Treeview(self.tree_frame, columns=("Nome", "Categoria", "Qtd"), show="headings", height=15)
        self.tree.heading("Nome", text="MATERIAL")
        self.tree.heading("Categoria", text="CATEGORIA")
        self.tree.heading("Qtd", text="SALDO")
        self.tree.column("Qtd", width=100, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        
        sb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        
        self.refresh_inventory_table()

    def refresh_inventory_table(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        query = self.search_var.get().lower() if hasattr(self, 'search_var') else ""
        
        for p in self.state.get("products", []):
            if query in p["name"].lower() or query in p["category"].lower():
                self.tree.insert("", "end", values=(p["name"], p["category"], f"{p['quantity']} unid."))

    def show_employees(self):
        self.clear_content()
        header = tk.Frame(self.content, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 20))
        
        tk.Label(header, text="Gestão de Funcionários", font=("Inter", 18, "bold"), fg=COLORS["text"], bg=COLORS["bg"]).pack(side="left")
        tk.Button(header, text="+ NOVO FUNCIONÁRIO", command=lambda: self.show_modal("employee"), bg=COLORS["accent"], fg="white", font=("Inter", 9, "bold"), bd=0, padx=15, pady=8).pack(side="right")
        
        self.emp_list_frame = tk.Frame(self.content, bg=COLORS["bg"])
        self.emp_list_frame.pack(fill="both", expand=True)
        self.refresh_employees()

    def refresh_employees(self):
        for widget in self.emp_list_frame.winfo_children(): widget.destroy()
        for e in self.state.get("employees", []):
            f = tk.Frame(self.emp_list_frame, bg=COLORS["card"], padx=20, pady=15, highlightthickness=1, highlightbackground=COLORS["border"])
            f.pack(fill="x", pady=5)
            tk.Label(f, text=e["name"], font=("Inter", 11, "bold"), fg=COLORS["text"], bg=COLORS["card"]).pack(side="left")
            tk.Label(f, text=f"•  {e.get('role', 'Geral')}", font=("Inter", 10), fg=COLORS["text_muted"], bg=COLORS["card"]).pack(side="left", padx=20)
            tk.Button(f, text="REMOVER", command=lambda id=e["id"]: self.delete_employee(id), bg=COLORS["bg"], fg=COLORS["error"], font=("Inter", 8, "bold"), bd=0, padx=10).pack(side="right")

    def show_history(self):
        self.clear_content()
        tk.Label(self.content, text="Histórico de Movimentações", font=("Inter", 20, "bold"), fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 30))
        
        tree_frame = tk.Frame(self.content, bg=COLORS["card"], highlightthickness=1, highlightbackground=COLORS["border"])
        tree_frame.pack(fill="both", expand=True)
        
        self.hist_tree = ttk.Treeview(tree_frame, columns=("Data", "Func", "Prod", "Qtd"), show="headings", height=15)
        self.hist_tree.heading("Data", text="DATA/HORA")
        self.hist_tree.heading("Func", text="FUNCIONÁRIO")
        self.hist_tree.heading("Prod", text="MATERIAL")
        self.hist_tree.heading("Qtd", text="QT")
        
        self.hist_tree.column("Data", width=150)
        self.hist_tree.column("Qtd", width=50, anchor="center")
        self.hist_tree.pack(side="left", fill="both", expand=True)
        
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.hist_tree.yview)
        sb.pack(side="right", fill="y")
        self.hist_tree.configure(yscrollcommand=sb.set)
        
        for t in sorted(self.state.get("transactions", []), key=lambda x: x.get("timestamp", 0), reverse=True):
            dt = time.strftime('%d/%m %H:%M', time.localtime(t.get("timestamp", 0)/1000))
            self.hist_tree.insert("", "end", values=(dt, t.get("employeeName"), t.get("productName"), t.get("quantity")))

    def show_withdraw(self):
        self.clear_content()
        tk.Label(self.content, text="Registrar Saída de Material", font=("Inter", 20, "bold"), fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 30))
        
        card = tk.Frame(self.content, bg=COLORS["card"], padx=30, pady=30, highlightthickness=1, highlightbackground=COLORS["border"])
        card.pack(fill="x")
        
        tk.Label(card, text="FUNCIONÁRIO", font=("Inter", 9, "bold"), fg=COLORS["text_muted"], bg=COLORS["card"]).pack(anchor="w")
        emp_var = tk.StringVar()
        emp_opt = ttk.Combobox(card, textvariable=emp_var, font=("Inter", 11), state="readonly")
        emp_opt['values'] = [e["name"] for e in self.state.get("employees", [])]
        emp_opt.pack(fill="x", pady=(5, 20))
        
        tk.Label(card, text="MATERIAL / PRODUTO", font=("Inter", 9, "bold"), fg=COLORS["text_muted"], bg=COLORS["card"]).pack(anchor="w")
        prod_var = tk.StringVar()
        prod_opt = ttk.Combobox(card, textvariable=prod_var, font=("Inter", 11), state="readonly")
        prod_opt['values'] = [f"{p['name']} (Saldo: {p['quantity']})" for p in self.state.get("products", [])]
        prod_opt.pack(fill="x", pady=(5, 20))
        
        tk.Label(card, text="QUANTIDADE", font=("Inter", 9, "bold"), fg=COLORS["text_muted"], bg=COLORS["card"]).pack(anchor="w")
        qty_entry = tk.Entry(card, font=("Inter", 11), bd=0, bg=COLORS["bg"], fg=COLORS["text"], highlightthickness=1, highlightbackground=COLORS["border"])
        qty_entry.pack(fill="x", pady=(5, 30), ipady=8)
        qty_entry.insert(0, "1")
        
        def confirm():
            e_name = emp_var.get()
            p_val = prod_var.get()
            q_val = qty_entry.get()
            if not e_name or not p_val or not q_val.isdigit():
                messagebox.showerror("Erro", "Preencha todos os campos corretamente!")
                return
            
            p_name = p_val.split(" (Saldo:")[0]
            product = next((p for p in self.state["products"] if p["name"] == p_name), None)
            qty = int(q_val)
            
            if product and product["quantity"] >= qty:
                fb_request(f"products/{product['id']}", "PATCH", {"quantity": product["quantity"] - qty})
                fb_request("transactions", "POST", {
                    "employeeName": e_name,
                    "productName": p_name,
                    "quantity": qty,
                    "timestamp": int(time.time() * 1000)
                })
                messagebox.showinfo("Sucesso", "Saída registrada com sucesso!")
                self.show_dashboard()
            else:
                messagebox.showerror("Erro", "Estoque insuficiente!")

        tk.Button(card, text="CONFIRMAR RETIRADA", command=confirm, bg=COLORS["accent"], fg="white", font=("Inter", 10, "bold"), bd=0, pady=12, cursor="hand2").pack(fill="x")

    def show_audit(self):
        self.clear_content()
        tk.Label(self.content, text="Ferramentas & Auditoria", font=("Inter", 20, "bold"), fg=COLORS["text"], bg=COLORS["bg"]).pack(anchor="w", pady=(0, 30))
        
        container = tk.Frame(self.content, bg=COLORS["bg"])
        container.pack(fill="both", expand=True)
        
        tools = [
            ("Mapear Maior Retirada", self.audit_biggest),
            ("Normalizar Nomes (Caps)", self.audit_normalize),
            ("Limpar Itens Esgotados", self.audit_clean_zero),
            ("Verificar Funcionários Inativos", self.audit_inactive),
            ("Ajuste de Estoque em Massa", self.audit_mass_update)
        ]
        
        for name, cmd in tools:
            f = tk.Frame(container, bg=COLORS["card"], padx=20, pady=10, highlightthickness=1, highlightbackground=COLORS["border"])
            f.pack(fill="x", pady=5)
            tk.Label(f, text=name, font=("Inter", 11, "bold"), fg=COLORS["text"], bg=COLORS["card"]).pack(side="left")
            tk.Button(f, text="EXECUTAR", command=cmd, bg=COLORS["bg"], fg=COLORS["accent"], font=("Inter", 8, "bold"), bd=0, padx=15).pack(side="right")

    # --- MODAIS E AÇÕES ---
    def show_modal(self, type):
        modal = tk.Toplevel(self)
        modal.title("Novo Registro")
        modal.geometry("400x450")
        modal.configure(bg=COLORS["bg"])
        
        container = tk.Frame(modal, bg=COLORS["card"], padx=30, pady=30, highlightthickness=1, highlightbackground=COLORS["border"])
        container.pack(expand=True, fill="both", padx=20, pady=20)
        
        title = "Novo Material" if type == "add" else "Novo Funcionário"
        tk.Label(container, text=title.upper(), font=("Inter", 12, "bold"), fg=COLORS["accent"], bg=COLORS["card"]).pack(pady=(0, 20))
        
        def create_field(label):
            tk.Label(container, text=label, font=("Inter", 8, "bold"), fg=COLORS["text_muted"], bg=COLORS["card"]).pack(anchor="w", pady=(10, 2))
            entry = tk.Entry(container, font=("Inter", 10), bd=0, bg=COLORS["bg"], fg=COLORS["text"], highlightthickness=1, highlightbackground=COLORS["border"])
            entry.pack(fill="x", ipady=6)
            return entry

        if type == "add":
            n_e = create_field("NOME DO MATERIAL")
            c_e = create_field("CATEGORIA")
            q_e = create_field("QUANTIDADE")
        else:
            n_e = create_field("NOME COMPLETO")
            r_e = create_field("CARGO / SETOR")

        def save():
            if type == "add":
                if n_e.get() and q_e.get().isdigit():
                    fb_request("products", "POST", {"name": n_e.get(), "category": c_e.get(), "quantity": int(q_e.get())})
                    self.show_inventory()
            else:
                if n_e.get():
                    fb_request("employees", "POST", {"name": n_e.get(), "role": r_e.get() or "Geral"})
                    self.show_employees()
            modal.destroy()

        tk.Button(container, text="SALVAR DADOS", command=save, bg=COLORS["accent"], fg="white", font=("Inter", 10, "bold"), bd=0, pady=10).pack(fill="x", pady=(30, 0))

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
