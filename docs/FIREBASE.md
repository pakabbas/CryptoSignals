# Firebase browser push (FCM HTTP v1)

CryptoSignals can send BUY/SELL alerts to your browser via Firebase Cloud Messaging. This avoids Gmail SMTP blocks on cloud servers.

## What you already configured

- Firebase **web app** config (apiKey, projectId, etc.) — baked into `app/config/firebase_client.py` defaults; override with env vars if needed.
- **Web Push certificate (VAPID) public key** — same file, `FIREBASE_VAPID_KEY`.

Do **not** use the legacy **Server key** in this app. It is deprecated; the server uses **HTTP v1** with a service account.

## One thing you still need (server)

1. In [Firebase Console](https://console.firebase.google.com/) → Project settings → **Service accounts**.
2. Click **Generate new private key** (JSON file).
3. In GitHub → repo **Settings → Secrets and variables → Actions**, add:
   - Name: `FIREBASE_SERVICE_ACCOUNT_JSON`
   - Value: paste the **entire JSON** file contents (one object).

Deploy writes it to `/var/www/cryptosignals/deploy/firebase-service-account.json` (not in git) and sets `FIREBASE_SERVICE_ACCOUNT_PATH` in `.env`.

## Enable on your machine

1. Deploy (or run locally with the JSON path in `.env`).
2. Open **Settings → Browser push**: `/settings/notifications`
3. Click **Enable notifications**, allow the browser prompt.
4. Click **Send test push**.

Registered tokens are stored in the `push_devices` table.

## Local development

```env
ENABLE_PUSH_ALERTS=true
FIREBASE_SERVICE_ACCOUNT_PATH=D:/path/to/your-firebase-adminsdk.json
```

Optional overrides: `FIREBASE_API_KEY`, `FIREBASE_VAPID_KEY`, `FIREBASE_PROJECT_ID`, etc.

## Security

- Rotate any **legacy Server key** or app passwords that were shared in chat.
- Never commit service account JSON or SMTP passwords to git.
