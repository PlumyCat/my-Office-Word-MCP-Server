Transformer **Office-Word-MCP-Server** en **serveur HTTP (Streamable)** déployable sur **Azure Container Apps** – donc “URL-ready” pour Copilot Studio.

> Référence utile : FastMCP sait lancer un serveur **Streamable HTTP** sans FastAPI externe :
> `mcp.run(transport="http", host="0.0.0.0", port=8000, path="/mcp")`. ([GitHub][[1](https://github.com/jlowin/fastmcp?utm_source=chatgpt.com)])

---

# 🎯 Objectif

* Passer le serveur de **STDIO** → **HTTP streamable** (endpoint `/mcp`).
* Dockeriser proprement (port **8000**).
* Déployer sur **Azure Container Apps**.
* Ajouter **API Key**.

---

# ✅ “Claude Code Workplan” (copie-colle tel quel)

**Context:** The repo is `GongRzhe/Office-Word-MCP-Server`. We need to turn it into an HTTP (Streamable) MCP server for ACA.

## 1) Add/ensure dependencies

* Open `requirements.txt`.
* **Ensure** these packages exist (add if missing):

  ```
  mcp
  fastmcp
  ```
* Keep existing Word libs (e.g., `python-docx`) untouched.
* Save.

(Sources: FastMCP “Streamable HTTP” run support.) ([GitHub][1])

## 2) Switch the server to HTTP streamable

* Open `word_mcp_server.py`.
* Find where the MCP server is instantiated (likely `from mcp.server.fastmcp import FastMCP` or `from fastmcp import FastMCP`) and where it’s run (often `mcp.run()` with default STDIO).
* **Change the run call** to HTTP streamable, listening on `0.0.0.0:8000` with path `/mcp`:

```python
if __name__ == "__main__":
    # previous: mcp.run() or mcp.run(transport="stdio")
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000,
        path="/mcp",
    )
```

* If the file uses the **old import** `from mcp.server.fastmcp import FastMCP`, keep it; otherwise `from fastmcp import FastMCP` also works (both support HTTP run – prefer whichever the repo already uses).
* Do **not** remove tool registrations; only modify the **runner** line.
* Save.

(Refs: fastmcp README + docs “Running server → Streamable HTTP”.) ([GitHub][1])

## 3) Add a health endpoint (simple)

FastMCP’s built-in HTTP transport exposes `/mcp`. For ACA readiness, add a tiny health route:

* Create a new file `health_http.py`:

```python
# Minimal ASGI app for /health (served by uvicorn separately if needed)
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
```

**Two ways to serve health:**

* **Simpler (one process):** skip this file for now; ACA can probe `/mcp` with a GET (it will 405). Often acceptable.
* **Safer:** run a second small uvicorn just for `/health`. If you want the safer way, add FastAPI to `requirements.txt` and run a tiny sidecar process.
  👉 Pour réduire la complexité, **tu peux ignorer `/health`** au début.

## 4) Dockerize (port 8000)

* Open `Dockerfile` (exists in repo). Replace content with:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Expose HTTP (Streamable) at :8000 (/mcp path)
ENV PORT=8000
EXPOSE 8000

# Run the MCP server in HTTP mode directly via the main file
# (Assumes you edited word_mcp_server.py runner to transport="http")
CMD ["python", "word_mcp_server.py"]
```

* Save.

## 5) Build & push image to ACR

Use your ACR name:

```bash
az acr build -t word-mcp:latest -r <ACR_NAME> .
```

## 6) Deploy to Azure Container Apps

If the managed environment exists (`<ENV_NAME>`), deploy:

```bash
az containerapp create \
  --name word-mcp \
  --resource-group <RG_NAME> \
  --environment <ENV_NAME> \
  --image <ACR_NAME>.azurecr.io/word-mcp:latest \
  --ingress external --target-port 8000 \
  --min-replicas 0 --max-replicas 1 \
  --query properties.configuration.ingress.fqdn -o tsv
```

This prints your public FQDN like `word-mcp.<region>.azurecontainerapps.io`.

> Notes ACA:
>
> * `--min-replicas 0` → **scale-to-zero** (coûts \~0 quand idle).
> * SSE/stream ok on ACA.
>   (Docs: ACA + free/scale-to-zero tiers.) ([GitHub][2])

## 7) Test quickly (local and remote)

* Local (optional): `docker run -p 8000:8000 word-mcp:latest`
* Remote: `curl -i https://<FQDN>/mcp` (should not 404; may 405 on GET, which is fine).

## 8) Plug into Copilot Studio

In your agent → **Tools → Add → Model Context Protocol**:

* **Server URL**: `https://<FQDN>/mcp`
* **Auth**: None (for the very first test).
  If you later want **API key**, we’ll add a tiny header check middleware, but start simple.

(How to connect existing MCP by URL per MS docs.) ([GitHub][3])

---

## 🔐 (Optionnel) API Key minimale

Si tu veux protéger l’URL :

1. Ajoute une variable d’env `MCP_API_KEY` dans ACA:

```
--secrets mcp-api-key=<YOUR_SECRET> \
--env-vars MCP_API_KEY=secretref:mcp-api-key
```

2. Au lieu d’utiliser le runner “tout-en-un”, bascule vers **FastAPI wrapper** plus tard (pour vérifier `Authorization: Bearer <key>`).
   Pour la première passe, **laisse sans auth** (réduit la complexité). On fera l’auth quand l’URL marche.

---

## 📎 Remarques spécifiques au repo

* Le README du repo montre l’usage **Claude Desktop** (STDIO). On ne casse rien : on ne modifie que **la ligne `mcp.run(...)`** pour HTTP. Le reste (tools Word) est inchangé. ([GitHub][3])
* Si l’import est `from mcp.server.fastmcp import FastMCP`, garde-le (FastMCP v1). Si c’est v2 : `from fastmcp import FastMCP`. Les deux ont `run(transport="http", ...)`. ([GitHub][1])

---

## 🧪 Check-list “ça marche”

* `GET https://<FQDN>/mcp` → 405 (OK)
* **Copilot Studio → Test connection** passe ✅
* Un prompt simple côté agent qui appelle un tool Word (création doc) renvoie un résultat.

