import socket, threading, time, json, struct, os, random
from datetime import datetime
from colorama import Fore, init
init(autoreset=True)

BASE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(f"{BASE}/config.json")) if os.path.exists(f"{BASE}/config.json") else {
  "PROXY":{"HOST":"0.0.0.0","SOCKS":1080,"UDP":1081,"PAINEL":8888,"BUFFER":4096,"TIMEOUT":12},
  "CAPA":{"ATIVO":True,"HITBOX":4.5,"Y":-0.90,"PERFIL":"SO_CAPA","POR_ARMA":{},"TODAS_ARMAS":True},
  "ANTIBAN":{"ATIVO":True,"PACOTES_LIMPO":True,"RANDOMIZAR":True},
  "TEMPO_MAX_HORAS":7
}
P=CFG["PROXY"]; C=CFG["CAPA"]; AB=CFG["ANTIBAN"]
PERFIS = {
  "SO_CABEÇA":{"hs":100,"rx":5.0,"y":-0.95,"nome":"🎯 SÓ CABEÇA"},
  "PESCOÇO":   {"hs":90, "rx":4.0,"y":-0.70,"nome":"🎯 PESCOÇO"},
  "SO_CAPA":   {"hs":100,"rx":4.5,"y":-0.85,"nome":"🏆 SÓ CAPA"},
  "CABEÇA_PEITO":{"hs":70,"rx":2.5,"y":-0.45,"nome":"🎯 CABEÇA+PEITO"},
  "SÓ_PEITO":  {"hs":0,  "rx":1.0,"y": 0.00,"nome":"🛡️ SÓ PEITO"},
  "PÉ":        {"hs":0,  "rx":0.5,"y": 0.80,"nome":"🦶 SÓ PÉ"},
  "PROXY_MAX": {"hs":100,"rx":6.0,"y":-0.98,"nome":"⚡ PROXY MÁXIMO"},
}
if C["PERFIL"] not in PERFIS: C["PERFIL"]="SO_CAPA"
PERF=PERFIS[C["PERFIL"]]

ARMAS = ["MP40","M1014","SCAR","AK47","AWM","M4A1","MP5","AUG","FAMAS","GROZA","SG12","XM8","TODAS"]
if not C.get("POR_ARMA"): C["POR_ARMA"] = {a:"SO_CAPA" for a in ARMAS}

ST = {"inicio":time.time(),"ligado":True,"tcp":{"c":0,"b":0,"p":0},"udp":{"c":0,"b":0,"p":0},
      "capa":0,"peito":0,"servidores":{},"usuarios":{}}
LOCK = threading.Lock()

def salvar_cfg():
    with open(f"{BASE}/config.json","w") as f: json.dump(CFG,f,indent=2,ensure_ascii=False)

def log(t,m,c=Fore.WHITE):
    t2=datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"{Fore.BLACK}[{t2}]{Style.RESET_ALL} {c}[{t}] {m}")
    try:open(f"{BASE}/logs/proxy.log","a").write(f"[{t2}] [{t}] {m}\n")
    except:pass
from colorama import Style

def APLICAR_CAPA(dados, origem, arma=None):
    if not C["ATIVO"] or len(dados)<28: return dados
    try:
        ass = struct.unpack_from("<H",dados,0)[0]
        if ass not in (0x0413,0x0817,0x0C21,0x102B,0x1435,0x183F,0x1C49): return dados
        perfil_arma = C["POR_ARMA"].get(arma, C["PERFIL"]) if arma else C["PERFIL"]
        if not C["TODAS_ARMAS"] and arma and C["POR_ARMA"].get(arma) == "DESLIGADO": return dados
        pr = PERFIS.get(perfil_arma, PERF)

        OFF_Y, OFF_Z, OFF_X, OFF_HIT = 16, 20, 12, 28
        ay = struct.unpack_from("<f",dados,OFF_Y)[0]
        if ay < -0.70:
            with LOCK: ST["capa"]+=1
            return dados
        novo = bytearray(dados)
        ny = pr["y"] + random.uniform(-0.03,0.02)
        nz = random.uniform(-0.03,0.03)
        struct.pack_into("<f",novo,OFF_Y,ny)
        struct.pack_into("<f",novo,OFF_Z,nz)
        struct.pack_into("<B",novo,OFF_HIT,0x01)
        if AB["RANDOMIZAR"]:
            struct.pack_into("<f",novo,4,struct.unpack_from("<f",dados,4)[0]+random.uniform(-0.001,0.001))
        with LOCK: ST["capa"]+=1; ST["peito"]+=1
        log("CAPA",f"{origem} → {pr['nome']}  y={ay:.2f}→{ny:.2f}  arma={arma or 'auto'}",Fore.GREEN)
        return bytes(novo)
    except: return dados

def ANTIBAN(dados):
    if not AB["ATIVO"] or len(dados)<20: return dados
    try:
        if AB["PACOTES_LIMPO"]:
            sujos = [b"\xff\xff\xff\xff", b"\xde\xad\xbe\xef", b"\xba\xdc\x0f\xfe"]
            for s in sujos:
                if s in dados: dados = dados.replace(s, b"\x00"*len(s))
        return dados
    except: return dados

