"""Catálogo de itens, validação e o 'Arquiteto offline' (previsão local, sem LLM).

Usado pelo servidor MCP. Se não houver ANTHROPIC_API_KEY (ou o LLM falhar),
o jogo continua funcionando com essa lógica aqui.
"""
import random
import re

TRAITS = ["coragem", "curiosidade", "cuidado", "liberdade", "ambicao", "misterio"]
TRAIT_LABEL = {
    "coragem": "Coragem", "curiosidade": "Curiosidade", "cuidado": "Cuidado",
    "liberdade": "Liberdade", "ambicao": "Ambição", "misterio": "Mistério",
}
SHAPES = ["orbe", "cristal", "chave", "pena", "frasco", "livro", "espada", "flor",
          "anel", "lanterna", "estrela", "concha", "ampulheta", "coracao", "mascara", "bussola"]
FRAMES = ["runas", "vinhas", "estrelas", "chamas", "ondas", "engrenagens", "espinhos", "nuvens"]
THEMES = ["biblioteca", "floresta", "forja", "oceano", "ceu", "cripta", "jardim", "tesouro"]
POS = ["esquerda", "meio", "direita"]


def _it(name, phrase, shape, color, glow, frame, trait, theme):
    return dict(name=name, phrase=phrase, shape=shape, color=color, glow=glow,
                frame=frame, trait=trait, theme=theme)


CATALOG = [
    # coragem
    _it("Espada de Brasa", "Ela só esquenta quando você hesita.", "espada", "#c0392b", "#ffa45c", "chamas", "coragem", "forja"),
    _it("Coração de Ferro", "Bate mais forte quando todo mundo foge.", "coracao", "#8e9aa6", "#ff7b7b", "engrenagens", "coragem", "forja"),
    _it("Estrela Cadente Domada", "Caiu do céu e decidiu ficar com quem não teve medo.", "estrela", "#f5b324", "#fff1a8", "estrelas", "coragem", "ceu"),
    _it("Lanterna do Primeiro Passo", "Ilumina só o próximo passo. Nunca o caminho inteiro.", "lanterna", "#d9772b", "#ffd27a", "chamas", "coragem", "floresta"),
    # curiosidade
    _it("Livro Sem Final", "Toda vez que você abre, ele tem uma página a mais.", "livro", "#2e6fd0", "#9fd3ff", "runas", "curiosidade", "biblioteca"),
    _it("Bússola Curiosa", "Não aponta pro norte. Aponta pra pergunta.", "bussola", "#b08d57", "#ffe7a3", "engrenagens", "curiosidade", "biblioteca"),
    _it("Frasco de Por Quês", "Dizem que tem uma resposta lá dentro. Ninguém conseguiu provar.", "frasco", "#8e44ad", "#e3b5ff", "runas", "curiosidade", "biblioteca"),
    _it("Concha que Escuta", "Encoste no ouvido: ela conta o que o mar esqueceu.", "concha", "#f19cb0", "#ffe3f0", "ondas", "curiosidade", "oceano"),
    # cuidado
    _it("Flor que Não Murcha", "Floresce um pouco mais cada vez que alguém é gentil.", "flor", "#ff6fae", "#ffd1e8", "vinhas", "cuidado", "jardim"),
    _it("Anel de Promessa", "Não pesa nada. Até você quebrar a promessa.", "anel", "#d4af37", "#fff0a0", "vinhas", "cuidado", "jardim"),
    _it("Pena de Ninho", "Caiu de um ninho onde nunca faltou abrigo.", "pena", "#e8d9bd", "#fffaf0", "nuvens", "cuidado", "floresta"),
    _it("Frasco de Chá Morno", "Nunca esfria. Nunca queima. Sempre na medida.", "frasco", "#c97b3d", "#ffd9a8", "vinhas", "cuidado", "jardim"),
    # liberdade
    _it("Pena do Vento Norte", "Quem a segura nunca mais pergunta 'posso?'.", "pena", "#6cc5df", "#e0fbff", "nuvens", "liberdade", "ceu"),
    _it("Chave de Lugar Nenhum", "Abre qualquer porta. Inclusive as que você ainda não imaginou.", "chave", "#a9a9cf", "#ffffff", "nuvens", "liberdade", "ceu"),
    _it("Concha do Horizonte", "Dentro dela, o mar não tem fim.", "concha", "#3dbfa5", "#b8fff0", "ondas", "liberdade", "oceano"),
    _it("Orbe de Céu Aberto", "Tem uma nuvem presa lá dentro. Ela parece feliz.", "orbe", "#4f9fd8", "#ffffff", "nuvens", "liberdade", "ceu"),
    # ambição
    _it("Anel do Rei Esquecido", "Serve em qualquer dedo que se ache digno.", "anel", "#f1c40f", "#fff3a0", "estrelas", "ambicao", "tesouro"),
    _it("Cristal de Mil Faces", "Cada face mostra uma versão maior de você.", "cristal", "#9b59b6", "#f5c6ff", "espinhos", "ambicao", "tesouro"),
    _it("Ampulheta de Ouro", "O tempo corre diferente pra quem tem pressa de chegar.", "ampulheta", "#c9a227", "#ffe9a0", "engrenagens", "ambicao", "tesouro"),
    _it("Estrela da Coroação", "Não brilha pra todo mundo. Só pra quem chega no topo.", "estrela", "#ef8f12", "#ffe08a", "espinhos", "ambicao", "tesouro"),
    # mistério
    _it("Máscara Sem Rosto", "Quem a usa vê tudo. Ninguém vê quem a usa.", "mascara", "#3b4a63", "#b3a6ff", "runas", "misterio", "cripta"),
    _it("Orbe da Meia-Noite", "Mostra o que você vai sonhar amanhã.", "orbe", "#3a2a78", "#b28dff", "estrelas", "misterio", "cripta"),
    _it("Ampulheta Invertida", "A areia sobe. Ninguém sabe pra onde.", "ampulheta", "#5b4b8a", "#c8b6ff", "runas", "misterio", "cripta"),
    _it("Cristal Sussurrante", "Às vezes ele sabe seu nome antes de você dizer.", "cristal", "#17a589", "#b3fff0", "espinhos", "misterio", "floresta"),
]

