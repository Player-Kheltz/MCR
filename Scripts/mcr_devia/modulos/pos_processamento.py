"""Pós-processamento — extrai blocos de código da resposta do LLM e salva arquivos.

O LLM escreve blocos ```lua, ```md, ```python na resposta.
O pós-processamento detecta e salva baseado no contexto:
  - Se trigger CREATE(npc) estava ativo → ```lua salva em data/npc/
  - Se trigger CREATE(lore) estava ativo → ```md salva em docs/
  - Se trigger EDIT estava ativo → escreve no path especificado

Uso:
    pp = PosProcessamento()
    arquivos = pp.extrair(resposta_llm, intencoes_ativas)
    # → ["data/npc/blacksmith.lua", "docs/lore_eridanus.md"]
"""
import os, re, json
from typing import List, Tuple, Dict, Optional


class PosProcessamento:
    """Extrai e salva blocos de código da resposta do LLM."""

    # Mapa: extensão → diretório base de saída
    _DIR_PADRAO = {
        "lua": "data",
        "md": "docs",
        "py": "scripts",
        "json": "data",
        "txt": "sandbox/test_output",
    }

    def __init__(self):
        self._arquivos_criados = []
        self._base = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                   '..', '..', '..'))

    def processar(self, resposta: str,
                  intencoes: List[Tuple[str, Dict, float]] = None) -> List[str]:
        """Processa a resposta do LLM e extrai/salva blocos de código.

        Args:
            resposta: resposta completa do LLM
            intencoes: intenções detectadas originalmente (para decidir diretório)

        Returns:
            Lista de paths dos arquivos criados
        """
        self._arquivos_criados = []

        if not resposta or len(resposta) < 20:
            return []

        # Detecta blocos de código
        blocos = self._detectar_blocos(resposta)
        if not blocos:
            return []

        # Decide diretórios baseados nas intenções
        mapa_dirs = self._montar_mapa_diretorios(intencoes or [])

        for linguagem, conteudo in blocos:
            if not conteudo.strip():
                continue
            path = self._salvar_bloco(linguagem, conteudo, mapa_dirs)
            if path:
                self._arquivos_criados.append(path)

        return self._arquivos_criados

    # ============================================================
    # DETECÇÃO DE BLOCOS
    # ============================================================

    def _detectar_blocos(self, resposta: str) -> List[Tuple[str, str]]:
        """Extrai blocos ```...``` da resposta.

        Returns:
            Lista de (linguagem, conteudo)
        """
        blocos = []

        # ```lua ... ```
        pattern = r'```(\w+)\s*\n(.*?)```'
        for match in re.finditer(pattern, resposta, re.DOTALL):
            linguagem = match.group(1).strip().lower()
            conteudo = match.group(2).strip()
            if conteudo and len(conteudo) > 30:
                blocos.append((linguagem, conteudo))

        return blocos

    # ============================================================
    # DIREtóRIOS
    # ============================================================

    def _montar_mapa_diretorios(self, intencoes: List[Tuple[str, Dict, float]]
                                 ) -> Dict[str, str]:
        """Decide diretórios baseado nas intenções.

        Returns:
            dict: extensão → caminho absoluto do diretório
        """
        mapa = dict(self._DIR_PADRAO)  # fallback

        for cat, params, conf in intencoes:
            if cat == "CREATE":
                tipo = params.get("tipo", "")
                if tipo == "npc":
                    # Tenta encontrar diretório de NPC
                    caminho = self._encontrar_dir(["data/npc", "data-canary/data/npc"])
                    if caminho:
                        mapa["lua"] = caminho
                elif tipo == "lore":
                    mapa["md"] = "docs"
                elif tipo == "codigo":
                    caminho = self._encontrar_dir(["data", "scripts", "src"])
                    if caminho:
                        mapa["lua"] = caminho
            elif cat == "EDIT":
                path = params.get("path", "")
                if path:
                    dir_path = os.path.dirname(path)
                    mapa["_edit_path"] = path  # path específico para edição

        return mapa

    def _encontrar_dir(self, candidatos: List[str]) -> Optional[str]:
        """Encontra o primeiro diretório que existe."""
        for c in candidatos:
            full = os.path.join(self._base, c)
            if os.path.isdir(full):
                return full
            # Tenta criar
            try:
                os.makedirs(full, exist_ok=True)
                return full
            except Exception:
                pass
        return None

    # ============================================================
    # SALVAMENTO
    # ============================================================

    def _salvar_bloco(self, linguagem: str, conteudo: str,
                      mapa_dirs: Dict[str, str]) -> Optional[str]:
        """Salva um bloco de código no diretório apropriado.

        Returns:
            path relativo do arquivo criado, ou None se falhou
        """
        # Verifica se é edição (EDIT)
        if "_edit_path" in mapa_dirs and linguagem in ("txt", "md", ""):
            return self._salvar_edicao(mapa_dirs["_edit_path"], conteudo)

        # Decide diretório e nome do arquivo
        dir_path = mapa_dirs.get(linguagem)
        if not dir_path:
            dir_path = self._DIR_PADRAO.get(linguagem, "sandbox/test_output")

        # Se é caminho relativo, resolve
        if not os.path.isabs(dir_path):
            dir_path = os.path.join(self._base, dir_path)

        # Garante que diretório existe
        try:
            os.makedirs(dir_path, exist_ok=True)
        except Exception:
            return None

        # Gera nome único baseado no conteúdo
        nome = self._gerar_nome(conteudo, linguagem)
        if not nome:
            return None

        full_path = os.path.join(dir_path, nome)

        # Verifica se já existe (evita sobrescrever sem necessidade)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                if f.read().strip() == conteudo.strip():
                    return os.path.relpath(full_path, self._base)

        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            return os.path.relpath(full_path, self._base)
        except Exception as e:
            print(f"  [PosProcessamento] Erro ao salvar {full_path}: {e}")
            return None

    def _salvar_edicao(self, path: str, conteudo: str) -> Optional[str]:
        """Salva edição em um path específico (append ou substitui)."""
        full_path = os.path.join(self._base, path) if not os.path.isabs(path) else path
        dir_path = os.path.dirname(full_path)

        try:
            os.makedirs(dir_path, exist_ok=True)
            # Se arquivo existe, faz append. Se não, cria.
            if os.path.exists(full_path):
                with open(full_path, 'a', encoding='utf-8') as f:
                    f.write("\n" + conteudo)
            else:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(conteudo)
            return os.path.relpath(full_path, self._base)
        except Exception as e:
            print(f"  [PosProcessamento] Erro na edicao {path}: {e}")
            return None

    def _gerar_nome(self, conteudo: str, linguagem: str) -> Optional[str]:
        """Gera nome de arquivo baseado no conteúdo."""
        # Tenta extrair nome de dentro do conteúdo
        # Ex: "local blacksmith = NPC:new("Hargrim")" → "blacksmith.lua"
        # Ex: "# Lore de Eridanus" → "lore_eridanus.md"

        primeira = conteudo.split("\n")[0].strip()

        if linguagem == "lua":
            # Extrai nome da variável após NPC:new ou similar
            m = re.search(r'(\w+)\s*=\s*NPC:\w+\(["\'](\w+)["\']', primeira)
            if m:
                nome = m.group(2).lower().replace(" ", "_")
            else:
                # Extrai primeira variável
                m = re.search(r'\blocal\s+(\w+)', primeira)
                nome = m.group(1).lower() if m else "artefato"
            return f"{nome}.lua"

        elif linguagem == "md":
            # Extrai título
            m = re.search(r'^#\s+(.+?)$', primeira, re.MULTILINE)
            if m:
                nome = m.group(1).lower().replace(" ", "_")
            else:
                nome = "artefato"
            # Remove acentos e caracteres especiais
            nome = re.sub(r'[^a-z0-9_]', '', nome)
            return f"{nome}.md"

        else:
            # Nome genérico com hash
            import hashlib
            h = hashlib.md5(conteudo.encode()).hexdigest()[:8]
            return f"artefato_{h}.{linguagem}"

    # ============================================================
    # RESULTADOS
    # ============================================================

    def relatorio(self) -> str:
        """Gera relatório dos arquivos criados."""
        if not self._arquivos_criados:
            return ""
        partes = ["[ARQUIVOS CRIADOS]"]
        for p in self._arquivos_criados:
            full = os.path.join(self._base, p)
            if os.path.exists(full):
                tamanho = os.path.getsize(full)
                partes.append(f"- {p} ({tamanho} bytes)")
            else:
                partes.append(f"- {p} (ERRO)")
        return "\n".join(partes)
