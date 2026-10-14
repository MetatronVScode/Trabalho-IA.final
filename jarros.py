import argparse
import sys
import time
from collections import deque

CAP_A, CAP_B = 4, 3


def eh_objetivo(s):
    return s[0] == 2 or s[1] == 2


def sucessores(s):
    a, b = s
    res = []
    if a < CAP_A:
        res.append(("encher 4L", (CAP_A, b)))
    if b < CAP_B:
        res.append(("encher 3L", (a, CAP_B)))
    if a > 0:
        res.append(("esvaziar 4L", (0, b)))
    if b > 0:
        res.append(("esvaziar 3L", (a, 0)))
    if a > 0 and b < CAP_B and a > CAP_B - b:
        t = CAP_B - b
        res.append(("completar 3L com 4L", (a - t, CAP_B)))
    if b > 0 and a < CAP_A and b > CAP_A - a:
        t = CAP_A - a
        res.append(("completar 4L com 3L", (CAP_A, b - t)))
    if a > 0 and a <= CAP_B - b:
        res.append(("despejar 4L em 3L", (0, b + a)))
    if b > 0 and b <= CAP_A - a:
        res.append(("despejar 3L em 4L", (a + b, 0)))
    return res


class No:
    __slots__ = ("estado", "pai", "acao", "prof", "filhos", "id", "status")

    def __init__(self, estado, pai=None, acao=None, prof=0):
        self.estado, self.pai, self.acao, self.prof = estado, pai, acao, prof
        self.filhos = []
        self.status = ""
        self.id = 0


class Contadores:
    def __init__(self):
        self.gerados = 0
        self.expandidos = 0
        self.max_fronteira = 0
        self.prof_solucao = None
        self.custo = None


def _novo_no(estado, pai, acao, c):
    n = No(estado, pai, acao, 0 if pai is None else pai.prof + 1)
    c.gerados += 1
    n.id = c.gerados
    if pai is not None:
        pai.filhos.append(n)
    return n


def caminho(n):
    p = []
    while n is not None:
        p.append(n)
        n = n.pai
    return p[::-1]


def bfs(inicial):
    c = Contadores()
    raiz = _novo_no(inicial, None, None, c)
    if eh_objetivo(inicial):
        raiz.status = "objetivo"
        c.prof_solucao = c.custo = 0
        return raiz, raiz, c
    fronteira = deque([raiz])
    visitados = {inicial}
    while fronteira:
        c.max_fronteira = max(c.max_fronteira, len(fronteira))
        n = fronteira.popleft()
        c.expandidos += 1
        for acao, s in sucessores(n.estado):
            filho = _novo_no(s, n, acao, c)
            if s in visitados:
                filho.status = "repetido"
                continue
            visitados.add(s)
            if eh_objetivo(s):
                filho.status = "objetivo"
                c.prof_solucao, c.custo = filho.prof, filho.prof
                return raiz, filho, c
            fronteira.append(filho)
    return raiz, None, c


def dfs(inicial):
    c = Contadores()
    raiz = _novo_no(inicial, None, None, c)
    pilha = [raiz]
    visitados = set()
    while pilha:
        c.max_fronteira = max(c.max_fronteira, len(pilha))
        n = pilha.pop()
        if n.estado in visitados:
            n.status = "repetido"
            continue
        visitados.add(n.estado)
        if eh_objetivo(n.estado):
            n.status = "objetivo"
            c.prof_solucao, c.custo = n.prof, n.prof
            return raiz, n, c
        c.expandidos += 1
        filhos = [_novo_no(s, n, a, c) for a, s in sucessores(n.estado)]
        for f in reversed(filhos):
            pilha.append(f)
    return raiz, None, c


def _dls(n, limite, c, no_caminho):
    if eh_objetivo(n.estado):
        n.status = "objetivo"
        return n
    if n.prof == limite:
        n.status = "limite"
        return None
    c.expandidos += 1
    no_caminho.add(n.estado)
    for acao, s in sucessores(n.estado):
        filho = _novo_no(s, n, acao, c)
        if s in no_caminho:
            filho.status = "repetido"
            continue
        r = _dls(filho, limite, c, no_caminho)
        if r is not None:
            return r
    no_caminho.discard(n.estado)
    return None


def iddfs(inicial, max_prof=50):
    total = Contadores()
    for limite in range(max_prof + 1):
        c = Contadores()
        raiz = _novo_no(inicial, None, None, c)
        r = _dls(raiz, limite, c, set())
        total.gerados += c.gerados
        total.expandidos += c.expandidos
        total.max_fronteira = max(total.max_fronteira, limite + 1)
        if r is not None:
            total.prof_solucao = total.custo = r.prof
            total.limite_final = limite
            return raiz, r, total
    return raiz, None, total


ALGORITMOS = {"bfs": ("Busca em Largura", bfs),
              "dfs": ("Busca em Profundidade", dfs),
              "iddfs": ("Aprofundamento Iterativo", iddfs)}


