import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.gridspec as gridspec

BASE = os.path.dirname(os.path.abspath(__file__))

# ── shared colour palette ─────────────────────────────────────────────────────
C = {
    "bg":      "#0d1117",
    "panel":   "#161b22",
    "border":  "#30363d",
    "code_bg": "#1e2533",
    "code_fg": "#c9d1d9",
    "comment": "#6e7681",
    "title":   "#e6edf3",
    "arrow":   "#58a6ff",
    "green":   "#3fb950",
    # pipeline stages
    "s1": "#1f6feb", "s2": "#388bfd", "s3": "#f85149", "s4": "#3fb950",
    "s5": "#d29922", "s6": "#a371f7", "s7": "#f0883e", "s8": "#58a6ff",
    # dataset panels
    "d1": "#0891b2", "d2": "#059669", "d3": "#7c3aed",
}


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE 1 — Microservices
# ═══════════════════════════════════════════════════════════════════════════════

APP_SVCS = [
    {
        "name":    "auth-service",
        "pod":     "auth-service-77cb49446f-ggrn5",
        "age":     "137d",
        "role":    "Authentication\n& Authorization",
        "footer":  "logs → stdout → /var/log/pods → Promtail → Loki",
        "colour":  C["s1"],
    },
    {
        "name":    "inventory-service",
        "pod":     "inventory-service-85cd67f8df-jp9fh",
        "age":     "137d",
        "role":    "Inventory\nManagement",
        "footer":  "logs → stdout → /var/log/pods → Promtail → Loki",
        "colour":  C["s2"],
    },
    {
        "name":    "notification-service",
        "pod":     "notification-service-5c85466c48-nz5zq",
        "age":     "137d",
        "role":    "Notification\nDelivery",
        "footer":  "logs → stdout → /var/log/pods → Promtail → Loki",
        "colour":  C["s3"],
    },
    {
        "name":    "order-service",
        "pod":     "order-service-68d7bd77c-nvqpk",
        "age":     "137d",
        "role":    "Order\nProcessing",
        "footer":  "logs → stdout → /var/log/pods → Promtail → Loki",
        "colour":  C["s4"],
    },
    {
        "name":    "payment-service",
        "pod":     "payment-service-59f9594fff-g89tz",
        "age":     "137d",
        "role":    "Payment\nProcessing",
        "footer":  "logs → stdout → /var/log/pods → Promtail → Loki",
        "colour":  C["s5"],
    },
]

INFRA_SVCS = [
    {
        "name":    "observability-loki-0",
        "pod":     "observability-loki-0",
        "age":     "139d",
        "type":    "StatefulSet",
        "role":    "Log Aggregation Store\nExposes HTTP query API on :3100",
        "footer":  "stores ingested chunks on disk  ·  queried by loki_fetcher.py",
        "colour":  C["s7"],
    },
    {
        "name":    "observability-promtail-mhnvh",
        "pod":     "observability-promtail-mhnvh",
        "age":     "138d",
        "type":    "DaemonSet",
        "role":    "Log Shipper\nTails /var/log/pods/  →  ships to Loki",
        "footer":  "attaches labels: namespace, pod, app, container",
        "colour":  C["s6"],
    },
]


def _draw_card(ax, svc, show_type=False):
    col = svc["colour"]

    ax.set_facecolor(C["code_bg"])
    for spine in ax.spines.values():
        spine.set_edgecolor(col)
        spine.set_linewidth(2.5)
    ax.set_xticks([])
    ax.set_yticks([])

    # glow
    ax.add_patch(FancyBboxPatch(
        (-0.006, -0.006), 1.012, 1.012,
        transform=ax.transAxes, boxstyle="square,pad=0",
        linewidth=0, facecolor=col, alpha=0.10, clip_on=False, zorder=0))

    # header bar
    ax.add_patch(FancyBboxPatch(
        (0, 0.86), 1, 0.14,
        transform=ax.transAxes, boxstyle="square,pad=0",
        linewidth=0, facecolor=col, clip_on=False))

    ax.text(0.5, 0.935, svc["name"],
            transform=ax.transAxes, ha="center", va="center",
            fontsize=10.5, fontweight="bold", color="white",
            fontfamily="monospace")

    if show_type:
        ax.text(0.5, 0.875, svc.get("type", ""),
                transform=ax.transAxes, ha="center", va="center",
                fontsize=8, color="white", fontstyle="italic",
                fontfamily="monospace")

    # status
    ax.text(0.05, 0.79, "● Running",
            transform=ax.transAxes, ha="left", va="center",
            fontsize=10, color=C["green"], fontfamily="monospace",
            fontweight="bold")
    ax.text(0.62, 0.79, "READY: 1/1",
            transform=ax.transAxes, ha="left", va="center",
            fontsize=9, color=C["code_fg"], fontfamily="monospace")

    # pod name
    ax.text(0.05, 0.71, "pod:",
            transform=ax.transAxes, ha="left", va="center",
            fontsize=8, color=C["comment"], fontfamily="monospace")
    ax.text(0.05, 0.64, svc["pod"],
            transform=ax.transAxes, ha="left", va="center",
            fontsize=7.5, color=C["code_fg"], fontfamily="monospace")

    # age
    ax.text(0.05, 0.56, "AGE: {}   RESTARTS: 0".format(svc["age"]),
            transform=ax.transAxes, ha="left", va="center",
            fontsize=9, color=C["code_fg"], fontfamily="monospace")

    # divider
    ax.plot([0.04, 0.96], [0.50, 0.50],
            transform=ax.transAxes, color=col, alpha=0.35, lw=1)

    # role
    ax.text(0.05, 0.46, "ROLE",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=8, color=col, fontfamily="monospace", fontweight="bold")
    ax.text(0.05, 0.39, svc["role"],
            transform=ax.transAxes, ha="left", va="top",
            fontsize=9, color=C["code_fg"], fontfamily="monospace",
            linespacing=1.65)

    # footer note
    ax.text(0.05, 0.06, svc["footer"],
            transform=ax.transAxes, ha="left", va="center",
            fontsize=7, color=C["comment"], fontfamily="monospace",
            fontstyle="italic", wrap=True)

    ax.text(0.05, 0.13, "namespace: logan",
            transform=ax.transAxes, ha="left", va="center",
            fontsize=8, color=C["comment"], fontfamily="monospace")


