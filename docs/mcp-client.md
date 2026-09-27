# DevLog MCP client guide (v4.1.0, free-tier friendly)

Endpoint: `POST https://YOUR-RENDER-URL/mcp` (Streamable HTTP, JSON-RPC 2.0).
Discovery: `GET https://YOUR-RENDER-URL/mcp` (no auth needed).

## 1. Get a token (same auth as REST)

```bash
curl -X POST https://YOUR-RENDER-URL/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=YOU@MAIL" --data-urlencode "password=SECRET"
export TOKEN=<access_token from response>
```

## 2. Handshake + list tools

```bash
curl -X POST https://YOUR-RENDER-URL/mcp -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}'
curl -X POST https://YOUR-RENDER-URL/mcp -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

## 3. Call tools

```bash
curl -X POST https://YOUR-RENDER-URL/mcp -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_sessions","arguments":{"limit":5}}}'
curl -X POST https://YOUR-RENDER-URL/mcp -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"activity_summary","arguments":{"start_date":"2026-09-01","end_date":"2026-09-20"}}}'
```

## 4. Claude Desktop (free)

`claude_desktop_config.json` (requires node/npx for `mcp-remote`):

```json
{"mcpServers": {"devlog": {"command": "npx",
  "args": ["-y", "mcp-remote", "https://YOUR-RENDER-URL/mcp",
           "--header", "Authorization: Bearer YOUR_TOKEN_HERE"]}}}
```

Then ask Claude: "list my DevLog sessions" / "summarise my September activity".

## Notes

- No `mcp` pip package needed (server is hand-rolled JSON-RPC). `requirements.txt` unchanged.
- Tools always filter by YOUR user id from the JWT — no cross-user leakage.
- `AI_PROVIDER=mock` (default) means AI summaries work with no key; RAG search degrades to `[]` + warning when pgvector is unavailable (SQLite tests).
- Render free: no new env vars are *required* (MCP defaults on); set `MCP_REQUIRE_AUTH=true` (default) in production.
