# Task 2 – Endpoints and cloud security (MC101)

Builds on Task 1 (FastAPI authentication API for a voting system). Task 2 adds:

- **Logging** – everything is logged (minimum level `INFO`) to `logs/logs.log`.
- **Docker** – a `Dockerfile` and a `docker-compose.yml` in the repo root.

## How to run the app

Prerequisite: Docker with Docker Compose v2, and a `.env` file (`cp .env.example .env`, then set at least `JWT_SECRET_KEY` and the SMTP values).

### 1. Build the image with Docker Compose
```bash
docker compose build
```

### 2. Run the app with Docker Compose
```bash
docker compose up
```
(add `-d` to run in the background). The API is then available at http://localhost:8000 and the docs at http://localhost:8000/docs.

### 3. Stop the app with Docker Compose
```bash
docker compose down
```
(`docker compose down -v` also deletes the stored database volume.)

## Logging

- Log file: **`logs/logs.log`** in the repo (the folder is mounted into the container, so the file appears on your machine). Logs are also printed to the console (`docker compose logs -f`).
- Format: `time | level | logger | message`. Minimum level is `INFO`; the file rotates at 5 MB (3 backups).
- Logged events: app start/stop, registrations, logins (successful and failed), MFA requested / wrong code / success, invalid or missing tokens, wrong-role access (403), account deletions, e-mail sending errors, plus uvicorn's server and access logs.
- **Never logged:** passwords, MFA codes, tokens.
- Configure with `LOG_LEVEL` (`INFO`, `WARNING`, ...) and `LOG_DIR` in `.env`.

## Docker notes
- The image is based on `python:3.12-slim`, installs only the main Poetry dependencies and runs as a non-root user.
- `docker-compose.yml` reads secrets from `.env` (never baked into the image), keeps the SQLite database in the named volume `app-data`, and has a healthcheck on `/`.
- On Linux, if `logs/` is not writable for the container user, build with your uid: `APP_UID=$(id -u) docker compose build`.

---

# Task 1 – Endpoints and cloud security (MC101)

Authentication API for a voting system built with **FastAPI**, managed with **Poetry**.
Users and admins can register, log in, fetch their info and delete themselves.
Admins **always** log in with email + password + a one-time MFA code sent by email (Ethereal SMTP via `smtplib`).

## Setup

```bash
poetry install
cp .env.example .env      # then fill in the values
poetry run python main.py # http://127.0.0.1:8000  (docs: /docs)
poetry run pytest         # run tests
```

### .env
| Variable | Meaning |
|---|---|
| `JWT_SECRET_KEY` | secret used to sign tokens (`python -c "import secrets; print(secrets.token_hex(32))"`) |
| `JWT_ALGORITHM` | e.g. `HS256` |
| `JWT_EXPIRATION_MINUTES` | token lifetime |
| `DATABASE_URL` | default `sqlite:///./app.db` |
| `MFA_EXPIRATION_MINUTES` / `MFA_MAX_ATTEMPTS` | MFA code lifetime / max wrong guesses |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM` | Ethereal SMTP credentials |

### Ethereal
1. Go to https://ethereal.email → **Create Ethereal Account**.
2. Put the SMTP username/password in `.env`.
3. Open the mailbox ("Open Mailbox") to read the MFA codes.
4. Register your admin with **that Ethereal email address** as the admin's email, so the code arrives in your mailbox.

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/v1/users/register` | – | `name`, `email`, `password` (min 8 chars) |
| POST | `/v1/users/login` | – | `email`, `password` → bearer token |
| GET | `/v1/users/info` | Bearer | validates token, returns token payload + profile |
| DELETE | `/v1/users/delete` | Bearer | deletes the logged-in user |
| POST | `/v1/admins/register` | – | `name`, `email`, `password` |
| POST | `/v1/admins/request-mfa` | – | `email`, `password` → emails a 6-digit code |
| POST | `/v1/admins/login` | – | `email`, `password`, `mfa_code` → bearer token |
| GET | `/v1/admins/info` | Bearer | validates token, returns token payload + profile |
| DELETE | `/v1/admins/delete` | Bearer | deletes the logged-in admin |

Send the token as `Authorization: Bearer <token>`.

## Security notes
- Passwords hashed with bcrypt; never returned.
- JWT contains `sub`, `role`, `iat`, `exp`, `jti`. User tokens cannot access admin routes and vice versa (403).
- MFA code: random 6 digits (`secrets`), stored only as an HMAC hash, expires after a few minutes, single use, locked after too many wrong attempts.
- Login errors are generic (no hint whether the email exists).
- Admin registration is open here because the task requires it; in a real system it should be restricted (invite or existing-admin approval).
