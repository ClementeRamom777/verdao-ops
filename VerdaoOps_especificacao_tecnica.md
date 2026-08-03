# Verdão Ops — Especificação Técnica

> Central de dados do Palmeiras em **Python 3.13+**.
> Blueprint para o **Claude Code**: construir **bloco a bloco**, na ordem da seção 10.
> Autor: Ramom Clemente. Stack e API verificadas em **03/08/2026**.
> Nome provisório — renomear à vontade (`verdao-ops`, `central-verdao`, `palestra-data`).

---

## 1. Visão geral

Ferramenta de linha de comando que consulta dados do **Palmeiras** no Brasileirão: próximos jogos, últimos resultados e posição na tabela. Gera relatório legível no terminal e em **HTML**, mantém **cache local** para não estourar o limite da API, e pode **avisar antes das partidas**.

Projeto pessoal, mas com substância de engenharia: as três decisões da seção 7 são as mesmas que sustentariam um sistema corporativo.

---

## 2. Problema que resolve

Acompanhar time exige abrir vários sites, cada um com layout e propaganda. A informação que interessa — *quando é o próximo jogo, como terminou o último, em que posição estamos* — está espalhada.

`Verdão Ops` centraliza isso num comando só, com dados oficiais, e funciona mesmo se a API estiver fora do ar (graças ao cache).

---

## 3. Fonte de dados (API)

**football-data.org** — plano gratuito (verificado em 03/08/2026):

- Inclui **Brasileirão Série A** (entre as 12 competições do tier gratuito).
- Fornece **jogos, resultados e tabela de classificação**.
- Limite: **10 chamadas por minuto**.
- Cadastro gratuito, sem cartão, gera uma **chave de API (token)**.

Endpoints principais (confirmar na documentação ao construir):
- Partidas de um time: `/v4/teams/{id}/matches`
- Classificação da competição: `/v4/competitions/BSA/standings`

Alternativa, se precisar de dados mais ricos: **API-Football** (100 requisições/dia no plano gratuito).

> Descobrir o **ID do Palmeiras** na API é parte do Bloco 2 — não chutar, consultar.

---

## 4. Segurança: a chave de API nunca vai para o código

**Regra absoluta:** a chave de API **não pode** ser escrita dentro de um arquivo `.py`, e **não pode** ser enviada ao GitHub.

Solução adotada:
- A chave vive num arquivo **`.env`** na raiz do projeto.
- O `.env` entra no **`.gitignore`** — nunca é comitado.
- O repositório inclui um **`.env.exemplo`** com a variável vazia, mostrando o formato.
- O código lê a chave com **python-dotenv** + `os.getenv`.

```
# .env  (nunca comitar)
FOOTBALL_DATA_TOKEN=sua_chave_aqui
```

Por que isso importa no portfólio: chave vazada em repositório público é um dos erros mais comuns — e mais graves — de desenvolvedor iniciante. Demonstrar que você sabe separar **segredo** de **código** é sinal de maturidade.

---

## 5. Configuração externa (nada hardcoded)

Preferências ficam em **`config.yaml`** (ou `config.json`), fora do código:

```yaml
time_id: 1769            # ID do Palmeiras na API (confirmar)
competicao: BSA          # Brasileirao Serie A
proximos_jogos: 5        # quantos jogos futuros mostrar
ultimos_jogos: 5         # quantos resultados passados mostrar
cache_minutos: 60        # validade do cache
fuso: America/Sao_Paulo  # horarios exibidos em Brasilia
```

Trocar de time, de competição ou de quantidade **não exige tocar no código** — muda-se uma linha do arquivo. Mesmo princípio do catálogo externo: configuração é dado, não código.

---

## 6. Cache local (a restrição vira decisão técnica)

A API limita chamadas. Rodar o programa várias vezes seguidas não pode disparar uma requisição a cada vez.

Solução: **cache em arquivo** (JSON ou SQLite) com carimbo de tempo.

- Antes de chamar a API, verifica se há resposta em cache **mais nova que `cache_minutos`**.
- Se houver, usa o cache e **avisa na tela** que o dado é de cache (transparência).
- Se não houver, chama a API e grava a resposta.
- Se a API falhar (fora do ar, limite estourado, sem internet), **usa o cache antigo e avisa claramente** que está desatualizado — em vez de quebrar ou, pior, mostrar nada.

Isso é resiliência: o programa continua útil quando a dependência externa falha.

---

## 7. Decisões técnicas (vão no README, escritas pelo Ramom)

### 7.1 Segredo fora do código, configuração fora do código
Chave de API em `.env` (ignorado pelo Git) e preferências em `config.yaml`. O código não contém nem segredo nem valor fixo de negócio. Trocar time ou competição é editar configuração, não programa.

