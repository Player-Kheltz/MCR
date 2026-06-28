"""MCR-DevIA — Teste Cego: Analisador Multi-Estagio
EU (70B) crio algo complexo. ELE tenta copiar. Se falhar, eu refaco enquanto ele observa."""
import os, sys, ast, json
from collections import defaultdict

class AnalisadorCodigo:
    """Analisa codigo Python em multi-estagios: extrai, grafa, documenta, diagnostica, sugere."""
    
    def __init__(self, path):
        self.path = path
        self.arvore = None
        self.funcoes = {}
        self.classes = {}
        self.grafo = defaultdict(list)
        self.doc = {}
        self.bugs = []
        self.sugestoes = []
    
    def executar(self):
        print(f"Analisando: {self.path}")
        self._estagio1_extrair()
        self._estagio2_grafar()
        self._estagio3_documentar()
        self._estagio4_diagnosticar()
        self._estagio5_sugerir()
        self._estagio6_relatorio()
        return self
    
    def _estagio1_extrair(self):
        """AST: extrai funcoes, classes, imports."""
        with open(self.path, encoding="utf-8") as f:
            self.arvore = ast.parse(f.read())
        
        for no in ast.walk(self.arvore):
            if isinstance(no, ast.FunctionDef):
                self.funcoes[no.name] = {
                    "linha": no.lineno,
                    "args": [a.arg for a in no.args.args],
                    "decoradores": [d.id for d in no.decorator_list if isinstance(d, ast.Name)],
                    "docstring": ast.get_docstring(no) or "",
                    "retornos": self._extrair_retornos(no),
                }
            elif isinstance(no, ast.ClassDef):
                bases = []
                for base in no.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(base.attr)
                self.classes[no.name] = {
                    "linha": no.lineno,
                    "bases": bases,
                    "metodos": [m.name for m in no.body if isinstance(m, ast.FunctionDef)],
                    "docstring": ast.get_docstring(no) or "",
                }
    
    def _extrair_retornos(self, no):
        """Extrai tipos de retorno de uma funcao."""
        retornos = set()
        for sub in ast.walk(no):
            if isinstance(sub, ast.Return) and sub.value:
                if isinstance(sub.value, ast.Constant):
                    retornos.add(type(sub.value.value).__name__)
                elif isinstance(sub.value, ast.List):
                    retornos.add("list")
                elif isinstance(sub.value, ast.Dict):
                    retornos.add("dict")
                elif isinstance(sub.value, ast.Name):
                    retornos.add(sub.value.id)
                elif isinstance(sub.value, ast.Call):
                    if isinstance(sub.value.func, ast.Name):
                        retornos.add(sub.value.func.id)
                elif isinstance(sub.value, ast.BinOp):
                    retornos.add("expr")
        return list(retornos)
    
    def _estagio2_grafar(self):
        """Constroi grafo de dependencias entre funcoes/classes."""
        for nome, info in self.funcoes.items():
            corpo = ""
            with open(self.path) as f:
                linhas = f.readlines()
            inicio = info["linha"] - 1
            for i in range(inicio, min(inicio + 50, len(linhas))):
                if linhas[i].strip().startswith(("def ", "class ")) and i > inicio:
                    break
                corpo += linhas[i]
            
            for outro_nome in self.funcoes:
                if outro_nome != nome and outro_nome in corpo:
                    self.grafo[nome].append(outro_nome)
            for cls_nome in self.classes:
                if cls_nome in corpo:
                    self.grafo[nome].append(cls_nome)
        
        for cls_nome, info in self.classes.items():
            for base in info["bases"]:
                if base in self.classes:
                    self.grafo[cls_nome].append(base)
    
    def _estagio3_documentar(self):
        """Gera documentacao baseada na AST."""
        for nome, info in self.funcoes.items():
            doc = f"### `{nome}({', '.join(info['args'])})`\n"
            doc += f"Linha {info['linha']}\n"
            if info["docstring"]:
                doc += f"{info['docstring']}\n"
            if info["retornos"]:
                doc += f"Retorna: {', '.join(info['retornos'])}\n"
            if info["decoradores"]:
                doc += f"Decoradores: @{', @'.join(info['decoradores'])}\n"
            if self.grafo[nome]:
                doc += f"Depende de: {', '.join(self.grafo[nome])}\n"
            self.doc[nome] = doc
        
        for nome, info in self.classes.items():
            doc = f"### Class `{nome}`\n"
            doc += f"Linha {info['linha']}\n"
            if info["bases"]:
                doc += f"Herda de: {', '.join(info['bases'])}\n"
            if info["docstring"]:
                doc += f"{info['docstring']}\n"
            if info["metodos"]:
                doc += f"Metodos: {', '.join(info['metodos'])}\n"
            self.doc[nome] = doc
    
    def _estagio4_diagnosticar(self):
        """Identifica bugs potenciais."""
        for nome, info in self.funcoes.items():
            if not info["docstring"] and not nome.startswith("_"):
                self.bugs.append(f"ALERTA: {nome} sem docstring")
            if len(info["args"]) > 5:
                self.bugs.append(f"SUGESTAO: {nome} tem {len(info['args'])} parametros - pode ser muitos")
            if "pass" in str(self.arvore) and nome in str(self.arvore):
                for no in ast.walk(self.arvore):
                    if isinstance(no, ast.FunctionDef) and no.name == nome:
                        if len(no.body) == 1 and isinstance(no.body[0], ast.Pass):
                            self.bugs.append(f"ALERTA: {nome} eh vazia (so pass)")
                            break
    
    def _estagio5_sugerir(self):
        """Sugere refatoracoes."""
        if self.grafo:
            mais_dependentes = max(self.grafo.items(), key=lambda x: len(x[1]))
            self.sugestoes.append(f"REFATORACAO: {mais_dependentes[0]} eh usada por {len(mais_dependentes[1])} outras funcoes - considere modularizar")
        
        classes_sem_metodos = [n for n, i in self.classes.items() if not i["metodos"]]
        if classes_sem_metodos:
            self.sugestoes.append(f"REFATORACAO: Classes sem metodos: {classes_sem_metodos}")
        
        funcoes_longas = [n for n, i in self.funcoes.items() if len(i["args"]) > 3]
        if funcoes_longas:
            self.sugestoes.append(f"REFATORACAO: Funcoes com muitos args: {funcoes_longas}")
    
    def _estagio6_relatorio(self):
        """Gera relatorio completo em JSON."""
        relatorio = {
            "arquivo": self.path,
            "funcoes": len(self.funcoes),
            "classes": len(self.classes),
            "dependencias": dict(self.grafo),
            "documentacao": self.doc,
            "bugs": self.bugs,
            "sugestoes": self.sugestoes,
            "resumo": f"{len(self.funcoes)} funcoes, {len(self.classes)} classes, {len(self.bugs)} alertas, {len(self.sugestoes)} sugestoes"
        }
        
        out_path = os.path.join(os.path.dirname(self.path), f"analise_{os.path.basename(self.path)}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
        print(f"\nRelatorio salvo em {out_path}")
        print(f"Resumo: {relatorio['resumo']}")
        return relatorio


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else __file__
    analisador = AnalisadorCodigo(path)
    relatorio = analisador.executar()
    
    # Le o JSON salvo (contem os dados reais)
    json_path = os.path.join(os.path.dirname(path), f"analise_{os.path.basename(path)}.json")
    if os.path.exists(json_path):
        with open(json_path, encoding="utf-8") as f:
            dados = json.load(f)
        
        print(f"\nDocumentacao:")
        for nome, doc in list(dados.get("documentacao", {}).items())[:5]:
            print(f"\n{doc}")
        
        print(f"\nBugs encontrados:")
        for bug in dados.get("bugs", []):
            print(f"  - {bug}")
        
        print(f"\nSugestoes:")
        for sug in dados.get("sugestoes", []):
            print(f"  - {sug}")
    else:
        print("[OK] Relatorio salvo em JSON")
