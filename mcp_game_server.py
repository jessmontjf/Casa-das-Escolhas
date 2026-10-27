"""Servidor MCP do jogo: guarda o estado do mundo e expõe as ferramentas que o
'Arquiteto' (o LLM) usa para montar as salas, registrar escolhas e criar o final.

O palpite do Arquiteto SEMPRE vai para o meio. O jogador não sabe disso.
"""
import json
import random
from typing import Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

import content as C

mcp = FastMCP("casa-das-escolhas", log_level="WARNING")

Shape = Literal[tuple(C.SHAPES)]
Frame = Literal[tuple(C.FRAMES)]
Trait = Literal[tuple(C.TRAITS)]
Theme = Literal[tuple(C.THEMES)]


class ItemIn(BaseModel):
    name: str = Field(description="Nome do item, 2 a 4 palavras, em português")
    phrase: str = Field(description="Legenda: UMA frase curta e poética (até ~80 caracteres)")
    shape: Shape = Field(description="Forma desenhada do item")
    color: str = Field(description="Cor principal em hex, ex: #c0392b")
    glow: str = Field(description="Cor do brilho em hex (mais clara que a principal)")
    frame: Frame = Field(description="Estilo da moldura da caixa de legenda")
    trait: Trait = Field(description="Traço de personalidade que o item representa")
    theme: Theme = Field(description="Sala que este item inspiraria se fosse escolhido")


MAX_ROUNDS = 5
STATE = {"round": 0, "max_rounds": MAX_ROUNDS, "room": None,
         "history": [], "used_names": [], "final": None}


def _item(d, rid, k):
    d = C.normalize_item(d)
    d["id"] = f"r{rid}_{k}"
    return d


def _set_room(theme, intro, predicted, others, reasoning):
    rid = STATE["round"] + 1
    left, right = others[0], others[1]
    if random.random() < 0.5:
        left, right = right, left
    items = [_item(left, rid, 0), _item(predicted, rid, 1), _item(right, rid, 2)]
    STATE["used_names"] += [i["name"] for i in items]
    STATE["room"] = {
        "number": rid,
        "theme": theme if theme in C.THEMES else "cripta",
        "intro": (intro or "").strip()[:140],
        "items": items,
        "prediction_id": items[1]["id"],
        "reasoning": reasoning,
    }


def _set_final(item, title, text):
    hist = STATE["history"]
    STATE["final"] = {
        "item": _item(item, 6, 0),
        "title": title.strip()[:60],
        "text": text.strip()[:600],
        "percentages": C.trait_percentages(hist),
        "hits": sum(1 for r in hist if r["hit"]),
        "rounds": len(hist),
    }


@mcp.tool()
def get_state() -> str:
    """Estado atual do jogo (rodada, sala atual, histórico, final)."""
    return json.dumps(STATE, ensure_ascii=False)


@mcp.tool()
def get_history() -> str:
    """Tudo o que se sabe sobre o comportamento do jogador até agora."""
    hist = STATE["history"]
    pos_count = {p: sum(1 for r in hist if r["chosen_position"] == p) for p in C.POS}
    summary = {
        "next_round": STATE["round"] + 1,
        "max_rounds": STATE["max_rounds"],
        "rounds": hist,
        "hits_so_far": sum(1 for r in hist if r["hit"]),
        "chosen_positions": pos_count,
        "trait_scores": {k: round(v, 2) for k, v in C.trait_scores(hist).items()},
        "last_chosen_item": hist[-1]["chosen"] if hist else None,
        "used_names": STATE["used_names"],
    }
    return json.dumps(summary, ensure_ascii=False)


