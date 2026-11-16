import os
import json
import time


class NoHuffman:
    def __init__(self, caractere, frequencia):
        self.caractere = caractere
        self.frequencia = frequencia
        self.esquerda = None
        self.direita = None


class CompactadorHuffman:
    def __init__(self):
        self.raiz = None
        self.tabela_codigos = {}
        self.frequencias = {}

    # PRÉ-COMPRESSÃO OPCIONAL: Algoritmo LZ77 (LZSS) com Janela Deslizante Manual
    def aplicar_lz77(self, texto, tamanho_janela=255, tamanho_max_match=32):
        resultado = []
        i = 0
        n = len(texto)

        while i < n:
            melhor_distancia = 0
            melhor_comprimento = 0
            inicio_janela = max(0, i - tamanho_janela)

            # Procura a maior repetição na janela deslizante
            for j in range(inicio_janela, i):
                comprimento = 0
                while (
                    comprimento < tamanho_max_match
                    and i + comprimento < n
                    and texto[j + comprimento] == texto[i + comprimento]
                ):
                    comprimento += 1
                    if j + comprimento >= i:
                        break

                if comprimento > melhor_comprimento:
                    melhor_comprimento = comprimento
                    melhor_distancia = i - j

            # Só cria ponteiro se a repetição economizar espaço (>= 4 caracteres)
            if melhor_comprimento >= 4:
                # Usa caractere sentinela \x00 seguido de (distância, comprimento)
                token = f"\x00{chr(melhor_distancia)}{chr(melhor_comprimento)}"
                resultado.append(token)
                i += melhor_comprimento
            else:
                if texto[i] == "\x00":
                    resultado.append("\x00\x00\x00")
                else:
                    resultado.append(texto[i])
                i += 1

        return "".join(resultado)

    def reverter_lz77(self, texto_lz):
        saida = []
        i = 0
        n = len(texto_lz)

        while i < n:
            if texto_lz[i] == "\x00" and i + 2 < n:
                distancia = ord(texto_lz[i + 1])
                comprimento = ord(texto_lz[i + 2])
                if distancia == 0 and comprimento == 0:
                    saida.append("\x00")
                else:
                    inicio = len(saida) - distancia
                    for k in range(comprimento):
                        saida.append(saida[inicio + k])
                i += 3
            else:
                saida.append(texto_lz[i])
                i += 1

        return "".join(saida)

    def contar_frequencias(self, texto):
        frequencias = {}
        for caractere in texto:
            frequencias[caractere] = frequencias.get(caractere, 0) + 1
        self.frequencias = frequencias
        return frequencias

    def construir_arvore(self, frequencias):
        fila_prioridade = [
            NoHuffman(caractere, freq) for caractere, freq in frequencias.items()
        ]
        if not fila_prioridade:
            return None

        while len(fila_prioridade) > 1:
            fila_prioridade.sort(key=lambda no: no.frequencia)
            no_esquerdo = fila_prioridade.pop(0)
            no_direito = fila_prioridade.pop(0)

            no_pai = NoHuffman(None, no_esquerdo.frequencia + no_direito.frequencia)
            no_pai.esquerda = no_esquerdo
            no_pai.direita = no_direito
            fila_prioridade.append(no_pai)

        self.raiz = fila_prioridade[0]
        return self.raiz

    def _gerar_codigos_recursivo(self, no_atual, codigo_atual):
        if no_atual is None:
            return
        if no_atual.caractere is not None:
            self.tabela_codigos[no_atual.caractere] = codigo_atual if codigo_atual != "" else "0"
            return
        self._gerar_codigos_recursivo(no_atual.esquerda, codigo_atual + "0")
        self._gerar_codigos_recursivo(no_atual.direita, codigo_atual + "1")

    def gerar_tabela_codigos(self):
        self.tabela_codigos = {}
        self._gerar_codigos_recursivo(self.raiz, "")
        return self.tabela_codigos

    def compactar_arquivo(self, caminho_entrada, caminho_saida, usar_lz77=False):
        inicio_tempo = time.perf_counter()

        with open(caminho_entrada, "r", encoding="utf-8") as f:
            texto_original = f.read()

        if not texto_original:
            raise ValueError("O arquivo selecionado está vazio.")

        texto_processado = self.aplicar_lz77(texto_original) if usar_lz77 else texto_original

        self.contar_frequencias(texto_processado)
        self.construir_arvore(self.frequencias)
        self.gerar_tabela_codigos()

        bits_compactados = "".join(self.tabela_codigos[c] for c in texto_processado)
        padding = (8 - len(bits_compactados) % 8) % 8
        bits_com_padding = bits_compactados + ("0" * padding)

        vetor_bytes = bytearray()
        for i in range(0, len(bits_com_padding), 8):
            vetor_bytes.append(int(bits_com_padding[i:i + 8], 2))

        cabecalho = json.dumps({
            "freq": self.frequencias,
            "pad": padding,
            "lz77": usar_lz77
        }).encode("utf-8")
        tamanho_cabecalho = len(cabecalho).to_bytes(4, byteorder="big")

        with open(caminho_saida, "wb") as f:
            f.write(tamanho_cabecalho)
            f.write(cabecalho)
            f.write(vetor_bytes)

        tempo_gasto = time.perf_counter() - inicio_tempo
        bytes_originais = len(texto_original.encode("utf-8"))
        bits_originais = bytes_originais * 8
        bits_finais_puros = len(bits_compactados)
        bytes_arquivo_final = os.path.getsize(caminho_saida)

        taxa_bits = (1 - (bits_finais_puros / bits_originais)) * 100
        taxa_arquivo = (1 - (bytes_arquivo_final / bytes_originais)) * 100

        return {
            "texto_original": texto_original,
            "bits_originais": bits_originais,
            "bits_compactados": bits_finais_puros,
            "bytes_originais": bytes_originais,
            "bytes_payload": len(vetor_bytes),
            "bytes_cabecalho": len(cabecalho) + 4,
            "bytes_arquivo_final": bytes_arquivo_final,
            "taxa_compactacao_pct": taxa_bits,
            "taxa_arquivo_pct": taxa_arquivo,
            "usar_lz77": usar_lz77,
            "tempo_s": tempo_gasto,
            "string_bits": bits_compactados
        }

    def descompactar_arquivo(self, caminho_entrada, caminho_saida):
        inicio_tempo = time.perf_counter()

        with open(caminho_entrada, "rb") as f:
            tamanho_cabecalho = int.from_bytes(f.read(4), byteorder="big")
            cabecalho = json.loads(f.read(tamanho_cabecalho).decode("utf-8"))
            bytes_compactados = f.read()

        frequencias = cabecalho["freq"]
        padding = cabecalho["pad"]
        usou_lz77 = cabecalho.get("lz77", False)

        self.construir_arvore(frequencias)
        self.gerar_tabela_codigos()

        lista_bits = [bin(byte)[2:].rjust(8, "0") for byte in bytes_compactados]
        string_bits = "".join(lista_bits)
        if padding > 0:
            string_bits = string_bits[:-padding]

        texto_reconstruido = []
        no_atual = self.raiz

        if no_atual.esquerda is None and no_atual.direita is None:
            texto_reconstruido.append(no_atual.caractere * no_atual.frequencia)
        else:
            for bit in string_bits:
                no_atual = no_atual.esquerda if bit == "0" else no_atual.direita
                if no_atual.caractere is not None:
                    texto_reconstruido.append(no_atual.caractere)
                    no_atual = self.raiz

        texto_intermediario = "".join(texto_reconstruido)
        texto_final = self.reverter_lz77(texto_intermediario) if usou_lz77 else texto_intermediario

        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(texto_final)

        tempo_gasto = time.perf_counter() - inicio_tempo
        return {
            "texto_restaurado": texto_final,
            "bytes_compactado": os.path.getsize(caminho_entrada),
            "bytes_restaurado": len(texto_final.encode("utf-8")),
            "usou_lz77": usou_lz77,
            "tempo_s": tempo_gasto
        }