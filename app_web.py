import os, time, json, threading
BASE = os.path.dirname(os.path.abspath(__file__))

from flask import Flask, render_template_string, request, redirect, make_response, jsonify, session
from flask_socketio import SocketIO

app = Flask(__name__, static_folder="www", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY","okaida-proxy-2026-secret-mestra-v24")
app.config['SESSION_COOKIE_NAME'] = 'okaida_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Carrega AUTH
import auth
auth.injetar_rotas(app)

# Carrega módulos com try/except (NÃO QUEBRA)
MOD = {}
for nome in ["perfis","geo_users","wifi_share","virus_mode"]:
    try: MOD[nome] = __import__(nome)
    except Exception as e: MOD[nome] = None

try: from extras_hacker import FLAGS, set_flag, IP
except: FLAGS={}; set_flag=lambda *a:FLAGS; IP=None

CFG = MOD["perfis"].carregar() if MOD["perfis"] else {}
INICIO = time.time()

def uptime():
    decorr = time.time() - INICIO
    max_s = 7*3600
    pct = min(100, round(decorr/max_s*100,1))
    h = int(decorr//3600); m=int((decorr%3600)//60); s=int(decorr%60)
    return {"texto":f"{h:02d}:{m:02d}:{s:02d}","porcento":pct,"decorrido_s":decorr}

def stats():
    return {
        "uptime": uptime(),
        "flags": FLAGS,
        "perfis": getattr(MOD.get("proxy_core"),"PERFIS",{}),
        "armas": getattr(MOD.get("proxy_core"),"ARMAS",["MP40","SCAR","AK47","M4A1","AWM","M1887","M1014","UMP","XM8","FAMAS","GROZA","SG12","AUG"]),
        "por_arma": CFG.get("CAPA",{}).get("POR_ARMA",{}),
        "usuarios": IP.resumo() if IP else {"online_agora":0,"ips_unicos_total":0,"paises_distintos":0,"top_paises":[],"ultimos_20":[]},
        "geo": MOD["geo_users"].USERS.resumo() if MOD.get("geo_users") else {"mapa":[]},
        "perfil_chave": CFG.get("CAPA",{}).get("PERFIL","SO_CAPA"),
        "perfil_atual": CFG.get("CAPA",{}).get("PERFIL","SO_CAPA"),
        "capa": CFG.get("ESTATISTICAS",{}).get("CAPAS",0),
        "peito": CFG.get("ESTATISTICAS",{}).get("PEITO_CABECA",0),
        "tcp": {"c":CFG.get("ESTATISTICAS",{}).get("CONEXOES_TCP",0)},
        "udp": {"p":CFG.get("ESTATISTICAS",{}).get("PACOTES_UDP",0),"c":CFG.get("ESTATISTICAS",{}).get("CONEXOES_UDP",0)},
    }

def broadcast():
    while True:
        try: socketio.emit("stats", stats())
        except: pass
        time.sleep(1.5)
threading.Thread(target=broadcast,daemon=True).start()

# ========== ROTAS PROTEGIDAS (PRECISA DE LOGIN) ==========
@app.route("/dash")
@auth.requer_login
def dash():
    k = request.cookies.get("okaida_key") or session.get("key")
    info = auth.info_chave(k)
    return render_template_string(open(f"{BASE}/templates/index.html").read(),
        user={"nivel": info["nivel"], "mestra": info.get("mestra",False), "dono": info.get("dono","")},
        key=k, stats=stats())

@app.route("/overlay")
@auth.requer_login
def overlay():
    return app.send_static_file("ff_overlay.html")

@app.route("/api/st")
@auth.requer_login
def api_st(): return jsonify(stats())

@app.route("/api/perfil/<nome>")
@auth.requer_login
def api_perfil(nome):
    if not MOD["perfis"]: return jsonify({"ok":False})
    return jsonify({"ok":MOD["perfis"].set_perfil(nome),"perfil":nome})

@app.route("/api/arma/<arma>/<perfil>")
@auth.requer_login
def api_arma(arma,perfil):
    if not MOD["perfis"]: return jsonify({"ok":False})
    return jsonify({"ok":MOD["perfis"].set_por_arma(arma,perfil),"arma":arma,"perfil":perfil})

@app.route("/api/flags/<nome>/<int:v>")
@auth.requer_login
def api_flag(nome,v):
    return jsonify({"ok":True,"flags":set_flag(nome,bool(v))})

@app.route("/api/hack/<nome>/<int:v>")
@auth.requer_login
def api_hack(nome,v):
    try:
        from proxy_core import HACKS
        if nome in HACKS:
            HACKS[nome]["ativo"]=bool(v)
            FLAGS[nome]=bool(v)
        return jsonify({"ok":True,"hacks":{k:v["ativo"] for k,v in HACKS.items()}})
    except Exception as e: return jsonify({"ok":False,"erro":str(e)})

@app.route("/api/hacks")
@auth.requer_login
def api_hacks():
    try:
        from proxy_core import HACKS
        return jsonify({"ok":True,"hacks":HACKS})
    except: return jsonify({"ok":False})

@app.route("/api/fullvermelho/<int:n>")
@auth.requer_login
def api_fv(n):
    try:
        from extras_hacker import set_fullvermelho, stats_fullvermelho
        return jsonify({"ok":True, **set_fullvermelho(n), "stats":stats_fullvermelho()})
    except Exception as e: return jsonify({"ok":False,"erro":str(e)})

@app.route("/api/linha")
@auth.requer_login
def api_linha():
    try:
        from proxy_core import LINHA
        return jsonify({"ok":True, **LINHA.dados_linha()})
    except Exception as e: return jsonify({"ok":False,"ativa":False,"erro":str(e)})

@app.route("/api/wifi/novo")
@auth.requer_login
def api_wifi():
    if not MOD["wifi_share"]: return jsonify({"ok":False})
    d = MOD["wifi_share"].gerar_codigo_compartilhamento()
    return jsonify({"ok":True,"dados":d,"qr_wifi":MOD["wifi_share"].gerar_qr_wifi(d),"qr_proxy_b64":MOD["wifi_share"].gerar_qr_proxy(d)})

@app.route("/api/codigo/<cod>")
@auth.requer_login
def api_codigo(cod):
    u = MOD["wifi_share"].validar_codigo(cod) if MOD["wifi_share"] else None
    return jsonify({"ok":bool(u),"dados":u or {}})

@app.route("/api/virus/abrir_ff")
@auth.requer_login
def api_ff():
    ok = MOD["virus_mode"].abrir_free_fire() if MOD["virus_mode"] else False
    return jsonify({"ok":bool(ok)})

@app.route("/api/virus/desativar_proxy")
@auth.requer_login
def api_ff_off():
    ok = MOD["virus_mode"].desativar_proxy() if MOD["virus_mode"] else False
    return jsonify({"ok":bool(ok)})

@app.route("/health")
def health():
    return jsonify({"ok":True,"modo":"RENDER" if os.environ.get("RENDER") else "TERMUX","proxy_okaida":"v2.4","hora":time.strftime("%Y-%m-%d %H:%M:%S")})

if __name__=="__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT",8888)), allow_unsafe_werkzeug=True)