def imprimir_arvore(raiz, objetivo):
    no_sol = set(id(n) for n in caminho(objetivo)) if objetivo else set()
    rot = {"repetido": " [repetido]", "objetivo": " [OBJETIVO]", "limite": " [limite]", "": ""}

    def rec(n, prefixo, ultimo):
        marca = "*" if id(n) in no_sol else " "
        conector = "" if n.pai is None else ("└── " if ultimo else "├── ")
        acao = "" if n.acao is None else f"{n.acao} -> "
        print(f"{marca} {prefixo}{conector}{acao}{n.estado}{rot[n.status]}")
        novo = prefixo + ("" if n.pai is None else ("    " if ultimo else "│   "))
        for i, f in enumerate(n.filhos):
            rec(f, novo, i == len(n.filhos) - 1)

    sys.setrecursionlimit(10000)
    rec(raiz, "", True)
    print("\n(*) = nó pertencente ao caminho da solução")


def imprimir_caminho(objetivo):
    if objetivo is None:
        print("Nenhuma solução encontrada.")
        return
    print("Caminho da solução:")
    for i, n in enumerate(caminho(objetivo)):
        print(f"  {i:2d}. {n.acao or 'estado inicial':<22} {n.estado}")


def gerar_dot(raiz, objetivo, arq):
    no_sol = set(id(n) for n in caminho(objetivo)) if objetivo else set()
    linhas = ["digraph G {", "  node [shape=box, fontname=Helvetica];"]

    def rec(n):
        cor = ""
        if id(n) in no_sol:
            cor = ', style=filled, fillcolor="#9be09b", penwidth=2'
        elif n.status == "repetido":
            cor = ', style=dashed, color=gray, fontcolor=gray'
        elif n.status == "limite":
            cor = ', style=dotted'
        linhas.append(f'  n{n.id} [label="{n.estado[0]},{n.estado[1]}"{cor}];')
        for f in n.filhos:
            pen = ', color="#1a7f1a", penwidth=2' if id(f) in no_sol else ""
            linhas.append(f'  n{n.id} -> n{f.id} [label="{f.acao}", fontsize=9{pen}];')
            rec(f)

    sys.setrecursionlimit(10000)
    rec(raiz)
    linhas.append("}")
    with open(arq, "w", encoding="utf-8") as fh:
        fh.write("\n".join(linhas))


def medir(func, inicial, repeticoes=2000):
    t0 = time.perf_counter()
    for _ in range(repeticoes):
        func(inicial)
    return (time.perf_counter() - t0) / repeticoes * 1e6


def executar(chave, inicial, mostrar_arvore=True, dot=None):
    nome, func = ALGORITMOS[chave]
    print("=" * 70)
    print(f"{nome}  |  estado inicial = {inicial}")
    print("=" * 70)
    raiz, obj, c = func(inicial)
    if mostrar_arvore:
        imprimir_arvore(raiz, obj)
        print()
    imprimir_caminho(obj)
    us = medir(func, inicial)
    print(f"\nNós gerados: {c.gerados} | Nós expandidos: {c.expandidos} | "
          f"Prof./custo da solução: {c.custo} | Tempo médio: {us:.1f} µs")
    if chave == "iddfs" and obj is not None:
        print(f"(limite de profundidade final = {c.limite_final})")
    if dot:
        arq = f"{dot}_{chave}.dot"
        gerar_dot(raiz, obj, arq)
        print(f"Árvore exportada para {arq}")
    print()
    return c, us


def validar(estado):
    a, b = estado
    if not (0 <= a <= CAP_A and 0 <= b <= CAP_B):
        sys.exit(f"Estado inválido: (4L) deve estar em [0,{CAP_A}] e (3L) em [0,{CAP_B}].")


def bench():
    print(f"{'Inicial':<9}{'Algoritmo':<26}{'Gerados':>8}{'Expand.':>8}{'Prof.':>6}{'Tempo (µs)':>12}")
    print("-" * 69)
    for ini in [(0, 0), (4, 0), (0, 3), (1, 2), (3, 0), (4, 3)]:
        for k, (nome, f) in ALGORITMOS.items():
            _, obj, c = f(ini)
            us = medir(f, ini, 1000)
            print(f"{str(ini):<9}{nome:<26}{c.gerados:>8}{c.expandidos:>8}{str(c.custo):>6}{us:>12.1f}")
        print()


def main():
    ap = argparse.ArgumentParser(description="Jarros d'água: BFS, DFS e IDDFS")
    ap.add_argument("a", nargs="?", type=int, default=0, help="litros no jarro de 4L")
    ap.add_argument("b", nargs="?", type=int, default=0, help="litros no jarro de 3L")
    ap.add_argument("--algo", choices=list(ALGORITMOS), help="executa apenas um algoritmo")
    ap.add_argument("--dot", metavar="PREFIXO", help="exporta a árvore em Graphviz .dot")
    ap.add_argument("--sem-arvore", action="store_true", help="não imprime a árvore completa")
    ap.add_argument("--bench", action="store_true", help="tabela comparativa")
    args = ap.parse_args()

    if args.bench:
        bench()
        return
    ini = (args.a, args.b)
    validar(ini)
    for k in ([args.algo] if args.algo else list(ALGORITMOS)):
        executar(k, ini, not args.sem_arvore, args.dot)


if __name__ == "__main__":
    main()
