
import os
import sqlite3
from datetime import datetime

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window

Window.clearcolor = (0.95, 0.96, 0.98, 1)


class NegocioFacil(App):

    def build(self):
        self.title = "Negócio Fácil"

        os.makedirs(self.user_data_dir, exist_ok=True)
        self.db_path = os.path.join(self.user_data_dir, "negocio.db")
        self.criar_banco()

        self.base = BoxLayout(
            orientation="vertical",
            padding=dp(10),
            spacing=dp(8)
        )

        titulo = Label(
            text="[b]NEGÓCIO FÁCIL[/b]",
            markup=True,
            font_size="24sp",
            color=(0.05, 0.25, 0.45, 1),
            size_hint_y=None,
            height=dp(55)
        )
        self.base.add_widget(titulo)

        menu = GridLayout(
            cols=3,
            spacing=dp(5),
            size_hint_y=None,
            height=dp(105)
        )

        botoes = [
            ("Início", self.inicio),
            ("Produtos", self.produtos),
            ("Vendas", self.vendas),
            ("Despesas", self.despesas),
            ("Dívidas", self.dividas),
            ("Atualizar", self.inicio)
        ]

        for nome, funcao in botoes:
            botao = Button(
                text=nome,
                font_size="14sp",
                background_normal="",
                background_color=(0.08, 0.35, 0.58, 1)
            )
            botao.bind(on_release=lambda btn, f=funcao: f())
            menu.add_widget(botao)

        self.base.add_widget(menu)

        self.conteudo = BoxLayout(orientation="vertical")
        self.base.add_widget(self.conteudo)

        self.inicio()
        return self.base

    def conectar(self):
        return sqlite3.connect(self.db_path)

    def criar_banco(self):
        with self.conectar() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT,
                    quantidade INTEGER,
                    preco REAL
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS vendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto TEXT,
                    quantidade INTEGER,
                    total REAL,
                    data TEXT
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS despesas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descricao TEXT,
                    valor REAL,
                    data TEXT
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS dividas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente TEXT,
                    descricao TEXT,
                    valor REAL,
                    estado TEXT,
                    data TEXT
                )
            """)

    def limpar(self):
        self.conteudo.clear_widgets()

    def rotulo(self, texto, tamanho=18):
        return Label(
            text=texto,
            font_size=f"{tamanho}sp",
            color=(0.12, 0.15, 0.20, 1),
            size_hint_y=None,
            height=dp(42)
        )

    def botao(self, texto, funcao, cor=(0.08, 0.35, 0.58, 1)):
        b = Button(
            text=texto,
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=cor
        )
        b.bind(on_release=lambda x: funcao())
        return b

    def inicio(self):
        self.limpar()

        with self.conectar() as db:
            produtos = db.execute(
                "SELECT COUNT(*) FROM produtos"
            ).fetchone()[0]

            stock = db.execute(
                "SELECT COALESCE(SUM(quantidade),0) FROM produtos"
            ).fetchone()[0]

            vendas = db.execute(
                "SELECT COALESCE(SUM(total),0) FROM vendas"
            ).fetchone()[0]

            despesas = db.execute(
                "SELECT COALESCE(SUM(valor),0) FROM despesas"
            ).fetchone()[0]

            dividas = db.execute(
                "SELECT COALESCE(SUM(valor),0) FROM dividas WHERE estado='Pendente'"
            ).fetchone()[0]

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(8)
        )

        layout.add_widget(self.rotulo("PAINEL DE CONTROLO", 21))

        dados = [
            f"Produtos registados: {produtos}",
            f"Unidades em stock: {stock}",
            f"Total de vendas: {vendas:,.2f} Kz",
            f"Total de despesas: {despesas:,.2f} Kz",
            f"Dívidas pendentes: {dividas:,.2f} Kz"
        ]

        for item in dados:
            layout.add_widget(self.rotulo(item, 16))

        layout.add_widget(self.rotulo(
            "Bem-vindo ao Negócio Fácil!", 17
        ))

        self.conteudo.add_widget(layout)

    def abrir_formulario(self, titulo, campos, guardar):
        layout = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8)
        )

        entradas = {}

        for chave, dica in campos:
            entrada = TextInput(
                hint_text=dica,
                multiline=False,
                size_hint_y=None,
                height=dp(48),
                font_size="16sp"
            )
            entradas[chave] = entrada
            layout.add_widget(entrada)

        botoes = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8)
        )

        popup = Popup(
            title=titulo,
            content=layout,
            size_hint=(0.92, 0.75)
        )

        def confirmar(instance):
            valores = {
                chave: campo.text.strip()
                for chave, campo in entradas.items()
            }

            if any(not v for v in valores.values()):
                self.mensagem("Preencha todos os campos.")
                return

            try:
                guardar(valores)
                popup.dismiss()
                self.inicio_atual()
            except ValueError as erro:
                self.mensagem(str(erro))
            except Exception:
                self.mensagem("Não foi possível guardar os dados.")

        botoes.add_widget(
            Button(text="Guardar", on_release=confirmar)
        )
        botoes.add_widget(
            Button(text="Cancelar", on_release=popup.dismiss)
        )

        layout.add_widget(botoes)
        popup.open()

    def inicio_atual(self):
        if self.pagina == "produtos":
            self.produtos()
        elif self.pagina == "vendas":
            self.vendas()
        elif self.pagina == "despesas":
            self.despesas()
        elif self.pagina == "dividas":
            self.dividas()
        else:
            self.inicio()

    def mensagem(self, texto):
        Popup(
            title="Negócio Fácil",
            content=Label(text=texto),
            size_hint=(0.85, 0.35)
        ).open()

    def produtos(self):
        self.pagina = "produtos"
        self.limpar()

        layout = BoxLayout(orientation="vertical", spacing=dp(8))
        layout.add_widget(self.rotulo("GESTÃO DE PRODUTOS", 20))

        layout.add_widget(self.botao(
            "+ Adicionar produto",
            self.adicionar_produto
        ))

        with self.conectar() as db:
            dados = db.execute(
                "SELECT nome, quantidade, preco FROM produtos ORDER BY id DESC"
            ).fetchall()

        for nome, quantidade, preco in dados:
            layout.add_widget(self.rotulo(
                f"{nome} | Stock: {quantidade} | {preco:,.2f} Kz",
                14
            ))

        scroll = ScrollView()
        scroll.add_widget(layout)
        self.conteudo.add_widget(scroll)

    def adicionar_produto(self):
        def guardar(v):
            quantidade = int(v["quantidade"])
            preco = float(v["preco"])

            if quantidade < 0 or preco < 0:
                raise ValueError("Use valores positivos.")

            with self.conectar() as db:
                db.execute(
                    "INSERT INTO produtos (nome, quantidade, preco) VALUES (?,?,?)",
                    (v["nome"], quantidade, preco)
                )

        self.abrir_formulario(
            "Novo produto",
            [
                ("nome", "Nome do produto"),
                ("quantidade", "Quantidade em stock"),
                ("preco", "Preço unitário em Kz")
            ],
            guardar
        )

    def vendas(self):
        self.pagina = "vendas"
        self.limpar()

        layout = BoxLayout(orientation="vertical", spacing=dp(8))
        layout.add_widget(self.rotulo("REGISTO DE VENDAS", 20))

        layout.add_widget(self.botao(
            "+ Registar venda",
            self.adicionar_venda
        ))

        with self.conectar() as db:
            dados = db.execute(
                "SELECT produto, quantidade, total, data FROM vendas ORDER BY id DESC"
            ).fetchall()

        for produto, quantidade, total, data in dados:
            layout.add_widget(self.rotulo(
                f"{produto} | {quantidade} un. | {total:,.2f} Kz | {data}",
                13
            ))

        scroll = ScrollView()
        scroll.add_widget(layout)
        self.conteudo.add_widget(scroll)

    def adicionar_venda(self):
        def guardar(v):
            quantidade = int(v["quantidade"])

            if quantidade <= 0:
                raise ValueError("Quantidade inválida.")

            with self.conectar() as db:
                produto = db.execute(
                    "SELECT id, quantidade, preco FROM produtos WHERE nome=?",
                    (v["produto"],)
                ).fetchone()

                if not produto:
                    raise ValueError("Produto não encontrado.")

                pid, stock, preco = produto

                if quantidade > stock:
                    raise ValueError("Stock insuficiente.")

                total = quantidade * preco

                db.execute(
                    "UPDATE produtos SET quantidade=? WHERE id=?",
                    (stock - quantidade, pid)
                )

                db.execute(
                    "INSERT INTO vendas (produto, quantidade, total, data) VALUES (?,?,?,?)",
                    (
                        v["produto"],
                        quantidade,
                        total,
                        datetime.now().strftime("%d/%m/%Y %H:%M")
                    )
                )

        self.abrir_formulario(
            "Nova venda",
            [
                ("produto", "Nome exato do produto"),
                ("quantidade", "Quantidade vendida")
            ],
            guardar
        )

    def despesas(self):
        self.pagina = "despesas"
        self.limpar()

        layout = BoxLayout(orientation="vertical", spacing=dp(8))
        layout.add_widget(self.rotulo("CONTROLO DE DESPESAS", 20))

        layout.add_widget(self.botao(
            "+ Adicionar despesa",
            self.adicionar_despesa
        ))

        with self.conectar() as db:
            dados = db.execute(
                "SELECT descricao, valor, data FROM despesas ORDER BY id DESC"
            ).fetchall()

        for descricao, valor, data in dados:
            layout.add_widget(self.rotulo(
                f"{descricao} | {valor:,.2f} Kz | {data}",
                14
            ))

        scroll = ScrollView()
        scroll.add_widget(layout)
        self.conteudo.add_widget(scroll)

    def adicionar_despesa(self):
        def guardar(v):
            valor = float(v["valor"])

            if valor <= 0:
                raise ValueError("O valor deve ser maior que zero.")

            with self.conectar() as db:
                db.execute(
                    "INSERT INTO despesas (descricao, valor, data) VALUES (?,?,?)",
                    (
                        v["descricao"],
                        valor,
                        datetime.now().strftime("%d/%m/%Y %H:%M")
                    )
                )

        self.abrir_formulario(
            "Nova despesa",
            [
                ("descricao", "Descrição da despesa"),
                ("valor", "Valor em Kz")
            ],
            guardar
        )

    def dividas(self):
        self.pagina = "dividas"
        self.limpar()

        layout = BoxLayout(orientation="vertical", spacing=dp(8))
        layout.add_widget(self.rotulo("CONTROLO DE DÍVIDAS", 20))

        layout.add_widget(self.botao(
            "+ Registar dívida",
            self.adicionar_divida
        ))

        with self.conectar() as db:
            dados = db.execute(
                "SELECT id, cliente, descricao, valor, estado FROM dividas ORDER BY id DESC"
            ).fetchall()

        for pid, cliente, descricao, valor, estado in dados:
            linha = BoxLayout(
                size_hint_y=None,
                height=dp(65),
                spacing=dp(5)
            )

            texto = Label(
                text=f"{cliente}: {descricao}\n{valor:,.2f} Kz - {estado}",
                color=(0.1, 0.1, 0.1, 1),
                font_size="12sp"
            )
            linha.add_widget(texto)

            if estado == "Pendente":
                btn = Button(
                    text="Recebido",
                    size_hint_x=0.35
                )
                btn.bind(
                    on_release=lambda x, i=pid: self.marcar_pago(i)
                )
                linha.add_widget(btn)

            layout.add_widget(linha)

        scroll = ScrollView()
        scroll.add_widget(layout)
        self.conteudo.add_widget(scroll)

    def adicionar_divida(self):
        def guardar(v):
            valor = float(v["valor"])

            if valor <= 0:
                raise ValueError("O valor deve ser maior que zero.")

            with self.conectar() as db:
                db.execute(
                    """INSERT INTO dividas
                    (cliente, descricao, valor, estado, data)
                    VALUES (?,?,?,?,?)""",
                    (
                        v["cliente"],
                        v["descricao"],
                        valor,
                        "Pendente",
                        datetime.now().strftime("%d/%m/%Y %H:%M")
                    )
                )

        self.abrir_formulario(
            "Nova dívida",
            [
                ("cliente", "Nome do cliente"),
                ("descricao", "Descrição da dívida"),
                ("valor", "Valor em Kz")
            ],
            guardar
        )

    def marcar_pago(self, pid):
        with self.conectar() as db:
            db.execute(
                "UPDATE dividas SET estado='Pago' WHERE id=?",
                (pid,)
            )

        self.dividas()


if __name__ == "__main__":
    NegocioFacil().run()
