"""O 'Arquiteto': Claude (LLM) + cliente MCP num thread com asyncio, para não
travar o loop do pygame. Sem ANTHROPIC_API_KEY, usa a previsão local do servidor."""
import asyncio
import json
import os
import sys
import threading

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
DEBUG = os.getenv("DEBUG_IA") == "1"

ARCHITECT = """Você é o Arquiteto invisível de um jogo. O jogador entra numa casa 5 vezes e,
em cada uma, escolhe 1 entre 3 itens mágicos. Cada sala nasce da escolha anterior.

Seu objetivo secreto: PREVER qual item o jogador vai escolher. O item que você prevê
vai no campo `predicted` e sempre aparece NO MEIO. Os outros dois (`others`) ficam nas laterais.

Regras:
- O jogador NÃO pode perceber que está sendo estudado. Ele deve achar que é coincidência.
  Nunca cite escolhas passadas nas frases ("de novo", "como antes", "você gosta de...").
- Os itens laterais precisam ser tentadores de verdade (nunca sabote). Use-os para aprender:
  um testando a 2ª tendência mais forte, outro explorando algo pouco testado.
- Os três itens têm `trait` diferentes. Nomes inéditos (veja used_names).
- O `theme` da sala nasce do último item escolhido (o `theme` daquele item é a sugestão
  mais forte, mas pode interpretar). Nunca repita o theme da sala anterior. Na primeira sala, escolha livremente.
- `intro`: uma frase curta de ambientação da sala, sem falar do jogador.
- `phrase`: legenda do item, uma frase curta, poética e um pouco misteriosa (até ~80
  caracteres), em português do Brasil.
- `color`/`glow` em hex; `glow` mais claro. `frame` e `shape` combinando com o item.
- Use os sinais: tempo examinando cada item (seconds), quantas vezes voltou nele (times),
  quanto demorou pra decidir e se escolheu o meio (hit). Se ele vem fugindo do meio,
  ele pode estar desconfiando: faça o palpite parecer menos óbvio.
- `reasoning`: 1 frase com o seu raciocínio (o jogador não vê)."""

ROOM_TASK = ("Monte a próxima sala chamando build_room. `predicted` é o seu palpite "
             "do item que o jogador vai escolher.")

ENDING_TASK = """As 5 escolhas acabaram. Chame build_ending com:
- final_item: o item que você acha que ele escolheria numa 6ª rodada. Ele vai aparecer
  sozinho num canto do campo, esperando por ele. Inédito.
- title: nome de arquétipo, no estilo resultado de teste de personalidade
  (ex.: "O Guardião de Lanternas").
- text: 3 a 4 frases em segunda pessoa, calorosas e certeiras, baseadas nos traços e no
  comportamento (pode citar que demorou, que voltou atrás...). Não revele que você
  previa as escolhas."""


def _inline_refs(schema):
    defs = schema.get("$defs", {})

    def walk(node):
        if isinstance(node, dict):
            if "$ref" in node:
                return walk(defs[node["$ref"].split("/")[-1]])
            return {k: walk(v) for k, v in node.items() if k != "$defs"}
        if isinstance(node, list):
            return [walk(x) for x in node]
        return node

    return walk(schema)


