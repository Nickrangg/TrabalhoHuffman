import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from huffman_core import CompactadorHuffman


class InterfaceHuffman:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("Compactador de Huffman - Teoria dos Grafos")
        self.janela.geometry("1050x700")
        self.compactador = CompactadorHuffman()

        self._construir_layout()

    def _construir_layout(self):
        # Painel Superior: Botões de Ação
        frame_topo = ttk.Frame(self.janela, padding=10)
        frame_topo.pack(fill=tk.X)

        btn_compactar = ttk.Button(
            frame_topo,
            text="1. Selecionar .TXT e Compactar",
            command=self.acao_compactar
        )
        btn_compactar.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=5)

        btn_descompactar = ttk.Button(
            frame_topo,
            text="2. Selecionar .HUFF e Descompactar",
            command=self.acao_descompactar
        )
        btn_descompactar.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=5)

        # Painel de Métricas e Taxa de Compactação
        self.lbl_metricas = ttk.Label(
            frame_topo,
            text="Aguardando seleção de arquivo...",
            font=("Segoe UI", 10, "bold")
        )
        self.lbl_metricas.pack(side=tk.LEFT, padx=20)

        # Painel Central com Abas (Notebook)
        self.abas = ttk.Notebook(self.janela)
        self.abas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Aba 1: Desenho Gráfico da Árvore (Canvas com Barras de Rolagem)
        self.aba_canvas = ttk.Frame(self.abas)
        self.abas.add(self.aba_canvas, text="Árvore de Huffman (Visual Gráfico)")
        self._configurar_canvas_arvore()

        # Aba 2: Tabela de Códigos e Árvore em Texto
        self.aba_tabela = ttk.Frame(self.abas)
        self.abas.add(self.aba_tabela, text="Tabela de Códigos e Árvore em Texto")
        self.txt_tabela = scrolledtext.ScrolledText(
            self.aba_tabela, font=("Consolas", 10)
        )
        self.txt_tabela.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Aba 3: Visualização do Arquivo Compactado e Texto Recuperado
        self.aba_arquivos = ttk.Frame(self.abas)
        self.abas.add(self.aba_arquivos, text="Arquivo Compactado e Texto")
        self.txt_arquivos = scrolledtext.ScrolledText(
            self.aba_arquivos, font=("Consolas", 10)
        )
        self.txt_arquivos.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _configurar_canvas_arvore(self):
        scroll_x = ttk.Scrollbar(self.aba_canvas, orient=tk.HORIZONTAL)
        scroll_y = ttk.Scrollbar(self.aba_canvas, orient=tk.VERTICAL)

        self.canvas = tk.Canvas(
            self.aba_canvas,
            bg="white",
            xscrollcommand=scroll_x.set,
            yscrollcommand=scroll_y.set
        )
        scroll_x.config(command=self.canvas.xview)
        scroll_y.config(command=self.canvas.yview)

        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # AÇÃO 1: COMPACTAR ARQUIVO .TXT
    def acao_compactar(self):
        caminho_txt = filedialog.askopenfilename(
            title="Selecione o arquivo .txt para compactar",
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os Arquivos", "*.*")]
        )
        if not caminho_txt:
            return

        caminho_huff = os.path.splitext(caminho_txt)[0] + "_compactado.huff"

        try:
            relatorio = self.compactador.compactar_arquivo(caminho_txt, caminho_huff)

            # Atualiza o painel superior com a Taxa de Compactação
            self.lbl_metricas.config(
                text=(
                    f"Original: {relatorio['bits_originais']} bits ({relatorio['bytes_originais']} B)  |  "
                    f"Compactado (Bits): {relatorio['bits_compactados']} bits  |  "
                    f"Arquivo Final: {relatorio['bytes_arquivo_final']} B  |  "
                    f"Taxa de Compactação: {relatorio['taxa_compactacao_pct']:.2f}%"
                )
            )

            # Desenha a árvore no Canvas
            self.desenhar_arvore_canvas(self.compactador.raiz)

            # Preenche a Aba 2 (Tabela de Códigos e Árvore em Texto)
            self.txt_tabela.delete("1.0", tk.END)
            self.txt_tabela.insert(tk.END, "=== TABELA DE CÓDIGOS DE HUFFMAN ===\n")
            self.txt_tabela.insert(tk.END, f"{'Caractere':<15} | {'Frequência':<12} | {'Código Binário'}\n")
            self.txt_tabela.insert(tk.END, "-" * 50 + "\n")

            # Ordena pela maior frequência para facilitar a explicação na aula
            itens_ordenados = sorted(
                self.compactador.frequencias.items(), key=lambda x: x[1], reverse=True
            )
            for char, freq in itens_ordenados:
                codigo = self.compactador.tabela_codigos[char]
                self.txt_tabela.insert(tk.END, f"{repr(char):<15} | {freq:<12} | {codigo}\n")

            self.txt_tabela.insert(tk.END, "\n=== ESTRUTURA DA ÁRVORE EM TEXTO ===\n")
            self.txt_tabela.insert(tk.END, self.compactador.formatar_arvore())

            # Preenche a Aba 3 (Amostra do arquivo compactado)
            with open(caminho_huff, "rb") as f:
                bytes_brutos = f.read(256)
            hex_dump = " ".join(f"{b:02X}" for b in bytes_brutos)

            self.txt_arquivos.delete("1.0", tk.END)
            self.txt_arquivos.insert(tk.END, f"Arquivo gerado com sucesso em:\n{caminho_huff}\n\n")
            self.txt_arquivos.insert(tk.END, "=== AMOSTRA DOS BITS COMPACTADOS (0 e 1) ===\n")
            self.txt_arquivos.insert(tk.END, relatorio["amostra_bits"] + "\n\n")
            self.txt_arquivos.insert(tk.END, "=== BYTES GRAVADOS NO ARQUIVO COMPACTADO (HEXADECIMAL) ===\n")
            self.txt_arquivos.insert(tk.END, hex_dump + "\n")

            messagebox.showinfo(
                "Compactação Concluída",
                f"Arquivo compactado salvo em:\n{caminho_huff}\n\n"
                f"Taxa de Compactação (Bits): {relatorio['taxa_compactacao_pct']:.2f}%"
            )
        except Exception as erro:
            messagebox.showerror("Erro ao Compactar", str(erro))

    # AÇÃO 2: DESCOMPACTAR ARQUIVO .HUFF
    def acao_descompactar(self):
        caminho_huff = filedialog.askopenfilename(
            title="Selecione o arquivo .huff para descompactar",
            filetypes=[("Arquivo Huffman", "*.huff"), ("Todos os Arquivos", "*.*")]
        )
        if not caminho_huff:
            return

        caminho_recuperado = os.path.splitext(caminho_huff)[0] + "_recuperado.txt"

        try:
            texto_final = self.compactador.descompactar_arquivo(caminho_huff, caminho_recuperado)

            # Atualiza também a árvore na tela caso o usuário descompacte direto
            self.desenhar_arvore_canvas(self.compactador.raiz)

            self.txt_arquivos.delete("1.0", tk.END)
            self.txt_arquivos.insert(tk.END, f"Arquivo descompactado salvo em:\n{caminho_recuperado}\n\n")
            self.txt_arquivos.insert(tk.END, "=== TEXTO ORIGINAL RECUPERADO ===\n")
            self.txt_arquivos.insert(tk.END, texto_final)

            self.abas.select(self.aba_arquivos)
            messagebox.showinfo(
                "Descompactação Concluída",
                f"Texto original recuperado com sucesso em:\n{caminho_recuperado}"
            )
        except Exception as erro:
            messagebox.showerror("Erro ao Descompactar", str(erro))

    # ALGORITMO DE POSICIONAMENTO E DESENHO DA ÁRVORE NO CANVAS
    def desenhar_arvore_canvas(self, raiz):
        self.canvas.delete("all")
        if raiz is None:
            return

        posicoes = {}
        contador_folhas = [0]
        espacamento_x = 75
        espacamento_y = 85

        # Calcula X e Y sem sobrepor nós usando percurso em-ordem (In-Order Traversal)
        def calcular_coordenadas(no, profundidade):
            if no is None:
                return
            if no.esquerda is None and no.direita is None:
                x = 60 + contador_folhas[0] * espacamento_x
                y = 50 + profundidade * espacamento_y
                posicoes[no] = (x, y)
                contador_folhas[0] += 1
            else:
                calcular_coordenadas(no.esquerda, profundidade + 1)
                calcular_coordenadas(no.direita, profundidade + 1)
                filhos_x = [
                    posicoes[f][0] for f in (no.esquerda, no.direita) if f is not None
                ]
                x = sum(filhos_x) / len(filhos_x)
                y = 50 + profundidade * espacamento_y
                posicoes[no] = (x, y)

        calcular_coordenadas(raiz, 0)

        # Desenha as arestas (linhas com rótulo 0 ou 1)
        def desenhar_arestas(no):
            if no is None:
                return
            x1, y1 = posicoes[no]
            if no.esquerda:
                x2, y2 = posicoes[no.esquerda]
                self.canvas.create_line(x1, y1, x2, y2, fill="#555555", width=2)
                self.canvas.create_text(
                    (x1 + x2) / 2 - 10, (y1 + y2) / 2,
                    text="0", fill="#0055cc", font=("Segoe UI", 9, "bold")
                )
                desenhar_arestas(no.esquerda)
            if no.direita:
                x2, y2 = posicoes[no.direita]
                self.canvas.create_line(x1, y1, x2, y2, fill="#555555", width=2)
                self.canvas.create_text(
                    (x1 + x2) / 2 + 10, (y1 + y2) / 2,
                    text="1", fill="#cc0000", font=("Segoe UI", 9, "bold")
                )
                desenhar_arestas(no.direita)

        # Desenha os vértices (círculos)
        def desenhar_nos(no):
            if no is None:
                return
            x, y = posicoes[no]
            raio = 24
            eh_folha = no.caractere is not None
            cor_fundo = "#d4edda" if eh_folha else "#e2e3e5"
            cor_borda = "#28a745" if eh_folha else "#6c757d"

            self.canvas.create_oval(
                x - raio, y - raio, x + raio, y + raio,
                fill=cor_fundo, outline=cor_borda, width=2
            )
            texto_no = f"{repr(no.caractere)}\n({no.frequencia})" if eh_folha else f"{no.frequencia}"
            self.canvas.create_text(x, y, text=texto_no, font=("Segoe UI", 8, "bold"))

            desenhar_nos(no.esquerda)
            desenhar_nos(no.direita)

        desenhar_arestas(raiz)
        desenhar_nos(raiz)

        # Ajusta a área de rolagem do Canvas ao tamanho total da árvore
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


if __name__ == "__main__":
    raiz_tk = tk.Tk()
    app = InterfaceHuffman(raiz_tk)
    raiz_tk.mainloop()