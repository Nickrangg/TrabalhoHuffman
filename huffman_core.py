import os
import json


class NoHuffman:
    """
    Representa um vértice (nó) da Árvore Binária de Huffman.
    Em Teoria dos Grafos, a árvore é um grafo acíclico e conexo.
    """
    def __init__(self, caractere, frequencia):
        self.caractere = caractere      # None se for um nó interno (pai)
        self.frequencia = frequencia    # Peso do vértice (soma das frequências)
        self.esquerda = None            # Aresta para o filho esquerdo (bit 0)
        self.direita = None             # Aresta para o filho direito (bit 1)


class CompactadorHuffman:
    def __init__(self):
        self.raiz = None
        self.tabela_codigos = {}
        self.frequencias = {}

    # ETAPA 1: Levantamento de Frequências
    def contar_frequencias(self, texto):
        frequencias = {}
        for caractere in texto:
            if caractere in frequencias:
                frequencias[caractere] += 1
            else:
                frequencias[caractere] = 1
        self.frequencias = frequencias
        return frequencias

    # ETAPA 2: Construção da Árvore de Huffman (Algoritmo Guloso)
    def construir_arvore(self, frequencias):
        # Cria uma lista de nós-folha (um para cada caractere único)
        fila_prioridade = [
            NoHuffman(caractere, freq) for caractere, freq in frequencias.items()
        ]

        # Caso especial: texto vazio
        if not fila_prioridade:
            return None

        # Loop até restar apenas 1 nó na fila (que será a raiz da árvore)
        while len(fila_prioridade) > 1:
            # Ordena a fila pela menor frequência (implementação manual da fila de prioridade)
            fila_prioridade.sort(key=lambda no: no.frequencia)

            # Retira os dois vértices de menor peso (frequência)
            no_esquerdo = fila_prioridade.pop(0)
            no_direito = fila_prioridade.pop(0)

            # Cria um novo vértice interno somando os pesos dos dois filhos
            soma_pesos = no_esquerdo.frequencia + no_direito.frequencia
            no_pai = NoHuffman(None, soma_pesos)
            no_pai.esquerda = no_esquerdo
            no_pai.direita = no_direito

            # Devolve o novo nó pai para a fila
            fila_prioridade.append(no_pai)

        self.raiz = fila_prioridade[0]
        return self.raiz

    # ETAPA 3: Geração da Tabela de Códigos Binários (Busca em Profundidade - DFS)
    def _gerar_codigos_recursivo(self, no_atual, codigo_atual):
        if no_atual is None:
            return

        # Se chegou a um nó-folha (possui caractere), salva o caminho binário
        if no_atual.caractere is not None:
            # Se o texto tiver apenas 1 tipo de caractere repetido, atribui bit "0"
            self.tabela_codigos[no_atual.caractere] = codigo_atual if codigo_atual != "" else "0"
            return

        # Caminha para a esquerda adicionando "0" e para a direita adicionando "1"
        self._gerar_codigos_recursivo(no_atual.esquerda, codigo_atual + "0")
        self._gerar_codigos_recursivo(no_atual.direita, codigo_atual + "1")

    def gerar_tabela_codigos(self):
        self.tabela_codigos = {}
        self._gerar_codigos_recursivo(self.raiz, "")
        return self.tabela_codigos

    # ETAPA 4: Codificação e Empacotamento em Bytes Reais
    def compactar_arquivo(self, caminho_entrada, caminho_saida):
        with open(caminho_entrada, "r", encoding="utf-8") as f:
            texto = f.read()

        if not texto:
            raise ValueError("O arquivo selecionado está vazio.")

        # Executa as etapas do algoritmo
        self.contar_frequencias(texto)
        self.construir_arvore(self.frequencias)
        self.gerar_tabela_codigos()

        # Substitui cada caractere pelo seu código binário de Huffman
        bits_compactados = "".join(self.tabela_codigos[c] for c in texto)

        # Arquivos reais gravam múltiplos de 8 bits (1 byte).
        # Calculamos quantos zeros extras (padding) precisamos no final para fechar 8 bits.
        padding = (8 - len(bits_compactados) % 8) % 8
        bits_com_padding = bits_compactados + ("0" * padding)

        # Converte os grupos de 8 bits em bytes reais
        vetor_bytes = bytearray()
        for i in range(0, len(bits_com_padding), 8):
            bloco_byte = bits_com_padding[i:i + 8]
            vetor_bytes.append(int(bloco_byte, 2))

        # Salva cabeçalho (frequências + padding) e os bytes compactados no arquivo final
        cabecalho = json.dumps({"freq": self.frequencias, "pad": padding}).encode("utf-8")
        tamanho_cabecalho = len(cabecalho).to_bytes(4, byteorder="big")

        with open(caminho_saida, "wb") as f:
            f.write(tamanho_cabecalho)
            f.write(cabecalho)
            f.write(vetor_bytes)

        # Cálculo matemático da Taxa de Compactação
        bytes_originais = len(texto.encode("utf-8"))
        bits_originais = bytes_originais * 8
        bits_finais_puros = len(bits_compactados)
        bytes_arquivo_final = os.path.getsize(caminho_saida)

        taxa_bits = (1 - (bits_finais_puros / bits_originais)) * 100

        return {
            "bits_originais": bits_originais,
            "bits_compactados": bits_finais_puros,
            "bytes_originais": bytes_originais,
            "bytes_arquivo_final": bytes_arquivo_final,
            "taxa_compactacao_pct": taxa_bits,
            "amostra_bits": bits_compactados[:120] + ("..." if len(bits_compactados) > 120 else "")
        }

    # ETAPA 5: Descompactação (Navegação na Árvore Bit a Bit)
    def descompactar_arquivo(self, caminho_entrada, caminho_saida):
        with open(caminho_entrada, "rb") as f:
            tamanho_cabecalho = int.from_bytes(f.read(4), byteorder="big")
            cabecalho = json.loads(f.read(tamanho_cabecalho).decode("utf-8"))
            bytes_compactados = f.read()

        frequencias = cabecalho["freq"]
        padding = cabecalho["pad"]

        # Reconstrói a mesma Árvore de Huffman a partir das frequências
        self.construir_arvore(frequencias)

        # Converte os bytes lidos de volta para a string de bits 0 e 1
        lista_bits = [bin(byte)[2:].rjust(8, "0") for byte in bytes_compactados]
        string_bits = "".join(lista_bits)

        # Remove os bits extras de padding do final
        if padding > 0:
            string_bits = string_bits[:-padding]

        # Percorre a árvore: 0 vai para a esquerda, 1 vai para a direita
        texto_reconstruido = []
        no_atual = self.raiz

        # Caso especial: arquivo com apenas 1 caractere distinto repetido
        if no_atual.esquerda is None and no_atual.direita is None:
            texto_reconstruido.append(no_atual.caractere * no_atual.frequencia)
        else:
            for bit in string_bits:
                if bit == "0":
                    no_atual = no_atual.esquerda
                else:
                    no_atual = no_atual.direita

                # Ao atingir uma folha, recupera o caractere e volta para a raiz
                if no_atual.caractere is not None:
                    texto_reconstruido.append(no_atual.caractere)
                    no_atual = self.raiz

        texto_final = "".join(texto_reconstruido)
        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(texto_final)

        return texto_final

    # ETAPA EXTRA: Gerador Visual da Árvore em Texto
    def formatar_arvore(self, no=None, prefixo="", eh_esquerda=True):
        if no is None:
            no = self.raiz
        if no is None:
            return "Árvore vazia"

        resultado = ""
        if no.direita is not None:
            novo_prefixo = prefixo + ("│   " if eh_esquerda else "    ")
            resultado += self.formatar_arvore(no.direita, novo_prefixo, False)

        if no.caractere is not None:
            char_visivel = repr(no.caractere)
            resultado += f"{prefixo}{'└── ' if eh_esquerda else '┌── '}Folha: {char_visivel} (Peso: {no.frequencia})\n"
        else:
            resultado += f"{prefixo}{'└── ' if eh_esquerda else '┌── '}[Nó Interno | Peso: {no.frequencia}]\n"

        if no.esquerda is not None:
            novo_prefixo = prefixo + ("    " if eh_esquerda else "│   ")
            resultado += self.formatar_arvore(no.esquerda, novo_prefixo, True)

        return resultado