class GameAgent:
    def __init__(self):
        self.llm = None
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                from anthropic import AsyncAnthropic
                self.llm = AsyncAnthropic()
            except Exception as e:  # noqa: BLE001
                print("[IA] anthropic indisponível:", e)
        print(f"[IA] modo: {'Claude (' + MODEL + ')' if self.llm else 'local (sem API key)'}")

        self.tools, self.session, self.error = {}, None, None
        self.ready = threading.Event()
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self._main_future = asyncio.run_coroutine_threadsafe(self._main(), self.loop)
        if not self.ready.wait(timeout=30) or self.error:
            raise RuntimeError(f"Falha ao iniciar o servidor MCP: {self.error}")

    # ---------- conexão MCP (uma task longa, abre e fecha no mesmo lugar) ----------
    async def _main(self):
        self.stop = asyncio.Event()
        try:
            here = os.path.dirname(os.path.abspath(__file__))
            params = StdioServerParameters(
                command=sys.executable,
                args=[os.path.join(here, "mcp_game_server.py")],
                cwd=here,
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    for t in (await session.list_tools()).tools:
                        self.tools[t.name] = {
                            "name": t.name,
                            "description": t.description or "",
                            "input_schema": _inline_refs(t.inputSchema),
                        }
                    self.session = session
                    self.ready.set()
                    await self.stop.wait()
        except Exception as e:  # noqa: BLE001
            self.error = e
            self.ready.set()

    async def _call(self, name, args=None):
        out = await self.session.call_tool(name, args or {})
        text = "".join(c.text for c in out.content if getattr(c, "type", "") == "text")
        return text, bool(out.isError)

    async def _state(self):
        text, _ = await self._call("get_state")
        return json.loads(text)

    # ---------- o LLM decide, o MCP aplica no mundo ----------
    async def _llm_build(self, tool_name, task):
        if not self.llm:
            return False
        try:
            return await asyncio.wait_for(self._llm_build_inner(tool_name, task), timeout=60)
        except Exception as e:  # noqa: BLE001
            print(f"[IA] falhou ({e!r}); usando modo local.")
            return False

    async def _llm_build_inner(self, tool_name, task):
        hist, _ = await self._call("get_history")
        messages = [{"role": "user", "content": f"{task}\n\nDADOS DO JOGADOR (JSON):\n{hist}"}]
        for _ in range(3):
            resp = await self.llm.messages.create(
                model=MODEL,
                max_tokens=1500,
                system=ARCHITECT,
                tools=[self.tools[tool_name]],
                tool_choice={"type": "tool", "name": tool_name},
                messages=messages,
            )
            use = next((b for b in resp.content if b.type == "tool_use"), None)
            if use is None:
                return False
            text, err = await self._call(tool_name, use.input)
            if not err:
                return True
            if DEBUG:
                print("[IA] ferramenta recusou:", text)
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": use.id, "content": text, "is_error": True}
            ]})
        return False

    async def _make_room(self):
        if not await self._llm_build("build_room", ROOM_TASK):
            await self._call("auto_room")
        st = await self._state()
        if DEBUG and st["room"]:
            r = st["room"]
            print(f"[IA] sala {r['number']} ({r['theme']}): palpite = {r['items'][1]['name']}"
                  f" | {r['reasoning']}")
        return st

    async def _prepare_room(self):
        return await self._make_room()

    async def _choose(self, chosen_id, secs, counts, decision):
        out, _ = await self._call("record_choice", {
            "chosen_id": chosen_id, "inspect_seconds": secs,
            "inspect_counts": counts, "decision_seconds": decision,
        })
        if DEBUG:
            print("[IA] escolha registrada:", out)
        st = await self._state()
        if st["round"] < st["max_rounds"]:
            return await self._make_room()
        if not await self._llm_build("build_ending", ENDING_TASK):
            await self._call("auto_ending")
        return await self._state()

    async def _ensure(self):
        """Garante que existe uma sala pronta (ou o final, depois da 5ª escolha)."""
        st = await self._state()
        if st["round"] < st["max_rounds"]:
            return st if st["room"] else await self._make_room()
        if not st["final"]:
            if not await self._llm_build("build_ending", ENDING_TASK):
                await self._call("auto_ending")
        return await self._state()

    def _sync(self, coro, timeout=10):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout=timeout)

    def ensure(self):
        return asyncio.run_coroutine_threadsafe(self._ensure(), self.loop)

    def reset(self):
        self._sync(self._call("reset"))

    def load(self, state):
        self._sync(self._call("load_state", {"state_json": json.dumps(state, ensure_ascii=False)}))

    # ---------- API síncrona pro jogo (devolve Futures) ----------
    def prepare_room(self):
        return asyncio.run_coroutine_threadsafe(self._prepare_room(), self.loop)

    def choose(self, chosen_id, inspect_seconds, inspect_counts, decision_seconds):
        return asyncio.run_coroutine_threadsafe(
            self._choose(chosen_id, inspect_seconds, inspect_counts, decision_seconds), self.loop)

    def get_state(self):
        return asyncio.run_coroutine_threadsafe(self._state(), self.loop).result(timeout=10)

    def close(self):
        try:
            self.loop.call_soon_threadsafe(self.stop.set)
            self._main_future.result(timeout=3)
        except Exception:  # noqa: BLE001
            pass
