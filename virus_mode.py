import os, time, subprocess, threading, json
BASE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = f"{BASE}/config.json"

def _adb(cmd, timeout=8):
    """Executa comando ADB (funciona no Termux com ADB over Wi-Fi)"""
    try:
        r = subprocess.run(f"adb {cmd}", shell=True, capture_output=True, text=True, timeout=timeout)
        return {"ok":r.returncode==0,"out":r.stdout.strip(),"err":r.stderr.strip()}
    except Exception as e:
        return {"ok":False,"err":str(e)}

def conectar_adb_wifi(ip_celular="127.0.0.1", porta=5555):
    """Conecta no celular via Wi-Fi (ativa depuração wireless)"""
    _adb("kill-server"); time.sleep(0.5)
    r1 = _adb(f"connect {ip_celular}:{porta}")
    r2 = _adb("devices")
    return {"ok":r1["ok"] or ("device" in r2["out"]), **r1, "devices":r2["out"]}

def abrir_free_fire(pacote="com.dts.freefireth"):
    """Abre o Free Fire no celular E ativa o proxy automaticamente"""
    # 1. Garante ADB conectado
    conectar_adb_wifi()
    # 2. Ativa proxy no celular automaticamente
    _proxy = "127.0.0.1:1080"
    try:
        if os.path.exists(CFG_PATH):
            c = json.load(open(CFG_PATH))
            _proxy = f"{c.get('PROXY',{}).get('HOST','127.0.0.1')}:{c.get('PROXY',{}).get('SOCKS',1080)}"
    except: pass
    # 3. Seta proxy global
    _adb(f"shell settings put global http_proxy {_proxy}")
    _adb(f"shell settings put global https_proxy {_proxy}")
    # 4. Abre o jogo
    r = _adb(f"shell monkey -p {pacote} -c android.intent.category.LAUNCHER 1")
    # 5. Marca no log
    try:
        if os.path.exists(CFG_PATH):
            c = json.load(open(CFG_PATH))
            c.setdefault("ESTATISTICAS",{})["ABERTURAS_FF"] = c.get("ESTATISTICAS",{}).get("ABERTURAS_FF",0)+1
            json.dump(c, open(CFG_PATH,"w"), indent=2, ensure_ascii=False)
    except: pass
    return {"ok":r["ok"],"proxy_aplicado":_proxy,"pacote":pacote,"out":r["out"],"err":r["err"]}

def desativar_proxy():
    """Remove o proxy do celular (ao sair do jogo)"""
    _adb("shell settings put global http_proxy :0")
    _adb("shell settings put global https_proxy :0")
    return {"ok":True}

def iniciar():
    print(f"   🦠 MODO VÍRUS · ADB WI-FI · ABRIR FF + PROXY AUTO PRONTO")

if __name__=="__main__":
    print(abrir_free_fire())
