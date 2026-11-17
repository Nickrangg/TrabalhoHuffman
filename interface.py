import os
import inspect
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from huffman_core import CompactadorHuffman

COR_FUNDO_PRINCIPAL = "#0b0f17"
COR_SIDEBAR = "#111622"
COR_CARD = "#161c2a"
COR_CARD_INTERNO = "#1d2436"
COR_BORDA = "#262f45"
COR_PRIMARIA = "#58a6ff"
COR_PRIMARIA_HOVER = "#388bfd"
COR_PRIMARIA_SUAVE = "#162647"
COR_SUCESSO = "#238636"
COR_SUCESSO_CLARO = "#3fb950"
COR_SUCESSO_SUAVE = "#122d1f"
COR_TEXTO = "#f0f6fc"
COR_TEXTO_SEC = "#8b949e"


class ToggleSwitch(tk.Canvas):
    def __init__(self, pai, texto, variable, bg_pai=COR_SIDEBAR, command=None):
        super().__init__(pai, height=28, bg=bg_pai, highlightthickness=0, bd=0, cursor="hand2")
        self.variable = variable
        self.texto = texto
        self.command = command
        self.bind("<Button-1>", self._alternar)
        self.bind("<Configure>", lambda _: self._desenhar())
        self._desenhar()

    def _alternar(self, _evento=None):
        self.variable.set(not self.variable.get())
        self._desenhar()
        if self.command:
            self.command()

    def _desenhar(self):
        self.delete("all")
        ativo = self.variable.get()
        cor_trilho = COR_PRIMARIA if ativo else "#2d3548"
        cor_pino = "#ffffff" if ativo else "#c9d1d9"

        x0, y0, largura, altura = 2, 5, 36, 18
        raio = altura // 2

        self.create_oval(x0, y0, x0 + altura, y0 + altura, fill=cor_trilho, outline="")
        self.create_oval(x0 + largura - altura, y0, x0 + largura, y0 + altura, fill=cor_trilho, outline="")
        self.create_rectangle(x0 + raio, y0, x0 + largura - raio, y0 + altura, fill=cor_trilho, outline="")

        cx = (x0 + largura - raio) if ativo else (x0 + raio)
        cy = y0 + raio
        r_pino = 6
        self.create_oval(cx - r_pino, cy - r_pino, cx + r_pino, cy + r_pino, fill=cor_pino, outline="")

        self.create_text(
            x0 + largura + 10,
            cy,
            text=self.texto,
            anchor="w",
            fill=COR_TEXTO if ativo else COR_TEXTO_SEC,
            font=("Segoe UI", 9)
        )


class ModernSlider(tk.Canvas):
    def __init__(self, pai, variable, from_, to, resolution=1, length=180, bg_pai=COR_CARD, command=None):
        super().__init__(pai, width=length, height=38, bg=bg_pai, highlightthickness=0, bd=0, cursor="hand2")
        self.variable = variable
        self.from_ = from_
        self.to = to
        self.resolution = resolution
        self.length = length
        self.command = command
        self.pad_x = 14

        self.bind("<Button-1>", self._interagir)
        self.bind("<B1-Motion>", self._interagir)
        self._desenhar()

    def _interagir(self, evento):
        largura_util = self.length - 2 * self.pad_x
        proporcao = max(0.0, min(1.0, (evento.x - self.pad_x) / largura_util))
        valor_bruto = self.from_ + proporcao * (self.to - self.from_)
        passos = round((valor_bruto - self.from_) / self.resolution)
        valor_final = max(self.from_, min(self.to, self.from_ + passos * self.resolution))

        if valor_final != self.variable.get():
            self.variable.set(int(valor_final))
            self._desenhar()
            if self.command:
                self.command(valor_final)
        else:
            self._desenhar()

    def _desenhar(self):
        self.delete("all")
        val = self.variable.get()
        proporcao = (val - self.from_) / (self.to - self.from_) if self.to > self.from_ else 0
        x_ini = self.pad_x
        x_fim = self.length - self.pad_x
        x_atual = x_ini + proporcao * (x_fim - x_ini)
        y_trilho = 26

        self.create_line(x_ini, y_trilho, x_fim, y_trilho, fill="#2d3548", width=4, capstyle=tk.ROUND)
        if x_atual > x_ini:
            self.create_line(x_ini, y_trilho, x_atual, y_trilho, fill=COR_PRIMARIA, width=4, capstyle=tk.ROUND)

        r = 7
        self.create_oval(x_atual - r, y_trilho - r, x_atual + r, y_trilho + r, fill=COR_PRIMARIA, outline="")
        self.create_text(x_atual, 10, text=str(val), fill=COR_PRIMARIA, font=("Segoe UI", 9, "bold"))


