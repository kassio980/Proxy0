import json, os, time
BASE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = f"{BASE}/config.json"

PERFIS = {
  "SO_CABEÇA":   {"hs":100,"rx":5.0,"y":-0.95,"nome":"🎯 SÓ CABEÇA","cor":"#ff0"},
  "PESCOÇO":     {"hs":90, "rx":4.0,"y":-0.70,"nome":"🎯 PESCOÇO","cor":"#f80"},
  "SO_CAPA":     {"hs":100,"rx":4.5,"y":-0.85,"nome":"🏆 SÓ CAPA","cor":"#0f0"},
  "CABEÇA_PEITO":{"hs":70, "rx":2.5,"y":-0.45,"nome":"🎯 CABEÇA+PEITO","cor":"#0ff"},
  "SÓ_PEITO":    {"hs":0,  "rx":1.0,"y": 0.00,"nome":"🛡️ SÓ PEITO","cor":"#88f"},
  "PÉ":          {"hs":0,  "rx":0.5,"y": 0.80,"nome":"🦶 SÓ PÉ","cor":"#f8f"},
  "PROXY_MAX":   {"hs":100,"rx":6.0,"y":-0.98,"nome":"⚡ PROXY MÁXIMO","cor":"#f00"},
  "DESLIGADO":   {"hs":0,  "rx":0.0,"y": 0.00,"nome":"❌ DESLIGADO","cor":"#555"},
}

ARMAS = ["MP40","M1014","SCAR","AK47","AWM","M4A1","MP5","AUG","FAMAS","GROZA","SG12","XM8","TODAS"]

DEFAULT = {
  "PROXY":{"HOST":"0.0.0.0","SOCKS":1080,"UDP":1081,"PAINEL":8888,"BUFFER":4096,"TIMEOUT":12},
  "CAPA":{"ATIVO":True,"HITBOX":4.5,"PERFIL":"SO_CAPA","POR_ARMA":{a:"SO_CAPA" for a in ARMAS},"TODAS_ARMAS":True},
  "ANTIBAN":{"ATIVO":True,"PACOTES_LIMPO":True,"RANDOMIZAR":True,"SEED":None,"LIMITADOR_PPS":True,"MAX_PPS":120},
  "TEMPO_MAX_HORAS":7,
  "WIFI":{"COMPARTILHAR":True,"CODIGO_AUTO":True},
  "EXTERNO":{"TUNEL":True,"DOMINIO":""},
  "USUARIOS":{"MAX":1000},
}

def carregar():
    if not os.path.exists(CFG_PATH): return json.loads(json.dumps(DEFAULT))
    try:
        with open(CFG_PATH) as f: d = json.load(f)
        # Merge com default pra não faltar chave
        def merge(a,b):
            for k,v in b.items():
                if k not in a: a[k]=v
                elif isinstance(v,dict) and isinstance(a[k],dict): merge(a[k],v)
            return a
        return merge(d, json.loads(json.dumps(DEFAULT)))
    except: return json.loads(json.dumps(DEFAULT))

def salvar(d):
    with open(CFG_PATH,"w") as f: json.dump(d,f,indent=2,ensure_ascii=False)

def set_perfil(nome):
    if nome not in PERFIS: return False
    d = carregar(); d["CAPA"]["PERFIL"]=nome; salvar(d); return True

def set_por_arma(arma, perfil):
    if arma not in ARMAS or perfil not in PERFIS: return False
    d = carregar()
    if arma == "TODAS":
        d["CAPA"]["TODAS_ARMAS"] = (perfil != "DESLIGADO")
        for a in ARMAS: d["CAPA"]["POR_ARMA"][a] = perfil
    else:
        d["CAPA"]["POR_ARMA"][arma] = perfil
        d["CAPA"]["TODAS_ARMAS"] = all(v!="DESLIGADO" for v in d["CAPA"]["POR_ARMA"].values())
    salvar(d); return True

def status_tempo_restante(inicio, max_h=7):
    decorrido = time.time()-inicio
    resta = max(3600*max_h - decorrido, 0)
    h = int(resta//3600); m=int((resta%3600)//60); s=int(resta%60)
    return {"decorrido_s":int(decorrido),"resta_s":int(resta),"texto":f"{h:02d}:{m:02d}:{s:02d}","porcento":round(100-resta/(3600*max_h)*100,1)}

if __name__=="__main__":
    salvar(carregar())
    print("✅ Config padrão gerada em config.json")
    print("Perfis:", list(PERFIS.keys()))
    print("Armas:", ARMAS)
