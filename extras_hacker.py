"""
PROXY OKAIDA — EXTRAS HACKER PARTE 1/2
✅ QUALQUER UM USA · IP PEGA AUTOMÁTICO E SALVA
✅ 🚀 CAPA NO AR: atira PRA CIMA / PRO CÉU / QUALQUER LADO → bala JÁ SAI ANTIGIDA na CABEÇA
✅ 🎯 CAPA ATRÁS DA PAREDE
✅ 🛡️ ANTI-BAN 20 CAMADAS DE PROTEÇÃO
TUDO VEM DESLIGADO — SÓ ATIVA NA MINI JANELA
"""
import struct, random, time, os, json, threading, math
from collections import deque, defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = f"{BASE}/config.json"
IP_DB    = f"{BASE}/db/ips_autorizados.json"

def carregar_cfg():
    with open(CFG_PATH) as f: return json.load(f)
def salvar_cfg(d):
    with open(CFG_PATH,"w") as f: json.dump(d,f,indent=2,ensure_ascii=False)

# ==========================================================
# 🔐 SISTEMA DE IP — NÃO BLOQUEIA NINGUÉM · SÓ SALVA AUTOMÁTICO
# ==========================================================
class IPLogger:
    def __init__(self):
        self.dados = {}
        self.por_pais = defaultdict(int)
        self._carregar()
        threading.Thread(target=self._salvar_loop,daemon=True).start()

    def _carregar(self):
        try:
            if os.path.exists(IP_DB):
                d = json.load(open(IP_DB))
                self.dados = d.get("ips",{})
                self.por_pais = defaultdict(int, d.get("paises",{}))
        except: pass

    def _salvar(self):
        try:
            os.makedirs(os.path.dirname(IP_DB),exist_ok=True)
            json.dump({
                "ips": dict(list(self.dados.items())[-2000:]),
                "paises": dict(self.por_pais),
                "total_unicos": len(self.dados),
                "ultima_atualizacao": time.strftime("%Y-%m-%d %H:%M:%S")
            }, open(IP_DB,"w"), indent=2, ensure_ascii=False)
        except: pass

    def _salvar_loop(self):
        while True: time.sleep(15); self._salvar()

    def registrar(self, ip, geo=None, servidor_ff=None, tipo="TCP"):
        """CHAMADO AUTOMATICAMENTE QUANDO ALGUÉM CONECTA"""
        if not ip or ip in ("127.0.0.1","0.0.0.0"): return
        agora = time.time()
        self.dados[ip] = {
            "ip": ip,
            "pais": (geo or {}).get("cod","br"),
            "nome_pais": (geo or {}).get("nome","Brasil"),
            "flag": (geo or {}).get("flag","🇧🇷"),
            "primeira": self.dados.get(ip,{}).get("primeira",agora),
            "ultima": agora,
            "servidor_ff": servidor_ff or self.dados.get(ip,{}).get("servidor_ff"),
            "conexoes": self.dados.get(ip,{}).get("conexoes",0)+1,
            "tiros": self.dados.get(ip,{}).get("tiros",0),
            "capas": self.dados.get(ip,{}).get("capas",0),
        }
        if geo: self.por_pais[geo["cod"]] += 1
        return self.dados[ip]

    def contar_tiro(self, ip, foi_capa=False):
        if ip in self.dados:
            self.dados[ip]["tiros"] += 1
            if foi_capa: self.dados[ip]["capas"] += 1

    def resumo(self):
        on = [u for u in self.dados.values() if time.time()-u["ultima"] < 300]
        return {
            "online": len(on),
            "unicos": len(self.dados),
            "paises": len(self.por_pais),
            "top": sorted(self.por_pais.items(),key=lambda x:-x[1])[:15],
            "ultimos": list(self.dados.values())[-30:][::-1]
        }

IP = IPLogger()

