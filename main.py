#!/usr/bin/env python3
import os, sys, time
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

for p in ["logs","capturas","db","scripts","www","templates"]:
    os.makedirs(f"{BASE}/{p}", exist_ok=True)

try:
    import perfis
    if not os.path.exists(f"{BASE}/config.json"): perfis.salvar(perfis.carregar())
except: pass

MODO_RENDER = bool(os.environ.get("RENDER","") or os.environ.get("PORT","") or os.environ.get("RENDER_EXTERNAL_URL",""))
PORTA = int(os.environ.get("PORT", 8888))

print("\n\033[32m\033[1m" + "═"*60 + "\033[0m")
print(f"\033[32m\033[1m   🕵️ PROXY OKAIDA  ·  {'☁️  RENDER NUVEM' if MODO_RENDER else '📱 TERMUX LOCAL'}\033[0m")
print("\033[32m\033[1m" + "═"*60 + "\033[0m\n")

if not MODO_RENDER:
    for mod,nome in [("proxy_core","🧦 PROXY"),("virus_mode","🦠 VÍRUS"),("wifi_share","📶 WI-FI")]:
        try:
            m = __import__(mod)
            if nome=="🧦 PROXY":
                m.iniciar()
                print(f"   {nome} :{m.CFG['PROXY']['SOCKS']} / UDP :{m.CFG['PROXY']['UDP']}")
            else:
                threading = __import__("threading")
                threading.Thread(target=m.iniciar, daemon=True).start()
                print(f"   {nome} OK")
        except Exception as e:
            print(f"   ⚠️  {nome}: {e}")

import importlib.util
spec = importlib.util.spec_from_file_location("app_web", f"{BASE}/app_web.py")
aw = importlib.util.module_from_spec(spec); spec.loader.exec_module(aw)
app = aw.app; socketio = aw.socketio
print(f"   🕸️ PAINEL WEB :{PORTA}")
print(f"   🔐 LOGIN      : okaida2026")

print(f"\n\033[32m✅ TUDO CARREGADO · INICIANDO\033[0m")
socketio.run(app, host="0.0.0.0", port=PORTA, allow_unsafe_werkzeug=True, debug=False, log_output=False)
