# Spike: i guardrail MCP esistenti tengono?

**Data**: 16 agosto 2026
**Autore**: Claudio (analisi assistita)
**Scopo**: decidere se implementare REQ-001..REQ-009 di questo repo, adottare
uno strumento esistente, o chiudere il progetto.

---

## 1. Perché questo spike

Il progetto originale — un orchestratore che dà a modelli Ollama accesso
controllato al filesystem via MCP — è stato specificato a gennaio 2026 e mai
implementato (61 righe di scaffold). Nel frattempo l'ecosistema si è mosso in
modo tale da erodere quasi per intero la proposta di valore:

| Componente prevista | Stato del mercato ad agosto 2026 |
|---------------------|----------------------------------|
| 9 tool filesystem (REQ-001) | Il [server filesystem MCP ufficiale](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) ne offre 15, con allowed-dirs da CLI e aggiornamento dinamico via protocollo `roots` |
| Loop ReAct (REQ-002) | Da Ollama v0.32.0 (11 luglio 2026) il comando `ollama` nudo apre un agente interattivo che legge/scrive file, esegue comandi e cerca sul web |
| CLI agentica (REQ-003) | `ollama launch claude\|opencode\|codex\|copilot` configura harness maturi su modelli locali senza env var |
| Client Ollama (REQ-006) | Endpoint compat OpenAI e Anthropic Messages nativi in Ollama (`/v1/messages` da v0.14.0, gennaio 2026) |
| Sandbox + audit (REQ-004, REQ-005) | Almeno sette progetti di gateway/proxy MCP con policy e audit |