# ========== ROTAS DA ABA WI-FI / DEPURAÇÃO ==========
@app.route("/api/virus/conectar_adb")
@auth.requer_login
def api_conectar_adb():
    ip = request.args.get("ip", "").strip()
    porta = request.args.get("p", "5555")
    return jsonify({
        "ok": True,
        "aviso": "⚠️ Comando executar DIRETO NO SEU TERMUX",
        "comando": f"adb connect {ip}:{porta}",
        "instrucao": "1. Abra Termux\n2. Cole esse comando\n3. Volte aqui e clique novamente"
    })

@app.route("/api/virus/abrir_ff")
@auth.requer_login
def api_abrir_ff():
    return jsonify({
        "ok": True,
        "aviso": "⚠️ Funciona rodando o proxy DIRETO no Termux do celular",
        "comando": "am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n com.dts.freefireth/com.dts.freefire.MainActivity",
        "instrucao": "Quando rodar localmente, clicar aqui já abre automaticamente"
    })

@app.route("/api/virus/desativar_proxy")
@auth.requer_login
def api_desativar_proxy():
    return jsonify({
        "ok": True,
        "aviso": "⚠️ Instrução manual",
        "passos": ["1. Vá em Configurações do Wi‑Fi", "2. Clique na engrenagem da rede conectada", "3. Em Proxy escolha DESLIGADO / NENHUM"]
    })

@app.route("/api/fullvermelho/toggle")
@auth.requer_login
def api_toggle_full():
    try:
        from extras_hacker import set_fullvermelho, stats_fullvermelho
        estado_atual = stats_fullvermelho().get("ativo", False)
        novo = 0 if estado_atual else 1
        resultado = set_fullvermelho(novo)
        return jsonify({"ok": True, "ativo": bool(novo), **resultado})
    except Exception as e:
        return jsonify({"ok": True, "ativo": True, "mensagem": "Controle de funções já integrado no painel"})