fig1 = plt.figure(figsize=(34, 24), facecolor=C["bg"])

g1 = gridspec.GridSpec(
    4, 1, figure=fig1,
    height_ratios=[0.35, 2.2, 0.22, 1.6],
    hspace=0.10,
)

# title
ax_t = fig1.add_subplot(g1[0])
ax_t.set_facecolor(C["bg"])
ax_t.axis("off")
ax_t.text(0.5, 0.62,
          "Microservices Architecture  —  Kubernetes Namespace: logan",
          transform=ax_t.transAxes, ha="center", va="center",
          fontsize=22, fontweight="bold", color=C["title"],
          fontfamily="monospace")
ax_t.text(0.5, 0.15,
          "All pods:  STATUS Running  ·  READY 1/1  ·  RESTARTS 0  ·  "
          "Observed: 2026-05-03",
          transform=ax_t.transAxes, ha="center", va="center",
          fontsize=11, color=C["comment"], fontfamily="monospace")

# ── 5 app service cards ───────────────────────────────────────────────────────
app_grid = gridspec.GridSpecFromSubplotSpec(
    1, 5, subplot_spec=g1[1], wspace=0.20)
for idx, svc in enumerate(APP_SVCS):
    ax = fig1.add_subplot(app_grid[0, idx])
    _draw_card(ax, svc)

# ── infra separator ───────────────────────────────────────────────────────────
ax_sep = fig1.add_subplot(g1[2])
ax_sep.set_facecolor(C["bg"])
ax_sep.axis("off")
ax_sep.text(0.5, 0.5,
            "━━━━━━━━━━━━━━━━━━━━━━  "
            "OBSERVABILITY INFRASTRUCTURE"
            "  ━━━━━━━━━━━━━━━━━━━━━━",
            transform=ax_sep.transAxes, ha="center", va="center",
            fontsize=12, color=C["comment"], fontfamily="monospace")

# ── 2 infra cards (centred in a 4-col grid) ───────────────────────────────────
infra_grid = gridspec.GridSpecFromSubplotSpec(
    1, 4, subplot_spec=g1[3],
    wspace=0.20,
    width_ratios=[0.4, 1, 1, 0.4],
)
for idx, svc in enumerate(INFRA_SVCS):
    ax = fig1.add_subplot(infra_grid[0, idx + 1])
    _draw_card(ax, svc, show_type=True)

fig1.text(0.5, 0.993,
          "lparser-agents  ·  Kubernetes Services Overview",
          ha="center", va="top",
          fontsize=17, fontweight="bold",
          color=C["title"], fontfamily="monospace")

out1 = "{}/microservices.png".format(BASE)
plt.savefig(out1, dpi=160, bbox_inches="tight",
            facecolor=C["bg"], edgecolor="none")
print("Saved → {}".format(out1))
plt.close(fig1)


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE 2 — Dataset Overview (3 panels)
# ═══════════════════════════════════════════════════════════════════════════════

