# YCAP Mail System — README

Welcome to **YCAP Mail System**, a delightfully chaotic, semi-secure, developer-crafted email stack. It comes with a server, a client, and a web UI — and a protocol that absolutely *rizzes*. If you like packets, brainrot, and a tiny bit of cryptography, you’re in the right place.

> ⚠️ This project is intentionally playful and experimental. Treat it as a learning/demo toy — not a production-ready mail server.

---

## Table of Contents
1. [Features](#features)
2. [YCAP Protocol: The Email BRAINROT](#ycap-protocol-the-email-brainrot)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
   - [Run the Server](#run-the-server)
   - [Run the Web App](#run-the-web-app)
   - [Using the Client API](#using-the-client-api)
6. [Commands (Quick Reference)](#commands-quick-reference)
7. [Database & Storage](#database--storage)
8. [Troubleshooting](#troubleshooting)
9. [Contributors & Credits](#contributors--credits)
10. [License](#license)

---

## Features

- **Custom YCAP protocol** for fun messaging between client and server.
- **Fernet encryption** for exchanged keys (toy-level crypto — don't ship this to the moon).
- **SQLite persistence** (`mails.db`) for users and emails.
- **Flask web UI** with inbox/sent/compose/view/delete and Markdown rendering.
- Clear (and occasionally dubious) error handling and warnings for the brave.

---

## YCAP Protocol: The Email BRAINROT

Welcome to the YCAP Email Protocol, where emails rizz, packets noop, and servers occasionally watch brainrot. Below are the official (no cap fr fr) specs — read the meme part first, then the serious bits below it.

### 1. Connection Initiation 🤝
- Client: "Hey, SKIBIDI, wanna chat?"
- Server: "Sure, but first, take this random key. It's shiny NCAP FR."
- Client: "Thanks! My email is gonzaliz^ycap.com. Don't spam me FR."

### 2. Commands (The rizzers of server) 🪄

#### YCAP
- **Purpose:** To check if the server is capping or not.
- **Packet:**
```json
{
  "connection_key": "<your shiny key>",
  "command": "YCAP",
  "arguments": [["localhost", 1200]]
}
```
- **Server Response:** `{ "return": ["OK"] }` (If server is feeling good vibes)

#### NRIZZ
- **Purpose:** GOODBYE! CHANGE TH WRLD.
- **Packet:**
```json
{
  "connection_key": "<your shiny key>",
  "command": "NRIZZ",
  "arguments": ["GOODBYE"]
}
```
- **Server Response:** `{ "return": ["GOODBYE"] }` (tear falls)

#### NOOP
- **Purpose:** Brainrot test. Keep-alive / silly ping.
- **Packet:**
```json
{
  "connection_key": "<your shiny key>",
  "command": "NOOP",
  "arguments": ["NOOP"]
}
```
- **Server Response:** `{ "return": ["NOOP"] }` (The server sends brainrot back)

#### YAP
- **Purpose:** Send a mail (YAP = yap about mail).
- **Packet:**
```json
{
  "connection_key": "<your shiny key>",
  "command": "YAP",
  "arguments": [["FROM", "TO"], "TYPE", "DATA"]
}
```
- **Server Response:** `["MAIL_SENT", "<mail_id>"]` or `["MAIL_NOT_SENT", "<reason>"]`

#### LYAP
- **Purpose:** List mail IDs (inbox or sent).
- **Packet:**
```json
{
  "connection_key": "<your shiny key>",
  "command": "LYAP",
  "arguments": [true]  // sent=True for sent box, False for inbox
}
```
- **Server Response:** `{ "return": [<mail_id>, ...] }`

#### GMA
- **Purpose:** Get Mail by ID.
- **Packet:**
```json
{
  "connection_key": "<your shiny key>",
  "command": "GMA",
  "arguments": ["<mail_id>"]
}
```
- **Server Response:** The mail row: `[id, from, to, type, data]`

#### NYAP
- **Purpose:** Delete a mail by ID.
- **Packet:**
```json
{
  "connection_key": "<your shiny key>",
  "command": "NYAP",
  "arguments": ["<mail_id>"]
}
```
- **Server Response:** `["MAIL_DELETED", "<mail_id>"]` or `["MAIL_NOT_DELETED", "<reason>"]`

### 3. Error Handling (aka Blame the Client) 🚨
- Wrong key → server drops you and probably laughs.
- Unknown command → server ignores and watches brainrot.
- LYAP/visibility checks prevent listing other people's mail (attempts are detected and rejected).

### 4. Database
- All emails and users are stored in `mails.db` (SQLite). Guarded by a very rizzed SQLite DB.

### 5. Fun Facts
- Invented by a committee of sleep-deprived squirrels (aka developers).
- "YCAP" stands for "Yetting Capping And Porting" (citation needed).

---

## Installation

1. Clone the repo:
```bash
git clone https://github.com/yourusername/ycap-mail.git
cd ycap-mail
```

2. Create a virtualenv (recommended):
```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\activate    # Windows PowerShell
```

3. Install dependencies:
```bash
pip install flask cryptography markdown
```

4. Set the `YCAP_KEY` environment variable (shared between server & client):

macOS / Linux:
```bash
export YCAP_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

Windows (PowerShell):
```powershell
setx YCAP_KEY (python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

---

## Configuration

- Default host: `localhost`  
- Default port: `1200`  
- Change these values in `server.py` and `app.py` if you want the server to listen elsewhere.

---

## Usage

### Run the Server
```bash
python server.py
```
Server will create `mails.db` automatically and start listening on the configured port.

### Run the Web App
```bash
python app.py
```
Open `http://127.0.0.1:5000` in your browser. The Flask app uses the same YCAP client code to interact with the server.

### Using the Client API
```python
from client import Client, sign_up

# Signup a user (client-side helper that performs signup flow)
sign_up("alice^ycap.com", "mypassword", "localhost", 1200)

# Connect and send mail
client = Client("localhost", 1200, "alice^ycap.com", "mypassword")
client.send_mail("bob^ycap.com", "text", "Hello, Bob!")
```

---

## Commands (Quick Reference)
- `YCAP` — handshake/verify server
- `YAP` — send mail
- `LYAP` — list mail IDs (sent/inbox)
- `GMA` — fetch mail by ID
- `NYAP` — delete mail by ID
- `NOOP` — ping/brainrot test
- `NRIZZ` — logout

---

## Database & Storage

- Database file: `mails.db`
- Tables:
  - `users` (`username`, `password`)
  - `mail` (`id` (PK autoinc), `from_`, `to_`, `type_`, `data`, `id` (yes, there is a duplicate column name in the provided code — consider fixing to avoid confusion) )

> ⚠️ NOTE: The `mail` table in `server.py` currently creates two columns named `id` (one AUTOINCREMENT integer PK and another `id` field used as token `mail_id`). This will cause issues or confusion. Consider renaming the token column to `mail_token` or making the primary key the token itself.

---

## Troubleshooting

- **Port in use / bind error:** Choose another port or free the port.
- **Login fails:** Ensure signup completed and passwords match. Check server logs for errors.
- **Encryption errors / Invalid token:** Verify `YCAP_KEY` is set and the server & clients use compatible keys.
- **Emails not delivered:** Recipient must be signed up (exists in `users` table).

If you hit a bug that looks criminally funny, open an issue — we want to hear your brainrot stories.

---

## Contributors & Credits

- Author: Skanda
- Inspired by coffee, tired devs, and "Face Dev" project memes.

---

## License

MIT License. Use responsibly, and please don't cause too much chaos with this protocol.

---

*If you read this far, congratulations — you are now a Certified YCAP Brainrot Specialist.*
