import os

from web.app import app

if __name__ == "__main__":
    # 0.0.0.0: 사내 LAN의 다른 PC에서 본인 PC IP:포트로 접속 가능
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_RUN_PORT", "5000"))
    app.run(host=host, port=port, debug=True)
