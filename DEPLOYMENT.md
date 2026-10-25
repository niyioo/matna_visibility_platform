# Deployment & Operations

## Architecture

```
browser ──HTTPS──▶ TLS proxy (your LB / Caddy / nginx+certbot)
                        │ HTTP + X-Forwarded-Proto
                        ▼
                  web (nginx) ── serves the React SPA
                        │ /api, /admin, /static, /health
                        ▼
                  backend (Gunicorn + Django) ──▶ db (PostgreSQL 16)
```

SPA and API share one origin, so production needs no CORS. The database has no
published port.

## First deployment

1. Create the env files and fill in every value:
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   python -c "import secrets; print(secrets.token_urlsafe(64))"   # SECRET_KEY
   ```
   `DB_*` must match in both files. Production refuses to start with a weak `SECRET_KEY`.
2. Build and start: `docker compose up -d --build`
   The one-shot `migrate` service applies migrations, creates the throttle cache
   table and seeds inventory items before the API starts.
3. Create the first administrator:
   `docker compose exec backend python manage.py createsuperuser`
   then set its role to `ADMIN` in the Django admin (`/<ADMIN_URL>`).
4. Put a TLS-terminating proxy in front of port 80 that sets `X-Forwarded-Proto: https`.
   If that proxy also appends `X-Forwarded-For`, set `NUM_PROXIES=2` for the backend.

## Go-live checklist

- [ ] `SECRET_KEY` is unique, ≥ 50 random characters, stored outside git
- [ ] `DEBUG=False`, `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` list only your domain
- [ ] `ADMIN_URL` changed from `admin/`; `ENABLE_API_DOCS=False`
- [ ] HTTPS works end-to-end; `http://` redirects to `https://`
- [ ] `docker compose ps` shows `db`, `backend` and `web` healthy
- [ ] `curl https://<domain>/health/` returns `{"status": "ok", "db": "connected"}`
- [ ] `docker compose exec backend python manage.py check --deploy` has no security errors
- [ ] `docker compose exec backend python manage.py reconcile_inventory` reports consistent
- [ ] Backup cron installed, and **one restore tested** on a separate machine
- [ ] Backups are copied off the server
- [ ] KPI thresholds, analysis windows and `LIVE_REFRESH_SECONDS` in `backend/.env` agreed with operations management (the UI reads them live; restart `backend` after changing)

## Backups

`scripts/backup.sh` writes a compressed, verified `pg_dump` to `backups/` and
deletes dumps older than `BACKUP_RETENTION_DAYS` (default 14).

```cron
30 2 * * * cd /opt/matna && ./scripts/backup.sh >> backups/backup.log 2>&1
```

Restore (destructive, asks for confirmation): `./scripts/restore.sh backups/<file>.dump`

## Inventory integrity

Stock is an append-only ledger. Records are never edited or deleted: an admin
**voids** a production entry or delivery (with a reason) and the stock movements
are reversed; a corrected entry can then be recorded for the same date.

Run the reconciliation daily. It exits with status 1 on any discrepancy, so it
can drive alerting:

```cron
0 6 * * * cd /opt/matna && docker compose exec -T backend python manage.py reconcile_inventory || <notify>
```

The admin UI has the same check under **Inventory → Stock integrity check**.

Fixes are opt-in and logged:

| Problem | Command |
|---|---|
| Documents with no ledger postings (e.g. rows created before the admin was locked) | `reconcile_inventory --repair-missing <admin-username>` |
| Cached balance differs from a verified ledger | `reconcile_inventory --rebuild-balances` |

## Upgrades

```bash
./scripts/backup.sh
git pull
docker compose up -d --build        # migrate runs before the new backend starts
docker compose exec backend python manage.py reconcile_inventory
```

## Monitoring

- Health: `GET /health/` (200 ok / 503 database unavailable), used by Docker healthchecks
- Logs: `docker compose logs -f backend web` (rotated at 10 MB × 5 per container)
- Security events worth alerting on: repeated `429` on `/api/auth/login/`, user deactivations, voids