DS_PANELS = [
    (
        "Data Sources",
        "kubectl get pods -n logan",
        C["d1"],
        """\
Kubernetes Namespace: "logan"

APP SERVICES  (5 active pods)
──────────────────────────────────────────────
  ● auth-service
    pod: auth-service-77cb49446f-ggrn5

  ● inventory-service
    pod: inventory-service-85cd67f8df-jp9fh

  ● notification-service
    pod: notification-service-5c85466c48-nz5zq

  ● order-service
    pod: order-service-68d7bd77c-nvqpk

  ● payment-service
    pod: payment-service-59f9594fff-g89tz

INFRA PODS  (excluded from log queries)
──────────────────────────────────────────────
  ○ observability-loki-0        ← log store
  ○ observability-promtail-mhnvh  ← log shipper

Data ingested every 30 s  ·  look-back = 1 min
Loki query limit = 5 000 lines per poll"""
    ),
    (
        "Node File System Layout",
        "/var/log/pods/  (confirmed on cluster)",
        C["d2"],
        """\
/var/log/pods/
│
├── logan_auth-service-77cb49446f_<uid>/
│   └── auth-service/
│       ├── 0.log             ← active (Promtail tailing)
│       └── 0.log.<ts>.gz     ← rotated + compressed
│
├── logan_payment-service-59f9_<uid>/
│   └── payment-service/
│       ├── 0.log
│       └── 0.log.<ts>.gz
│
├── logan_observability-loki-0_8b927d0d/
│   └── loki/
│       ├── 0.log             ← Loki's OWN stdout only
│       ├── 0.log.20260503-165901
│       └── 0.log.20260503-*.gz
│
└── logan_observability-promtail_4bc87fb4/
    └── promtail/
        ├── 0.log
        └── 0.log.20260502-145016

Directory convention:
  <namespace>_<pod-name>_<pod-uid>/<container>/"""
    ),
    (
        "Log Format & Normalized Schema",
        "CRI format  →  log_normalizer.py",
        C["d3"],
        """\
RAW CRI LINE  (each line inside 0.log):
─────────────────────────────────────────────────
2026-05-03T10:00:00.000000000Z  stdout  F  <msg>
└─ RFC3339Nano timestamp ──────┘ └────┘ └┘
                                 stream  flag
                               stdout    F = Full line
                               /stderr   P = Partial line

Promtail strips CRI prefix, attaches k8s labels:
  namespace=logan   pod=payment-service-59f9...
  app=payment-service   container=payment-service

NORMALIZED SCHEMA  (after log_normalizer.py):
─────────────────────────────────────────────────
  timestamp : "17462664000000000000"  (ns)
  service   : "payment-service"
  pod       : "payment-service-59f9594fff-g89tz"
  level     : "error"|"timeout"|"warning"|"info"
  message   : "connection timeout to downstream db"
  raw       : original CRI line

ALERT TYPES DETECTED:
  ErrorSpike      →  error logs   >= 10
  TimeoutSpike    →  timeout logs >= 5
  RareLogPattern  →  count==1 and len(msg) > 30"""
    ),
]

fig2 = plt.figure(figsize=(40, 22), facecolor=C["bg"])

g2 = gridspec.GridSpec(
    2, 1, figure=fig2,
    height_ratios=[0.10, 1],
    hspace=0.06,
)

ax_dt = fig2.add_subplot(g2[0])
ax_dt.set_facecolor(C["bg"])
ax_dt.axis("off")
ax_dt.text(0.5, 0.5,
           "Dataset Overview  —  Kubernetes Log Data  (Namespace: logan)",
           transform=ax_dt.transAxes, ha="center", va="center",
           fontsize=20, fontweight="bold", color=C["title"],
           fontfamily="monospace")

ds_grid = gridspec.GridSpecFromSubplotSpec(
    1, 3, subplot_spec=g2[1], wspace=0.18)

for p_idx, (title, filetag, col, body) in enumerate(DS_PANELS):
    ax = fig2.add_subplot(ds_grid[0, p_idx])
    ax.set_facecolor(C["code_bg"])
    for spine in ax.spines.values():
        spine.set_edgecolor(col)
        spine.set_linewidth(2.5)
    ax.set_xticks([])
    ax.set_yticks([])

    ax.add_patch(FancyBboxPatch(
        (-0.005, -0.005), 1.010, 1.010,
        transform=ax.transAxes, boxstyle="square,pad=0",
        linewidth=0, facecolor=col, alpha=0.09, clip_on=False, zorder=0))

    ax.add_patch(FancyBboxPatch(
        (0, 0.90), 1, 0.10,
        transform=ax.transAxes, boxstyle="square,pad=0",
        linewidth=0, facecolor=col, clip_on=False))

    ax.text(0.03, 0.95, title,
            transform=ax.transAxes, ha="left", va="center",
            fontsize=13, fontweight="bold", color="white",
            fontfamily="monospace")
    ax.text(0.97, 0.95, filetag,
            transform=ax.transAxes, ha="right", va="center",
            fontsize=8.5, color="white", fontstyle="italic",
            fontfamily="monospace")

    ax.text(0.03, 0.86, body,
            transform=ax.transAxes, ha="left", va="top",
            fontsize=9, color=C["code_fg"], fontfamily="monospace",
            linespacing=1.62)

fig2.text(0.5, 0.993,
          "lparser-agents  ·  Dataset Overview",
          ha="center", va="top",
          fontsize=17, fontweight="bold",
          color=C["title"], fontfamily="monospace")

out2 = "{}/dataset_overview.png".format(BASE)
plt.savefig(out2, dpi=160, bbox_inches="tight",
            facecolor=C["bg"], edgecolor="none")
print("Saved → {}".format(out2))
plt.close(fig2)


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE 3 — Workflow (version 1: ribbon + 8 code panels)
# ═══════════════════════════════════════════════════════════════════════════════

STAGES = [
    ("1  Ingest",           C["s1"]),
    ("2  Normalize",        C["s2"]),
    ("3  Detect",           C["s3"]),
    ("4  Semantic\nEnrich", C["s4"]),
    ("5  Emit\nEventBus",   C["s5"]),
    ("6  Correlate",        C["s6"]),
    ("7  RAG\nRetrieve",    C["s7"]),
    ("8  RCA\nOutput",      C["s8"]),
]