# salas "parentes" de cada traço, usadas quando o tema sugerido repetiria a sala anterior
TRAIT_THEMES = {
    "coragem": ["forja", "floresta", "ceu"], "curiosidade": ["biblioteca", "oceano", "cripta"],
    "cuidado": ["jardim", "floresta", "oceano"], "liberdade": ["ceu", "oceano", "floresta"],
    "ambicao": ["tesouro", "forja", "ceu"], "misterio": ["cripta", "floresta", "biblioteca"],
}

# itens exclusivos do final (o que espera o jogador no campo)
FINAL_ITEMS = {
    "coragem": _it("Brasa do Último Passo", "Ela nunca se apaga. Só espera você decidir.", "lanterna", "#e2582b", "#ffc07a", "chamas", "coragem", "forja"),
    "curiosidade": _it("Chave da Última Pergunta", "Abre a única porta que você ainda não viu.", "chave", "#3f7fd8", "#bfe4ff", "runas", "curiosidade", "biblioteca"),
    "cuidado": _it("Semente Guardada", "Cresce na velocidade de quem cuida dela.", "flor", "#f27cb4", "#ffe0ef", "vinhas", "cuidado", "jardim"),
    "liberdade": _it("Pena Sem Gaiola", "Não pertence a ninguém. Por isso veio até você.", "pena", "#79d4ef", "#f0fdff", "nuvens", "liberdade", "ceu"),
    "ambicao": _it("Estrela Que Já Era Sua", "Sempre esteve aqui. Só faltava você chegar.", "estrela", "#f2b51b", "#fff2b0", "estrelas", "ambicao", "tesouro"),
    "misterio": _it("Espelho Que Sabe", "Mostra quem você é quando ninguém está olhando.", "orbe", "#4b3a8f", "#d3c2ff", "runas", "misterio", "cripta"),
}

