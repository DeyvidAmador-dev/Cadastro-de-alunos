import psycopg2
from psycopg2 import Error
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# 🔗 Função para criar conexão com PostgreSQL
def criar_conexao():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="escola",
            user="guedes",
            password="Guedes123",
            port=5432
        )
        return conn
    except Error as e:
        print(f"Erro na conexão: {e}")
        return None

# 🗄️ Criação de tabelas
def criar_tabelas(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alunos (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        idade INTEGER,
        curso TEXT,
        matricula TEXT UNIQUE
    );""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notas (
        id SERIAL PRIMARY KEY,
        matricula TEXT NOT NULL,
        materia TEXT NOT NULL,
        nota REAL,
        FOREIGN KEY(matricula) REFERENCES alunos(matricula)
    );""")
    conn.commit()

# 🔥 CRUD Alunos
def inserir_aluno(conn, aluno):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO alunos (nome, idade, curso, matricula) VALUES (%s, %s, %s, %s)", aluno)
    conn.commit()

def atualizar_aluno(conn, aluno):
    cursor = conn.cursor()
    cursor.execute("UPDATE alunos SET nome=%s, idade=%s, curso=%s WHERE matricula=%s", aluno)
    conn.commit()

def deletar_aluno(conn, matricula):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alunos WHERE matricula=%s", (matricula,))
    cursor.execute("DELETE FROM notas WHERE matricula=%s", (matricula,))
    conn.commit()

def selecionar_alunos(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alunos")
    return cursor.fetchall()

def buscar_matriculas(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT nome, matricula FROM alunos")
    return cursor.fetchall()

# 🔥 CRUD Notas
def inserir_nota(conn, nota):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notas (matricula, materia, nota) VALUES (%s, %s, %s)", nota)
    conn.commit()

def selecionar_notas_organizadas(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.nome, n.matricula, n.materia, n.nota
        FROM notas n
        JOIN alunos a ON a.matricula = n.matricula
        ORDER BY a.nome, n.materia
    """)
    resultados = cursor.fetchall()
    agrupado = {}
    for nome, matricula, materia, nota in resultados:
        if matricula not in agrupado:
            agrupado[matricula] = {"nome": nome, "notas": []}
        agrupado[matricula]["notas"].append((materia, nota))
    return agrupado