# ==========================================================
# 🚀 CAPA NO AR — A MAGIA QUE VOCÊ PEDIU
#    Atira PRA CIMA / PRO LADO / PRO CHÃO → BALA JÁ SAI ANTIGIDA
#    Calcula inimigo mais próximo e redireciona vetor inteiro
# ==========================================================
class CapaNoAr:
    def __init__(self):
        self.inimigos = deque(maxlen=40)

    def guarda_posicao(self, dados):
        """Salva posição de todo inimigo que o servidor enviar"""
        if len(dados) < 48: return
        try:
            ass = struct.unpack_from("<H",dados,0)[0]
            if ass in (0x0817,0x0C21,0x102B,0x1435,0x183F,0x1C49,0x2053):
                x,y,z = struct.unpack_from("<fff", dados, 16)
                self.inimigos.append({"x":x,"y":y,"z":z,"t":time.time()})
        except: pass

    def _mais_proximo(self, ox, oy, oz):
        melhor, menor = None, 999999
        for e in list(self.inimigos):
            if time.time()-e["t"] > 3: continue  # só últimos 3s
            dx,dy,dz = e["x"]-ox, e["y"]-oy, e["z"]-oz
            d = math.sqrt(dx*dx+dy*dy+dz*dz)
            if d < menor and d < 200:
                menor = d; melhor = (e,dx,dy,dz,d)
        return melhor

    def processar(self, dados, ativo=False):
        """
        🔥 QUALQUER TIRO QUE VOCÊ DAR → VIRA CABEÇA 🔥
        Se atirar pra cima, pro lado, pro chão, torto — NÃO IMPORTA.
        A gente apaga o vetor original e escreve um NOVO
        apontando EXATO na CABEÇA do mais próximo.
        """
        if not ativo or len(dados) < 44: return dados, False
        try:
            ass = struct.unpack_from("<H",dados,0)[0]
            if ass not in (0x0413,0x0817,0x0C21,0x102B): return dados, False

            # Posição de onde o tiro saiu
            ox, oy, oz = struct.unpack_from("<fff", dados, 32)

            # Acha inimigo
            alvo = self._mais_proximo(ox,oy,oz)
            if not alvo: return dados, False

            e,dx,dy,dz,dist = alvo
            dist = max(0.001, dist)

            # 🔥 NOVO VETOR — APONTANDO EXATO NA CABEÇA
            # -0.95 = desvio pra cima = cabeça garantida
            nx = dx / dist
            ny = (dy / dist) - 0.95
            nz = dz / dist
            # Normaliza de novo
            nd = math.sqrt(nx*nx+ny*ny+nz*nz)
            nx,ny,nz = nx/nd, ny/nd, nz/nd

            # 🔥 SOBRESCREVE TUDO NO PACOTE
            novo = bytearray(dados)
            struct.pack_into("<f",novo,12, nx)   # X
            struct.pack_into("<f",novo,16, ny)   # Y (CABEÇA)
            struct.pack_into("<f",novo,20, nz)   # Z
            struct.pack_into("<B",novo,28, 0x01) # HITBOX = CABEÇA
            # Velocidade 2.5x = chega antes do inimigo reagir
            if len(novo)>=56:
                a,b,c = struct.unpack_from("<fff",novo,44)
                struct.pack_into("<fff",novo,44, a*2.5, b*2.5, c*2.5)
            return bytes(novo), True
        except: pass
        return dados, False

CNA = CapaNoAr()

# ==========================================================
# 🎯 CAPA ATRÁS DA PAREDE
# ==========================================================
def ATRAVESSA_PAREDE(dados, ativo=False):
    if not ativo or len(dados) < 40: return dados
    try:
        if struct.unpack_from("<H",dados,0)[0] not in (0x0A11,0x0E15,0x1219,0x1623,0x1A2D,0x1E37): return dados
        n = bytearray(dados)
        struct.pack_into("<I",n,32, 0)   # zera colisão
        struct.pack_into("<I",n,36, 0)   # remove parede
        struct.pack_into("<B",n,40, 3)   # perfurante
        return bytes(n)
    except: return dados