THEME_INTROS = {
    "biblioteca": ["Cheiro de papel velho e de perguntas sem resposta.", "As estantes parecem se inclinar pra ouvir."],
    "floresta": ["Raízes atravessam o chão como se a casa tivesse crescido aqui.", "Vaga-lumes desenham caminhos que somem."],
    "forja": ["O ar é quente e o metal canta baixinho.", "Faíscas sobem como se tivessem pressa."],
    "oceano": ["A sala respira devagar, como maré.", "Bolhas sobem carregando segredos pequenos."],
    "ceu": ["O teto sumiu. Sobrou o céu inteiro.", "Você pisa em nuvens e elas não reclamam."],
    "cripta": ["Velas acesas por ninguém. Silêncio de quem guarda algo.", "As sombras aqui parecem educadas demais."],
    "jardim": ["Tudo aqui cresce devagar e com carinho.", "Borboletas fazem fila pra passar pela janela."],
    "tesouro": ["Ouro até onde a vista alcança. E ainda parece pouco.", "Moedas tilintam sozinhas quando você entra."],
}

ARCHETYPES = {
    "coragem": ("A Chama que Não Pede Licença",
                "Você é do tipo que entra primeiro e pensa no caminho depois — e, curiosamente, quase sempre dá certo. Quando o resto hesita, alguma coisa em você acende."),
    "curiosidade": ("O Cartógrafo de Perguntas",
                    "Você não escolhe coisas; escolhe mistérios pra abrir. Uma resposta, pra você, nunca é o fim: é só a porta da próxima pergunta."),
    "cuidado": ("O Guardião das Coisas Pequenas",
                "Você repara no que os outros deixam passar: a flor torta, o amigo quieto, o chá esfriando. O mundo fica mais macio por onde você passa."),
    "liberdade": ("O Vento que Ninguém Segura",
                  "Portas abertas te chamam mais do que tesouros trancados. Você precisa de espaço pra respirar — e de um horizonte que não termine."),
    "ambicao": ("O Coroado Antes da Coroa",
                "Você enxerga a versão maior das coisas — e de si. Não é vaidade: você só não consegue mirar baixo."),
    "misterio": ("A Sombra que Sabe Demais",
                 "Você gosta do que está escondido, do que não se explica fácil. E, sejamos sinceros, você também prefere não se explicar fácil."),
}
SECOND_LINE = {
    "coragem": "quando precisa, você não recua.",
    "curiosidade": "você sempre quer ver o que tem atrás da próxima porta.",
    "cuidado": "no fundo, você escolhe pensando em alguém.",
    "liberdade": "nada te prende por muito tempo.",
    "ambicao": "você sabe exatamente o quanto vale.",
    "misterio": "tem uma parte sua que ninguém viu ainda.",
}


# ---------------------------------------------------------------- validação
def _hex(v, default):
    v = str(v or "").strip()
    if not v.startswith("#"):
        v = "#" + v
    return v.lower() if re.fullmatch(r"#[0-9a-fA-F]{6}", v) else default


def normalize_item(d):
    d = dict(d or {})
    return {
        "name": (str(d.get("name") or "Item Sem Nome").strip())[:40],
        "phrase": (str(d.get("phrase") or "...").strip())[:120],
        "shape": d.get("shape") if d.get("shape") in SHAPES else "orbe",
        "frame": d.get("frame") if d.get("frame") in FRAMES else "estrelas",
        "trait": d.get("trait") if d.get("trait") in TRAITS else "misterio",
        "theme": d.get("theme") if d.get("theme") in THEMES else "cripta",
        "color": _hex(d.get("color"), "#9b59b6"),
        "glow": _hex(d.get("glow"), "#ffffff"),
    }


