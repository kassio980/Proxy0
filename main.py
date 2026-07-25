#!/usr/bin/env python3
"""
🕵️ PROXY OKAIDA — ARQUIVO PRINCIPAL
✅ Roda LOCAL no Termux (Proxy SOCKS5/UDP + TUDO)
✅ Roda NA NUVEM no Render (Painel público + Login + API + Mapa + Códigos Wi-Fi)
✅ Login com chave: okaida2026
✅ Anti-Ban 20 camadas · Capa no Ar · Avião · IP Logger
"""
import os, sys, time, json, threading
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# Cria pastas obrigatórias
for p in ["logs","capturas","db","scripts","www","templates","geoip"]:
    os.makedirs(f"{BASE}/{p}", exist_ok=True)

# Garante config padrão
import perfis
if not os.path.exists(f"{BASE}/config.json"):
    perfis.salvar(perfis.carregar())
CFG = perfis.carregar()

# ==========================================================
# 🚀 DECIDE MODO: RENDER (nuvem) vs LOCAL (Termux)
# ==========================================================
MODO_RENDER = bool(os.environ.get("RENDER","") or os.environ.get("PORT",""))
PORTA_WEB  = int(os.environ.get("PORT", CFG["PROXY"]["PAINEL"]))

print(f"\n\033[32m\033[1m" + "═"*60 + "\033[0m")
print(f"\033[32m\033[1m   🕵️ PROXY OKAIDA  ·  MODO: {'☁️ RENDER NUVEM' if MODO_RENDER else '📱 TERMUX LOCAL'}\033[0m")
print(f"\033[32m\033[1m" + "═"*60 + "\033[0m\n")

# ==========================================================
# 📱 MODO LOCAL (TERMUX): liga PROXY SOCKS5 + UDP + VÍRUS
# ==========================================================
if not MODO_RENDER:
    try:
        import proxy_core, virus_mode, wifi_share
        proxy_core.iniciar()
        threading.Thread(target=virus_mode.iniciar, daemon=True).start()
        threading.Thread(target=wifi_share.iniciar, daemon=True).start()
        print(f"   🧦 SOCKS5 :{CFG['PROXY']['SOCKS']}")
        print(f"   🚀 UDP    :{CFG['PROXY']['UDP']}")
        print(f"   🦠 MODO VÍRUS · ADB WI-FI · CONECTA AUTOMÁTICO FF")
    except Exception as e:
        print(f"   ⚠️  Proxy local não iniciou: {e}")

# ==========================================================
# 🌐 TANTO FAZ: LIGA PAINEL WEB + LOGIN + API + SOCKET
# ==========================================================
try:
    from app_web import app, socketio
    print(f"   🕸️ PAINEL :{PORTA_WEB}")
    print(f"   🔐 LOGIN  : chave mestra = okaida2026")
except Exception as e:
    print(f"\033[31m❌ ERRO app_web: {e}\033[0m"); sys.exit(1)

# Rota raiz segura
@app.route("/")
def home():
    from auth import chave_valida
    from flask import request, redirect, make_response
    k = request.cookies.get("okaida_key") or request.args.get("key")
    if k and chave_valida(k):
        resp = make_response(redirect("/dash"))
        resp.set_cookie("okaida_key", k, max_age=7*86400)
        return resp
    return redirect("/login")

@app.route("/dash")
def dash():
    from auth import requer_login
    return requer_login(lambda: __import__('app_web').index())()

@app.route("/health")
def health():
    from geo_users import USERS
    from extras_hacker import IP
    return {
        "ok": True,
        "modo": "RENDER" if MODO_RENDER else "TERMUX",
        "hora": datetime.now().isoformat(),
        "ips_unicos": IP.total_unicos,
        "online": len(USERS.todos_online()),
        "paises": len(IP.por_pais),
        "proxy_okaida": "v2.0 HACKER"
    }

@app.route("/api/flags")
def api_flags():
    from extras_hacker import FLAGS
    return {"ok":True,"flags":FLAGS}

@app.route("/api/flags/<nome>/<int:valor>")
def api_set_flag(nome,valor):
    from auth import requer_login
    from extras_hacker import set_flag
    return requer_login(lambda: {"ok":True,"flags":set_flag(nome,bool(valor))})()

@app.route("/api/ips")
def api_ips():
    from extras_hacker import IP
    return {"ok":True, **IP.resumo()}

# ==========================================================
# 🚀 LIGA TUDO
# ==========================================================
if __name__=="__main__":
    print(f"\n\033[32m✅ TUDO CARREGADO · LIGANDO NA PORTA {PORTA_WEB}\033[0m")
    print(f"   🌐 Acesse: http{'s' if MODO_RENDER else ''}://{'SEU_DOMINIO_RENDER' if MODO_RENDER else '127.0.0.1:'+str(PORTA_WEB)}\n")
    try:
        socketio.run(app, host="0.0.0.0", port=PORTA_WEB, allow_unsafe_werkzeug=True, debug=False, async_mode="threading")
    except KeyboardInterrupt:
        print("\n👋 Desligando...")
        sys.exit(0)