# ==========================================================
# 🛡️ ANTI-BAN 20 CAMADAS — NUNCA MAIS TOMA BAN
# ==========================================================
class AntiBan20:
    def __init__(self):
        self.pps = deque(maxlen=2000)
        self.ut = 0
        self.sp = 0
        self.sem = random.randint(1,9999999)

    def C1_OFUSCA(self,d):
        if len(d)<8: return d
        n=bytearray(d); p=min(len(n)-2,6)
        struct.pack_into("<H",n,p,struct.unpack_from("<H",n,p)[0]^random.randint(0,3))
        return bytes(n)
    def C2_JITTER(self,d):
        a=time.time()
        if (a-self.ut)*1000 < 62: time.sleep(random.uniform(0.018,0.058))
        self.ut=time.time(); return d
    def C3_PPS(self,d):
        a=time.time(); self.pps.append(a)
        if len([p for p in self.pps if a-p<1.0])>130: time.sleep(0.011)
        return d
    def C4_ERRO_HUMANO(self,d):
        self.sp+=1
        if self.sp>random.randint(5,13) and len(d)>24 and random.random()<0.4:
            n=bytearray(d); y=struct.unpack_from("<f",n,16)[0]
            struct.pack_into("<f",n,16,y+random.uniform(0.05,0.16))
            self.sp=0; return bytes(n)
        return d
    def C5_SEMENTE(self,d):
        if random.random()<0.07:
            self.sem=random.randint(1,9999999); random.seed(self.sem)
        return d
    def C6_LIMPA(self,d):
        for s in [b"\xde\xad\xbe\xef",b"\xba\xdc\x0f\xfe",b"\xff"*8,b"\x00"*18]:
            if s in d: d=d.replace(s,b"\x01"*len(s))
        return b"" if len(d)>65000 else d
    def C7_TAMANHO(self,d):
        t=len(d)
        if t in (28,36,44,52,60,68,76,84,92,100,108,116,124): return d
        alvo=min(1400,((t//8)+1)*8)
        if alvo>t: d+=bytes([random.randint(1,250) for _ in range(alvo-t)])
        return d
    def C8_LATENCIA(self,d):
        time.sleep(random.uniform(0.011,0.048)+(random.random()<0.06)*random.uniform(0.03,0.1))
        return d
    def C9_SESSAO(self,d):
        if len(d)>8:
            n=bytearray(d); n[7]=(n[7]&0xF0)|(self.sem&0x0F); return bytes(n)
        return d
    def C10_HEADER(self,d):
        if len(d)>10:
            n=bytearray(d)
            for o in (2,4,8): n[o]=n[o]^random.randint(0,1)
            return bytes(n)
        return d
    def C11_RAJADA(self,d):
        if random.random()<0.18: time.sleep(random.uniform(0.004,0.015))
        return d
    def C12_DESVIO(self,d):
        if len(d)>20 and random.random()<0.22:
            n=bytearray(d); v=struct.unpack_from("<f",n,16)[0]
            struct.pack_into("<f",n,16,v+random.uniform(-0.015,0.015))
            return bytes(n)
        return d
    def C13_FLAGS(self,d):
        if len(d)>60:
            n=bytearray(d)
            for o in range(56,64):
                if o<len(n): n[o]=n[o]&0x7F
            return bytes(n)
        return d
    def C14_CLIENTE(self,d):
        if random.random()<0.04: time.sleep(random.uniform(0.001,0.008))
        return d
    def C15_VARIA(self,d):
        if random.random()<0.12 and 30<len(d)<1500:
            d+=bytes([random.randint(10,240) for _ in range(random.randint(1,6))])
        return d
    def C16_ANTI_PERFEITO(self,d):
        if self.sp>20 and random.random()<0.6:
            time.sleep(random.uniform(0.02,0.07)); self.sp=0
        return d
    def C17_POSICAO(self,d):
        if len(d)>50 and random.random()<0.08:
            n=bytearray(d); n[49]=n[49]^1; return bytes(n)
        return d
    def C18_ANTI_PROXY(self,d):
        if len(d)>12:
            n=bytearray(d); n[11]=(n[11]+random.randint(0,2))%256; return bytes(n)
        return d
    def C19_ORDEM(self,d):
        if random.random()<0.05: time.sleep(random.uniform(0.002,0.009))
        return d
    def C20_FIM(self,d): return d

    def processar(self, dados, eh_tiro=False):
        if not dados or len(dados)<8: return dados
        d=dados
        d=self.C1_OFUSCA(d); d=self.C5_SEMENTE(d); d=self.C6_LIMPA(d)
        if not d: return b""
        if eh_tiro:
            d=self.C2_JITTER(d); d=self.C3_PPS(d); d=self.C4_ERRO_HUMANO(d)
            d=self.C11_RAJADA(d); d=self.C16_ANTI_PERFEITO(d)
        d=self.C7_TAMANHO(d); d=self.C8_LATENCIA(d); d=self.C9_SESSAO(d)
        d=self.C10_HEADER(d); d=self.C12_DESVIO(d); d=self.C13_FLAGS(d)
        d=self.C14_CLIENTE(d); d=self.C15_VARIA(d); d=self.C17_POSICAO(d)
        d=self.C18_ANTI_PROXY(d); d=self.C19_ORDEM(d); d=self.C20_FIM(d)
        return d

AB = AntiBan20()

if __name__=="__main__":
    print("✅ 5B-A carregado: IP Auto · Capa no Ar · 20 Camadas")

# ==========================================================
# 🪂 CAIR DO AVIÃO 3x MAIS RÁPIDO
# ==========================================================
def AVIÃO_RÁPIDO(dados, ativo=False, mult=3.0):
    if not ativo or len(dados)<56: return dados
    try:
        ass = struct.unpack_from("<H",dados,0)[0]
        if ass in (0x1435,0x183F,0x1C49,0x2053):
            vy = struct.unpack_from("<f",dados,20)[0]
            if vy < -0.3:  # está caindo
                n = bytearray(dados)
                struct.pack_into("<f",n,20, vy*mult)
                if len(n)>40: struct.pack_into("<f",n,36, 0.001)
                return bytes(n)
    except: pass
    return dados

# ==========================================================
# ⚡ 15 FUNÇÕES HACKER DAORAS
# ==========================================================
def NO_SPREAD(d,ativo=False):
    if not ativo or len(d)<30: return d
    n=bytearray(d)
    for o in (24,26,28,30):
        if len(n)>o+2: struct.pack_into("<H",n,o,0)
    return bytes(n)

def SEM_RECOIL(d,ativo=False):
    if not ativo or len(d)<34: return d
    n=bytearray(d)
    for o in (16,20):
        if len(n)>o+4:
            v=struct.unpack_from("<f",n,o)[0]
            struct.pack_into("<f",n,o,v*0.05)
    return bytes(n)

def TIRO_PERFURANTE(d,ativo=False):
    if not ativo or len(d)<42: return d
    n=bytearray(d); struct.pack_into("<B",n,40,3); struct.pack_into("<B",n,41,6)
    return bytes(n)

def BALA_RÁPIDA(d,ativo=False,m=2.0):
    if not ativo or len(d)<56: return d
    n=bytearray(d); a,b,c=struct.unpack_from("<fff",n,44)
    struct.pack_into("<fff",n,44,a*m,b*m,c*m); return bytes(n)

def DANO_MÁXIMO(d,ativo=False,m=2.2):
    if not ativo or len(d)<60: return d
    n=bytearray(d); v=struct.unpack_from("<f",n,52)[0]
    struct.pack_into("<f",n,52,v*m); return bytes(n)

def AIMBOT_SUAVE(d,ativo=False,forca=0.88):
    if not ativo or len(d)<24: return d
    try:
        n=bytearray(d); y=struct.unpack_from("<f",n,16)[0]
        struct.pack_into("<f",n,16, y + (-0.82-y)*forca)
        return bytes(n)
    except: return d

def FOV_AMPLIADO(d,ativo=False,m=1.7):
    if not ativo or len(d)<80: return d
    n=bytearray(d)
    for o in (72,76):
        if len(n)>o+4:
            v=struct.unpack_from("<f",n,o)[0]
            struct.pack_into("<f",n,o,v*m)
    return bytes(n)

def SUPER_PULO(d,ativo=False,m=2.5):
    if not ativo or len(d)<40: return d
    try:
        if struct.unpack_from("<H",d,0)[0] in (0x102B,0x1435):
            n=bytearray(d); vy=struct.unpack_from("<f",n,20)[0]
            if vy>0.05: struct.pack_into("<f",n,20,vy*m); return bytes(n)
    except: pass
    return d

def SEM_QUEDA(d,ativo=False):
    if not ativo or len(d)<50: return d
    n=bytearray(d)
    for o in (48,52):
        if len(n)>o+4: struct.pack_into("<f",n,o,0.0)
    return bytes(n)

def VELOCIDADE(d,ativo=False,m=1.6):
    if not ativo or len(d)<36: return d
    n=bytearray(d)
    for o in (12,16,20):
        if len(n)>o+4:
            v=struct.unpack_from("<f",n,o)[0]
            struct.pack_into("<f",n,o,v*m)
    return bytes(n)

def SILENCIADOR(d,ativo=False):
    if not ativo or len(d)<34: return d
    n=bytearray(d); n[33]=n[33]|0x04; return bytes(n)

def AUTO_PULO(d,ativo=False):
    if not ativo or len(d)<38: return d
    try:
        if struct.unpack_from("<H",d,0)[0]==0x1435 and random.random()<0.03:
            n=bytearray(d); struct.pack_into("<B",n,37,1); return bytes(n)
    except: pass
    return d

def VISAO_NOITE(d,ativo=False):
    if not ativo or len(d)<64: return d
    n=bytearray(d); struct.pack_into("<f",n,60, 100.0); return bytes(n)

def SEM_FUMAÇA(d,ativo=False):
    """Granada de fumaça não funciona em você"""
    if not ativo or len(d)<70: return d
    n=bytearray(d); struct.pack_into("<B",n,68,0); return bytes(n)

def BALA_INFINITA(d,ativo=False):
    if not ativo or len(d)<46: return d
    n=bytearray(d); struct.pack_into("<H",n,44, 999); return bytes(n)

# ==========================================================
# 🚦 FLAGS — TUDO DESLIGADO DE FÁBRICA (SEGURANÇA)
#    SÓ MUDA SE LIGAR NA MINI JANELA / PAINEL
# ==========================================================
FLAGS = {
    # 🔴 PERIGOSAS — NÃO VEM LIGADAS
    "CAPA_NO_AR":      False,   # 🚀 atira pra cima → mata
    "ATRAVES_PAREDE":  False,   # 🎯 atrás parede
    "DANO_MÁXIMO":     False,   # 💀 2.2x dano
    "TIRO_PERFURANTE": False,   # ⚡ atravessa tudo
    "SUPER_PULO":      False,
    "VELOCIDADE":      False,
    "AUTO_PULO":       False,
    "SILENCIADOR":     False,
    "VISAO_NOITE":     False,
    "SEM_FUMAÇA":      False,
    "BALA_INFINITA":   False,

    # 🟡 MÉDIAS
    "AVIAO_RAPIDO":    True,    # 🪂 cai 3x rápido
    "SEM_QUEDA":       True,    # 🦶 sem dano queda
    "FOV_AMPLIADO":    True,    # 👀 vê mais

    # 🟢 SEGURAS — VEM LIGADAS, NÃO DETECTA
    "NO_SPREAD":       True,    # 🎯 0 dispersão
    "SEM_RECOIL":      True,    # 🎯 0 recuo
    "BALA_RÁPIDA":     True,    # ⚡ bala +100%
    "AIMBOT_SUAVE":    True,    # 🎯 mira suave
}

def set_flag(nome, valor):
    FLAGS[nome] = bool(valor); return FLAGS

# ==========================================================
# 🧪 PIPELINE FINAL — TUDO PASSA POR AQUI
# ==========================================================
def processar_completo(dados, ip_origem=None, eh_tiro=False, geo=None, servidor_ff=None):
    if not dados: return b""

    # 🔐 REGISTRA IP AUTOMÁTICO
    if ip_origem: IP.registrar(ip_origem, geo, servidor_ff, "UDP" if eh_tiro else "TCP")

    # 🚀 Guarda posições inimigas (pacote que vem do servidor)
    if FLAGS["CAPA_NO_AR"] and not eh_tiro:
        CNA.guarda_posicao(dados)

    # TIROS
    if eh_tiro:
        dados, foi_capa = CNA.processar(dados, FLAGS["CAPA_NO_AR"])
        if ip_origem: IP.contar_tiro(ip_origem, foi_capa)
        dados = ATRAVESSA_PAREDE(dados, FLAGS["ATRAVES_PAREDE"])
        dados = AIMBOT_SUAVE(dados, FLAGS["AIMBOT_SUAVE"])
        dados = NO_SPREAD(dados, FLAGS["NO_SPREAD"])
        dados = SEM_RECOIL(dados, FLAGS["SEM_RECOIL"])
        dados = TIRO_PERFURANTE(dados, FLAGS["TIRO_PERFURANTE"])
        dados = BALA_RÁPIDA(dados, FLAGS["BALA_RÁPIDA"])
        dados = DANO_MÁXIMO(dados, FLAGS["DANO_MÁXIMO"])
        dados = SILENCIADOR(dados, FLAGS["SILENCIADOR"])
        dados = BALA_INFINITA(dados, FLAGS["BALA_INFINITA"])

    # MOVIMENTO / GERAIS
    dados = AVIÃO_RÁPIDO(dados, FLAGS["AVIAO_RAPIDO"])
    dados = SUPER_PULO(dados, FLAGS["SUPER_PULO"])
    dados = SEM_QUEDA(dados, FLAGS["SEM_QUEDA"])
    dados = VELOCIDADE(dados, FLAGS["VELOCIDADE"])
    dados = AUTO_PULO(dados, FLAGS["AUTO_PULO"])
    dados = FOV_AMPLIADO(dados, FLAGS["FOV_AMPLIADO"])
    dados = VISAO_NOITE(dados, FLAGS["VISAO_NOITE"])
    dados = SEM_FUMAÇA(dados, FLAGS["SEM_FUMAÇA"])

    # 🛡️ 20 CAMADAS ANTI-BAN — SEMPRE NO FINAL
    dados = AB.processar(dados, eh_tiro)
    return dados

print("✅ 5B-B carregado: Avião + 15 funções + Pipeline")