class InterfaceHuffman:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("Compactador de Huffman")
        self.janela.geometry("1300x820")
        self.janela.minsize(1020, 640)
        self.janela.configure(bg=COR_FUNDO_PRINCIPAL)

        self.compactador = CompactadorHuffman()

        self.var_usar_lzss = tk.BooleanVar(value=True)
        self.var_usar_lz77 = tk.BooleanVar(value=False)
        self.var_max_folhas = tk.IntVar(value=14)
        self.var_bytes_hexdump = tk.IntVar(value=704)

        self.caminho_atual = None
        self.caminho_huff_gerado = None
        self.ultimo_relatorio = None
        self.modo_atual = None

        self._configurar_ttk()
        self._construir_layout_vertical()

    def _configurar_ttk(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "TScrollbar",
            background=COR_CARD,
            troughcolor=COR_FUNDO_PRINCIPAL,
            bordercolor=COR_FUNDO_PRINCIPAL,
            arrowcolor=COR_TEXTO_SEC
        )

    def _construir_layout_vertical(self):
        self.sidebar = tk.Frame(
            self.janela,
            bg=COR_SIDEBAR,
            width=300,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        cabecalho = tk.Frame(self.sidebar, bg=COR_SIDEBAR)
        cabecalho.pack(fill=tk.X, padx=22, pady=(26, 18))

        icone_app = tk.Label(
            cabecalho,
            text="H",
            font=("Segoe UI", 13, "bold"),
            bg=COR_PRIMARIA_SUAVE,
            fg=COR_PRIMARIA,
            width=3,
            pady=4
        )
        icone_app.pack(side=tk.LEFT, padx=(0, 12))

        titulos_app = tk.Frame(cabecalho, bg=COR_SIDEBAR)
        titulos_app.pack(side=tk.LEFT)
        tk.Label(
            titulos_app,
            text="Huffman",
            font=("Segoe UI", 14, "bold"),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO
        ).pack(anchor="w")
        tk.Label(
            titulos_app,
            text="Árvore de Prefixo & LZ",
            font=("Segoe UI", 8),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w")

        tk.Frame(self.sidebar, bg=COR_BORDA, height=1).pack(fill=tk.X, padx=22, pady=(0, 18))

        tk.Label(
            self.sidebar,
            text="Arquivo",
            font=("Segoe UI", 9, "bold"),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO
        ).pack(anchor="w", padx=22, pady=(0, 8))

        self.btn_anexo = tk.Button(
            self.sidebar,
            text="Selecionar arquivo\n.txt ou .huff",
            font=("Segoe UI", 9, "bold"),
            bg=COR_CARD,
            fg=COR_PRIMARIA,
            activebackground=COR_CARD_INTERNO,
            activeforeground=COR_PRIMARIA,
            bd=0,
            highlightbackground=COR_BORDA,
            highlightthickness=1,
            cursor="hand2",
            command=self._acao_anexar_arquivo_inteligente
        )
        self.btn_anexo.pack(fill=tk.X, padx=22, pady=(0, 20), ipady=14)

        tk.Label(
            self.sidebar,
            text="Opções",
            font=("Segoe UI", 9, "bold"),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO
        ).pack(anchor="w", padx=22, pady=(0, 8))

        ToggleSwitch(
            self.sidebar,
            texto="Usar LZSS antes do Huffman",
            variable=self.var_usar_lzss,
            bg_pai=COR_SIDEBAR
        ).pack(fill=tk.X, padx=22, pady=(0, 6))

        ToggleSwitch(
            self.sidebar,
            texto="Usar LZ77 antes do Huffman",
            variable=self.var_usar_lz77,
            bg_pai=COR_SIDEBAR
        ).pack(fill=tk.X, padx=22, pady=(0, 16))

        tk.Frame(self.sidebar, bg=COR_BORDA, height=1).pack(fill=tk.X, padx=22, pady=8)

        self.container_acao = tk.Frame(self.sidebar, bg=COR_SIDEBAR)
        self.container_acao.pack(fill=tk.X, padx=22, pady=(10, 10))

        self.area_principal = tk.Frame(self.janela, bg=COR_FUNDO_PRINCIPAL)
        self.area_principal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scroll_y = ttk.Scrollbar(self.area_principal, orient=tk.VERTICAL)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas_tela = tk.Canvas(
            self.area_principal,
            bg=COR_FUNDO_PRINCIPAL,
            highlightthickness=0,
            yscrollcommand=self.scroll_y.set
        )
        self.canvas_tela.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll_y.config(command=self.canvas_tela.yview)

        self.conteudo = tk.Frame(self.canvas_tela, bg=COR_FUNDO_PRINCIPAL, padx=38, pady=32)
        self.janela_canvas_id = self.canvas_tela.create_window(
            (0, 0), window=self.conteudo, anchor="nw"
        )

        self.conteudo.bind(
            "<Configure>",
            lambda _: self.canvas_tela.configure(scrollregion=self.canvas_tela.bbox("all"))
        )
        self.canvas_tela.bind(
            "<Configure>",
            lambda e: self.canvas_tela.itemconfig(self.janela_canvas_id, width=e.width)
        )
        self.janela.bind_all("<MouseWheel>", self._scroll_mouse)

        self._mostrar_tela_boas_vindas()

    def _scroll_mouse(self, evento):
        if not isinstance(evento.widget, tk.Text):
            self.canvas_tela.yview_scroll(int(-1 * (evento.delta / 120)), "units")

    def _acao_anexar_arquivo_inteligente(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar arquivo",
            filetypes=[("Arquivos Suportados", "*.txt;*.huff"), ("Todos os Arquivos", "*.*")]
        )
        if not caminho:
            return

        if not (caminho.endswith(".txt") or caminho.endswith(".huff")):
            messagebox.showerror("Formato Inválido", "Selecione um arquivo .txt ou .huff.")
            return

        self.caminho_atual = caminho
        nome_arq = os.path.basename(caminho)
        tamanho_kb = os.path.getsize(caminho) / 1024

        self.btn_anexo.config(
            text=f"{nome_arq}\n{tamanho_kb:.2f} KB",
            fg=COR_TEXTO,
            bg=COR_CARD_INTERNO
        )

        self._revelar_botao_acao_correspondente(caminho, nome_arq, tamanho_kb)

    def _revelar_botao_acao_correspondente(self, caminho, nome_arq, tamanho_kb):
        for widget in self.container_acao.winfo_children():
            widget.destroy()

        if caminho.endswith(".txt"):
            btn_executar = tk.Button(
                self.container_acao,
                text="Compactar",
                font=("Segoe UI", 10, "bold"),
                bg=COR_PRIMARIA,
                fg="#0b0f17",
                activebackground=COR_PRIMARIA_HOVER,
                activeforeground="#ffffff",
                bd=0,
                pady=10,
                cursor="hand2",
                command=self._executar_fluxo_compactacao
            )
            btn_executar.pack(fill=tk.X)
            subtitulo = "Pronto para compactação"
        else:
            btn_executar = tk.Button(
                self.container_acao,
                text="Descompactar",
                font=("Segoe UI", 10, "bold"),
                bg=COR_SUCESSO,
                fg="#ffffff",
                activebackground="#2ea043",
                activeforeground="#ffffff",
                bd=0,
                pady=10,
                cursor="hand2",
                command=self._executar_fluxo_descompactacao
            )
            btn_executar.pack(fill=tk.X)
            subtitulo = "Pronto para descompactação"

        for widget in self.conteudo.winfo_children():
            widget.destroy()

        tk.Label(
            self.conteudo,
            text=nome_arq,
            font=("Segoe UI", 20, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO
        ).pack(anchor="w", pady=(10, 4))

        tk.Label(
            self.conteudo,
            text=f"{tamanho_kb:.2f} KB  •  {subtitulo}",
            font=("Segoe UI", 10),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w")

    def _ocultar_botao_acao(self):
        for widget in self.container_acao.winfo_children():
            widget.destroy()

    def _executar_fluxo_compactacao(self):
        saida_huff = os.path.splitext(self.caminho_atual)[0] + ".huff"
        try:
            self.modo_atual = "compactacao"

            params = inspect.signature(self.compactador.compactar_arquivo).parameters
            kwargs = {}
            if "usar_lzss" in params:
                kwargs["usar_lzss"] = self.var_usar_lzss.get()
            if "usar_lz77" in params:
                kwargs["usar_lz77"] = (
                    self.var_usar_lz77.get()
                    if "usar_lzss" in params
                    else self.var_usar_lzss.get()
                )

            self.ultimo_relatorio = self.compactador.compactar_arquivo(
                self.caminho_atual, saida_huff, **kwargs
            )
            self.caminho_huff_gerado = saida_huff

            self._ocultar_botao_acao()

            for widget in self.conteudo.winfo_children():
                widget.destroy()

            self.canvas_tela.yview_moveto(0)
            self._renderizar_bloco_titulo(
                "Visão Geral da Compactação",
                f"Arquivo processado: {os.path.basename(self.caminho_atual)}"
            )
            self._renderizar_bloco_metricas_compactacao()
            self._renderizar_bloco_hexdump(saida_huff)
            self._renderizar_bloco_arvore()

        except Exception as e:
            messagebox.showerror("Erro na Compactação", str(e))

    def _executar_fluxo_descompactacao(self):
        saida_txt = os.path.splitext(self.caminho_atual)[0] + "_restaurado.txt"
        try:
            self.modo_atual = "descompactacao"
            self.ultimo_relatorio = self.compactador.descompactar_arquivo(
                self.caminho_atual, saida_txt
            )
            self.caminho_huff_gerado = self.caminho_atual

            self._ocultar_botao_acao()

            for widget in self.conteudo.winfo_children():
                widget.destroy()

            self.canvas_tela.yview_moveto(0)
            self._renderizar_bloco_titulo(
                "Visão Geral da Descompactação",
                f"Arquivo restaurado: {os.path.basename(saida_txt)}"
            )
            self._renderizar_bloco_metricas_descompactacao()
            self._renderizar_bloco_hexdump(self.caminho_atual)
            self._renderizar_bloco_arvore()

        except Exception as e:
            messagebox.showerror("Erro na Descompactação", str(e))

    def _mostrar_tela_boas_vindas(self):
        tk.Label(
            self.conteudo,
            text="Nenhum arquivo carregado",
            font=("Segoe UI", 18, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO
        ).pack(anchor="w", pady=(10, 4))

        tk.Label(
            self.conteudo,
            text="Selecione um arquivo .txt ou .huff no painel lateral.",
            font=("Segoe UI", 10),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w")

    def _renderizar_bloco_titulo(self, titulo, subtitulo=""):
        cab = tk.Frame(self.conteudo, bg=COR_FUNDO_PRINCIPAL)
        cab.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            cab,
            text=titulo,
            font=("Segoe UI", 20, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO
        ).pack(anchor="w")

        if subtitulo:
            tk.Label(
                cab,
                text=subtitulo,
                font=("Segoe UI", 10),
                bg=COR_FUNDO_PRINCIPAL,
                fg=COR_TEXTO_SEC
            ).pack(anchor="w", pady=(2, 0))

    def _renderizar_bloco_metricas_compactacao(self):
        r = self.ultimo_relatorio

        grid = tk.Frame(self.conteudo, bg=COR_FUNDO_PRINCIPAL)
        grid.pack(fill=tk.X, pady=(0, 18))

        metricas = [
            ("📄", "ENTRADA", f"{r['bytes_originais']/1024:.2f} KB", "Tamanho Original", f"{r['bits_originais']} bits"),
            ("🗜️", "SAÍDA", f"{r['bytes_arquivo_final']/1024:.2f} KB", "Arquivo .huff", f"{r['bits_compactados']} bits codificados"),
            ("📉", f"-{r['taxa_compactacao_pct']:.1f}%", f"{r['taxa_compactacao_pct']:.2f}%", "Taxa de Compactação", "Redução de bits"),
            ("⏱️", "TEMPO", f"{r['tempo_s']:.4f} s", "Tempo de Execução", "Processamento total")
        ]

        for idx, (icone, badge, valor, titulo, sub) in enumerate(metricas):
            padx_col = (0, 14) if idx < 3 else (0, 0)
            col = tk.Frame(
                grid,
                bg=COR_CARD,
                padx=18,
                pady=16,
                highlightbackground=COR_BORDA,
                highlightthickness=1
            )
            col.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=padx_col)

            topo_col = tk.Frame(col, bg=COR_CARD)
            topo_col.pack(fill=tk.X, pady=(0, 12))

            tk.Label(
                topo_col,
                text=icone,
                font=("Segoe UI", 10),
                bg=COR_CARD_INTERNO,
                fg=COR_PRIMARIA,
                padx=7,
                pady=3
            ).pack(side=tk.LEFT)

            cor_bg_badge = COR_SUCESSO_SUAVE if idx == 2 else COR_PRIMARIA_SUAVE
            cor_fg_badge = COR_SUCESSO_CLARO if idx == 2 else COR_PRIMARIA
            tk.Label(
                topo_col,
                text=badge,
                font=("Segoe UI", 8, "bold"),
                bg=cor_bg_badge,
                fg=cor_fg_badge,
                padx=8,
                pady=2
            ).pack(side=tk.RIGHT)

            tk.Label(col, text=valor, font=("Segoe UI", 18, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(anchor="w")
            tk.Label(col, text=titulo, font=("Segoe UI", 9, "bold"), bg=COR_CARD, fg=COR_TEXTO).pack(anchor="w", pady=(4, 1))
            tk.Label(col, text=sub, font=("Segoe UI", 8), bg=COR_CARD, fg=COR_TEXTO_SEC).pack(anchor="w")

        card = tk.Frame(
            self.conteudo,
            bg=COR_CARD,
            padx=22,
            pady=18,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        card.pack(fill=tk.X, pady=(0, 20))

        tk.Label(
            card,
            text="Análise Matemática e Tabela de Códigos",
            font=("Segoe UI", 12, "bold"),
            bg=COR_CARD,
            fg=COR_TEXTO
        ).pack(anchor="w", pady=(0, 12))

        txt_mat = tk.Text(
            card,
            height=9,
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO,
            font=("Consolas", 10),
            bd=0,
            highlightbackground=COR_BORDA,
            highlightthickness=1,
            padx=14,
            pady=12
        )
        txt_mat.pack(fill=tk.X)

        resumo_mat = (
            f"Taxa (%) = (1 - (Bits_Compactados / Bits_Originais)) * 100\n"
            f"Taxa (%) = (1 - ({r['bits_compactados']} / {r['bits_originais']})) * 100 = {r['taxa_compactacao_pct']:.2f}%\n\n"
            f"{'Símbolo':<16} | {'Frequência (Peso)':<18} | {'Bits':<6} | {'Código Binário'}\n"
            + ("-" * 68) + "\n"
        )
        txt_mat.insert(tk.END, resumo_mat)

        ordenados = sorted(self.compactador.frequencias.items(), key=lambda x: x[1], reverse=True)
        for char, freq in ordenados[:35]:
            cod = self.compactador.tabela_codigos[char]
            txt_mat.insert(tk.END, f"{repr(char):<16} | {freq:<18} | {len(cod):<6} | {cod}\n")

        txt_mat.config(state=tk.DISABLED)

    def _renderizar_bloco_metricas_descompactacao(self):
        r = self.ultimo_relatorio
        card = tk.Frame(
            self.conteudo,
            bg=COR_CARD,
            padx=22,
            pady=18,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        card.pack(fill=tk.X, pady=(0, 20))

        topo = tk.Frame(card, bg=COR_CARD)
        topo.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            topo,
            text="Texto Original Restaurado",
            font=("Segoe UI", 12, "bold"),
            bg=COR_CARD,
            fg=COR_TEXTO
        ).pack(side=tk.LEFT)

        tk.Label(
            topo,
            text=f"{r['bytes_restaurado']} B  •  {r['tempo_s']:.4f} s",
            font=("Segoe UI", 8, "bold"),
            bg=COR_SUCESSO_SUAVE,
            fg=COR_SUCESSO_CLARO,
            padx=10,
            pady=3
        ).pack(side=tk.RIGHT)

        txt = tk.Text(
            card,
            height=8,
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO,
            font=("Consolas", 10),
            bd=0,
            highlightbackground=COR_BORDA,
            highlightthickness=1,
            padx=14,
            pady=12
        )
        txt.pack(fill=tk.X)
        txt.insert("1.0", r["texto_restaurado"][:1500])
        txt.config(state=tk.DISABLED)

    def _renderizar_bloco_hexdump(self, caminho_huff):
        card = tk.Frame(
            self.conteudo,
            bg=COR_CARD,
            padx=22,
            pady=18,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        card.pack(fill=tk.X, pady=(0, 20))

        topo_hex = tk.Frame(card, bg=COR_CARD)
        topo_hex.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            topo_hex,
            text="Hexdump (.huff)",
            font=("Segoe UI", 12, "bold"),
            bg=COR_CARD,
            fg=COR_TEXTO
        ).pack(side=tk.LEFT)

        painel_slider_hex = tk.Frame(topo_hex, bg=COR_CARD)
        painel_slider_hex.pack(side=tk.RIGHT)

        tk.Label(
            painel_slider_hex,
            text="Bytes no hexdump",
            font=("Segoe UI", 9),
            bg=COR_CARD,
            fg=COR_TEXTO_SEC
        ).pack(side=tk.LEFT, padx=(0, 10), pady=(12, 0))

        ModernSlider(
            painel_slider_hex,
            variable=self.var_bytes_hexdump,
            from_=64,
            to=2048,
            resolution=64,
            length=180,
            bg_pai=COR_CARD,
            command=lambda _: self._atualizar_hexdump_ao_vivo()
        ).pack(side=tk.LEFT)

        self.txt_hexdump_tela = tk.Text(
            card,
            height=10,
            bg=COR_FUNDO_PRINCIPAL,
            fg="#79c0ff",
            font=("Consolas", 10),
            bd=0,
            highlightbackground=COR_BORDA,
            highlightthickness=1,
            padx=14,
            pady=12
        )
        self.txt_hexdump_tela.pack(fill=tk.X)
        self._atualizar_hexdump_ao_vivo(caminho_huff)

        if self.modo_atual == "compactacao" and "string_bits" in self.ultimo_relatorio:
            tk.Label(
                card,
                text="Fluxo de Bits (0 e 1)",
                font=("Segoe UI", 9, "bold"),
                bg=COR_CARD,
                fg=COR_TEXTO_SEC
            ).pack(anchor="w", pady=(14, 6))

            txt_bits = tk.Text(
                card,
                height=4,
                bg=COR_FUNDO_PRINCIPAL,
                fg=COR_SUCESSO_CLARO,
                font=("Consolas", 10),
                bd=0,
                highlightbackground=COR_BORDA,
                highlightthickness=1,
                padx=14,
                pady=10
            )
            txt_bits.pack(fill=tk.X)
            txt_bits.insert("1.0", self.ultimo_relatorio["string_bits"][:1500])
            txt_bits.config(state=tk.DISABLED)

    def _renderizar_bloco_arvore(self):
        card = tk.Frame(
            self.conteudo,
            bg=COR_CARD,
            padx=22,
            pady=18,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        card.pack(fill=tk.X, pady=(0, 20))

        topo_arvore = tk.Frame(card, bg=COR_CARD)
        topo_arvore.pack(fill=tk.X, pady=(0, 6))

        bloco_esq = tk.Frame(topo_arvore, bg=COR_CARD)
        bloco_esq.pack(side=tk.LEFT)

        tk.Label(
            bloco_esq,
            text="Árvore de Huffman",
            font=("Segoe UI", 12, "bold"),
            bg=COR_CARD,
            fg=COR_TEXTO
        ).pack(anchor="w")

        tk.Label(
            bloco_esq,
            text="Esquerda (azul): bit 0   |   Direita (laranja): bit 1",
            font=("Segoe UI", 9),
            bg=COR_CARD,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w", pady=(2, 0))

        painel_slider_folhas = tk.Frame(topo_arvore, bg=COR_CARD)
        painel_slider_folhas.pack(side=tk.RIGHT)

        tk.Label(
            painel_slider_folhas,
            text="Folhas exibidas na árvore",
            font=("Segoe UI", 9),
            bg=COR_CARD,
            fg=COR_TEXTO_SEC
        ).pack(side=tk.LEFT, padx=(0, 10), pady=(12, 0))

        ModernSlider(
            painel_slider_folhas,
            variable=self.var_max_folhas,
            from_=5,
            to=80,
            resolution=1,
            length=180,
            bg_pai=COR_CARD,
            command=lambda _: self._atualizar_arvore_ao_vivo()
        ).pack(side=tk.LEFT)

        frame_canvas = tk.Frame(
            card,
            bg=COR_FUNDO_PRINCIPAL,
            highlightbackground=COR_BORDA,
            highlightthickness=1,
            height=450
        )
        frame_canvas.pack(fill=tk.X, pady=(8, 0))
        frame_canvas.pack_propagate(False)

        sx = ttk.Scrollbar(frame_canvas, orient=tk.HORIZONTAL)
        sy = ttk.Scrollbar(frame_canvas, orient=tk.VERTICAL)
        self.canvas_arvore = tk.Canvas(
            frame_canvas,
            bg=COR_FUNDO_PRINCIPAL,
            highlightthickness=0,
            xscrollcommand=sx.set,
            yscrollcommand=sy.set
        )
        sx.config(command=self.canvas_arvore.xview)
        sy.config(command=self.canvas_arvore.yview)
        sx.pack(side=tk.BOTTOM, fill=tk.X)
        sy.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_arvore.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._atualizar_arvore_ao_vivo()

    def _atualizar_hexdump_ao_vivo(self, caminho=None):
        if not hasattr(self, "txt_hexdump_tela") or not self.txt_hexdump_tela.winfo_exists():
            return

        caminho_alvo = caminho or getattr(self, "caminho_huff_gerado", None)
        if not caminho_alvo or not os.path.exists(caminho_alvo):
            return

        limite = self.var_bytes_hexdump.get()
        with open(caminho_alvo, "rb") as f:
            dados = f.read(limite)

        linhas = []
        for i in range(0, len(dados), 16):
            bloco = dados[i:i + 16]
            hex_str = " ".join(f"{b:02X}" for b in bloco)
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in bloco)
            linhas.append(f"{i:04X}  |  {hex_str:<47}  |  {ascii_str}")

        self.txt_hexdump_tela.config(state=tk.NORMAL)
        self.txt_hexdump_tela.delete("1.0", tk.END)
        self.txt_hexdump_tela.insert("1.0", "\n".join(linhas))
        self.txt_hexdump_tela.config(state=tk.DISABLED)

    def _atualizar_arvore_ao_vivo(self):
        if not hasattr(self, "canvas_arvore") or not self.canvas_arvore.winfo_exists():
            return
        if not self.compactador.raiz:
            return

        limite_folhas = self.var_max_folhas.get()
        self.canvas_arvore.delete("all")
        posicoes = {}
        folhas_contadas = [0]
        esp_x, esp_y = 80, 85

        def calc_coords(no, prof):
            if no is None:
                return False
            if no.esquerda is None and no.direita is None:
                if folhas_contadas[0] >= limite_folhas:
                    return False
                x = 60 + folhas_contadas[0] * esp_x
                y = 50 + prof * esp_y
                posicoes[no] = (x, y)
                folhas_contadas[0] += 1
                return True
            calc_coords(no.esquerda, prof + 1)
            calc_coords(no.direita, prof + 1)
            filhos = [posicoes[f][0] for f in (no.esquerda, no.direita) if f in posicoes]
            if not filhos:
                return False
            posicoes[no] = (sum(filhos) / len(filhos), 50 + prof * esp_y)
            return True

        calc_coords(self.compactador.raiz, 0)

        for no, (x1, y1) in posicoes.items():
            if no.esquerda in posicoes:
                x2, y2 = posicoes[no.esquerda]
                self.canvas_arvore.create_line(x1, y1, x2, y2, fill=COR_PRIMARIA, width=2)
                self.canvas_arvore.create_text(
                    (x1 + x2) / 2 - 10, (y1 + y2) / 2,
                    text="0", fill=COR_PRIMARIA, font=("Segoe UI", 9, "bold")
                )
            if no.direita in posicoes:
                x2, y2 = posicoes[no.direita]
                self.canvas_arvore.create_line(x1, y1, x2, y2, fill="#f0883e", width=2)
                self.canvas_arvore.create_text(
                    (x1 + x2) / 2 + 10, (y1 + y2) / 2,
                    text="1", fill="#f0883e", font=("Segoe UI", 9, "bold")
                )

        for no, (x, y) in posicoes.items():
            r = 24
            eh_folha = no.caractere is not None
            bg = "#1f6feb" if eh_folha else COR_CARD_INTERNO
            outline = COR_PRIMARIA if eh_folha else COR_BORDA
            self.canvas_arvore.create_oval(
                x - r, y - r, x + r, y + r, fill=bg, outline=outline, width=2
            )
            txt = f"{repr(no.caractere)}\n({no.frequencia})" if eh_folha else f"{no.frequencia}"
            self.canvas_arvore.create_text(
                x, y, text=txt, fill=COR_TEXTO, font=("Segoe UI", 8, "bold")
            )

        self.canvas_arvore.configure(scrollregion=self.canvas_arvore.bbox("all"))


if __name__ == "__main__":
    raiz_tk = tk.Tk()
    app = InterfaceHuffman(raiz_tk)
    raiz_tk.mainloop()