### 7.2 Falha visível, nunca silenciosa
Toda resposta da API é validada antes de usar: campo ausente, formato inesperado ou erro HTTP geram **mensagem clara** e registro em log. Quando o dado exibido vem do cache, o programa **avisa a idade dele**. O usuário nunca recebe informação errada achando que é atual.

### 7.3 Camadas separadas + logging
Cliente da API, cache, modelos, relatórios e interface de linha de comando são módulos independentes. A lógica não sabe se o dado veio da rede ou do cache — isso permite testar sem internet.

---

## 8. Stack (verificada em 03/08/2026 — confirmar versões ao construir)

- **Python 3.13+** (ambiente atual: 3.13.14).
- **requests** — chamadas HTTP. Padrão de mercado, maduro.
- **python-dotenv** — carrega o `.env`.
- **rich** — saída bonita no terminal (tabelas, cores, painéis). Faz o projeto **parecer profissional em captura de tela** — vale muito no portfólio.
- **PyYAML** — leitura do `config.yaml` (ou usar `json`, da biblioteca padrão, e dispensar dependência).
- **Jinja2** — template do relatório HTML.
- **sqlite3 / json**, **logging**, **pathlib**, **datetime**, **zoneinfo** — biblioteca padrão.

Ambiente: **venv** + `requirements.txt`.

---

## 9. Estrutura do repositório

```
verdao-ops/
├── src/
│   ├── main.py             (CLI + argparse: --proximos, --resultados, --tabela, --relatorio)
│   ├── config.py           (carrega config.yaml e valida)
│   ├── api_client.py       (chamadas HTTP + tratamento de erro)
│   ├── cache.py            (leitura/escrita e validade do cache)
│   ├── modelos.py          (dataclasses: Partida, Classificacao)
│   ├── relatorio.py        (saida no terminal com rich + HTML com Jinja2)
│   └── templates/
│       └── relatorio.html
├── .env.exemplo
├── config.yaml
├── requirements.txt
├── .gitignore              (.env, .venv/, __pycache__/, cache/)
├── LICENSE
└── README.md
```

---

## 10. Ordem de construção (blocos)

Um bloco por vez. Ao fim de cada um: reescrever à mão, explicar com as próprias palavras, e só então avançar.

- **Bloco 1 — Esqueleto e segredo.** venv, `requirements.txt`, `main.py` com `argparse`, `.env` + `.env.exemplo` + `.gitignore`, leitura da chave com python-dotenv. Testar: o programa confirma que **encontrou** a chave (sem imprimi-la).
- **Bloco 2 — Primeira chamada à API.** `api_client.py`: buscar o Palmeiras, **descobrir o ID do time**, imprimir a resposta crua. Tratar erro de rede e de autenticação.
- **Bloco 3 — Modelos + configuração.** `modelos.py` (dataclass `Partida`) e `config.py` lendo o `config.yaml`. Converter a resposta da API em objetos, com horário no fuso de Brasília.
- **Bloco 4 — Próximos jogos e resultados.** Comandos `--proximos` e `--resultados`, exibidos em tabela com **rich**.
- **Bloco 5 — Cache.** `cache.py` com validade por tempo, aviso de dado em cache e fallback quando a API falha.
- **Bloco 6 — Tabela de classificação.** Comando `--tabela`, com o Palmeiras destacado.
- **Bloco 7 — Relatório HTML + log + acabamento.** `--relatorio` gerando HTML com Jinja2, logging configurado, README completo, `.env.exemplo`, LICENSE.

**Melhoria futura:** alerta automático antes das partidas (Agendador de Tarefas do Windows chamando o script), e histórico de desempenho em gráfico.

---

## 11. Como rodar (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install requests python-dotenv rich pyyaml jinja2
pip freeze > requirements.txt

# criar o .env com a chave obtida em football-data.org
python src\main.py --proximos
python src\main.py --tabela
python src\main.py --relatorio
```

---

## 12. README (estrutura)

1. Título + uma frase.
2. Print do terminal (com `rich`, fica bonito — vale muito).
3. Como rodar e como obter a chave de API.
4. **Decisões técnicas** — as três da seção 7, nas palavras do Ramom.
5. **Processo (transparência sobre IA)**:
   > Código inicial gerado com IA (Claude Code), depois reescrito à mão e revisado bloco a bloco até eu conseguir explicar cada parte sem consultar. As decisões de design foram minhas.
6. Melhorias futuras.

---

## 13. Critérios de aceite

- [ ] A chave nunca aparece no código nem no histórico do Git.
- [ ] Rodar sem internet usa o cache e **avisa** que o dado está velho.
- [ ] Trocar o time no `config.yaml` muda o resultado **sem tocar no código**.
- [ ] Erro da API gera mensagem clara, não travamento.
- [ ] Horários exibidos no fuso de Brasília.
- [ ] README com as três decisões e a transparência sobre IA.
- [ ] Ramom explica cada bloco de memória, com o arquivo fechado.
