# Ollama-MCP Filesystem Orchestrator

> **Progetto chiuso — agosto 2026.** Non è mai stato implementato, e non lo
> sarà: fra la specifica e oggi, l'ecosistema ha assorbito ogni componente
> prevista. Questo repository resta pubblico come registro della decisione e
> degli spike che l'hanno motivata.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Cosa doveva essere

Un orchestratore Python che permettesse a modelli Ollama locali di accedere al
filesystem in sicurezza tramite MCP: nove tool filesystem, loop agentico ReAct,
sandbox sui path, conferme per le operazioni distruttive, audit JSONL. La
specifica è di gennaio 2026 ed è completa — nove documenti di requisiti,
architettura, threat model, WBS in 15 attività.

Il codice scritto è di 61 righe: solo lo scaffold.

## Perché si ferma

| Componente prevista | Cosa la copre oggi |
|---|---|
| 9 tool filesystem | Il [server filesystem MCP ufficiale](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) ne offre 15, con allowed-dirs e protocollo `roots` |
| Loop agentico ReAct | Da Ollama v0.32.0 (luglio 2026) il comando `ollama` nudo apre un agente che legge, scrive, esegue comandi e cerca sul web |
| CLI agentica | `ollama launch claude\|opencode\|codex\|copilot` configura harness maturi su modelli locali |
| Client Ollama | Endpoint compat OpenAI e Anthropic Messages nativi in Ollama |
| Sandbox, conferme, audit | Almeno sette gateway/proxy MCP con policy e audit trail |

L'unico gap reale è che **Ollama non parla MCP nativamente**
([issue #7865](https://github.com/ollama/ollama/issues/7865), aperta): l'agente
v0.32 usa tool interni. Ma quel gap è coperto da client terzi
([ollmcp](https://github.com/jonigl/mcp-client-for-ollama), MCPHost) e dagli
harness lanciabili con `ollama launch`.

## Cosa abbiamo verificato prima di chiudere

Restava una domanda che la ricerca documentale non risolve: **i guardrail
esistenti funzionano davvero?** Se non funzionassero, ci sarebbe ancora spazio.
Quindi due candidati sono stati installati e messi alla prova con lo stesso
protocollo — server MCP di prova, policy restrittiva, quattro sonde.

Le due sonde che contano: un path con `../` che tenta di uscire dalla
allow-list, e una scrittura in approvazione umana **quando nessun umano può
approvare** — che è la condizione normale, dato che il proxy gira come
sottoprocesso del client, senza terminale.

| | [mcp-firewall](https://pypi.org/project/mcp-firewall/) 0.1.0 | [airlock](https://github.com/airlock-dev/airlock) 0.2.38 |
|---|---|---|
| Traversal `../` nella allow-list | passa ⚠️ | passa ⚠️ |
| Approvazione non ottenibile | **esegue lo stesso** ⚠️ | **rifiuta** ✅ |
| Postura di default | `prompt` → auto-allow ⇒ allow | deny reale |
| `resources/read` | non ispezionato ⚠️ | passa dal gateway |
| Audit | argomenti solo hashed; troncamento in coda non rilevato | argomenti completi, con redazione |
| Sandbox a livello OS | assente | `@anthropic-ai/sandbox-runtime` |

Report completo con citazioni dal codice e output:
**[docs/09-SPIKE-MCP-GUARDRAILS.md](docs/09-SPIKE-MCP-GUARDRAILS.md)**.
Artefatti riproducibili: **[spike/](spike/)**.

## Cosa usare al posto di questo progetto

**Per far lavorare un modello locale sui tuoi file**: `ollama` v0.32 da solo,
oppure `ollama launch claude` / `ollama launch opencode` per un harness più
capace sullo stesso modello locale.

**Per mettere un guinzaglio agli agenti che parlano MCP**:
[airlock](https://github.com/airlock-dev/airlock), con un preset sandbox e le
scritture in approvazione. Configurazione di partenza commentata in
[`examples/airlock.recommended.yaml`](examples/airlock.recommended.yaml).
Attenzione al limite noto sul matching dei path documentato lì dentro: il
confine vero lo devono dare il server filesystem (che riceve le sue directory
consentite come argomento) e il sandbox del sistema operativo, non la
arg_policy.

**Da non fare**: fidarsi di `mcp-firewall` 0.1.0 come confine di sicurezza
finché i tre fallimenti in apertura descritti nel report non sono chiusi.

## Cosa resta di valido qui dentro

I documenti di specifica restano leggibili e marcati `superseded`. Reggono
ancora come esempio di analisi: [threat model](docs/06-SECURITY.md),
[requisiti tracciabili](docs/requirements/REQ-INDEX.md),
[architettura](docs/02-ARCHITECTURE.md), [WBS](docs/08-WBS.md), gate di qualità
in [CONTROL.yaml](CONTROL.yaml).

Non è il metodo ad aver fallito: è il bersaglio ad essere diventato commodity
mentre la specifica aspettava. La decisione, le alternative valutate e i
criteri per riaprirla sono in
[ARC-002](docs/architecture/ARC-002.closure-decision.md).

## Seguito

REQ-004 (validazione dei path) è l'unica parte con ancora qualcosa da dire:
entrambi i guardrail testati sbagliano lì. In airlock il difetto ha un punto
d'innesto naturale — `arg-policy.js` ha già un meccanismo di normalizzatori
(`trim`, `lower`, `email`, `phone`) applicato prima del confronto. Aggiungerne
uno `path`, che risolve e rifiuta ciò che esce dalle basi consentite, è il modo
di far vivere quel requisito dove serve a qualcuno.

## Licenza

MIT © 2026 Claudio
