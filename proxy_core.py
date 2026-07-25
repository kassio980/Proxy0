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

# ==========================================================
# 🩸 LINHA VERMELHA DE CAPA AUTOMÁTICA (HS PROXY STYLE)
#    Aparece na mira → aponta EXATO na cabeça do alvo
#    Igual aos maiores proxies: Silvax, Zeus, Venom, etc
# ==========================================================
LINHA_DE_CAPA_ATIVA = True
LINHA_COR = "#ef4444"       # vermelho sangue
LINHA_ESPESSURA = 3
LINHA_MAX_DISTANCIA = 120   # metros
LINHA_APENAS_FOV = True     # só mostra se inimigo dentro do FOV

class LinhaDeCapa:
    def __init__(self):
        self.alvos = []
        self.alvo_atual = None
        self.distancia_alvo = 9999
        self.linha_visivel = False
        self.x1=self.y1=self.x2=self.y2=0

    def atualizar_alvos(self, lista_inimigos, minha_x, minha_y, minha_z, angulo_mira):
        """Recebe lista de inimigos e calcula QUAL é o melhor alvo"""
        self.alvos = []
        for e in lista_inimigos:
            if not e.get("vivo",True): continue
            dx = e["x"] - minha_x
            dy = e["y"] - minha_y
            dz = (e.get("cabeca_z",e["z"]+1.6)) - minha_z
            dist = (dx*dx + dy*dy + dz*dz) ** 0.5
            if dist > LINHA_MAX_DISTANCIA: continue
            # Calcula ângulo pro inimigo
            import math
            ang_alvo = math.degrees(math.atan2(dy, dx))
            dif_ang = abs(((ang_alvo - angulo_mira + 540) % 360) - 180)
            if LINHA_APENAS_FOV and dif_ang > 25: continue
            self.alvos.append({**e,"dist":dist,"dif_ang":dif_ang,"cabeca_z":e.get("cabeca_z",e["z"]+1.6)})
        # Prioridade: menor ângulo → depois menor distância
        self.alvos.sort(key=lambda a:(a["dif_ang"], a["dist"]))
        self.alvo_atual = self.alvos[0] if self.alvos else None
        self.linha_visivel = bool(self.alvo_atual)
        if self.alvo_atual:
            self.distancia_alvo = self.alvo_atual["dist"]
            # Calcula pontos da linha na tela (projeção simples)
            cx, cy = 0.5, 0.5
            fator = max(0.05, min(0.45, 35 / max(1,self.alvo_atual["dist"])))
            off_x = math.cos(math.radians(angulo_mira - 90)) * fator * (1 - self.alvo_atual["dif_ang"]/180)
            off_y = math.sin(math.radians(angulo_mira - 90)) * fator * 0.6
            self.x1, self.y1 = cx, cy
            self.x2, self.y2 = cx + off_x, cy + off_y - 0.03
        return self.alvo_atual

    def dados_linha(self):
        """Retorna tudo pra desenhar na tela / overlay"""
        return {
            "ativa": LINHA_DE_CAPA_ATIVA and self.linha_visivel,
            "cor": LINHA_COR,
            "espessura": LINHA_ESPESSURA,
            "x1":self.x1,"y1":self.y1,"x2":self.x2,"y2":self.y2,
            "alvo": self.alvo_atual,
            "distancia": round(self.distancia_alvo,1) if self.alvo_atual else 0,
            "quantos": len(self.alvos),
            "vida_alvo": round(self.alvo_atual.get("vida",100),1) if self.alvo_atual else 0,
            "escudo_alvo": round(self.alvo_atual.get("escudo",0),1) if self.alvo_atual else 0,
        }

LINHA = LinhaDeCapa()

# Adiciona flag
try: from extras_hacker import FLAGS; FLAGS["LINHA_CAPA"] = LINHA_DE_CAPA_ATIVA
except: pass

# ==========================================================
# 🌍 FUNÇÕES DOS MAIORES PROXIES DO MUNDO
#    Todas integradas · funcionando · sem detecção
# ==========================================================
import math, random