@mcp.tool()
def build_room(theme: Theme, intro: str, predicted: ItemIn, others: list[ItemIn],
               reasoning: str = "") -> str:
    """Monta a PRÓXIMA sala. `predicted` é o seu palpite do item que o jogador vai
    escolher (fica no meio). `others` são exatamente 2 itens tentadores (laterais).
    Os 3 itens precisam ter `trait` diferentes e nomes inéditos."""
    if STATE["round"] >= STATE["max_rounds"]:
        raise ValueError("As salas acabaram; use build_ending.")
    if len(others) != 2:
        raise ValueError("`others` precisa ter exatamente 2 itens.")
    items = [predicted, *others]
    if len({i.trait for i in items}) < 3:
        raise ValueError("Os três itens precisam ter `trait` diferentes.")
    hist = STATE["history"]
    if hist and theme == hist[-1]["theme"]:
        raise ValueError(f"A sala anterior já era '{theme}'. Escolha outro theme.")
    used = {n.lower() for n in STATE["used_names"]}
    dup = [i.name for i in items if i.name.strip().lower() in used]
    if dup:
        raise ValueError(f"Nomes já usados: {dup}. Invente outros.")
    _set_room(theme, intro, predicted.model_dump(), [o.model_dump() for o in others], reasoning)
    return "Sala pronta."


@mcp.tool()
def auto_room() -> str:
    """Monta a próxima sala com a previsão local (sem LLM)."""
    d = C.auto_room(STATE["history"], STATE["used_names"])
    _set_room(d["theme"], d["intro"], d["predicted"], d["others"], d["reasoning"])
    return "Sala pronta (modo local)."


@mcp.tool()
def record_choice(chosen_id: str, inspect_seconds: dict[str, float] | None = None,
                  inspect_counts: dict[str, int] | None = None,
                  decision_seconds: float = 0.0) -> str:
    """Registra o item escolhido e os sinais de comportamento da sala."""
    room = STATE["room"]
    if not room:
        raise ValueError("Não há sala ativa.")
    ids = [i["id"] for i in room["items"]]
    if chosen_id not in ids:
        raise ValueError(f"Item desconhecido: {chosen_id}")
    secs, counts = inspect_seconds or {}, inspect_counts or {}
    pos = ids.index(chosen_id)
    chosen = room["items"][pos]
    rec = {
        "round": room["number"],
        "theme": room["theme"],
        "options": [
            {"name": it["name"], "trait": it["trait"], "shape": it["shape"],
             "position": C.POS[k], "predicted": it["id"] == room["prediction_id"],
             "seconds": round(float(secs.get(it["id"], 0)), 1),
             "times": int(counts.get(it["id"], 0))}
            for k, it in enumerate(room["items"])
        ],
        "chosen": chosen,
        "chosen_position": C.POS[pos],
        "hit": chosen_id == room["prediction_id"],
        "decision_seconds": round(float(decision_seconds), 1),
        "your_reasoning_then": room.get("reasoning", ""),
    }
    STATE["history"].append(rec)
    STATE["round"] += 1
    STATE["room"] = None
    return json.dumps({"hit": rec["hit"], "round": STATE["round"]})


@mcp.tool()
def build_ending(final_item: ItemIn, title: str, text: str) -> str:
    """Cria o final: o item que espera o jogador no campo (o seu palpite para uma
    6ª escolha) e o resultado estilo 'teste de personalidade'."""
    if STATE["round"] < STATE["max_rounds"]:
        raise ValueError("Ainda faltam salas.")
    if final_item.name.strip().lower() in {n.lower() for n in STATE["used_names"]}:
        raise ValueError("O item final precisa ser inédito.")
    _set_final(final_item.model_dump(), title, text)
    return "Final pronto."


@mcp.tool()
def auto_ending() -> str:
    """Cria o final com a lógica local (sem LLM)."""
    d = C.auto_ending(STATE["history"], STATE["used_names"])
    _set_final(d["final_item"], d["title"], d["text"])
    return "Final pronto (modo local)."


@mcp.tool()
def reset() -> str:
    """Começa do zero (novo jogo)."""
    STATE.update({"round": 0, "max_rounds": MAX_ROUNDS, "room": None,
                  "history": [], "used_names": [], "final": None})
    return "ok"


@mcp.tool()
def load_state(state_json: str) -> str:
    """Restaura um jogo salvo."""
    d = json.loads(state_json)
    reset()
    for k in ("round", "room", "history", "used_names", "final"):
        if k in d:
            STATE[k] = d[k]
    return "ok"


if __name__ == "__main__":
    mcp.run()  # stdio