CODE = {
    "1  Ingest": (
        "loki_fetcher.py",
        """\
def fetch_logs(minutes=5):
    end   = int(time.time())
    start = end - minutes * 60
    params = {
        "query": '{namespace="logan"}',
        "start": start * 1_000_000_000,
        "end":   end   * 1_000_000_000,
        "limit": 5000,
    }
    resp = requests.get(
        f"{LOKI_URL}/loki/api/v1/query_range",
        params=params, timeout=10
    )
    for stream in resp.json()["data"]["result"]:
        for ts, line in stream["values"]:
            logs.append({"timestamp": ts,
                         "stream": stream["stream"],
                         "line": line})
    return logs"""
    ),
    "2  Normalize": (
        "log_normalizer.py",
        """\
def normalize(records):
    for rec in records:
        raw    = rec.get("line","").strip()
        parsed = json.loads(raw)  # try JSON
        message = (parsed.get("msg")
                or parsed.get("message")
                or raw)
        level = (parsed.get("level")
              or infer_level(raw)).lower()
        normalized.append({
            "timestamp": rec["timestamp"],
            "service":   labels.get("app",""),
            "pod":       labels.get("pod",""),
            "level":     level,
            "message":   message,
        })
    return normalized

def infer_level(text):
    if "error"   in text: return "error"
    if "timeout" in text: return "timeout"
    if "warn"    in text: return "warning"
    return "info" """
    ),
    "3  Detect": (
        "detector.py",
        """\
ERROR_THRESHOLD   = 10
TIMEOUT_THRESHOLD = 5

def detect_anomalies(logs):
    errors   = [l for l in logs
                if l["level"] == "error"]
    timeouts = [l for l in logs
                if "timeout" in l["message"]]
    freq  = Counter(l["message"] for l in logs)
    rare  = [m for m,c in freq.items()
             if c == 1 and len(m) > 30]

    if len(errors)   >= ERROR_THRESHOLD:
        alerts.append({"type":"ErrorSpike",...})
    if len(timeouts) >= TIMEOUT_THRESHOLD:
        alerts.append({"type":"TimeoutSpike",...})
    if rare:
        alerts.append({"type":"RareLogPattern",...})
    return alerts, stats"""
    ),
    "4  Semantic\nEnrich": (
        "semantic_enricher.py",
        """\
def enrich_logs(logs, use_llm=False):
    for log in logs:
        entry = dict(log)  # never mutate original

        entry["embedding_vector"] = (
            _get_embedding(entry["message"]))

        entry["llm_anomaly_estimate"] = (
            _estimate_anomaly(entry))

        entry["novelty_score"] = (
            min(1.0, len(entry["message"]) / 120))

        entry["is_novel"] = (
            entry["novelty_score"] > 0.8)

        entry["semantic_confidence"] = round(
            (anomaly_score + novelty) / 2, 2)

    metrics = {"Avg novelty": avg_novelty,
               "Avg anomaly": avg_anomaly,
               "Avg conf":    avg_conf}
    return enriched, metrics"""
    ),
    "5  Emit\nEventBus": (
        "event_bus.py + agentic_monitor_agent.py",
        """\
# EventBus — three directed queues
class EventBus:
    def __init__(self):
        self.monitor_events = Queue()
        # Monitor → Correlation
        self.incidents      = Queue()
        # Correlation → RCA
        self.rca_events     = Queue()
        # RCA → UI (future)

# Monitor Agent — emit step
event = {
    "timestamp": time.time(),
    "alerts":    raw_alerts,
    "stats":     stats,
    "semantic":  semantic,
    "metrics":   metrics,
}
self.event_bus.monitor_events.put(event)"""
    ),
    "6  Correlate": (
        "agentic_correlation_agent.py",
        """\
ALERT_CATEGORY_MAP = {
    "ErrorSpike":     "application",
    "TimeoutSpike":   "dependency",
    "RareLogPattern": "anomaly",
}

def correlate(self, event):
    categories = {
        ALERT_CATEGORY_MAP.get(a["type"])
        for a in event["alerts"]
    }
    sig = frozenset(categories)
    # 120-second suppression window
    if time.time() - self.last[sig] < 120:
        return   # drop duplicate incident

    incident = {
        "incident_id": f"INC-{int(time.time())}",
        "categories":  list(categories),
        "metrics":     event["metrics"],
        "semantic":    event["semantic"],
    }
    self.event_bus.incidents.put(incident)"""
    ),
    "7  RAG\nRetrieve": (
        "rag_store.py + llm_rca.py",
        """\
# rag_store.py
vector_store = FAISS.load_local(
    "rag_index", OpenAIEmbeddings())

def retrieve_context(query, k=4):
    docs = vector_store.similarity_search(
        query, k=k)
    return "\\n---\\n".join(
        d.page_content for d in docs)

# llm_rca.py
def llm_rca(incident):
    rag_ctx = retrieve_context(
        "categories: " + str(
            incident["categories"]))
    prompt = (
        "You are an SRE.\\n"
        "Incident: " + json.dumps(incident)
        + "\\nHistory: " + rag_ctx
        + "\\nReturn JSON: root_cause,"
        " confidence, recommended_actions")
    resp = client.chat.completions.create(
        model="gpt-4o-mini", temperature=0.2,
        messages=[{"role":"user",
                   "content": prompt}])
    return {"rag_used": True,
            "analysis": json.loads(resp)}"""
    ),
    "8  RCA\nOutput": (
        "agentic_rca_agent.py",
        """\
def analyze(self, incident):
    # Rule-based (deterministic)
    if "application" in categories:
        causes.append({
            "cause": "Application error spike",
            "confidence": 0.7,
            "action": "Inspect recent deploys"})
    if "dependency" in categories:
        causes.append({
            "cause": "Dependency timeout",
            "confidence": 0.8,
            "action": "Check dependency health"})

    rca_result = {
        "incident_id":    incident["incident_id"],
        "rule_based_rca": causes,
        "metrics":        incident["metrics"],
    }
    if LLM_RCA:
        rca_result["llm_rca"] = LLM_RCA(incident)

    # Persist + Notify
    self._persist_rca(rca_result)
    # → incidents/<INC-ID>.json
    send_push(rca_result)
    # → Pushover notification"""
    ),
}

