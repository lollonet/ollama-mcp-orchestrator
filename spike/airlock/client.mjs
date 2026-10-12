import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const t = new StdioClientTransport({ command: "node", args: ["node_modules/.bin/airlock", "--agent", "dev", "--config", "airlock.yaml"], stderr: "pipe" });
const c = new Client({ name: "probe", version: "1.0.0" }, { capabilities: {} });
await c.connect(t);
const tools = await c.listTools();
console.log("TOOLS VISIBLE TO CLIENT:", tools.tools.map(x => x.name).join(", ") || "(none)");
const probes = [
  ["fs_read_file", { path: "/home/user/projects/app.py" },            "lettura legittima"],
  ["fs_read_file", { path: "/home/user/.ssh/id_rsa" },                "chiave SSH"],
  ["fs_read_file", { path: "/home/user/projects/../../../etc/shadow" }, "TRAVERSAL"],
  ["fs_write_file", { path: "/home/user/projects/app.py" },           "write (ask, nessuno approva)"],
];
for (const [name, args, label] of probes) {
  const t0 = Date.now();
  try {
    const r = await c.callTool({ name, arguments: args }, undefined, { timeout: 20000 });
    const txt = (r.content?.[0]?.text ?? JSON.stringify(r)).slice(0, 90);
    console.log(`  [${label}] isError=${!!r.isError} (${Date.now()-t0}ms) -> ${txt}`);
  } catch (e) {
    console.log(`  [${label}] EXCEPTION (${Date.now()-t0}ms) -> ${String(e.message).slice(0,400)}`);
  }
}
await c.close();
process.exit(0);