# BLOCO DE TESTE RÁPIDO NO TERMINAL
if __name__ == "__main__":
    # Cria um arquivo de teste automático caso não exista
    arquivo_original = "teste.txt"
    arquivo_compactado = "teste_compactado.huff"
    arquivo_descompactado = "teste_recuperado.txt"

    with open(arquivo_original, "w", encoding="utf-8") as f:
        f.write("ABRACADABRA! Este e um teste do algoritmo de Huffman para Teoria dos Grafos.")

    huff = CompactadorHuffman()
    relatorio = huff.compactar_arquivo(arquivo_original, arquivo_compactado)
    texto_recuperado = huff.descompactar_arquivo(arquivo_compactado, arquivo_descompactado)

    print("=== ÁRVORE DE HUFFMAN MONTADA ===")
    print(huff.formatar_arvore())
    print("=== TABELA DE CÓDIGOS ===")
    for char, cod in huff.tabela_codigos.items():
        print(f"Caractere {repr(char)}: {cod}")
    print("\n=== ESTATÍSTICAS DE COMPACTAÇÃO ===")
    print(f"Bits originais (UTF-8): {relatorio['bits_originais']} bits")
    print(f"Bits após Huffman:      {relatorio['bits_compactados']} bits")
    print(f"Taxa de Compactação:    {relatorio['taxa_compactacao_pct']:.2f}%")
    print(f"Texto recuperado fielmente? {open(arquivo_original, encoding='utf-8').read() == texto_recuperado}")