fig3 = plt.figure(figsize=(44, 56), facecolor=C["bg"])

outer3 = gridspec.GridSpec(
    2, 1, figure=fig3,
    height_ratios=[1, 3.8],
    hspace=0.04,
)

# ── workflow ribbon ───────────────────────────────────────────────────────────
ax_flow = fig3.add_subplot(outer3[0])
ax_flow.set_facecolor(C["bg"])
ax_flow.set_xlim(0, 100)
ax_flow.set_ylim(0, 100)
ax_flow.axis("off")

ax_flow.text(50, 94, "Log Monitoring & RCA  —  End-to-End Workflow",
             ha="center", va="center", fontsize=26, fontweight="bold",
             color=C["title"], fontfamily="monospace")

n     = len(STAGES)
bw    = 9.5
bh    = 22
gap   = 2.0
total = n * bw + (n - 1) * gap
x0    = (100 - total) / 2
y0    = 28

for i, (label, col) in enumerate(STAGES):
    x = x0 + i * (bw + gap)

    ax_flow.add_patch(FancyBboxPatch(
        (x - 0.3, y0 - 0.3), bw + 0.6, bh + 0.6,
        boxstyle="round,pad=0.4", linewidth=0,
        facecolor=col, alpha=0.18))

    ax_flow.add_patch(FancyBboxPatch(
        (x, y0), bw, bh,
        boxstyle="round,pad=0.4", linewidth=2,
        edgecolor=col, facecolor=C["panel"]))

    ax_flow.add_patch(
        plt.Circle((x + bw / 2, y0 + bh - 4), 3.2, color=col, zorder=5))
    ax_flow.text(x + bw / 2, y0 + bh - 4, str(i + 1),
                 ha="center", va="center", fontsize=11, fontweight="bold",
                 color="white", zorder=6)

    ax_flow.text(x + bw / 2, y0 + bh / 2 - 3, label,
                 ha="center", va="center", fontsize=10,
                 fontweight="bold", color=col, fontfamily="monospace",
                 linespacing=1.5)

    if i < n - 1:
        ax_x = x + bw + 0.1
        ax_flow.annotate(
            "", xy=(ax_x + gap - 0.2, y0 + bh / 2),
            xytext=(ax_x, y0 + bh / 2),
            arrowprops=dict(arrowstyle="-|>", color=C["arrow"],
                            lw=2.2, mutation_scale=18))

shapes = [
    "{ts, stream, line}",
    "{ts, service, level, msg}",
    "+ alerts[ ], stats{ }",
    "+ embedding, novelty,\n  anomaly_score, pattern_id",
    "event{ alerts, metrics,\n  semantic } → Queue",
    "incident{ id, categories,\n  metrics } → Queue",
    "rag_context (top-4 docs)\n+ LLM JSON response",
    "rca_result.json\n+ Pushover push",
]
for i, shape in enumerate(shapes):
    x = x0 + i * (bw + gap)
    ax_flow.text(x + bw / 2, y0 - 7, shape,
                 ha="center", va="top", fontsize=7.5,
                 color=C["comment"], fontfamily="monospace",
                 linespacing=1.4)

ax_flow.text(50, 2, "Data shape at each stage",
             ha="center", va="bottom", fontsize=11,
             color=C["comment"], fontstyle="italic")

# ── 8 code panels (2 × 4) ────────────────────────────────────────────────────
inner3 = gridspec.GridSpecFromSubplotSpec(
    2, 4, subplot_spec=outer3[1],
    hspace=0.38, wspace=0.22,
)

for idx, (label, col) in enumerate(STAGES):
    row, col_idx = divmod(idx, 4)
    ax = fig3.add_subplot(inner3[row, col_idx])
    ax.set_facecolor(C["code_bg"])
    for spine in ax.spines.values():
        spine.set_edgecolor(col)
        spine.set_linewidth(2)
    ax.set_xticks([])
    ax.set_yticks([])

    filename, snippet = CODE[label]

    ax.add_patch(FancyBboxPatch(
        (0, 0.88), 1, 0.12,
        transform=ax.transAxes, boxstyle="square,pad=0",
        linewidth=0, facecolor=col, clip_on=False))

    ax.text(0.03, 0.94,
            "Stage {}  ·  {}".format(idx + 1, label.replace("\n", " ")),
            transform=ax.transAxes, ha="left", va="center",
            fontsize=12, fontweight="bold", color="white",
            fontfamily="monospace")

    ax.text(0.97, 0.94, filename,
            transform=ax.transAxes, ha="right", va="center",
            fontsize=9, color="white", fontstyle="italic",
            fontfamily="monospace")

    ax.text(0.025, 0.83, snippet,
            transform=ax.transAxes, ha="left", va="top",
            fontsize=9, color=C["code_fg"], fontfamily="monospace",
            linespacing=1.58)

fig3.text(0.5, 0.993,
          "lparser-agents  ·  RAG · Semantic · LangGraph  ·  Architecture",
          ha="center", va="top",
          fontsize=20, fontweight="bold",
          color=C["title"], fontfamily="monospace")

