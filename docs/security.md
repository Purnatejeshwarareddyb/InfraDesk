# Security

InfraDesk is built for a trusted local network. It applies sensible protections, but it has **not**
been security-reviewed or penetration-tested and must not be exposed directly to the public internet.

## What is implemented (and where to find it)

| Topic | Implementation |
|---|---|
| Password storage | Argon2 (`argon2-cffi`), automatic re-hash on login if parameters change (`core/security.py`) |
| Password rules | at least 10 characters, upper case, lower case and a digit (`schemas/user.py`) |
| Login errors | one message for unknown user, wrong password and inactive account; a dummy hash check keeps timing similar |
| Sessions | signed JWT (HS256, default 60 minutes) in an **HttpOnly, SameSite=Lax** cookie; no token in JavaScript or `localStorage`; `Secure` flag via `COOKIE_SECURE=true` behind HTTPS |
| Immediate revocation | the user is loaded from the database on every request, so deactivating an account ends its session at once |
| Authorization | enforced in the backend: `AdminUser` dependency on admin routes; ticket visibility inside `ticket_service` (workers see only tickets they reported or are assigned to, others get 404) |
| No privilege escalation | request schemas have no role/assignee/status fields for workers; extra JSON fields are ignored (tested) |
| Last admin | the last active administrator cannot be deactivated or demoted; nobody can deactivate themselves |
| CSRF | cookie auth plus an Origin check on every write: a cross-site Origin gets 403 (tested) |
| CORS | explicit origin list (`CORS_ORIGINS`), credentials allowed only for those, never a wildcard |
| Input validation | Pydantic on every request: lengths, enums, trimmed text, username pattern |
| SQL injection | ORM with bound parameters only; no SQL built from user input |
| CSV export | cells starting with `=`, `+`, `-`, `@` are prefixed with `'` to stop spreadsheet formula injection |
| Error handling | one error shape; unexpected errors are logged server-side and returned as a generic message; `/ready` never reveals paths or exception text |
| Secrets | `SECRET_KEY` is mandatory, at least 32 characters, and the placeholder `change-me` is rejected at start; `.env` is git-ignored; Terraform `secret_key` is a sensitive variable; Ansible reads it from the environment or Vault |
| Seed data | demo users exist only after the explicit `seed_demo_data.py --yes` command, which refuses `ENVIRONMENT=production`; no default accounts |
| Containers | non-root user, `no-new-privileges`, capabilities dropped, memory and CPU limits, no Docker socket, no privileged mode, backend port not published |
| Browser hardening | nginx sends CSP, `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy` |
| No third-party calls | no CDN, web font, analytics or external API at run time |

## Known limitations

- **No rate limiting or account lockout.** Repeated password guessing is not slowed down. For a shared network put a reverse proxy with rate limiting in front, or add it before wider use.
- **No HTTPS by default.** Traffic on the local network is plain HTTP. Use a TLS-terminating proxy and set `COOKIE_SECURE=true` if the network is not trusted.
- **Sessions cannot be revoked individually** (only by deactivating the user or changing `SECRET_KEY`, which logs everyone out). Logout removes the cookie in the browser; an already copied token stays valid until it expires.
- **SQLite file permissions** depend on the host. Backups are plain files containing all data (including password hashes); protect them.
- **Swagger UI `/docs` is public** (it only describes the API). Disable it if you do not want that.
- The CSP for `/docs` allows inline scripts because Swagger UI starts with one; the application pages use a strict policy.
- Dependencies were current when the project was built (the frontend `npm audit` reported 0 vulnerabilities then). Re-run `pip list --outdated`, `pip-audit` and `npm audit` before any real use.

## Changing the demo credentials

Demo accounts share one password printed by the seed command. Change it with `DEMO_PASSWORD=...` when seeding, or sign in as
`demo_admin` and use **Users, Reset password** for each account (admins) and **My account** (workers). Delete demo users by
deactivating them. Never run the seed command against a database that holds real records.
