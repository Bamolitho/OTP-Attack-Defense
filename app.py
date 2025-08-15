
from flask import Flask, request, session, render_template_string, redirect, url_for
import os, time, random

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

OTP_TTL_SECONDS = int(os.environ.get("OTP_TTL_SECONDS", "60"))       # durée de validité OTP
LOCK_COOLDOWN_SECONDS = int(os.environ.get("LOCK_COOLDOWN_SECONDS", "10"))  # verrouillage après x erreurs (demo)
MAX_ATTEMPTS = int(os.environ.get("MAX_ATTEMPTS", "3"))              # tentatives autorisées

DEBUG_SHOW_CODE = os.environ.get("DEBUG_SHOW_CODE", "1") == "1"      # affiche l'OTP pour le lab

TEMPLATE = '''
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Lab OTP - Démo Sécurisée</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; }
    .card { max-width: 620px; padding: 1.25rem; border: 1px solid #ddd; border-radius: 12px; }
    h1 { margin-top: 0; }
    .debug { padding: .5rem .75rem; border-radius: 8px; background: #f7f7f7; border: 1px dashed #aaa; margin-bottom: 1rem; }
    .ok { padding: .75rem 1rem; border-radius: 8px; background: #e6ffed; border: 1px solid #b7f5c3; }
    .err { padding: .75rem 1rem; border-radius: 8px; background: #fff4f4; border: 1px solid #ffc7c7; }
    form { display: flex; gap: .5rem; align-items: center; }
    input[type="text"] { padding: .5rem .75rem; font-size: 1rem; border: 1px solid #ccc; border-radius: 8px; width: 200px; }
    button { padding: .6rem .9rem; border-radius: 8px; border: 1px solid #333; background: #333; color: #fff; cursor: pointer; }
    .meta { color: #666; font-size: .9rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Validation OTP (Lab défensif)</h1>

    {% if debug_code %}
    <div class="debug">
      <strong>DEBUG (lab) :</strong> code OTP actuel = <code>{{ debug_code }}</code><br>
      expire à {{ expiry_readable }} — tentatives restantes : {{ attempts_left }}
    </div>
    {% endif %}

    {% if message %}
      <div class="{{ 'ok' if success else 'err' }}">{{ message }}</div>
    {% endif %}

    <form method="post" action="{{ url_for('verify') }}">
      <label for="otp">Code (6 chiffres)</label>
      <input id="otp" name="otp" type="text" inputmode="numeric" pattern="\\d{6}" maxlength="6" required />
      <button type="submit">Valider</button>
    </form>

    <p class="meta">
      Politique : {{ MAX_ATTEMPTS }} tentatives, verrouillage {{ LOCK_COOLDOWN_SECONDS }}s, OTP TTL {{ OTP_TTL_SECONDS }}s.
    </p>
    <p><a href="{{ url_for('reset') }}">[Re-générer un OTP]</a></p>
  </div>
</body>
</html>
'''

def _now():
    return int(time.time())

def _new_otp():
    return f"{random.randint(0, 999999):06d}"

def ensure_context():
    if "otp" not in session or _now() >= session.get("otp_expiry", 0):
        session["otp"] = _new_otp()
        session["otp_expiry"] = _now() + OTP_TTL_SECONDS
        session["attempts"] = 0
        session["lock_until"] = 0

@app.route("/", methods=["GET"])
def index():
    ensure_context()
    debug_code = session["otp"] if DEBUG_SHOW_CODE else None
    expiry_readable = time.strftime("%H:%M:%S", time.localtime(session["otp_expiry"]))
    attempts_left = max(0, MAX_ATTEMPTS - session.get("attempts", 0))
    return render_template_string(
        TEMPLATE,
        message=None,
        success=False,
        debug_code=debug_code,
        expiry_readable=expiry_readable,
        attempts_left=attempts_left,
        MAX_ATTEMPTS=MAX_ATTEMPTS,
        LOCK_COOLDOWN_SECONDS=LOCK_COOLDOWN_SECONDS,
        OTP_TTL_SECONDS=OTP_TTL_SECONDS,
    )