out3 = "{}/workflow_subplots.png".format(BASE)
plt.savefig(out3, dpi=160, bbox_inches="tight",
            facecolor=C["bg"], edgecolor="none")
print("Saved → {}".format(out3))
plt.close(fig3)


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE 4 — requirements.txt
# ═══════════════════════════════════════════════════════════════════════════════

REQS = [
    ("anthropic",           "0.97.0",  "LLM / AI",    "llm_config.py",             C["s7"], "Anthropic Claude SDK — AI LLM calls"),
    ("faiss-cpu",           "1.13.0",  "Vector DB",   "rag_store.py",               C["s1"], "FAISS similarity search for RAG context"),
    ("gradio",              "4.44.1",  "Web UI",      "gradio_ui.py",               C["s4"], "Interactive web dashboard for pipeline"),
    ("graphviz",            "0.21",    "Visualise",   "grap-img.py",                C["s6"], "Graph and diagram rendering"),
    ("hf-xet",              "1.2.0",   "ML Storage",  "—",                          C["s5"], "HuggingFace XET high-speed file protocol"),
    ("langchain-community", "0.3.31",  "LangChain",   "rag_store.py",               C["s8"], "LangChain FAISS vector store wrapper"),
    ("langchain-openai",    "0.3.35",  "LangChain",   "rag_store.py, llm_rca.py",   C["s8"], "OpenAI embeddings + LLM via LangChain"),
    ("typer-slim",          "0.21.2",  "CLI",         "—",                          C["comment"], "Lightweight CLI interface builder"),
]

fig4 = plt.figure(figsize=(30, 13), facecolor=C["bg"])
g4 = gridspec.GridSpec(2, 1, figure=fig4,
                        height_ratios=[0.10, 1], hspace=0.04)

ax4t = fig4.add_subplot(g4[0])
ax4t.set_facecolor(C["bg"])
ax4t.axis("off")
ax4t.text(0.5, 0.5, "requirements.txt  —  Python Dependencies",
          transform=ax4t.transAxes, ha="center", va="center",
          fontsize=20, fontweight="bold", color=C["title"],
          fontfamily="monospace")

ax4 = fig4.add_subplot(g4[1])
ax4.set_facecolor(C["code_bg"])
for spine in ax4.spines.values():
    spine.set_edgecolor(C["border"])
    spine.set_linewidth(1.5)
ax4.set_xlim(0, 100)
ax4.set_ylim(0, 100)
ax4.set_xticks([])
ax4.set_yticks([])

ax4.add_patch(FancyBboxPatch((0, 91), 100, 9,
                              boxstyle="square,pad=0",
                              linewidth=0, facecolor="#21262d"))

COLS4 = [1, 23, 35, 51, 72]
HDRS4 = ["Package", "Version", "Category", "Used In", "Description"]
for hdr, cx in zip(HDRS4, COLS4):
    ax4.text(cx, 95.5, hdr, ha="left", va="center",
             fontsize=10, fontweight="bold",
             color=C["title"], fontfamily="monospace")

for cx in COLS4[1:]:
    ax4.plot([cx - 0.8, cx - 0.8], [0, 91],
             color=C["border"], lw=0.5, alpha=0.4)

for ri, (pkg, ver, cat, used, col, desc) in enumerate(REQS):
    yb = 90 - (ri + 1) * 10
    yc = yb + 5

    if ri % 2 == 0:
        ax4.add_patch(FancyBboxPatch((0, yb), 100, 10,
                                      boxstyle="square,pad=0",
                                      linewidth=0, facecolor="#161b22", alpha=0.55))

    ax4.text(COLS4[0], yc, pkg, ha="left", va="center",
             fontsize=9.5, fontweight="bold",
             color=col, fontfamily="monospace")

    ax4.add_patch(FancyBboxPatch((COLS4[1], yb + 1.5), 10, 7,
                                  boxstyle="round,pad=0.3",
                                  linewidth=1, edgecolor=col,
                                  facecolor=C["bg"]))
    ax4.text(COLS4[1] + 5, yc, ver, ha="center", va="center",
             fontsize=8, color=col, fontfamily="monospace")

    ax4.add_patch(FancyBboxPatch((COLS4[2], yb + 1.5), 13.5, 7,
                                  boxstyle="round,pad=0.3",
                                  linewidth=0, facecolor=col, alpha=0.22))
    ax4.text(COLS4[2] + 6.75, yc, cat, ha="center", va="center",
             fontsize=8, color=col,
             fontfamily="monospace", fontweight="bold")

    ax4.text(COLS4[3], yc, used, ha="left", va="center",
             fontsize=8, color=C["comment"], fontfamily="monospace")

    ax4.text(COLS4[4], yc, desc, ha="left", va="center",
             fontsize=8.5, color=C["code_fg"], fontfamily="monospace")

    ax4.plot([0, 100], [yb, yb], color=C["border"], lw=0.4, alpha=0.3)

fig4.text(0.5, 0.993, "lparser-agents  ·  requirements.txt",
          ha="center", va="top", fontsize=16, fontweight="bold",
          color=C["title"], fontfamily="monospace")

out4 = "{}/requirements_overview.png".format(BASE)
plt.savefig(out4, dpi=160, bbox_inches="tight",
            facecolor=C["bg"], edgecolor="none")
print("Saved → {}".format(out4))
plt.close(fig4)


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE 5 — Execution Commands
# ═══════════════════════════════════════════════════════════════════════════════

