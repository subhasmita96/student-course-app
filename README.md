# Student Course Portal (Docker + Node.js + PostgreSQL 17)

A small full-stack app: students register/login, browse courses, and enroll.
Everything is stored in PostgreSQL. Two containers, wired together with docker-compose.

## Project layout
```
student-course-app/
├── docker-compose.yml
├── db/
│   └── init.sql          # creates tables + seeds sample courses (runs once, on first DB startup)
└── backend/
    ├── Dockerfile         # node:latest image
    ├── package.json
    ├── server.js          # Express API (register/login/courses/enroll)
    └── public/            # static frontend (served by Express) — index.html, style.css, app.js
```

## Step 1 — Prerequisites
- Docker Desktop (or Docker Engine + docker-compose) installed and running.
- Nothing else needed — Node.js and PostgreSQL run inside containers.

## Step 2 — Get the files
Unzip the project, then open a terminal in the `student-course-app` folder:
```bash
cd student-course-app
```

## Step 3 — Build and start the containers
```bash
docker compose up --build
```
This will:
1. Pull `postgres:17` and start the DB container, running `db/init.sql` automatically the
   first time (creates `students`, `courses`, `enrollments` tables and seeds 5 sample courses).
2. Build the Node.js app image (`node:latest`) and install dependencies (`express`, `pg`, `bcryptjs`, `cors`).
3. Start the Node app, which waits/retries until PostgreSQL is ready, then listens on port 3000.

Wait until you see:
```
sc_app  | Connected to PostgreSQL
sc_app  | Server running on http://localhost:3000
```

## Step 4 — Access the app locally
Open your browser at:
```
http://localhost:3000
```
- Go to the **Register** tab, create a student account (name, email, password).
- Switch to **Login** and sign in — this calls the API and stores the returned student
  record in the DB (password is hashed with bcrypt, never stored in plain text).
- Browse the **Available Courses** list (loaded from PostgreSQL) and click **Enroll**.
- Your enrollments appear under **My Enrollments**, all persisted in the `enrollments` table.

## Step 5 — Verify data landed in PostgreSQL
```bash
docker exec -it sc_db psql -U appuser -d studentdb
```
Then inside psql:
```sql
SELECT * FROM students;
SELECT * FROM courses;
SELECT * FROM enrollments;
```

## Step 6 — Stopping / resetting
```bash
docker compose down          # stop containers, keep DB data (named volume)
docker compose down -v       # stop containers AND wipe DB data (fresh start next time)
```

## Notes / where to extend
- **Ports**: app → `3000`, Postgres → `5432` (both mapped to localhost; change the left
  side of `ports:` in `docker-compose.yml` if either is already in use on your machine).
- **Credentials**: DB user/password are set as plain env vars in `docker-compose.yml` for
  simplicity (`appuser` / `apppassword`). For anything beyond local testing, move these into
  a `.env` file (git-ignored) or Docker secrets instead of committing them.
- **Auth**: this demo keeps the logged-in student in the browser's `localStorage` after a
  successful login check against the hashed password in Postgres. For production use, add
  proper sessions/JWT and HTTPS.
- **Node version**: Dockerfile uses `node:latest`. Pin it (e.g. `node:22-alpine`) once you're
  happy with the setup, so rebuilds stay reproducible.
- **DB schema changes**: `init.sql` only runs the *first* time the Postgres data volume is
  created. If you edit it later, run `docker compose down -v` first so it re-initializes.
  <!-- webhook test -->