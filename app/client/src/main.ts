import "./style.css";
import { api } from "./api/client";

function el<T extends HTMLElement>(id: string): T {
  const node = document.getElementById(id);
  if (!node) throw new Error(`missing #${id}`);
  return node as T;
}

function setText(id: string, value: string): void {
  el(id).textContent = value;
}

async function loadConnectors(): Promise<void> {
  const box = el("connectors");
  box.replaceChildren();
  try {
    const { connectors } = await api.connectors();
    for (const c of connectors) {
      const card = document.createElement("div");
      card.className = "card";
      const row = document.createElement("div");
      row.className = "row";
      const left = document.createElement("div");
      const name = document.createElement("strong");
      name.textContent = c.id;
      const meta = document.createElement("div");
      meta.className = "tiny";
      meta.textContent = `${c.kind} · ${c.models.join(", ") || "slot"}`;
      left.append(name, meta);
      const pill = document.createElement("span");
      pill.className = c.status === "granted" ? "pill on" : "pill";
      pill.textContent = c.status;
      row.append(left, pill);
      card.append(row);
      box.append(card);
    }
  } catch (error) {
    const p = document.createElement("p");
    p.className = "tiny";
    p.textContent = error instanceof Error ? error.message : "backend offline";
    box.append(p);
  }
}

function policy(): RivetOptions {
  return {
    slot: el<HTMLSelectElement>("slot").value as RivetOptions["slot"],
    route: el<HTMLSelectElement>("policy").value as RivetOptions["route"],
    residency: el<HTMLSelectElement>("residency").value as RivetOptions["residency"],
    max_usd: Number(el<HTMLInputElement>("maxusd").value),
    split_challenger_pct: 0,
  };
}

function showReceipt(r: RivetReceipt): void {
  setText("r-model", r.model_used);
  setText("r-why", r.why);
  setText("r-vendor", r.vendor_usd.toFixed(6));
  setText("r-rivet", r.rivet_usd.toFixed(2));
  setText("r-esc", String(r.escalated));
  setText("r-cache", String(r.cache_hit));
  setText("r-slot", r.classifier.slot);
}

async function loadLedger(): Promise<void> {
  const trace = el("trace");
  trace.replaceChildren();
  try {
    const { data } = await api.ledger(12);
    for (const row of data) {
      const card = document.createElement("div");
      card.className = "card";
      const stamp = (row.created_at || "").slice(11, 19);
      card.textContent = `${stamp}  ${row.model_used}  $${Number(row.vendor_usd).toFixed(4)}  ${row.cache_hit ? "cache" : ""}`;
      trace.append(card);
    }
  } catch {
    /* ledger empty until first send */
  }
}

async function send(): Promise<void> {
  const out = el("out");
  out.textContent = "routing…";
  try {
    const body = await api.chat({
      model: el<HTMLInputElement>("model").value || "auto",
      messages: [{ role: "user", content: el<HTMLTextAreaElement>("prompt").value }],
      rivet: policy(),
    });
    out.textContent = JSON.stringify(body, null, 2);
    showReceipt(body.rivet);
    await loadLedger();
  } catch (error) {
    const message = error instanceof Error ? error.message : "request failed";
    out.textContent = JSON.stringify({ error: message }, null, 2);
  }
}

async function runEval(): Promise<void> {
  const out = el("evalout");
  out.textContent = "running fixture…";
  try {
    const body = await api.compare(20);
    out.textContent = JSON.stringify(
      { note: body.note, quality_delta: body.quality_delta, columns: body.columns },
      null,
      2,
    );
    await loadLedger();
  } catch (error) {
    out.textContent = error instanceof Error ? error.message : "eval failed";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  el("send").addEventListener("click", () => {
    void send();
  });
  el("eval").addEventListener("click", () => {
    void runEval();
  });
  void loadConnectors();
  void loadLedger();
});
