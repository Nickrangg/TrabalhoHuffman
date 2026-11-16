import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from huffman_core import CompactadorHuffman


# PALETA DE CORES BASE DO PROJETO
COR_FUNDO_PRINCIPAL = "#0e1117"   # Fundo escuro principal
COR_SIDEBAR = "#1d2327"           # Fundo da barra lateral
COR_CARD = "#161b22"              # Fundo dos cartões/widgets
COR_BORDA_CARD = "#30363d"        # Borda sutil estilo container de Widget
COR_PRIMARIA = "#ff4b4b"          # Vermelho/Coral de ação principal e sliders
COR_DESTAQUE_MENU = "#2271b1"     # Azul de destaque de seleção
COR_SUCESSO_BG = "#133223"        # Fundo verde escuro dos alertas
COR_SUCESSO_TXT = "#3fb950"       # Texto verde claro dos alertas
COR_TEXTO = "#f0f6fc"             # Texto principal claro
COR_TEXTO_SEC = "#8b949e"         # Texto secundário/legendas


class InterfaceHuffman:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("Compactador de Huffman - Teoria dos Grafos")
        self.janela.geometry("1280x780")
        self.janela.configure(bg=COR_FUNDO_PRINCIPAL)

        self.compactador = CompactadorHuffman()

        # Opções separadas de pré-compressão (LZSS e LZ77)
        self.var_usar_lzss = tk.BooleanVar(value=True)
        self.var_usar_lz77 = tk.BooleanVar(value=False)

        # Controles de visualização (Folhas padrão: 14 | Hexdump padrão: 704)
        self.var_max_folhas = tk.IntVar(value=14)
        self.var_bytes_hexdump = tk.IntVar(value=704)

        self.caminho_txt_atual = None
        self.caminho_huff_atual = None
        self.ultimo_relatorio_comp = None
        self.ultimo_relatorio_descomp = None
        self.botoes_abas = {}

        self._construir_estrutura_base()
        self.selecionar_aba("compactar")

    def _construir_estrutura_base(self):
        # 1. BARRA LATERAL ESQUERDA (SIDEBAR)
        self.sidebar = tk.Frame(self.janela, bg=COR_SIDEBAR, width=260)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self._popular_sidebar()

        # 2. ÁREA DE CONTEÚDO PRINCIPAL (DIREITA)
        self.area_principal = tk.Frame(self.janela, bg=COR_FUNDO_PRINCIPAL)
        self.area_principal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=35, pady=25)

        # Título Principal
        tk.Label(
            self.area_principal,
            text="Compactador de Huffman",
            font=("Segoe UI", 22, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO
        ).pack(anchor="w", pady=(0, 12))

        # Barra Horizontal de Abas (4 Abas)
        self.barra_abas = tk.Frame(self.area_principal, bg=COR_FUNDO_PRINCIPAL)
        self.barra_abas.pack(fill=tk.X, pady=(0, 2))

        abas_info = [
            ("compactar", "📦 Compactar"),
            ("descompactar", "📂 Descompactar"),
            ("arquivo", "📄 Arquivo compactado"),
            ("arvore", "🌳 Árvore de Huffman"),
        ]

        for chave, rotulo in abas_info:
            btn = tk.Button(
                self.barra_abas,
                text=rotulo,
                font=("Segoe UI", 9, "bold"),
                bg=COR_FUNDO_PRINCIPAL,
                fg=COR_TEXTO_SEC,
                activebackground=COR_CARD,
                activeforeground=COR_TEXTO,
                bd=0,
                padx=12,
                pady=8,
                cursor="hand2",
                command=lambda k=chave: self.selecionar_aba(k)
            )
            btn.pack(side=tk.LEFT, padx=(0, 6))
            self.botoes_abas[chave] = btn

        # Linha divisória abaixo das abas
        tk.Frame(self.area_principal, bg=COR_BORDA_CARD, height=1).pack(fill=tk.X, pady=(0, 18))

        # Container Dinâmico onde cada aba é renderizada
        self.container_aba = tk.Frame(self.area_principal, bg=COR_FUNDO_PRINCIPAL)
        self.container_aba.pack(fill=tk.BOTH, expand=True)

    def _popular_sidebar(self):
        # Cabeçalho da Sidebar
        tk.Label(
            self.sidebar,
            text="🗜️ Huffman",
            font=("Segoe UI", 15, "bold"),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO
        ).pack(anchor="w", padx=18, pady=(22, 4))

        tk.Label(
            self.sidebar,
            text="Compactador de texto com Huffman\n+ pré-compressão LZSS e LZ77",
            font=("Segoe UI", 8),
            justify="left",
            bg=COR_SIDEBAR,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w", padx=18, pady=(0, 18))

        tk.Frame(self.sidebar, bg=COR_BORDA_CARD, height=1).pack(fill=tk.X, padx=15, pady=5)

        # Seção: Opções de Pré-compressão (Separadas)
        tk.Label(
            self.sidebar,
            text="Opções de Pré-compressão",
            font=("Segoe UI", 10, "bold"),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO
        ).pack(anchor="w", padx=18, pady=(12, 8))

        chk_lzss = tk.Checkbutton(
            self.sidebar,
            text="Habilitar pré-compressão (LZSS)",
            variable=self.var_usar_lzss,
            font=("Segoe UI", 9),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO,
            selectcolor=COR_FUNDO_PRINCIPAL,
            activebackground=COR_SIDEBAR,
            activeforeground=COR_TEXTO,
            cursor="hand2"
        )
        chk_lzss.pack(anchor="w", padx=14, pady=(0, 6))

        chk_lz77 = tk.Checkbutton(
            self.sidebar,
            text="Habilitar pré-compressão (LZ77 / llz7)",
            variable=self.var_usar_lz77,
            font=("Segoe UI", 9),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO,
            selectcolor=COR_FUNDO_PRINCIPAL,
            activebackground=COR_SIDEBAR,
            activeforeground=COR_TEXTO,
            cursor="hand2"
        )
        chk_lz77.pack(anchor="w", padx=14, pady=(0, 14))

        tk.Frame(self.sidebar, bg=COR_BORDA_CARD, height=1).pack(fill=tk.X, padx=15, pady=8)

        # Seção: Estado (Cards de Status)
        tk.Label(
            self.sidebar,
            text="Estado",
            font=("Segoe UI", 10, "bold"),
            bg=COR_SIDEBAR,
            fg=COR_TEXTO
        ).pack(anchor="w", padx=18, pady=(8, 8))

        self.lbl_estado_txt = tk.Label(
            self.sidebar,
            text="📄 Nenhum .txt carregado",
            font=("Segoe UI", 8),
            bg=COR_CARD,
            fg=COR_TEXTO,
            anchor="w",
            padx=10,
            pady=8
        )
        self.lbl_estado_txt.pack(fill=tk.X, padx=16, pady=4)

        self.lbl_estado_huff = tk.Label(
            self.sidebar,
            text="🗜️ Nenhum .huff gerado",
            font=("Segoe UI", 8),
            bg=COR_CARD,
            fg=COR_TEXTO_SEC,
            anchor="w",
            padx=10,
            pady=8
        )
        self.lbl_estado_huff.pack(fill=tk.X, padx=16, pady=4)

        # Card "Como usar" no rodapé da Sidebar
        card_ajuda = tk.Frame(
            self.sidebar, bg=COR_CARD, highlightbackground=COR_BORDA_CARD, highlightthickness=1
        )
        card_ajuda.pack(fill=tk.X, padx=16, pady=15)
        tk.Label(
            card_ajuda,
            text=(
                "▸ Como usar:\n"
                "1. Escolha LZSS e/ou LZ77 acima.\n"
                "2. Compacte um .txt e veja a Taxa.\n"
                "3. Ajuste os bytes no Arquivo compactado\n"
                "   e as folhas na Árvore de Huffman."
            ),
            font=("Segoe UI", 8),
            justify="left",
            bg=COR_CARD,
            fg=COR_TEXTO_SEC,
            padx=8,
            pady=8
        ).pack(anchor="w")

    def _obter_rotulo_pre_compressao(self, usar_lzss, usar_lz77):
        ativos = []
        if usar_lzss:
            ativos.append("LZSS")
        if usar_lz77:
            ativos.append("LZ77")
        return " + ".join(ativos) if ativos else "Nenhuma (Huffman puro)"

    # UTILITÁRIO: CRIA UM CONTAINER DE WIDGET ESTILIZADO
    def _criar_widget_card(self, pai, titulo):
        outer = tk.Frame(
            pai,
            bg=COR_CARD,
            highlightbackground=COR_BORDA_CARD,
            highlightthickness=1,
            padx=14,
            pady=10
        )
        outer.pack(fill=tk.X, pady=5)

        header = tk.Frame(outer, bg=COR_CARD)
        header.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            header,
            text=f"▾  {titulo}",
            font=("Segoe UI", 9, "bold"),
            bg=COR_CARD,
            fg=COR_TEXTO
        ).pack(side=tk.LEFT)

        corpo = tk.Frame(outer, bg=COR_CARD)
        corpo.pack(fill=tk.X, expand=True)
        return corpo

    def _criar_banner_sucesso(self, pai, texto):
        banner = tk.Frame(
            pai,
            bg=COR_SUCESSO_BG,
            highlightbackground=COR_SUCESSO_TXT,
            highlightthickness=1,
            padx=14,
            pady=8
        )
        banner.pack(fill=tk.X, pady=6)
        tk.Label(
            banner,
            text=texto,
            font=("Segoe UI", 9, "bold"),
            bg=COR_SUCESSO_BG,
            fg=COR_SUCESSO_TXT
        ).pack(anchor="w")

    def _criar_linha_metricas(self, pai, lista_metricas):
        frame_m = tk.Frame(pai, bg=COR_FUNDO_PRINCIPAL)
        frame_m.pack(fill=tk.X, pady=8)

        for rotulo, valor in lista_metricas:
            col = tk.Frame(frame_m, bg=COR_FUNDO_PRINCIPAL)
            col.pack(side=tk.LEFT, expand=True, fill=tk.X)
            tk.Label(
                col, text=rotulo, font=("Segoe UI", 8), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO_SEC
            ).pack(anchor="w")
            tk.Label(
                col, text=valor, font=("Segoe UI", 16, "bold"), bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO
            ).pack(anchor="w", pady=(2, 0))

    def selecionar_aba(self, chave):
        self.aba_atual = chave
        for k, btn in self.botoes_abas.items():
            if k == chave:
                btn.config(fg=COR_PRIMARIA, bg=COR_CARD)
            else:
                btn.config(fg=COR_TEXTO_SEC, bg=COR_FUNDO_PRINCIPAL)

        for widget in self.container_aba.winfo_children():
            widget.destroy()

        if chave == "compactar":
            self._render_aba_compactar()
        elif chave == "descompactar":
            self._render_aba_descompactar()
        elif chave == "arquivo":
            self._render_aba_arquivo()
        elif chave == "arvore":
            self._render_aba_arvore()

    # ==========================================
    # ABA 1: COMPACTAR + TAXA DE COMPACTAÇÃO CENTRALIZADA
    # ==========================================
    def _render_aba_compactar(self):
        tk.Label(
            self.container_aba,
            text="Compactar arquivo de texto (.txt)",
            font=("Segoe UI", 14, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO
        ).pack(anchor="w", pady=(0, 8))

        card_upload = self._criar_widget_card(self.container_aba, "Selecionar arquivo de entrada (.txt)")

        linha_up = tk.Frame(card_upload, bg=COR_CARD)
        linha_up.pack(fill=tk.X, pady=2)

        btn_escolher = tk.Button(
            linha_up,
            text="⬆️  Upload .TXT",
            font=("Segoe UI", 9, "bold"),
            bg=COR_DESTAQUE_MENU,
            fg=COR_TEXTO,
            bd=0,
            padx=14,
            pady=6,
            cursor="hand2",
            command=self._escolher_arquivo_txt
        )
        btn_escolher.pack(side=tk.LEFT, padx=(0, 12))

        nome_arq = (
            os.path.basename(self.caminho_txt_atual)
            if self.caminho_txt_atual
            else "Nenhum arquivo selecionado (ex: teste.txt)"
        )
        tk.Label(
            linha_up,
            text=nome_arq,
            font=("Segoe UI", 9),
            bg=COR_CARD,
            fg=COR_TEXTO_SEC
        ).pack(side=tk.LEFT)

        # Botão Principal Largo
        tk.Button(
            self.container_aba,
            text="🗜️  Compactar agora",
            font=("Segoe UI", 10, "bold"),
            bg=COR_PRIMARIA,
            fg=COR_TEXTO,
            activebackground="#d93838",
            activeforeground=COR_TEXTO,
            bd=0,
            pady=9,
            cursor="hand2",
            command=self._executar_compactacao
        ).pack(fill=tk.X, pady=8)

        # Resultado e Matemática da Taxa de Compactação logo abaixo do botão
        if self.ultimo_relatorio_comp:
            r = self.ultimo_relatorio_comp
            self._criar_banner_sucesso(
                self.container_aba,
                f"Compactado com sucesso em {r['tempo_s']:.4f} s."
            )

            kb_orig = r["bytes_originais"] / 1024
            kb_comp = r["bytes_arquivo_final"] / 1024
            rotulo_lz = self._obter_rotulo_pre_compressao(r["usar_lzss"], r["usar_lz77"])

            self._criar_linha_metricas(self.container_aba, [
                ("Bits Originais (8 bits/char)", f"{r['bits_originais']} bits ({kb_orig:.2f} KB)"),
                ("Bits Finais (Huffman)", f"{r['bits_compactados']} bits ({kb_comp:.2f} KB)"),
                ("Taxa de Compactação (Bits)", f"{r['taxa_compactacao_pct']:.2f}%"),
                ("Pré-compressão Ativa", rotulo_lz)
            ])

            card_taxa = self._criar_widget_card(
                self.container_aba,
                "Detalhamento Matemático da Taxa de Compactação e Tabela de Códigos"
            )

            frame_txt = tk.Frame(card_taxa, bg=COR_FUNDO_PRINCIPAL)
            frame_txt.pack(fill=tk.BOTH, expand=True)

            scroll_taxa = ttk.Scrollbar(frame_txt, orient=tk.VERTICAL)
            txt_mat = tk.Text(
                frame_txt,
                height=11,
                bg=COR_FUNDO_PRINCIPAL,
                fg=COR_TEXTO,
                font=("Consolas", 9),
                bd=0,
                yscrollcommand=scroll_taxa.set
            )
            scroll_taxa.config(command=txt_mat.yview)
            scroll_taxa.pack(side=tk.RIGHT, fill=tk.Y)
            txt_mat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            explicacao = (
                f"FÓRMULA MATEMÁTICA DA TAXA DE COMPACTAÇÃO:\n"
                f"  Taxa (%) = (1 - (Bits_Compactados / Bits_Originais)) * 100\n"
                f"  Taxa (%) = (1 - ({r['bits_compactados']} / {r['bits_originais']})) * 100 = {r['taxa_compactacao_pct']:.2f}% de redução de bits\n"
                f"  Tamanho em Disco: {r['bytes_originais']} bytes (original) -> {r['bytes_arquivo_final']} bytes (.huff c/ cabeçalho)\n\n"
                f"{'Símbolo':<15} | {'Frequência':<12} | {'Bits':<6} | {'Código Binário de Huffman'}\n"
                + "-" * 65 + "\n"
            )
            txt_mat.insert(tk.END, explicacao)

            ordenados = sorted(self.compactador.frequencias.items(), key=lambda x: x[1], reverse=True)
            for char, freq in ordenados[:40]:
                cod = self.compactador.tabela_codigos[char]
                txt_mat.insert(tk.END, f"{repr(char):<15} | {freq:<12} | {len(cod):<6} | {cod}\n")

            txt_mat.config(state=tk.DISABLED)

    def _escolher_arquivo_txt(self):
        caminho = filedialog.askopenfilename(
            title="Selecione um arquivo .txt",
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
        )
        if caminho:
            self.caminho_txt_atual = caminho
            tam_kb = os.path.getsize(caminho) / 1024
            self.lbl_estado_txt.config(text=f"📄 {os.path.basename(caminho)} - {tam_kb:.2f} KB")
            self.selecionar_aba("compactar")

    def _executar_compactacao(self):
        if not self.caminho_txt_atual:
            if os.path.exists("teste.txt"):
                self.caminho_txt_atual = os.path.abspath("teste.txt")
            else:
                self._escolher_arquivo_txt()
                if not self.caminho_txt_atual:
                    return

        saida = os.path.splitext(self.caminho_txt_atual)[0] + ".huff"
        try:
            relatorio = self.compactador.compactar_arquivo(
                self.caminho_txt_atual,
                saida,
                usar_lzss=self.var_usar_lzss.get(),
                usar_lz77=self.var_usar_lz77.get()
            )
            self.caminho_huff_atual = saida
            self.ultimo_relatorio_comp = relatorio

            kb_orig = relatorio["bytes_originais"] / 1024
            kb_comp = relatorio["bytes_arquivo_final"] / 1024
            rotulo_lz = self._obter_rotulo_pre_compressao(
                relatorio["usar_lzss"], relatorio["usar_lz77"]
            )
            self.lbl_estado_txt.config(
                text=f"📄 {os.path.basename(self.caminho_txt_atual)} - {kb_orig:.2f} KB"
            )
            self.lbl_estado_huff.config(
                text=f"🗜️ {kb_comp:.2f} KB ({rotulo_lz})", fg=COR_SUCESSO_TXT
            )
            self.selecionar_aba("compactar")
        except Exception as e:
            messagebox.showerror("Erro na Compactação", str(e))

    # ==========================================
    # ABA 2: DESCOMPACTAR
    # ==========================================
    def _render_aba_descompactar(self):
        tk.Label(
            self.container_aba,
            text="Restaurar o texto original",
            font=("Segoe UI", 14, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO
        ).pack(anchor="w", pady=(0, 8))

        nome_huff = (
            f"Usando {os.path.basename(self.caminho_huff_atual)} ({os.path.getsize(self.caminho_huff_atual)/1024:.2f} KB)."
            if self.caminho_huff_atual and os.path.exists(self.caminho_huff_atual)
            else "Nenhum arquivo .huff selecionado ainda."
        )
        tk.Label(
            self.container_aba,
            text=nome_huff,
            font=("Segoe UI", 9),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w", pady=(0, 8))

        card_conf = self._criar_widget_card(
            self.container_aba, "Selecionar arquivo .huff ou conferir com o .txt original"
        )
        tk.Label(
            card_conf,
            text="Se você compactou nesta sessão, a conferência byte a byte é automática.",
            font=("Segoe UI", 8),
            bg=COR_CARD,
            fg=COR_TEXTO_SEC
        ).pack(anchor="w", pady=(0, 8))

        btn_escolher_huff = tk.Button(
            card_conf,
            text="⬆️  Escolher outro arquivo .HUFF",
            font=("Segoe UI", 9, "bold"),
            bg=COR_BORDA_CARD,
            fg=COR_TEXTO,
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._escolher_arquivo_huff
        )
        btn_escolher_huff.pack(anchor="w")

        tk.Button(
            self.container_aba,
            text="📂  Descompactar",
            font=("Segoe UI", 10, "bold"),
            bg=COR_PRIMARIA,
            fg=COR_TEXTO,
            activebackground="#d93838",
            activeforeground=COR_TEXTO,
            bd=0,
            pady=10,
            cursor="hand2",
            command=self._executar_descompactacao
        ).pack(fill=tk.X, pady=12)

        if self.ultimo_relatorio_descomp:
            rd = self.ultimo_relatorio_descomp
            self._criar_banner_sucesso(
                self.container_aba,
                f"Descompactado em {rd['tempo_s']:.4f} s."
            )

            kb_c = rd["bytes_compactado"] / 1024
            kb_r = rd["bytes_restaurado"] / 1024
            rotulo_lz = self._obter_rotulo_pre_compressao(rd["usou_lzss"], rd["usou_lz77"])

            self._criar_linha_metricas(self.container_aba, [
                ("Compactado", f"{kb_c:.2f} KB"),
                ("Restaurado", f"{kb_r:.2f} KB"),
                ("Pré-compressão no arquivo", rotulo_lz)
            ])

            if self.ultimo_relatorio_comp and rd["texto_restaurado"] == self.ultimo_relatorio_comp["texto_original"]:
                self._criar_banner_sucesso(
                    self.container_aba,
                    "✅ O texto restaurado é idêntico ao original, byte a byte."
                )

            card_rest = self._criar_widget_card(self.container_aba, "Texto restaurado")
            txt_rest = tk.Text(
                card_rest, height=8, bg=COR_FUNDO_PRINCIPAL, fg=COR_TEXTO, font=("Consolas", 9), bd=0
            )
            txt_rest.pack(fill=tk.BOTH, expand=True)
            txt_rest.insert("1.0", rd["texto_restaurado"][:2000])
            txt_rest.config(state=tk.DISABLED)

    def _escolher_arquivo_huff(self):
        caminho = filedialog.askopenfilename(
            title="Selecione o arquivo .huff",
            filetypes=[("Arquivo Huffman", "*.huff"), ("Todos os Arquivos", "*.*")]
        )
        if caminho:
            self.caminho_huff_atual = caminho
            self.selecionar_aba("descompactar")

    def _executar_descompactacao(self):
        if not self.caminho_huff_atual or not os.path.exists(self.caminho_huff_atual):
            self._escolher_arquivo_huff()
            if not self.caminho_huff_atual:
                return

        saida_txt = os.path.splitext(self.caminho_huff_atual)[0] + "_restaurado.txt"
        try:
            self.ultimo_relatorio_descomp = self.compactador.descompactar_arquivo(
                self.caminho_huff_atual, saida_txt
            )
            self.selecionar_aba("descompactar")
        except Exception as e:
            messagebox.showerror("Erro ao Descompactar", str(e))

    # ==========================================
    # ABA 3: ARQUIVO COMPACTADO + SLIDER DE BYTES NO HEXDUMP EMBUTIDO
    # ==========================================
    def _render_aba_arquivo(self):
        tk.Label(
            self.container_aba,
            text="Inspeção do Arquivo Compactado (.huff)",
            font=("Segoe UI", 14, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO
        ).pack(anchor="w", pady=(0, 8))

        if not self.caminho_huff_atual or not os.path.exists(self.caminho_huff_atual):
            tk.Label(
                self.container_aba,
                text="Compacte um arquivo primeiro para inspecionar os bits e o Hexdump.",
                font=("Segoe UI", 10),
                bg=COR_FUNDO_PRINCIPAL,
                fg=COR_TEXTO_SEC
            ).pack(anchor="w")
            return

        # Controle deslizante de Bytes no Hexdump dentro da própria seção
        card_ajuste_hex = self._criar_widget_card(
            self.container_aba, "Ajuste de Bytes no Hexdump"
        )
        linha_slider_hex = tk.Frame(card_ajuste_hex, bg=COR_CARD)
        linha_slider_hex.pack(fill=tk.X)

        tk.Label(
            linha_slider_hex,
            text="Bytes exibidos no hexdump:",
            font=("Segoe UI", 9),
            bg=COR_CARD,
            fg=COR_TEXTO_SEC
        ).pack(side=tk.LEFT, padx=(0, 12))

        scale_hex = tk.Scale(
            linha_slider_hex,
            from_=64,
            to=2048,
            resolution=64,
            orient=tk.HORIZONTAL,
            variable=self.var_bytes_hexdump,
            bg=COR_CARD,
            fg=COR_PRIMARIA,
            troughcolor=COR_FUNDO_PRINCIPAL,
            highlightthickness=0,
            bd=0,
            command=lambda _: self._atualizar_conteudo_hexdump()
        )
        scale_hex.pack(side=tk.LEFT, fill=tk.X, expand=True)

        card_hex = self._criar_widget_card(
            self.container_aba, "Hexdump dos bytes gravados em disco"
        )
        self.txt_hex_aba = tk.Text(
            card_hex, height=10, bg=COR_FUNDO_PRINCIPAL, fg="#79c0ff", font=("Consolas", 9), bd=0
        )
        self.txt_hex_aba.pack(fill=tk.BOTH, expand=True)
        self._atualizar_conteudo_hexdump()

        if self.ultimo_relatorio_comp:
            card_bits = self._criar_widget_card(
                self.container_aba, "Fluxo de Bits Gerados pela Árvore (0 e 1)"
            )
            txt_bits = tk.Text(
                card_bits, height=5, bg=COR_FUNDO_PRINCIPAL, fg=COR_SUCESSO_TXT, font=("Consolas", 9), bd=0
            )
            txt_bits.pack(fill=tk.BOTH, expand=True)
            txt_bits.insert("1.0", self.ultimo_relatorio_comp["string_bits"][:1200] + "...")
            txt_bits.config(state=tk.DISABLED)

    def _atualizar_conteudo_hexdump(self):
        if not hasattr(self, "txt_hex_aba") or not self.txt_hex_aba.winfo_exists():
            return
        if not self.caminho_huff_atual or not os.path.exists(self.caminho_huff_atual):
            return

        limite_bytes = self.var_bytes_hexdump.get()
        with open(self.caminho_huff_atual, "rb") as f:
            dados = f.read(limite_bytes)

        linhas_hex = []
        for i in range(0, len(dados), 16):
            bloco = dados[i:i + 16]
            hex_str = " ".join(f"{b:02X}" for b in bloco)
            ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in bloco)
            linhas_hex.append(f"{i:04X}  |  {hex_str:<47}  |  {ascii_str}")

        self.txt_hex_aba.config(state=tk.NORMAL)
        self.txt_hex_aba.delete("1.0", tk.END)
        self.txt_hex_aba.insert("1.0", "\n".join(linhas_hex))
        self.txt_hex_aba.config(state=tk.DISABLED)

    # ==========================================
    # ABA 4: ÁRVORE DE HUFFMAN + SLIDER DE FOLHAS EXIBIDAS EMBUTIDO
    # ==========================================
    def _render_aba_arvore(self):
        tk.Label(
            self.container_aba,
            text="Árvore de Huffman Montada",
            font=("Segoe UI", 14, "bold"),
            bg=COR_FUNDO_PRINCIPAL,
            fg=COR_TEXTO
        ).pack(anchor="w", pady=(0, 8))

        if not self.compactador.raiz:
            tk.Label(
                self.container_aba,
                text="Compacte um arquivo na aba 1 para visualizar a Árvore de Huffman.",
                font=("Segoe UI", 10),
                bg=COR_FUNDO_PRINCIPAL,
                fg=COR_TEXTO_SEC
            ).pack(anchor="w", pady=10)
            return

        # Controle deslizante de Folhas Exibidas dentro da própria seção da Árvore
        card_ajuste_folhas = self._criar_widget_card(
            self.container_aba, "Ajuste de Folhas Exibidas na Árvore"
        )
        linha_slider_folhas = tk.Frame(card_ajuste_folhas, bg=COR_CARD)
        linha_slider_folhas.pack(fill=tk.X)

        self.lbl_info_folhas = tk.Label(
            linha_slider_folhas,
            text=f"Folhas exibidas na árvore ({self.var_max_folhas.get()}):",
            font=("Segoe UI", 9),
            bg=COR_CARD,
            fg=COR_TEXTO_SEC
        )
        self.lbl_info_folhas.pack(side=tk.LEFT, padx=(0, 12))

        scale_folhas = tk.Scale(
            linha_slider_folhas,
            from_=5,
            to=80,
            orient=tk.HORIZONTAL,
            variable=self.var_max_folhas,
            bg=COR_CARD,
            fg=COR_PRIMARIA,
            troughcolor=COR_FUNDO_PRINCIPAL,
            highlightthickness=0,
            bd=0,
            command=lambda _: self._atualizar_desenho_arvore()
        )
        scale_folhas.pack(side=tk.LEFT, fill=tk.X, expand=True)

        frame_canvas = tk.Frame(
            self.container_aba, bg=COR_CARD, highlightbackground=COR_BORDA_CARD, highlightthickness=1
        )
        frame_canvas.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        sx = ttk.Scrollbar(frame_canvas, orient=tk.HORIZONTAL)
        sy = ttk.Scrollbar(frame_canvas, orient=tk.VERTICAL)
        self.canvas_arvore_aba = tk.Canvas(
            frame_canvas, bg=COR_CARD, highlightthickness=0, xscrollcommand=sx.set, yscrollcommand=sy.set
        )
        sx.config(command=self.canvas_arvore_aba.xview)
        sy.config(command=self.canvas_arvore_aba.yview)
        sx.pack(side=tk.BOTTOM, fill=tk.X)
        sy.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_arvore_aba.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._atualizar_desenho_arvore()

    def _atualizar_desenho_arvore(self):
        if not hasattr(self, "canvas_arvore_aba") or not self.canvas_arvore_aba.winfo_exists():
            return
        limite = self.var_max_folhas.get()
        if hasattr(self, "lbl_info_folhas") and self.lbl_info_folhas.winfo_exists():
            self.lbl_info_folhas.config(text=f"Folhas exibidas na árvore ({limite}):")

        self.canvas_arvore_aba.delete("all")
        self._desenhar_grafo_arvore(self.canvas_arvore_aba, self.compactador.raiz, limite)

    def _desenhar_grafo_arvore(self, canvas, raiz, limite_folhas):
        posicoes = {}
        folhas_contadas = [0]
        esp_x, esp_y = 75, 82

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
            filhos_visiveis = [
                posicoes[f][0] for f in (no.esquerda, no.direita) if f in posicoes
            ]
            if not filhos_visiveis:
                return False
            posicoes[no] = (sum(filhos_visiveis) / len(filhos_visiveis), 50 + prof * esp_y)
            return True

        calc_coords(raiz, 0)

        for no, (x1, y1) in posicoes.items():
            if no.esquerda in posicoes:
                x2, y2 = posicoes[no.esquerda]
                canvas.create_line(x1, y1, x2, y2, fill="#58a6ff", width=2)
                canvas.create_text(
                    (x1 + x2) / 2 - 8, (y1 + y2) / 2,
                    text="0", fill="#58a6ff", font=("Segoe UI", 9, "bold")
                )
            if no.direita in posicoes:
                x2, y2 = posicoes[no.direita]
                canvas.create_line(x1, y1, x2, y2, fill=COR_PRIMARIA, width=2)
                canvas.create_text(
                    (x1 + x2) / 2 + 8, (y1 + y2) / 2,
                    text="1", fill=COR_PRIMARIA, font=("Segoe UI", 9, "bold")
                )

        for no, (x, y) in posicoes.items():
            r = 23
            eh_folha = no.caractere is not None
            cor_bg = "#1f6feb" if eh_folha else "#21262d"
            cor_borda = "#58a6ff" if eh_folha else "#8b949e"
            canvas.create_oval(x - r, y - r, x + r, y + r, fill=cor_bg, outline=cor_borda, width=2)
            rotulo = f"{repr(no.caractere)}\n({no.frequencia})" if eh_folha else f"{no.frequencia}"
            canvas.create_text(x, y, text=rotulo, fill=COR_TEXTO, font=("Segoe UI", 8, "bold"))

        canvas.configure(scrollregion=canvas.bbox("all"))


if __name__ == "__main__":
    raiz_tk = tk.Tk()
    app = InterfaceHuffman(raiz_tk)
    raiz_tk.mainloop()