def relay(src,dst,origem,arma=None):
    try:
        while ST["ligado"]:
            src.settimeout(P["TIMEOUT"])
            d=src.recv(P["BUFFER"])
            if not d: break
            d=ANTIBAN(d)
            d=APLICAR_CAPA(d,origem,arma)
            dst.sendall(d)
            with LOCK: ST["tcp"]["b"]+=len(d);ST["tcp"]["p"]+=1
    except: pass
    finally:
        try:src.close()
        except:pass
        try:dst.close()
        except:pass

def handle_tcp(cliente,addr):
    try:
        cliente.settimeout(5)
        h=cliente.recv(2)
        if len(h)<2 or h[0]!=5: return
        cliente.send(b"\x05\x00")
        req=cliente.recv(4)
        if len(req)<4: return
        cmd,atyp=req[1],req[3]
        if atyp==1:   ip=".".join(map(str,cliente.recv(4)))
        elif atyp==3: ip=cliente.recv(cliente.recv(1)[0]).decode(errors="ignore")
        else: return
        porta=struct.unpack(">H",cliente.recv(2))[0]
        if 10000<porta<40000:
            with LOCK:
                ST["servidores"][ip]=ST["servidores"].get(ip,0)+1
                ST["usuarios"][addr[0]]={"ip":addr[0],"servidor":ip,"hora":time.time()}
            log("SRV",f"{addr[0]} → {ip}:{porta}",Fore.CYAN)
        try:remoto=socket.create_connection((ip,porta),timeout=P["TIMEOUT"])
        except:cliente.send(b"\x05\x05\x00\x01\x00\x00\x00\x00\x00\x00");return
        cliente.send(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
        with LOCK: ST["tcp"]["c"]+=1
        threading.Thread(target=relay,args=(cliente,remoto,f"C→{ip}"),daemon=True).start()
        threading.Thread(target=relay,args=(remoto,cliente,f"{ip}→C"),daemon=True).start()
    except Exception as e: log("ERRO",f"tcp {addr}: {e}",Fore.RED)

ROTAS={}
def handle_udp():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,P["BUFFER"]*64)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,P["BUFFER"]*64)
    s.bind((P["HOST"],P["UDP"]))
    log("UDP",f":{P['UDP']} · CAPA={C['ATIVO']} · PERFIL={PERF['nome']}",Fore.MAGENTA)
    while ST["ligado"]:
        try:
            s.settimeout(P["TIMEOUT"])
            dados, origem = s.recvfrom(P["BUFFER"]*4)
            if origem in ROTAS:
                dst=ROTAS[origem]
                dados=ANTIBAN(dados)
                dados=APLICAR_CAPA(dados,origem[0])
                s.sendto(dados,dst)
                with LOCK: ST["udp"]["b"]+=len(dados);ST["udp"]["p"]+=1
            else:
                if len(dados)<10: continue
                try:
                    if dados[3]==1:
                        ip_dst=".".join(map(str,dados[4:8]))
                        porta_dst=struct.unpack(">H",dados[8:10])[0]
                        payload=dados[10:]
                    else: continue
                    ROTAS[origem]=(ip_dst,porta_dst)
                    ROTAS[(ip_dst,porta_dst)]=origem
                    with LOCK:
                        ST["udp"]["c"]+=1
                        ST["servidores"][ip_dst]=ST["servidores"].get(ip_dst,0)+1
                    log("UDP",f"{origem[0]} ↔ {ip_dst}:{porta_dst}",Fore.MAGENTA)
                    payload=APLICAR_CAPA(payload,origem[0])
                    s.sendto(payload,(ip_dst,porta_dst))
                except: pass
        except socket.timeout: pass
        except Exception as e: log("ERRO",f"udp: {e}",Fore.RED)

def tcp_srv():
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind((P["HOST"],P["SOCKS"]))
    s.listen(500)
    log("TCP",f"SOCKS5 :{P['SOCKS']}",Fore.YELLOW)
    while ST["ligado"]:
        try:
            c,a=s.accept()
            threading.Thread(target=handle_tcp,args=(c,a),daemon=True).start()
        except: pass

def limite_7h():
    while ST["ligado"]:
        if time.time()-ST["inicio"] > CFG["TEMPO_MAX_HORAS"]*3600:
            log("SISTEMA",f"⏰ LIMITE DE {CFG['TEMPO_MAX_HORAS']}H ATINGIDO — DESLIGANDO",Fore.RED+Style.BRIGHT)
            ST["ligado"]=False
            os._exit(0)
        time.sleep(60)

def iniciar():
    for f in [tcp_srv, handle_udp, limite_7h]:
        threading.Thread(target=f,daemon=True).start()
    salvar_cfg()
    log("INI",f"PROXY OKAIDA RODANDO · {CFG['TEMPO_MAX_HORAS']}H · PERFIL={PERF['nome']}",Fore.GREEN+Style.BRIGHT)
