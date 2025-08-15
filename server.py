from flask import Flask, request, jsonify

app = Flask(__name__)

# OTP fixe pour la démo
SECRET_OTP = "654321"

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    code = data.get("otp", "")

    if code == SECRET_OTP:
        return jsonify({"status": "success", "message": "OTP correct"}), 200
    else:
        return jsonify({"status": "fail", "message": "OTP incorrect"}), 401

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000)