# ---------------------------------------------------------------- previsão local
def trait_scores(history):
    """Pontua cada traço: escolhas pesam muito; tempo examinando e voltar a
    examinar pesam pouco. Rodadas recentes valem mais."""
    s = {t: 0.0 for t in TRAITS}
    for i, rec in enumerate(history):
        w = 1 + 0.25 * i
        for o in rec["options"]:
            s[o["trait"]] += w * min(o["seconds"], 8) / 4
            if o["times"] > 1:
                s[o["trait"]] += w * 0.3 * (o["times"] - 1)
        s[rec["chosen"]["trait"]] += 3 * w
    return s


def trait_percentages(history):
    s = trait_scores(history)
    total = sum(s.values()) or 1
    return {t: round(v / total * 100) for t, v in s.items()}


def _pick_item(trait, used, rng, taken=()):
    """Item inédito do traço pedido; se o traço esgotou, um inédito de outro traço."""
    pool = [it for it in CATALOG if it["trait"] == trait and it["name"].lower() not in used]
    if not pool:
        pool = [it for it in CATALOG if it["name"].lower() not in used and it["trait"] not in taken]
    if not pool:
        pool = [it for it in CATALOG if it["trait"] == trait]
    item = dict(rng.choice(pool))
    used.add(item["name"].lower())
    return item


def auto_room(history, used_names, rng=random):
    used = {n.lower() for n in used_names}
    scores = trait_scores(history)
    order = TRAITS[:]
    rng.shuffle(order)
    order.sort(key=lambda t: scores[t], reverse=True)
    predicted, second = order[0], order[1]
    # terceiro: explorar o traço que menos apareceu até agora
    offered = {t: 0 for t in TRAITS}
    for rec in history:
        for o in rec["options"]:
            offered[o["trait"]] += 1
    rest = order[2:]
    rng.shuffle(rest)
    third = min(rest, key=lambda t: offered[t])
    items, taken = [], set()
    for t in (predicted, second, third):
        it = _pick_item(t, used, rng, taken)
        taken.add(it["trait"])
        items.append(it)
    theme = next_theme(history) if history else rng.choice(THEMES)
    return {
        "theme": theme,
        "intro": rng.choice(THEME_INTROS[theme]),
        "predicted": items[0],
        "others": items[1:],
        "reasoning": f"(local) '{predicted}' tem a maior pontuação ({scores[predicted]:.1f}).",
    }


def next_theme(history):
    """Sala nasce do último item escolhido, mas nunca repete a sala anterior."""
    last = history[-1]
    cands = [last["chosen"]["theme"]] + TRAIT_THEMES[last["chosen"]["trait"]] + THEMES
    return next(t for t in cands if t != last["theme"])


def auto_ending(history, used_names, rng=random):
    used = {n.lower() for n in used_names}
    scores = trait_scores(history)
    order = sorted(TRAITS, key=lambda t: scores[t], reverse=True)
    top, second = order[0], order[1]
    title, text = ARCHETYPES[top]
    text = f"{text} Mas tem um traço de {TRAIT_LABEL[second].lower()} aí também: {SECOND_LINE[second]}"
    return {"final_item": dict(FINAL_ITEMS[top]), "title": title, "text": text}


# ---------------------------------------------------------------- roupas (3 x 3 x 3 = 27)
TOPS = [
    {"name": "Moletom Azul + Manga Longa", "color": "#4a70b2", "style": "hoodie_blue"},
    {"name": "Polo Listrada", "color": "#e2a096", "style": "rugby"},
    {"name": "Jaqueta Cinza de Zíper", "color": "#b0acac", "style": "zip_grey"},
]
BOTTOMS = [
    {"name": "Bermuda Jeans Larga", "color": "#2e3a5c", "style": "denim_shorts"},
    {"name": "Short de Moletom", "color": "#a8a6aa", "style": "sweat_shorts"},
    {"name": "Calça Esportiva Larga", "color": "#484850", "style": "track_pants"},
]
SHOES = [
    {"name": "Tênis Marinho + Meia", "color": "#2c3450", "style": "navy_sneaker"},
    {"name": "Mocassim + Meião", "color": "#1e1a1e", "style": "loafer"},
    {"name": "Tênis Bordô", "color": "#8a2832", "style": "burgundy_sneaker"},
]
