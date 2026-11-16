import os
import inspect
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from huffman_core import CompactadorHuffman

# PALETA DE CORES BASE DO PROJETO (Modo Escuro Moderno)
COR_FUNDO_PRINCIPAL = "#0d1117"   # Fundo da tela de resultados (3/4)
COR_SIDEBAR = "#161b22"           # Fundo da barra lateral (1/4)
COR_CARD = "#21262d"              # Fundo dos cartões de resultado
COR_BORDA = "#30363d"             # Bordas sutis
COR_PRIMARIA = "#58a6ff"          # Azul de destaque (Compactar e detalhes)
COR_PRIMARIA_HOVER = "#1f6feb"    # Azul escuro ao clicar
COR_SUCESSO = "#238636"           # Verde estilo "Upload" / Descompactar
COR_SUCESSO_CLARO = "#3fb950"     # Verde claro para textos de confirmação
COR_TEXTO = "#c9d1d9"             # Texto principal claro
COR_TEXTO_SEC = "#8b949e"         # Texto secundário/legendas


class InterfaceHuffman:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("Compactador de Huffman - Teoria dos Grafos")
        self.janela.geometry("1300x820")
        self.janela.minsize(1020, 640)
        self.janela.configure(bg=COR_FUNDO_PRINCIPAL)

        self.compactador = CompactadorHuffman()

        # Variáveis de Estado (Padrões: LZSS ativo, 14 folhas, 704 bytes)
        self.var_usar_lzss = tk.BooleanVar(value=True)
        self.var_usar_lz77 = tk.BooleanVar(value=False)
        self.var_max_folhas = tk.IntVar(value=14)
        self.var_bytes_hexdump = tk.IntVar(value=704)

        self.caminho_atual = None
        self.caminho_huff_gerado = None
        self.ultimo_relatorio = None
        self.modo_atual = None  # 'compactacao' ou 'descompactacao'

        self._configurar_ttk()
        self._construir_layout_vertical()

    def _configurar_ttk(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "TScrollbar",
            background=COR_CARD,
            troughcolor=COR_FUNDO_PRINCIPAL,
            bordercolor=COR_BORDA,
            arrowcolor=COR_TEXTO_SEC
        )

    def _construir_layout_vertical(self):
        # ======================================================================
        # 1. BARRA LATERAL (1/4 DA TELA) - ENTRADA E CONTROLE DE SEQUÊNCIA
        # ======================================================================
        self.sidebar = tk.Frame(
            self.janela,
            bg=COR_SIDEBAR,
            width=330,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Cabeçalho da Sidebar
        tk.Label(
            self.sidebar,
            text="🗜️ Huffman",
            font=("Segoe UI", 18, "bold"),
            bg=COR_SIDEBAR,
            fg="white"
        ).pack(anchor="w", padx=20, pady=(28, 4))

        tk.Label(
            self.sidebar,
            text="Compressão por Árvore de Prefixo\ne Janela Deslizante",
            font=("Segoe UI", 9),
            justify="left",
            bg=COR_SIDEBAR,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w", padx=20, pady=(0, 18))

        tk.Frame(self.sidebar, bg=COR_BORDA, height=1).pack(fill=tk.X, padx=20, pady=8)

        # PASSO 1: BOTÃO DE ANEXO (Dropzone simulada)
        tk.Label(
            self.sidebar,
            text="1. ARQUIVO DE ENTRADA",
            font=("Segoe UI", 9, "bold"),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w", padx=20, pady=(6, 6))

        self.btn_anexo = tk.Button(
            self.sidebar,
            text="📂\n\nClique para Anexar Arquivo\n\n(Reconhecimento Automático:\n.txt ou .huff)",
            font=("Segoe UI", 10, "bold"),
            bg=COR_CARD,
            fg=COR_PRIMARIA,
            activebackground=COR_BORDA,
            activeforeground=COR_PRIMARIA,
            bd=1,
            relief="solid",
            highlightbackground=COR_BORDA,
            cursor="hand2",
            command=self._acao_anexar_arquivo_inteligente
        )
        self.btn_anexo.pack(fill=tk.X, padx=20, pady=(0, 12), ipady=16)

        # Opções de Pré-compressão
        tk.Label(
            self.sidebar,
            text="OPÇÕES DE PRÉ-COMPRESSÃO (.TXT)",
            font=("Segoe UI", 9, "bold"),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w", padx=20, pady=(8, 6))

        tk.Checkbutton(
            self.sidebar,
            text="Habilitar LZSS (Recomendado)",
            variable=self.var_usar_lzss,
            font=("Segoe UI", 9),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO,
            selectcolor=COR_CARD,
            activebackground=COR_SIDEBAR,
            activeforeground=COR_TEXTO,
            cursor="hand2"
        ).pack(anchor="w", padx=16, pady=(0, 4))

        tk.Checkbutton(
            self.sidebar,
            text="Habilitar LZ77 / llz7",
            variable=self.var_usar_lz77,
            font=("Segoe UI", 9),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO,
            selectcolor=COR_CARD,
            activebackground=COR_SIDEBAR,
            activeforeground=COR_TEXTO,
            cursor="hand2"
        ).pack(anchor="w", padx=16, pady=(0, 12))

        tk.Frame(self.sidebar, bg=COR_BORDA, height=1).pack(fill=tk.X, padx=20, pady=8)

        # PASSO 2: CONTAINER DINÂMICO DO BOTÃO DE AÇÃO (Aparece ao anexar e some após clicar)
        self.container_acao = tk.Frame(self.sidebar, bg=COR_SIDEBAR)
        self.container_acao.pack(fill=tk.X, padx=20, pady=(6, 10))

        # ======================================================================
        # 2. ÁREA PRINCIPAL (3/4 DA TELA) - ROLAGEM VERTICAL DOS RESULTADOS
        # ======================================================================
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

        # Container interno onde as informações empilham verticalmente
        self.conteudo = tk.Frame(self.canvas_tela, bg=COR_FUNDO_PRINCIPAL, padx=40, pady=36)
        self.janela_canvas_id = self.canvas_tela.create_window(
            (0, 0), window=self.conteudo, anchor="nw"
        )

        self.conteudo.bind(
            "<Configure>",
            lambda e: self.canvas_tela.configure(scrollregion=self.canvas_tela.bbox("all"))
        )
        self.canvas_tela.bind(
            "<Configure>",
            lambda e: self.canvas_tela.itemconfig(self.janela_canvas_id, width=e.width)
        )
        self.janela.bind_all("<MouseWheel>", self._scroll_mouse)

        self._mostrar_tela_boas_vindas()

    def _scroll_mouse(self, evento):
        # Evita conflito de rolagem quando o cursor está sobre caixas de texto
        if not isinstance(evento.widget, tk.Text):
            self.canvas_tela.yview_scroll(int(-1 * (evento.delta / 120)), "units")

    # ==========================================================================
    # LÓGICA DE DETECÇÃO AUTOMÁTICA + REVELAÇÃO DO BOTÃO DE AÇÃO
    # ==========================================================================
    def _acao_anexar_arquivo_inteligente(self):
        caminho = filedialog.askopenfilename(
            title="Anexe um arquivo (.txt ou .huff)",
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

        # Atualiza visualmente a caixa de anexo
        self.btn_anexo.config(
            text=f"📄 Arquivo Carregado:\n{nome_arq}\n({tamanho_kb:.2f} KB)\n\nClique para anexar outro arquivo",
            fg="white",
            bg=COR_CARD
        )

        # Revela o botão correspondente na barra lateral e prepara a tela principal
        self._revelar_botao_acao_correspondente(caminho, nome_arq, tamanho_kb)

    def _revelar_botao_acao_correspondente(self, caminho, nome_arq, tamanho_kb):
        for widget in self.container_acao.winfo_children():
            widget.destroy()

        tk.Label(
            self.container_acao,
            text="2. AÇÃO RECONHECIDA",
            font=("Segoe UI", 9, "bold"),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w", pady=(0, 6))

        if caminho.endswith(".txt"):
            tk.Label(
                self.container_acao,
                text="✔ Texto (.txt) detectado para compactação.",
                font=("Segoe UI", 9),
                bg=COR_SIDEBAR,
                fg=COR_PRIMARIA
            ).pack(anchor="w", pady=(0, 10))

            btn_executar = tk.Button(
                self.container_acao,
                text="⚡ Compactar Arquivo .TXT",
                font=("Segoe UI", 11, "bold"),
                bg=COR_PRIMARIA,
                fg="#0d1117",
                activebackground=COR_PRIMARIA_HOVER,
                activeforeground="white",
                bd=0,
                pady=12,
                cursor="hand2",
                command=self._executar_fluxo_compactacao
            )
            btn_executar.pack(fill=tk.X)
            acao_desc = "compactar e gerar a Árvore de Huffman"
        else:
            tk.Label(
                self.container_acao,
                text="✔ Binário (.huff) detectado para restauração.",
                font=("Segoe UI", 9),
                bg=COR_SIDEBAR,
                fg=COR_SUCESSO_CLARO
            ).pack(anchor="w", pady=(0, 10))

            btn_executar = tk.Button(
                self.container_acao,
                text="🔓 Descompactar Arquivo .HUFF",
                font=("Segoe UI", 11, "bold"),
                bg=COR_SUCESSO,
                fg="white",
                activebackground="#2ea043",
                activeforeground="white",
                bd=0,
                pady=12,
                cursor="hand2",
                command=self._executar_fluxo_descompactacao
            )
            btn_executar.pack(fill=tk.X)
            acao_desc = "descompactar e reconstruir o texto original"

        # Atualiza a tela principal mostrando que o programa aguarda o clique no botão
        for widget in self.conteudo.winfo_children():
            widget.destroy()

        tk.Label(
            self.conteudo,
            text=f"Arquivo pronto: {nome_arq} ({tamanho_kb:.2f} KB)",
            font=("Segoe UI", 22, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg="white"
        ).pack(pady=(90, 10))

        tk.Label(
            self.conteudo,
            text=f"⬅️ Clique no botão de ação que apareceu na barra lateral para {acao_desc}.",
            font=("Segoe UI", 12),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO_SEC,
            justify="center"
        ).pack()

    def _ocultar_botao_acao(self):
        # Remove o botão de ação após cumprir sua função
        for widget in self.container_acao.winfo_children():
            widget.destroy()

    # ==========================================================================
    # FLUXOS DE EXECUÇÃO E EMPILHAMENTO DOS BLOCOS (3/4 DA TELA)
    # ==========================================================================
    def _executar_fluxo_compactacao(self):
        saida_huff = os.path.splitext(self.caminho_atual)[0] + ".huff"
        try:
            self.modo_atual = "compactacao"

            # Compatível com qualquer assinatura do seu huffman_core.py
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

            # Faz o botão de compactar sumir imediatamente após cumprir a função
            self._ocultar_botao_acao()

            for widget in self.conteudo.winfo_children():
                widget.destroy()

            self.canvas_tela.yview_moveto(0)
            self._renderizar_bloco_titulo("Resultados da Compactação")
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

            # Faz o botão de descompactar sumir imediatamente após cumprir a função
            self._ocultar_botao_acao()

            for widget in self.conteudo.winfo_children():
                widget.destroy()

            self.canvas_tela.yview_moveto(0)
            self._renderizar_bloco_titulo("Resultados da Descompactação")
            self._renderizar_bloco_metricas_descompactacao()
            self._renderizar_bloco_hexdump(self.caminho_atual)
            self._renderizar_bloco_arvore()

        except Exception as e:
            messagebox.showerror("Erro na Descompactação", str(e))

    # ==========================================================================
    # CARTÕES VISUAIS EMPILHADOS (COM SLIDERS EMBUTIDOS NAS RESPECTIVAS SEÇÕES)
    # ==========================================================================
    def _mostrar_tela_boas_vindas(self):
        tk.Label(
            self.conteudo,
            text="Nenhum arquivo processado",
            font=("Segoe UI", 24, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg="white"
        ).pack(pady=(100, 10))

        tk.Label(
            self.conteudo,
            text="⬅️ Passo 1: Anexe um arquivo (.txt ou .huff) na barra lateral.\n"
                 "⬅️ Passo 2: Clique no botão de ação que surgirá após o reconhecimento automático.",
            font=("Segoe UI", 12),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO_SEC,
            justify="center"
        ).pack()

    def _renderizar_bloco_titulo(self, titulo):
        tk.Label(
            self.conteudo,
            text=titulo,
            font=("Segoe UI", 20, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg="white"
        ).pack(anchor="w", pady=(0, 20))

    # BLOCO 1A: MÉTRICAS, FÓRMULA E TABELA DA COMPACTAÇÃO
    def _renderizar_bloco_metricas_compactacao(self):
        r = self.ultimo_relatorio
        card = tk.Frame(
            self.conteudo,
            bg=COR_CARD,
            padx=22,
            pady=20,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        card.pack(fill=tk.X, pady=(0, 22))

        tk.Label(
            card,
            text="📊 Taxa de Compactação e Análise Matemática",
            font=("Segoe UI", 14, "bold"),
            bg=COR_CARD,
            fg=COR_PRIMARIA
        ).pack(anchor="w", pady=(0, 15))

        grid = tk.Frame(card, bg=COR_CARD)
        grid.pack(fill=tk.X, pady=(0, 16))

        metricas = [
            ("Tamanho Original", f"{r['bytes_originais']/1024:.2f} KB", f"{r['bits_originais']} bits (8 bits/char)"),
            ("Tamanho Final (.huff)", f"{r['bytes_arquivo_final']/1024:.2f} KB", f"{r['bits_compactados']} bits codificados"),
            ("Taxa de Compactação", f"{r['taxa_compactacao_pct']:.2f}%", "Redução real de bits"),
            ("Tempo de Execução", f"{r['tempo_s']:.4f} s", "Processamento total")
        ]

        for titulo, valor, sub in metricas:
            col = tk.Frame(grid, bg=COR_FUNDO_PRINCIPAL, padx=14, pady=12)
            col.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10))
            tk.Label(col, text=titulo, font=("Segoe UI", 9), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_SEC).pack(anchor="w")
            tk.Label(col, text=valor, font=("Segoe UI", 16, "bold"), bg=COR_FUNDO_PRINCIPAL, fg="white").pack(anchor="w", pady=(2, 2))
            tk.Label(col, text=sub, font=("Segoe UI", 8), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_SEC).pack(anchor="w")

        tk.Label(
            card,
            text="Fórmula Matemática e Tabela de Códigos Binários de Huffman:",
            font=("Segoe UI", 9, "bold"),
            bg=COR_CARD,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w", pady=(4, 6))

        txt_mat = tk.Text(
            card,
            height=9,
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO,
            font=("Consolas", 10),
            bd=1,
            relief="solid",
            padx=12,
            pady=10
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

    # BLOCO 1B: MÉTRICAS E TEXTO DA DESCOMPACTAÇÃO
    def _renderizar_bloco_metricas_descompactacao(self):
        r = self.ultimo_relatorio
        card = tk.Frame(
            self.conteudo,
            bg=COR_CARD,
            padx=22,
            pady=20,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        card.pack(fill=tk.X, pady=(0, 22))

        tk.Label(
            card,
            text="✅ Arquivo Restaurado com Sucesso",
            font=("Segoe UI", 14, "bold"),
            bg=COR_CARD,
            fg=COR_SUCESSO_CLARO
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(
            card,
            text=f"Foram restaurados {r['bytes_restaurado']} bytes de forma idêntica ao original em {r['tempo_s']:.4f} segundos.",
            font=("Segoe UI", 10),
            bg=COR_CARD,
            fg=COR_TEXTO
        ).pack(anchor="w", pady=(0, 14))

        tk.Label(
            card,
            text="Prévia do Texto Original Recuperado:",
            font=("Segoe UI", 9, "bold"),
            bg=COR_CARD,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w")

        txt = tk.Text(
            card,
            height=7,
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO,
            font=("Consolas", 10),
            bd=1,
            relief="solid",
            padx=12,
            pady=10
        )
        txt.pack(fill=tk.X, pady=(6, 0))
        txt.insert("1.0", r["texto_restaurado"][:1500])
        txt.config(state=tk.DISABLED)

    # BLOCO 2: HEXDUMP COM SLIDER DE BYTES EMBUTIDO NA PRÓPRIA SEÇÃO
    def _renderizar_bloco_hexdump(self, caminho_huff):
        card = tk.Frame(
            self.conteudo,
            bg=COR_CARD,
            padx=22,
            pady=20,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        card.pack(fill=tk.X, pady=(0, 22))

        topo_hex = tk.Frame(card, bg=COR_CARD)
        topo_hex.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            topo_hex,
            text="📄 Bytes Gravados no Arquivo (.huff) — Hexdump",
            font=("Segoe UI", 14, "bold"),
            bg=COR_CARD,
            fg=COR_PRIMARIA
        ).pack(side=tk.LEFT)

        painel_slider_hex = tk.Frame(
            topo_hex,
            bg=COR_FUNDO_PRINCIPAL,
            padx=12,
            pady=6,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        painel_slider_hex.pack(side=tk.RIGHT)

        self.lbl_valor_hexdump = tk.Label(
            painel_slider_hex,
            text=f"Bytes no hexdump: {self.var_bytes_hexdump.get()} B",
            font=("Segoe UI", 9, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO
        )
        self.lbl_valor_hexdump.pack(side=tk.LEFT, padx=(0, 10))

        slider_hex = tk.Scale(
            painel_slider_hex,
            from_=64,
            to=2048,
            resolution=64,
            orient=tk.HORIZONTAL,
            variable=self.var_bytes_hexdump,
            showvalue=False,
            length=180,
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_PRIMARIA,
            troughcolor=COR_CARD,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            command=lambda _: self._atualizar_hexdump_ao_vivo()
        )
        slider_hex.pack(side=tk.LEFT)

        self.txt_hexdump_tela = tk.Text(
            card,
            height=10,
            bg=COR_FUNDO_PRINCIPAL,
            fg="#79c0ff",
            font=("Consolas", 10),
            bd=1,
            relief="solid",
            padx=12,
            pady=10
        )
        self.txt_hexdump_tela.pack(fill=tk.X)
        self._atualizar_hexdump_ao_vivo(caminho_huff)

        if self.modo_atual == "compactacao" and "string_bits" in self.ultimo_relatorio:
            tk.Label(
                card,
                text="Amostra do fluxo contínuo de bits gerado pela árvore (0 e 1):",
                font=("Segoe UI", 9, "bold"),
                bg=COR_CARD,
                fg=COR_TEXTO_SEC
            ).pack(anchor="w", pady=(14, 5))

            txt_bits = tk.Text(
                card,
                height=4,
                bg=COR_FUNDO_PRINCIPAL,
                fg=COR_SUCESSO_CLARO,
                font=("Consolas", 10),
                bd=1,
                relief="solid",
                padx=12,
                pady=8
            )
            txt_bits.pack(fill=tk.X)
            txt_bits.insert("1.0", self.ultimo_relatorio["string_bits"][:1500])
            txt_bits.config(state=tk.DISABLED)

    # BLOCO 3: ÁRVORE DE HUFFMAN COM SLIDER DE FOLHAS EMBUTIDO NA PRÓPRIA SEÇÃO
    def _renderizar_bloco_arvore(self):
        card = tk.Frame(
            self.conteudo,
            bg=COR_CARD,
            padx=22,
            pady=20,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        card.pack(fill=tk.X, pady=(0, 22))

        topo_arvore = tk.Frame(card, bg=COR_CARD)
        topo_arvore.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            topo_arvore,
            text="🌳 Estrutura da Árvore de Huffman",
            font=("Segoe UI", 14, "bold"),
            bg=COR_CARD,
            fg=COR_PRIMARIA
        ).pack(side=tk.LEFT)

        painel_slider_folhas = tk.Frame(
            topo_arvore,
            bg=COR_FUNDO_PRINCIPAL,
            padx=12,
            pady=6,
            highlightbackground=COR_BORDA,
            highlightthickness=1
        )
        painel_slider_folhas.pack(side=tk.RIGHT)

        self.lbl_valor_folhas = tk.Label(
            painel_slider_folhas,
            text=f"Folhas exibidas na árvore: {self.var_max_folhas.get()}",
            font=("Segoe UI", 9, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO
        )
        self.lbl_valor_folhas.pack(side=tk.LEFT, padx=(0, 10))

        slider_folhas = tk.Scale(
            painel_slider_folhas,
            from_=5,
            to=80,
            orient=tk.HORIZONTAL,
            variable=self.var_max_folhas,
            showvalue=False,
            length=180,
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_PRIMARIA,
            troughcolor=COR_CARD,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            command=lambda _: self._atualizar_arvore_ao_vivo()
        )
        slider_folhas.pack(side=tk.LEFT)

        tk.Label(
            card,
            text="Arestas à esquerda (azul) = bit 0  |  Arestas à direita (laranja) = bit 1. Deslize o controle acima para ajustar a visualização.",
            font=("Segoe UI", 9),
            bg=COR_CARD,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w", pady=(0, 10))

        frame_canvas = tk.Frame(
            card,
            bg=COR_FUNDO_PRINCIPAL,
            highlightbackground=COR_BORDA,
            highlightthickness=1,
            height=450
        )
        frame_canvas.pack(fill=tk.X)
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

    # ==========================================================================
    # ATUALIZAÇÕES EM TEMPO REAL DOS SLIDERS EMBUTIDOS
    # ==========================================================================
    def _atualizar_hexdump_ao_vivo(self, caminho=None):
        if not hasattr(self, "txt_hexdump_tela") or not self.txt_hexdump_tela.winfo_exists():
            return

        caminho_alvo = caminho or getattr(self, "caminho_huff_gerado", None)
        if not caminho_alvo or not os.path.exists(caminho_alvo):
            return

        limite = self.var_bytes_hexdump.get()
        if hasattr(self, "lbl_valor_hexdump") and self.lbl_valor_hexdump.winfo_exists():
            self.lbl_valor_hexdump.config(text=f"Bytes no hexdump: {limite} B")

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
        if hasattr(self, "lbl_valor_folhas") and self.lbl_valor_folhas.winfo_exists():
            self.lbl_valor_folhas.config(text=f"Folhas exibidas na árvore: {limite_folhas}")

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
                self.canvas_arvore.create_line(x1, y1, x2, y2, fill="#58a6ff", width=2)
                self.canvas_arvore.create_text(
                    (x1 + x2) / 2 - 10, (y1 + y2) / 2,
                    text="0", fill="#58a6ff", font=("Segoe UI", 9, "bold")
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
            bg = "#1f6feb" if eh_folha else "#21262d"
            outline = "#58a6ff" if eh_folha else "#8b949e"
            self.canvas_arvore.create_oval(
                x - r, y - r, x + r, y + r, fill=bg, outline=outline, width=2
            )
            txt = f"{repr(no.caractere)}\n({no.frequencia})" if eh_folha else f"{no.frequencia}"
            self.canvas_arvore.create_text(
                x, y, text=txt, fill="white", font=("Segoe UI", 8, "bold")
            )

        self.canvas_arvore.configure(scrollregion=self.canvas_arvore.bbox("all"))


if __name__ == "__main__":
    raiz_tk = tk.Tk()
    app = InterfaceHuffman(raiz_tk)
    raiz_tk.mainloop()