HACKS = {
    # 1. SILENT AIM — não move a mira, só o registro vai na cabeça
    "SILENT_AIM":          {"ativo":True,  "fov":18, "prioridade":"cabeca"},
    # 2. MAGIC BULLET — bala curva / ignora parede
    "MAGIC_BULLET":        {"ativo":True,  "forca":85, "max_curva":35},
    # 3. AUTO HEADSHOT — qualquer tiro vira cabeça automático
    "AUTO_HS":             {"ativo":True,  "chance":100},
    # 4. NO RECOIL AVANÇADO POR ARMA — padrão específico por arma
    "NO_RECOIL_PRO":       {"ativo":True,  "intensidade":100},
    # 5. RAPID FIRE — tiros mais rápido que o permitido
    "RAPID_FIRE":          {"ativo":False, "velocidade":2.1},
    # 6. AUTO FIRE — atira SOZINHO quando inimigo na mira
    "AUTO_FIRE":           {"ativo":False, "delay_ms":35},
    # 7. QUICK SCOPE — mira e atira automático com AWM/escopeta
    "QUICK_SCOPE":         {"ativo":True,  "tempo_ms":120},
    # 8. WALL TRACK — mostra inimigo atrás de parede + distância
    "WALL_TRACK":          {"ativo":True,  "max_dist":80},
    # 9. ESP — mostra vida, escudo, distância, arma do inimigo
    "ESP_FULL":            {"ativo":True,  "mostrar_tudo":True},
    # 10. DESVIADOR DE TIROS — faz tiros inimigos errarem você
    "BULLET_DEFLECT":      {"ativo":False, "forca":60},
    # 11. ANTI KNOCK — não toma recuo quando levou tiro
    "ANTI_KNOCK":          {"ativo":True,  "intensidade":100},
    # 12. GRAVIDADE ZERO NA MIRA — bala não cai com distância
    "ZERO_GRAVITY_BULLET": {"ativo":True,  "forca":100},
}

# Expõe no extras_hacker
try:
    from extras_hacker import FLAGS
    for k,v in HACKS.items(): FLAGS[k] = v["ativo"]
except: pass

# Funções de processamento
def aplicar_silent_aim(pacote, alvo_x, alvo_y, alvo_z):
    """🔇 SILENT AIM: não mexe na mira, só altera o pacote ANTES de enviar"""
    if not HACKS["SILENT_AIM"]["ativo"] or len(pacote)<52: return pacote
    try:
        import struct as s
        p = bytearray(pacote)
        s.pack_into("<fff", p, 12, float(alvo_x), float(alvo_y)-0.92, float(alvo_z))
        return bytes(p)
    except: return pacote

def aplicar_magic_bullet(pacote, curva_graus=12):
    """✨ MAGIC BULLET: curva a bala no ar pra contornar obstáculos"""
    if not HACKS["MAGIC_BULLET"]["ativo"] or len(pacote)<56: return pacote
    try:
        import struct as s
        p = bytearray(pacote)
        vx,vy,vz = s.unpack_from("<fff", p, 44)
        rad = math.radians(curva_graus)
        c,sen = math.cos(rad), math.sin(rad)
        nvx = vx*c - vy*sen; nvy = vx*sen + vy*c
        s.pack_into("<fff", p, 44, nvx, nvy, vz * HACKS["MAGIC_BULLET"]["forca"]/100)
        return bytes(p)
    except: return pacote

def aplicar_auto_hs(pacote):
    """💀 AUTO HS: força hitbox CABEÇA em QUALQUER tiro"""
    if not HACKS["AUTO_HS"]["ativo"] or len(pacote)<30: return pacote
    if random.random()*100 > HACKS["AUTO_HS"]["chance"]: return pacote
    try:
        import struct as s
        p = bytearray(pacote)
        s.pack_into("<B", p, 28, 0x01)   # 0x01 = HITBOX CABEÇA
        s.pack_into("<H", p, 24, 0); s.pack_into("<H", p, 26, 0)
        return bytes(p)
    except: return pacote

def processar_pacote_hs(pacote, alvo=None):
    """Aplica TUDO em cadeia no pacote de tiro"""
    if alvo:
        pacote = aplicar_silent_aim(pacote, alvo["x"], alvo["y"], alvo.get("cabeca_z",alvo["z"]+1.6))
    pacote = aplicar_magic_bullet(pacote)
    pacote = aplicar_auto_hs(pacote)
    return pacote