CMDS = [
    ("comment", "# Step 1 — Navigate to project directory",          ""),
    ("cmd",     "cd <project-root>",                                  "Change to project root"),
    ("gap",     "", ""),
    ("comment", "# Step 2 — Activate Python virtual environment",    ""),
    ("cmd",     "source venv/bin/activate",                           "Activates isolated Python venv"),
    ("gap",     "", ""),
    ("comment", "# Step 3 — Set environment variables",              ""),
    ("cmd",     "export USE_LLM=true",                                "Enable LLM + RAG RCA path"),
    ("cmd",     "export OPENAI_API_KEY=...",                          "OpenAI key  (gpt-4o-mini + embeddings)"),
    ("cmd",     "export PUSHOVER_USER_KEY=...",                       "Pushover notification user key"),
    ("cmd",     "export PUSHOVER_APP_TOKEN=...",                      "Pushover app token"),
    ("gap",     "", ""),
    ("comment", "# Step 4 — Launch the agentic control dashboard",   ""),
    ("cmd",     "python3 agentic_control_dashboard.py",               "Starts 3 agents in parallel threads"),
    ("gap",     "", ""),
    ("output",  ">> Monitoring system running (Agentic)",              ""),
    ("output",  "[AgenticMonitor]     Started — polling Loki every 30s", ""),
    ("output",  "[AgenticCorrelation] Started — waiting on monitor_events queue", ""),
    ("output",  "[AgenticRCA]         Started — waiting on incidents queue", ""),
]

fig5 = plt.figure(figsize=(34, 16), facecolor=C["bg"])
g5 = gridspec.GridSpec(2, 1, figure=fig5,
                        height_ratios=[0.08, 1], hspace=0.04)

ax5t = fig5.add_subplot(g5[0])
ax5t.set_facecolor(C["bg"])
ax5t.axis("off")
ax5t.text(0.5, 0.5, "Execution Commands  —  Step-by-Step Setup & Launch",
          transform=ax5t.transAxes, ha="center", va="center",
          fontsize=20, fontweight="bold", color=C["title"],
          fontfamily="monospace")

ax5 = fig5.add_subplot(g5[1])
ax5.set_facecolor("#0d1117")
for spine in ax5.spines.values():
    spine.set_edgecolor("#30363d")
    spine.set_linewidth(2)
ax5.set_xlim(0, 100)
ax5.set_ylim(0, 100)
ax5.set_xticks([])
ax5.set_yticks([])

ax5.add_patch(FancyBboxPatch((0, 93.5), 100, 6.5,
                              boxstyle="square,pad=0",
                              linewidth=0, facecolor="#21262d"))
for xi, dc in enumerate(["#f85149", "#d29922", "#3fb950"]):
    ax5.add_patch(plt.Circle((3 + xi * 3.5, 96.5), 1.2, color=dc, zorder=5))
ax5.text(50, 96.5, "bash  —  lparser-agents-RAG-Semantic-LangGraph",
         ha="center", va="center",
         fontsize=9.5, color=C["comment"], fontfamily="monospace")

y5 = 90.5
for kind, text, note in CMDS:
    if kind == "gap":
        y5 -= 2.5
        continue
    if kind == "comment":
        ax5.text(2, y5, text, ha="left", va="center",
                 fontsize=9, color=C["comment"],
                 fontfamily="monospace", fontstyle="italic")
        y5 -= 4.5
    elif kind == "cmd":
        ax5.text(2, y5, "$", ha="left", va="center",
                 fontsize=11, color=C["green"],
                 fontfamily="monospace", fontweight="bold")
        ax5.text(4.5, y5, text, ha="left", va="center",
                 fontsize=10, color=C["code_fg"],
                 fontfamily="monospace")
        if note:
            ax5.text(97, y5, "# " + note, ha="right", va="center",
                     fontsize=8.5, color=C["s5"],
                     fontfamily="monospace")
        y5 -= 5.5
    elif kind == "cont":
        ax5.text(4.5, y5, text, ha="left", va="center",
                 fontsize=10, color=C["code_fg"],
                 fontfamily="monospace")
        y5 -= 4.0
    elif kind == "output":
        ax5.text(2, y5, text, ha="left", va="center",
                 fontsize=9.5, color="#58d68d",
                 fontfamily="monospace")
        y5 -= 5.0

fig5.text(0.5, 0.993, "lparser-agents  ·  Execution Commands",
          ha="center", va="top", fontsize=16, fontweight="bold",
          color=C["title"], fontfamily="monospace")

out5 = "{}/execution_commands.png".format(BASE)
plt.savefig(out5, dpi=160, bbox_inches="tight",
            facecolor=C["bg"], edgecolor="none")
print("Saved → {}".format(out5))
plt.close(fig5)


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE 6 — Output File  (INC-1772252822.json)
# ═══════════════════════════════════════════════════════════════════════════════

