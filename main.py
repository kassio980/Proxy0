#!/usr/bin/env python3
"""
🕵️ PROXY OKAIDA — MAIN
✅ RENDER (nuvem): só roda PAINEL WEB + LOGIN + API
✅ TERMUX (celular): roda TUDO (proxy + painel + virus + wifi)
"""
import os, sys, time
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# Pastas obrigatórias
for p in ["logs","capturas","db","scripts","www","templates"]:
    os.makedirs(f"{BASE}/{p}", exist_ok=True)

# Garante config padrão
try:
    import perfis
    if not os.path.exists(f"{BASE}/config.json"): perfis.salvar(perfis.carregar())
except: pass

# DETECTA MODO
MODO_RENDER = bool(os.environ.get("RENDER","") or os.environ.get("PORT","") or os.environ.get("RENDER_EXTERNAL_URL",""))
PORTA = int(os.environ.get("PORT", os.environ.get("PAINEL_PORTA", 8888)))

print("\n\033[32m\033[1m" + "═"*60 + "\033[0m")
print(f"\033[32m\033[1m   🕵️ PROXY OKAIDA  ·  {'☁️  MODO RENDER (NUVEM)' if MODO_RENDER else '📱 MODO TERMUX (LOCAL)'}\033[0m")
print("\033[32m\033[1m" + "═"*60 + "\033[0m\n")

# ==========================================================
# 📱 SÓ NO TERMUX: LIGA PROXY + VÍRUS + WI-FI
# ==========================================================
if not MODO_RENDER:
    try:
        import proxy_core
        proxy_core.iniciar()
        print(f"   🧦 SOCKS5 :{proxy_core.CFG['PROXY']['SOCKS']}")
        print(f"   🚀 UDP    :{proxy_core.CFG['PROXY']['UDP']}")
    except Exception as e:
        print(f"   ⚠️  Proxy local: {e}")
    try:
        import threading, virus_mode
        threading.Thread(target=virus_mode.iniciar, daemon=True).start()
        print(f"   🦠 MODO VÍRUS · ADB WI-FI")
    except Exception as e:
        print(f"   ⚠️  Vírus: {e}")
    try:
        import threading, wifi_share
        threading.Thread(target=wifi_share.iniciar, daemon=True).start()
        print(f"   📶 WI-FI SHARE · CÓDIGO 6D")
    except Exception as e:
        print(f"   ⚠️  Wi-Fi: {e}")

# ==========================================================
# 🌐 TANTO FAZ: CARREGA PAINEL WEB (SAFE IMPORT)
# ==========================================================
try:
    sys.path.insert(0, BASE)
    # Importa app_web de forma segura
    if "app_web" not in sys.modules:
        import importlib.util
        spec = importlib.util.spec_from_file_location("app_web", f"{BASE}/app_web.py")
        app_web = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_web)
        app = app_web.app
        socketio = app_web.socketio
    else:
        app_web = sys.modules["app_web"]
        app = app_web.app
        socketio = app_web.socketio
    print(f"   🕸️ PAINEL WEB :{PORTA}")
    print(f"   🔐 LOGIN     : chave = okaida2026")
except Exception as e:
    print(f"\033[31m❌ ERRO AO CARREGAR PAINEL: {e}\033[0m")
    import traceback; traceback.print_exc()
    sys.exit(1)

# Rotas seguras
@app.route("/")
def home():
    from flask import request, redirect, make_response
    try: from auth import chave_valida
    except: return redirect("/login")
    k = request.cookies.get("okaida_key") or request.args.get("key")
    if k and chave_valida(k):
        r = make_response(redirect("/dash"))
        r.set_cookie("okaida_key", k, max_age=7*86400)
        return r
    return redirect("/login")

@app.route("/dash")
def dash():
    try:
        from auth import requer_login
        return requer_login(lambda: app_web.index())()
    except Exception as e:
        return f"Painel: {e}", 500

@app.route("/health")
def health():
    return {"ok":True,"modo":"RENDER" if MODO_RENDER else "TERMUX","proxy_okaida":"v2.2","hora":time.strftime("%Y-%m-%d %H:%M:%S")}

@app.route("/api/flags")
def api_flags():
    try: from extras_hacker import FLAGS; return {"ok":True,"flags":FLAGS}
    except: return {"ok":False}

@app.route("/api/ips")
def api_ips():
    try: from extras_hacker import IP; return {"ok":True, **IP.resumo()}
    except: return {"ok":False}

# ==========================================================
# 🚀 LIGA
# ==========================================================
print(f"\n\033[32m✅ TUDO CARREGADO · INICIANDO NA PORTA {PORTA}\033[0m")
if MODO_RENDER:
    # RENDER: usa gunicorn por fora, mas se cair aqui usa werkzeug seguro
    socketio.run(app, host="0.0.0.0", port=PORTA, allow_unsafe_werkzeug=True, debug=False, log_output=False)
else:
    socketio.run(app, host="0.0.0.0", port=PORTA, allow_unsafe_werkzeug=True, debug=False, async_mode="threading")