@app.route("/verify", methods=["POST"])
def verify():
    ensure_context()
    now = _now()
    locked = session.get("lock_until", 0)
    if now < locked:
        wait = locked - now
        return render_template_string(
            TEMPLATE, message=f"Compte verrouillé. Réessaie dans {wait}s.",
            success=False, debug_code=session["otp"] if DEBUG_SHOW_CODE else None,
            expiry_readable=time.strftime("%H:%M:%S", time.localtime(session["otp_expiry"])),
            attempts_left=max(0, MAX_ATTEMPTS - session.get('attempts', 0)),
            MAX_ATTEMPTS=MAX_ATTEMPTS, LOCK_COOLDOWN_SECONDS=LOCK_COOLDOWN_SECONDS, OTP_TTL_SECONDS=OTP_TTL_SECONDS
        )
    if now >= session["otp_expiry"]:
        # Expiré → régénérer
        session["otp"] = _new_otp()
        session["otp_expiry"] = now + OTP_TTL_SECONDS
        session["attempts"] = 0
        session["lock_until"] = 0
        return render_template_string(
            TEMPLATE, message="OTP expiré → nouveau OTP généré.", success=False,
            debug_code=session["otp"] if DEBUG_SHOW_CODE else None,
            expiry_readable=time.strftime("%H:%M:%S", time.localtime(session["otp_expiry"])),
            attempts_left=MAX_ATTEMPTS,
            MAX_ATTEMPTS=MAX_ATTEMPTS, LOCK_COOLDOWN_SECONDS=LOCK_COOLDOWN_SECONDS, OTP_TTL_SECONDS=OTP_TTL_SECONDS
        )
    code = (request.form.get("otp") or "").strip()
    if code == session["otp"]:
        # Succès : régénérer un OTP pour prochaine opération
        session["otp"] = _new_otp()
        session["otp_expiry"] = now + OTP_TTL_SECONDS
        session["attempts"] = 0
        session["lock_until"] = 0
        return render_template_string(
            TEMPLATE, message=" OTP bon : authentification réussie (lab). Nouveau OTP généré.",
            success=True, debug_code=session["otp"] if DEBUG_SHOW_CODE else None,
            expiry_readable=time.strftime("%H:%M:%S", time.localtime(session["otp_expiry"])),
            attempts_left=MAX_ATTEMPTS,
            MAX_ATTEMPTS=MAX_ATTEMPTS, LOCK_COOLDOWN_SECONDS=LOCK_COOLDOWN_SECONDS, OTP_TTL_SECONDS=OTP_TTL_SECONDS
        )
    else:
        session["attempts"] = session.get("attempts", 0) + 1
        if session["attempts"] >= MAX_ATTEMPTS:
            session["lock_until"] = now + LOCK_COOLDOWN_SECONDS
            return render_template_string(
                TEMPLATE, message=f"❌ Code incorrect. Trop d'essais : verrouillage {LOCK_COOLDOWN_SECONDS}s.",
                success=False, debug_code=session["otp"] if DEBUG_SHOW_CODE else None,
                expiry_readable=time.strftime("%H:%M:%S", time.localtime(session["otp_expiry"])),
                attempts_left=0,
                MAX_ATTEMPTS=MAX_ATTEMPTS, LOCK_COOLDOWN_SECONDS=LOCK_COOLDOWN_SECONDS, OTP_TTL_SECONDS=OTP_TTL_SECONDS
            )
        else:
            attempts_left = MAX_ATTEMPTS - session["attempts"]
            return render_template_string(
                TEMPLATE, message=f"❌ Code incorrect. Tentatives restantes : {attempts_left}.",
                success=False, debug_code=session["otp"] if DEBUG_SHOW_CODE else None,
                expiry_readable=time.strftime("%H:%M:%S", time.localtime(session["otp_expiry"])),
                attempts_left=attempts_left,
                MAX_ATTEMPTS=MAX_ATTEMPTS, LOCK_COOLDOWN_SECONDS=LOCK_COOLDOWN_SECONDS, OTP_TTL_SECONDS=OTP_TTL_SECONDS
            )

@app.route("/reset")
def reset():
    session.clear()
    ensure_context()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
