# A Casa das Escolhas (pygame + Claude + MCP)

Um RPG curtinho, em tons quentes e pastéis. Fluxo completo:

1. **Caixa de correio**: as cartas voam e se abrem, e cada papel vira uma opção.
   - Acordar: abre as 3 cartas de save.
   - Opções: volume de música e de efeitos, janela ou tela cheia.
   - Sair.
2. **Nome**: as letras balançam, e a selecionada sobe.
3. **Introdução**: ele dormindo, abrindo os olhos, e depois sentado na cama às 6h. Z, X, Enter ou → passam os quadros.
4. **Quarto**: banho e depois guarda-roupa (3×3×3 = 27 combinações). Não dá pra sair antes.
5. **Corredor**: o quarto da mãe fica trancado e há itens com os quais dá pra interagir.
6. **Térreo**: cozinha (lembrança da mãe + 3 tarefinhas de café da manhã), sala, entrada e quintal.
7. **Bairro**: vizinhos e um cachorro, até chegar ao campo.
8. **A casa no campo**: 5 escolhas. O "Arquiteto" (Claude) tenta prever cada escolha e põe o palpite no meio.
9. **Final**: se aceitar o item, vem o resultado de teste de personalidade. Se recusar, aparece um gato com um sininho e o jogo fecha.

## Visual em pixel art
- Tudo é desenhado numa grade de **3 px por pixel** (`pixel.py`). Os sprites (personagens, itens, árvores, pedras, mãos) são feitos em tamanho pequeno, ganham contorno de 1 px e são ampliados sem suavizar.
- A grama segue a técnica: base → manchas escuras → tufos → florzinhas. As pedras seguem: base → rachaduras → luz → musgo → contorno.
- As mãos da tela do item foram adaptadas da foto de referência: sobem de baixo abertas e, ao apertar Enter, fecham no item.
- Fonte pixel: **Pixelify Sans** (licença OFL, em `assets/fonts/`, junto com o `OFL.txt`).
- **Efeito TV (CRT)**: em Opções (ou na pausa), com linhas de varredura, máscara RGB, brilho e moldura de TV. Vem ligado por padrão.

## Rodando no VS Code
```
python -m venv .venv
.venv\Scripts\activate            # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt   # usa pygame-ce
python game.py                    # ou F5
```
A `ANTHROPIC_API_KEY` é opcional. Sem ela, o jogo usa a previsão local. Use `DEBUG_IA=1` para ver os palpites da IA no terminal.

## Controles
- Setas/WASD: andar.
- E, Z, Espaço ou Enter: interagir e confirmar.
- X: voltar ou apagar.
- Esc: pausa.
- F11: tela cheia.
- Mouse: funciona nos menus.

## Arquivos
| arquivo | o que faz |
|---|---|
| `game.py` | App: troca de cenas, saves (`saves/cartaN.json`), opções (`settings.json`) |
| `scene_menu.py` | caixa de correio, cartas, saves e opções |
| `scene_name.py` | escolha do nome |
| `scene_home.py` | introdução, quarto, guarda-roupa, corredor, térreo |
| `minigames.py` | omelete, café com leite, pão com manteiga |
| `scene_street.py` | bairro e vizinhos |
| `scene_choices.py` | a casa do campo e os finais |
| `world.py` / `ui.py` | movimento, pontos de interação, balões, diálogos, quadros, pausa |
| `art.py` / `art_home.py` | todo o desenho procedural (personagem em camadas, cenários, quadros) |
| `audio.py` / `fx.py` | sons e música gerados por código; efeitos de "se desfazer" |
| `assets.py` | carrega suas sprites, se existirem |
| `llm_agent.py` / `mcp_game_server.py` / `content.py` | o Arquiteto (Claude + MCP), o catálogo de itens e as roupas |

## Usando suas sprites
Coloque PNGs em `assets/`. Se um arquivo existe, ele substitui o desenho feito por código.

- **Cenários:** `bg_correio`, `bg_quarto`, `bg_corredor`, `bg_terreo` (960×640) e `bg_bairro` (3200×640).
- **Quadros da história:** `cut_dormindo`, `cut_acordando`, `cut_sentado`, `cut_banho`, `cut_pronto`, `cut_lembranca`, `cut_cafe`, `cut_satisfeito` (960×640).
- **Protagonista:** `player_idle_down`, `player_walk_down`, e o mesmo para `up`, `left` e `right`. São tiras horizontais de quadros.
- **Quantidade de quadros e velocidade:** se precisar, defina em `assets/manifest.json`, por exemplo `{"player_walk_down": {"frames": 4, "fps": 8}}`.
- **Música:** `assets/music/tema.ogg`.

Como as roupas mudam (27 combinações), o ideal é desenhar as sprites do protagonista em camadas: corpo, parte de cima, parte de baixo e sapatos. Quando você mandar as suas, eu ajusto o encaixe.