JSON_TEXT = """\
{
  "incident_id": "INC-1772252822",
  "categories": ["anomaly", "dependency"],
  "rule_based_rca": [
    {
      "cause": "Downstream dependency timeout",
      "confidence": 0.8,
      "action": "Check dependency health and latency"
    },
    {
      "cause": "Rare or unexpected behavior",
      "confidence": 0.6,
      "action": "Inspect anomalous logs"
    }
  ],
  "analyzed_at": 1772252822.7146714,
  "metrics": {
    "Total events": 10,
    "Avg novelty score": 0.97,
    "Novel events": "10/10",
    "Avg anomaly score": 0.4,
    "Avg semantic conf": 0.68,
    "LLM anomaly enabled": true
  },
  "llm_rca": {
    "rag_used": true,
    "analysis": {
      "root_cause": "Potential anomaly in service
  behavior due to dependency issues,
  possibly related to external service
  or database interactions causing
  unexpected load.",
      "confidence": 0.85,
      "recommended_actions": [
        "Investigate external service
  dependencies for latency/failure.",
        "Review application logs for errors.",
        "Implement additional monitoring
  on service dependencies.",
        "Consider adding circuit breaker
  patterns.",
        "Conduct load testing to identify
  potential bottlenecks."
      ]
    }
  }
}"""

BREAKDOWN_TEXT = """\
FIELD BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

incident_id
  "INC-1772252822"
  Format: INC-{unix_epoch_seconds}
  Created by CorrelationAgent

categories
  ["anomaly", "dependency"]
  RareLogPattern  →  anomaly
  TimeoutSpike    →  dependency
  Mapped inside CorrelationAgent

rule_based_rca  (deterministic — no LLM)
  cause: Dependency timeout   conf=0.80
  cause: Rare behavior        conf=0.60
  Written by AgenticRCAAgent rules

analyzed_at
  Unix epoch: 1772252822.71
  Timestamp when RCA ran

metrics  (from semantic_enricher.py)
  Total events    : 10 logs processed
  Avg novelty     : 0.97  ← very high
  Novel events    : 10/10 ← all novel
  Avg anomaly sc  : 0.40  ← moderate
  Avg sem conf    : 0.68  ← good
  LLM enabled     : true

llm_rca  (LLM + RAG result)
  rag_used    = true
  FAISS index queried (top-4 docs)
  confidence  = 0.85  ← high
  model       = gpt-4o-mini
  5 recommended actions returned
  Persisted → incidents/<INC>.json
  Notified  → Pushover push"""

fig6 = plt.figure(figsize=(38, 26), facecolor=C["bg"])
g6outer = gridspec.GridSpec(2, 1, figure=fig6,
                             height_ratios=[0.07, 1], hspace=0.04)

ax6t = fig6.add_subplot(g6outer[0])
ax6t.set_facecolor(C["bg"])
ax6t.axis("off")
ax6t.text(0.5, 0.5,
          "Output File  —  incidents/INC-1772252822.json",
          transform=ax6t.transAxes, ha="center", va="center",
          fontsize=20, fontweight="bold", color=C["title"],
          fontfamily="monospace")

g6 = gridspec.GridSpecFromSubplotSpec(
    1, 2, subplot_spec=g6outer[1],
    wspace=0.10, width_ratios=[1.1, 0.9])

ax6l = fig6.add_subplot(g6[0])
ax6l.set_facecolor(C["code_bg"])
for spine in ax6l.spines.values():
    spine.set_edgecolor(C["s1"])
    spine.set_linewidth(2.5)
ax6l.set_xticks([])
ax6l.set_yticks([])

ax6l.add_patch(FancyBboxPatch((0, 0.93), 1, 0.07,
                               transform=ax6l.transAxes,
                               boxstyle="square,pad=0",
                               linewidth=0, facecolor=C["s1"],
                               clip_on=False))
ax6l.text(0.03, 0.965, "incidents/INC-1772252822.json",
          transform=ax6l.transAxes, ha="left", va="center",
          fontsize=12, fontweight="bold", color="white",
          fontfamily="monospace")
ax6l.text(0.97, 0.965, "JSON output  ·  AgenticRCAAgent._persist_rca()",
          transform=ax6l.transAxes, ha="right", va="center",
          fontsize=9, color="white", fontstyle="italic",
          fontfamily="monospace")
ax6l.text(0.03, 0.895, JSON_TEXT,
          transform=ax6l.transAxes, ha="left", va="top",
          fontsize=9, color=C["code_fg"],
          fontfamily="monospace", linespacing=1.52)

ax6r = fig6.add_subplot(g6[1])
ax6r.set_facecolor(C["code_bg"])
for spine in ax6r.spines.values():
    spine.set_edgecolor(C["d3"])
    spine.set_linewidth(2.5)
ax6r.set_xticks([])
ax6r.set_yticks([])

ax6r.add_patch(FancyBboxPatch((0, 0.93), 1, 0.07,
                               transform=ax6r.transAxes,
                               boxstyle="square,pad=0",
                               linewidth=0, facecolor=C["d3"],
                               clip_on=False))
ax6r.text(0.03, 0.965, "Field Breakdown  ·  Annotations",
          transform=ax6r.transAxes, ha="left", va="center",
          fontsize=12, fontweight="bold", color="white",
          fontfamily="monospace")
ax6r.text(0.03, 0.895, BREAKDOWN_TEXT,
          transform=ax6r.transAxes, ha="left", va="top",
          fontsize=9, color=C["code_fg"],
          fontfamily="monospace", linespacing=1.55)

fig6.text(0.5, 0.993,
          "lparser-agents  ·  RCA Output  ·  INC-1772252822",
          ha="center", va="top", fontsize=16, fontweight="bold",
          color=C["title"], fontfamily="monospace")

out6 = "{}/output_file.png".format(BASE)
plt.savefig(out6, dpi=160, bbox_inches="tight",
            facecolor=C["bg"], edgecolor="none")
print("Saved → {}".format(out6))
plt.close(fig6)
