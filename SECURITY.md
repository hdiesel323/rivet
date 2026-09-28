# Security

Do not file issues that contain live API keys, OAuth grants, or production prompts with secrets.

This MVP stores prompts in a local SQLite ledger. Treat `RIVET_DB_PATH` as sensitive if you send real traffic.

If `RIVET_API_KEY` is set, the server requires `Authorization: Bearer <key>` on `/v1/*`.

To report a vulnerability, open a private GitHub security advisory on this repository. If that is unavailable, open an issue **without** secrets and say you need a private channel.
