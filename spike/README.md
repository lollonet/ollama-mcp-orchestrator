# Spike: guardrail MCP per agenti locali (agosto 2026)

Artefatti riproducibili dei due spike che hanno chiuso questo progetto.
Il report completo con i risultati è in [`docs/09-SPIKE-MCP-GUARDRAILS.md`](../docs/09-SPIKE-MCP-GUARDRAILS.md).

Entrambi gli spike usano lo stesso protocollo di prova: un server MCP finto,
una policy deliberatamente restrittiva e quattro sonde che verificano se il
confine di sicurezza dichiarato tiene davvero.

| Sonda | Cosa verifica |
|-------|---------------|
| lettura legittima | il traffico consentito passa (nessun falso positivo) |
| chiave SSH | una regola di deny esplicita blocca |
| **traversal** | `basedir/../../../etc/shadow` buca la allow-list? |
| **write in `ask`** | cosa succede quando nessun umano può approvare? |

## mcp-firewall (Python)

```bash
uv venv .venv && uv pip install --python .venv/bin/python mcp-firewall
cd mcp-firewall
../.venv/bin/python driver.py      # tiene stdin aperto: necessario, vedi report §3
../.venv/bin/mcp-firewall audit --config policy.yaml
```

`driver.py` esiste perché con un semplice `cat requests.jsonl | mcp-firewall wrap ...`
il proxy termina alla chiusura di stdin e scarta le risposte ancora in volo:
`asyncio.wait(..., return_when=FIRST_COMPLETED)` cancella il task
server→client senza drenarlo.

## airlock (Node)

```bash
npm install airlock-bot
cd airlock
node client.mjs
```

`mcp_server.mjs` è un server MCP reale costruito con l'SDK ufficiale (airlock
esegue l'handshake `initialize` + `tools/list`, quindi un finto server che
risponde a caso non basta). `client.mjs` lancia airlock in stdio mode come
sottoprocesso — esattamente il modo in cui lo lancerebbe Claude Code o OpenCode,
che è anche la ragione per cui stderr non è mai un TTY.

## Nota sui nomi dei tool

airlock espone i tool con namespace `provider_tool` (`fs_read_file`) mentre le
policy si scrivono con `provider/tool` (`fs/read_file`). Un tool chiamato con il
nome sbagliato non è un errore di sintassi: è un deny ("Tool not available"),
che è la postura giusta ma può confondere in fase di setup.