# 🖥️ Interface Tkinter
class App(tk.Tk):
    def _init_(self):
        super()._init_()
        self.title("Sistema de Alunos e Notas - PostgreSQL")
        self.geometry("750x600")

        self.conn = criar_conexao()
        criar_tabelas(self.conn)

        self.frame_botoes = tk.Frame(self)
        self.frame_botoes.pack(pady=10)

        self.frame_formulario = tk.Frame(self)
        self.frame_formulario.pack()

        self.output_box = scrolledtext.ScrolledText(self, width=90, height=20)
        self.output_box.pack(pady=10)

        botoes = [
            ("Adicionar Aluno", self.form_adicionar_aluno),
            ("Atualizar Aluno", self.form_atualizar_aluno),
            ("Deletar Aluno", self.form_deletar_aluno),
            ("Visualizar Alunos", self.visualizar_alunos),
            ("Adicionar Nota", self.form_adicionar_nota),
            ("Visualizar Notas", self.visualizar_notas)
        ]

        for texto, comando in botoes:
            tk.Button(self.frame_botoes, text=texto, command=comando).pack(side=tk.LEFT, padx=5)

    def limpar_formulario(self):
        for widget in self.frame_formulario.winfo_children():
            widget.destroy()

    def form_adicionar_aluno(self):
        self.limpar_formulario()
        campos = {}
        for campo in ["Nome", "Idade", "Curso", "Matrícula"]:
            tk.Label(self.frame_formulario, text=campo).pack()
            entrada = tk.Entry(self.frame_formulario)
            entrada.pack()
            campos[campo.lower()] = entrada

        def salvar():
            try:
                inserir_aluno(self.conn, (
                    campos["nome"].get(),
                    int(campos["idade"].get()),
                    campos["curso"].get(),
                    campos["matricula"].get()
                ))
                messagebox.showinfo("Sucesso", "Aluno adicionado!")
                self.visualizar_alunos()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        tk.Button(self.frame_formulario, text="Salvar", command=salvar).pack(pady=5)

    def form_atualizar_aluno(self):
        self.limpar_formulario()
        campos = {}
        for campo in ["Nome", "Idade", "Curso", "Matrícula"]:
            tk.Label(self.frame_formulario, text=campo).pack()
            entrada = tk.Entry(self.frame_formulario)
            entrada.pack()
            campos[campo.lower()] = entrada

        def atualizar():
            try:
                atualizar_aluno(self.conn, (
                    campos["nome"].get(),
                    int(campos["idade"].get()),
                    campos["curso"].get(),
                    campos["matricula"].get()
                ))
                messagebox.showinfo("Sucesso", "Aluno atualizado!")
                self.visualizar_alunos()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        tk.Button(self.frame_formulario, text="Atualizar", command=atualizar).pack(pady=5)

    def form_deletar_aluno(self):
        self.limpar_formulario()
        tk.Label(self.frame_formulario, text="Matrícula a deletar:").pack()
        matricula = tk.Entry(self.frame_formulario)
        matricula.pack()

        def deletar():
            try:
                deletar_aluno(self.conn, matricula.get())
                messagebox.showinfo("Sucesso", "Aluno deletado!")
                self.visualizar_alunos()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        tk.Button(self.frame_formulario, text="Deletar", command=deletar).pack(pady=5)

    def form_adicionar_nota(self):
        self.limpar_formulario()
        alunos = buscar_matriculas(self.conn)
        aluno_dict = {f"{nome} ({matricula})": matricula for nome, matricula in alunos}
        opcoes = list(aluno_dict.keys())
        tk.Label(self.frame_formulario, text="Selecione o aluno:").pack()
        combo = ttk.Combobox(self.frame_formulario, values=opcoes, state="readonly")
        combo.pack()

        tk.Label(self.frame_formulario, text="Matéria:").pack()
        materia = tk.Entry(self.frame_formulario)
        materia.pack()

        tk.Label(self.frame_formulario, text="Nota:").pack()
        nota = tk.Entry(self.frame_formulario)
        nota.pack()

        def salvar():
            try:
                matricula = aluno_dict[combo.get()]
                inserir_nota(self.conn, (matricula, materia.get(), float(nota.get())))
                messagebox.showinfo("Sucesso", "Nota adicionada!")
                self.visualizar_notas()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        tk.Button(self.frame_formulario, text="Salvar Nota", command=salvar).pack(pady=5)

    def visualizar_alunos(self):
        alunos = selecionar_alunos(self.conn)
        self.output_box.delete("1.0", "end")
        self.output_box.insert("end", "=== Alunos ===\n")
        for aluno in alunos:
            self.output_box.insert("end", f"{aluno}\n")

    def visualizar_notas(self):
        notas = selecionar_notas_organizadas(self.conn)
        self.output_box.delete("1.0", "end")
        self.output_box.insert("end", "=== Notas por Aluno ===\n")
        for matricula, dados in notas.items():
            self.output_box.insert("end", f"\nAluno: {dados['nome']} (Matrícula: {matricula})\n")
            total = 0
            for materia, nota in dados["notas"]:
                self.output_box.insert("end", f"  - {materia}: {nota}\n")
                total += nota
            media = total / len(dados["notas"])
            situacao = "✅ Aprovado" if media >= 6 else "❌ Reprovado"
            self.output_box.insert("end", f"  Média: {media:.2f} - Situação: {situacao}\n")

if _name_ == "_main_":
    app = App()
    app.mainloop(