L'unico gap reale è che **Ollama non parla MCP nativamente**
([issue #7865](https://github.com/ollama/ollama/issues/7865), tuttora aperta):
l'agente v0.32 usa tool interni, non server MCP. Ma quel gap è coperto da
client terzi (ollmcp, MCPHost, ollama-mcp-bridge) e dagli harness lanciabili
con `ollama launch`.

Restava una domanda che nessuna ricerca documentale può risolvere: **i
guardrail esistenti fanno davvero il loro lavoro?** Se non lo facessero, ci
sarebbe ancora spazio per costruire. Da qui lo spike.

## 2. Protocollo di prova

Identico per entrambi i candidati:

1. un server MCP minimale che esegue e conferma qualunque chiamata riceva;
2. una policy deliberatamente restrittiva: default deny, letture consentite
   solo sotto `/home/user/projects/`, chiavi SSH negate, scritture in
   approvazione umana;
3. quattro sonde inviate come vero traffico JSON-RPC attraverso il proxy.

Le sonde che contano sono la terza e la quarta. La terza (`traversal`) verifica
se la allow-list resiste a `basedir/../../../etc/shadow`. La quarta verifica
la postura di fallimento: cosa succede a una scrittura che richiede
approvazione **quando nessun umano può approvare** — che è la condizione
normale, non l'eccezione, visto che il proxy gira come sottoprocesso del client
MCP e non ha un terminale.

Artefatti riproducibili: [`spike/`](../spike/).

## 3. mcp-firewall 0.1.0 (Python)

3.358 righe, 39 moduli, struttura pulita (pipeline inbound/outbound, policy
engine, audit, dashboard). Autore con credenziali di offensive security.
JSON-RPC parsato a mano, senza SDK MCP.

### Risultati

```
✓ ALLOW  read_file  /home/user/projects/app.py                    corretto
✗ DENIED read_file  /home/user/.ssh/id_rsa                        corretto
✓ ALLOW  read_file  /home/user/projects/../../../etc/shadow       EVASIONE SANDBOX
✓ ALLOW  write_file (regola: prompt)                              APPROVAZIONE SALTATA
    —    resources/read file:///home/user/.ssh/id_rsa             NON INTERCETTATO
```

### Tre fallimenti in apertura (fail-open)

**F1 — Il traversal batte le allow-list.** `pipeline/inbound/policy.py`
converte il glob in regex e usa `re.match`, che àncora solo l'inizio, **senza
alcuna normalizzazione del path**: nessun `Path.resolve()` nel modulo. Il
prefisso `/home/user/projects/` soddisfa la regola e il resto del path è libero
di risalire. È la classe di vulnerabilità che REQ-004 di questo repo esisteva
per prevenire.

**F2 — L'approvazione umana non esiste.** Nel proxy stdio, testualmente:
`# In Phase 1, prompt falls through to allow (interactive approval in Phase 2)`.
Lo stage `HumanApproval`, quando viene raggiunto, fa
`if not sys.stderr.isatty(): return self._allow("Non-interactive, auto-approved")`
— e stderr non è mai un TTY nel modo in cui il proxy viene realmente lanciato.
L'audit lo registra da sé: `"stage":"human_approval","reason":"Non-interactive, auto-approved"`.
Difetto architetturale più profondo: se il prompt scattasse userebbe `input()`,
che legge da **stdin, lo stesso canale del protocollo JSON-RPC**. Non è uno
stub da completare, è da riprogettare.

**F3 — Solo `tools/call` viene ispezionato.** `resources/read` e `prompts/get`
passano intatti, senza policy e senza audit, anche con `defaultAction: deny`.
Il server filesystem ufficiale espone risorse.

### L'audit regge, con riserve

```
verify su log integro       → ✓ verified (5 entries)
modifico "deny" → "allw"    → ✗ FAILED: Hash chain broken at line 3
cancello le ultime 2 righe  → ✓ verified (3 entries)      ← troncamento invisibile
```

La catena rileva la manomissione ma non il troncamento in coda: manca un head
firmato o ancorato esternamente. La firma Ed25519 (`audit/signer.py`) non viene
mai verificata da `verify_chain()`, ed è comunque prodotta con una chiave in
chiaro accanto al log — chi può riscrivere il log può rifirmarlo. Infine il
record salva `arguments_hash`, non gli argomenti: si sa che `read_file` è stato
permesso, non *cosa* abbia letto.

### Difetti minori rilevati leggendo il codice

- `_intercept_request` e `_proxy_server_to_client` scrivono entrambi su
  `sys.stdout.buffer` da task concorrenti senza lock: corsa possibile sul flusso
  JSON-RPC.
- `asyncio.wait(..., FIRST_COMPLETED)` chiude il proxy senza drenare: alla
  chiusura di stdin le risposte in volo vengono perse.
- La scansione outbound correla la risposta a un `dummy_request`: nessun legame
  con la richiesta originale, quindi nessuna policy contestuale in uscita.
- Un batch JSON-RPC (lista invece di oggetto) solleva `AttributeError` non
  gestito nel loop di intercettazione.
- Doppia riga di audit per la stessa chiamata quando passa dallo stage di
  approvazione.

### Giudizio

Codice ordinato, commenti onesti sulle fasi non fatte, ma **la distanza tra la
vetrina e l'implementazione è ampia**: la pagina PyPI promette report DORA /
FINMA / SOC 2 e audit firmato crittograficamente, mentre il confine di
sicurezza cede su tre fronti. Oggi non è una cintura di sicurezza: è una spia
che segnala `allow` mentre l'agente esce dal recinto.

## 4. airlock-bot 0.2.38 (TypeScript/Node)

13 dipendenze dirette (195 pacchetti, 91 MB installati), fra cui l'**SDK MCP
ufficiale** e `@anthropic-ai/sandbox-runtime`. Audit su SQLite. CLI ricca:
`explain <agent>`, `who-can <tool>`, `lint`, discovery da `--help` e da OpenAPI.

### Risultati

```
lettura legittima  /home/user/projects/app.py              → eseguita              corretto
chiave SSH         /home/user/.ssh/id_rsa                  → bloccata (arg_policy) corretto
TRAVERSAL          /home/user/projects/../../../etc/shadow → ESEGUITA              EVASIONE
write (ask)        nessuno può approvare                   → RIFIUTATA             corretto
```

Risposta all'agente sulla quarta sonda:

```
MCP error -32602: Tool fs/write_file requires human approval.
Retry with _airlock.reason explaining why you are requesting this action now.
```

### Cosa fa bene

**Fail-closed sulle approvazioni.** In `middleware/core/hitl-gate.js` i tre
esiti non-approvati sono tutti chiusi: `denied` → errore, `timeout` → errore,
`disconnected` → errore. Solo un'approvazione esplicita prosegue con `next()`.
È l'esatto opposto di F2.

**Deny reale di default.** `allowlist/engine.js` restituisce `default-deny`
quando nessun pattern combacia, con risoluzione per specificità e deny che
vince i pareggi. Un tool fuori policy non è nemmeno visibile come chiamabile.

**Audit utilizzabile.** Registra gli argomenti completi (`JSON.stringify(ctx.args)`)
con redazione configurabile: si sa *cosa* è stato chiesto.

**Confine vero, delegato a chi può garantirlo.** I `sandbox_presets`
(`allow_read`, `allow_write`, `deny_read`, allowlist di rete) poggiano su
`@anthropic-ai/sandbox-runtime`, cioè confinamento a livello di sistema
operativo, non matching di stringhe. E l'SDK ufficiale evita di reinterpretare
JSON-RPC a mano.

### La debolezza che condivide

`middleware/core/arg-policy.js` fa matching glob **ancorato** (`^...$`, meglio
di `re.match`), ma il `*` è deliberatamente greedy attraverso `/` — scelta
documentata nel sorgente per i ref git annidati — e **non c'è normalizzazione
del path**. Quindi `glob_allow: ['/home/user/projects/*']` accetta
`/home/user/projects/../../../etc/shadow`.

Differenza importante rispetto a mcp-firewall: qui il difetto è *innestabile*.
`arg-policy.js` ha già un meccanismo di normalizzatori (`trim`, `lower`,
`email`, `phone`) applicato prima del confronto. Aggiungere un normalizzatore
`path` — risolvi, poi rifiuta se il risultato esce dalle basi consentite — sono
poche decine di righe che entrano in una struttura che le aspetta.

## 5. Confronto

| | mcp-firewall 0.1.0 | airlock-bot 0.2.38 |
|---|---|---|
| Postura di default | `prompt` → auto-allow ⇒ di fatto allow | deny reale |
| Approvazione umana | auto-allow quando stderr non è TTY (sempre, in uso reale) | fail-closed su denied / timeout / disconnessione |
| Traversal nelle allow-list | bypassabile, e senza punto d'innesto per il fix | bypassabile, ma con meccanismo di normalizzazione già presente |
| Metodi non-`tools/call` | non ispezionati | passano dal gateway SDK con namespace |
| Audit | JSONL hash-chained, argomenti solo hashed, troncamento non rilevato, firma non verificata | SQLite, argomenti completi con redazione |
| Sandbox OS | assente | `@anthropic-ai/sandbox-runtime` |
| Parsing protocollo | a mano | SDK ufficiale |
| Maturità | 1 release (feb 2026) | v0.2.38, 186 commit, 13 stelle |

## 6. Conclusioni

1. **Non implementare REQ-001..REQ-009.** Ogni componente prevista è oggi
   commodity, e la parte di governance — l'ultima difendibile — è coperta da
   almeno sette progetti, uno dei quali (airlock) sano dove conta.
2. **Adottare airlock** davanti ai client MCP, con un preset sandbox per il
   filesystem. L'agente nativo `ollama` v0.32 resta fuori: non parla MCP e usa
   le proprie approvazioni, che almeno sono implementate.
3. **Non fidarsi di mcp-firewall 0.1.0** come confine di sicurezza finché F1,
   F2 e F3 non sono chiuse.
4. **Contribuire il normalizzatore `path`** ad airlock. È REQ-004 di questo
   repo trasformato in codice utile, in un posto dove serve a più di una
   persona, senza assumersi la manutenzione di un runtime di sicurezza.

## 7. Limiti di questo spike

- Ho misurato la postura di sicurezza, non prestazioni, stabilità in sessioni
  lunghe, o compatibilità con ogni client MCP.
- Il server MCP a valle era finto: le sonde verificano le decisioni del
  proxy, non l'interazione con un server reale sotto carico.
- Non ho verificato se i `sandbox_presets` di airlock confinino anche i server
  MCP di tipo `stdio` oltre ai provider di esecuzione comandi. Se il sandbox
  copre anche quelli, il traversal è contenuto a livello di sistema operativo
  e il difetto di `arg-policy` diventa difesa in profondità mancante anziché
  buco singolo. **Da verificare prima di scrivere la patch.**
- I dati di adozione (13 stelle per airlock) dicono che nessuno dei due
  candidati ha ricevuto una revisione indipendente ampia. Vale per il codice
  che leggi tu quanto per quello che leggo io.
