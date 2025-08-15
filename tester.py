
import requests, re, time

BASE = "http://127.0.0.1:5001/"
s = requests.Session()

def get_debug_code(html):
    # Cherche "code OTP actuel = <code>123456</code>"
    m = re.search(r"code OTP actuel = <code>(\d{6})</code>", html)
    return m.group(1) if m else None

def main():
    print("[*] Récupération de la page d'accueil…")
    r = s.get(BASE, timeout=5)
    r.raise_for_status()
    code = get_debug_code(r.text)
    if not code:
        print("[!] Impossible de lire le code debug dans la page. Assure-toi que DEBUG_SHOW_CODE=1")
        return

    print(f"[*] Code OTP actuel (debug lab) = {code}")
    wrongs = ["000000", "111111", "222222"]
    for w in wrongs:
        print(f"[-] Tentative avec mauvais code {w} …")
        r = s.post(BASE + "verify", data={"otp": w}, timeout=5)
        print(f"    Statut: {r.status_code} | Réponse courte: ", re.sub(r"\s+", " ", r.text[:200]))

    print("[*] Nouvelle tentative (verrouillage en place ?)…")
    r = s.post(BASE + "verify", data={"otp": code}, timeout=5)
    print(f"    Statut: {r.status_code} | Extrait: ", re.sub(r"\s+", " ", r.text[:200]))

    print("[*] Attente 11 secondes pour la fin du verrouillage…")
    time.sleep(11)

    print("[*] Récupération du nouveau code (l'app régénère l'OTP après succès)…")
    r = s.get(BASE, timeout=5)
    r.raise_for_status()
    new_code = get_debug_code(r.text)
    print(f"[*] Nouveau code OTP (debug) = {new_code}")

    print("[+] Tentative avec le bon code…")
    r = s.post(BASE + "verify", data={"otp": new_code}, timeout=5)
    print(f"    Statut: {r.status_code} | Extrait: ", re.sub(r"\s+", " ", r.text[:200]))

if __name__ == "__main__":
    main()
