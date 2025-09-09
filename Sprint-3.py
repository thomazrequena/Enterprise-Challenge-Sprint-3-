# -*- coding: utf-8 -*-
"""
Populate >= 500 rows per table (cap06 schema) with synthetic data.
Uses oracledb thin mode with the provided connection.

Tabelas:
usuarios, ambientes, culturas, fases_cultivo, parametros_ideais,
ciclos, ciclo_fases, sensores, leituras, checklists, checklist_itens,
alertas, ajustes
"""

import random
import string
import datetime as dt
import itertools
import oracledb

# ========= CONFIG =========
N_MIN = 500                          # mínimo por tabela
SEED = 42                            # reprodutibilidade
TS_BASE = dt.datetime(2024, 1, 1)    # base para datas sintéticas
random.seed(SEED)

# ========= CONEXÃO =========
try:
    conn = oracledb.connect(user='rm563956', password="240981", dsn='oracle.fiap.com.br:1521/ORCL')
    cur = conn.cursor()
    print("OK: conectado.")
except Exception as e:
    print("Erro ao conectar:", e)
    raise SystemExit(1)

# ========= HELPERS =========
def rand_word(prefix, i=None, width=4):
    suffix = f"{i:0{width}d}" if i is not None else "".join(random.choices(string.digits, k=width))
    return f"{prefix}_{suffix}"

def rand_email(nome, i):
    base = nome.lower().replace(" ", ".")
    dom = random.choice(["@venezacomercio.com.br", "@aluminionacional.com.br", "@fiap.com.br"])
    return f"{base}.{i}{dom}"

def dt_spread(n, start=TS_BASE, max_days=365):
    for k in range(n):
        yield start + dt.timedelta(days=random.randint(0, max_days), seconds=random.randint(0, 86400))

def fetch_ids(table, idcol):
    cur.execute(f"SELECT {idcol} FROM {table}")
    return [r[0] for r in cur.fetchall()]

def chunked(iterable, size=500):
    it = iter(iterable)
    while True:
        buf = list(itertools.islice(it, size))
        if not buf:
            return
        yield buf

def range_for(tipo):
    if tipo == "temperatura": return (20.0, 26.0)
    if tipo == "umidade":     return (50.0, 70.0)
    if tipo == "EC":          return (1.4, 2.4)
    if tipo == "pH":          return (5.6, 6.2)
    if tipo == "luz":         return (10000.0, 25000.0)
    return (0.0, 100.0)

# ========= 1) USUARIOS (>=500) =========
usuarios = []
for i in range(N_MIN):
    nome = random.choice([
        "Thomaz Requena","Ana Silva","Carlos Pereira","Marina Souza","João Lima",
        "Beatriz Nunes","Luiz Santos","Paula Castro","Ricardo Alves","Fernanda Dias",
        "Pedro Rocha","Camila Prado","Hugo Neri","Julia Matos","Rafael Souza"
    ])
    usuarios.append((
        f"{nome} {i}",                 # nome único
        rand_email(nome, i),           # UNIQUE email
        random.choice(["admin","operador"]),
        "Y"
    ))
cur.executemany("""
INSERT INTO usuarios (nome, email, perfil, ativo)
VALUES (:1, :2, :3, :4)
""", usuarios)
conn.commit()
print(f"> usuarios: {len(usuarios)}")

# ========= 2) AMBIENTES (>=500) =========
ambientes = []
for i in range(N_MIN):
    nm = rand_word("Estufa", i, width=4)  # UNIQUE nome
    ambientes.append((
        nm,
        f"Ambiente de cultivo {nm}",
        round(random.uniform(10, 120), 2),
        "Y"
    ))
cur.executemany("""
INSERT INTO ambientes (nome, descricao, area_m2, ativo)
VALUES (:1, :2, :3, :4)
""", ambientes)
conn.commit()
print(f"> ambientes: {len(ambientes)}")

# ========= 3) CULTURAS (>=500) =========
culturas = []
base_cult = ["Alface","Tomate","Manjericão","Pimenta","Cacau","Soja","Arroz","Milho","Trigo","Café","Cacau","Cânhamo"]
for i in range(N_MIN):
    nm = f"{random.choice(base_cult)}_{i:04d}"  # UNIQUE
    culturas.append((nm, f"Cultura {nm} - variedade sintética"))
cur.executemany("""
INSERT INTO culturas (nome, descricao)
VALUES (:1, :2)
""", culturas)
conn.commit()
print(f"> culturas: {len(culturas)}")

# ========= 4) FASES_CULTIVO (>=500) =========
# apesar de na prática serem poucas, aqui vamos atender ao requisito de >=500
fases = []
nomes_fase_base = ["Germinação","Vegetativo","Floração","Colheita","Secagem","Cura"]
for i in range(N_MIN):
    nm = f"{random.choice(nomes_fase_base)}_{i:04d}"  # UNIQUE
    ordem = (i % 10) + 1
    fases.append((nm, ordem))
cur.executemany("""
INSERT INTO fases_cultivo (nome_fase, ordem)
VALUES (:1, :2)
""", fases)
conn.commit()
print(f"> fases_cultivo: {len(fases)}")

# IDs de apoio
ids_usuarios  = fetch_ids("usuarios",  "id_usuario")
ids_ambientes = fetch_ids("ambientes", "id_ambiente")
ids_culturas  = fetch_ids("culturas",  "id_cultura")
ids_fases     = fetch_ids("fases_cultivo", "id_fase")

# ========= 5) PARAMETROS_IDEAIS (>=500) =========
param_rows = []
for i in range(N_MIN):
    id_fase = random.choice(ids_fases)
    id_cult = random.choice(ids_culturas)
    id_amb  = random.choice(ids_ambientes) if random.random() < 0.5 else None
    temp_min = round(random.uniform(18, 22), 2)
    temp_max = round(max(temp_min + 1.5, random.uniform(24, 28)), 2)
    umid_min = round(random.uniform(45, 55), 2)
    umid_max = round(max(umid_min + 5, random.uniform(60, 80)), 2)
    fotoh    = round(random.uniform(12, 18), 1)
    ec_min   = round(random.uniform(1.0, 1.8), 2)
    ec_max   = round(max(ec_min + 0.4, random.uniform(2.0, 3.0)), 2)
    ph_min   = round(random.uniform(5.5, 5.9), 2)
    ph_max   = round(random.uniform(6.0, 6.5), 2)
    param_rows.append((id_fase, id_cult, id_amb, temp_min, temp_max, umid_min, umid_max,
                       fotoh, ec_min, ec_max, ph_min, ph_max))
for chunk in chunked(param_rows, 1000):
    cur.executemany("""
INSERT INTO parametros_ideais
(id_fase, id_cultura, id_ambiente, temp_min_c, temp_max_c, umid_rel_min_pct, umid_rel_max_pct,
 fotoperiodo_horas, ec_min_ms, ec_max_ms, ph_min, ph_max)
VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12)
""", chunk)
conn.commit()
print(f"> parametros_ideais: {len(param_rows)}")

# ========= 6) CICLOS (>=500) =========
ciclos = []
for i in range(N_MIN):
    id_cult = random.choice(ids_culturas)
    id_amb  = random.choice(ids_ambientes)
    di = TS_BASE + dt.timedelta(days=random.randint(0, 300))
    df = di + dt.timedelta(days=random.randint(45, 90))
    status = random.choice(["ativo","concluido","pausado"])
    ciclos.append((id_cult, id_amb, di, df, status))
for ch in chunked(ciclos, 1000):
    cur.executemany("""
INSERT INTO ciclos (id_cultura, id_ambiente, data_inicio, data_fim, status)
VALUES (:1, :2, :3, :4, :5)
""", ch)
conn.commit()
print(f"> ciclos: {len(ciclos)}")

ids_ciclos = fetch_ids("ciclos", "id_ciclo")

# ========= 7) CICLO_FASES (>=500) =========
# criaremos 2 fases por ciclo por amostragem até passarmos de 500
ciclo_fases = []
for id_ciclo in random.sample(ids_ciclos, k=min(len(ids_ciclos), 300)):
    # 2 fases por ciclo
    start = TS_BASE + dt.timedelta(days=random.randint(0, 300))
    for _ in range(2):
        id_fase = random.choice(ids_fases)
        fim = start + dt.timedelta(days=random.randint(5, 40))
        ciclo_fases.append((id_ciclo, id_fase, start, fim, "fase sintética"))
        start = fim + dt.timedelta(days=1)
# completa até >=500
while len(ciclo_fases) < N_MIN:
    id_ciclo = random.choice(ids_ciclos)
    id_fase  = random.choice(ids_fases)
    di = TS_BASE + dt.timedelta(days=random.randint(0, 300))
    df = di + dt.timedelta(days=random.randint(5, 40))
    ciclo_fases.append((id_ciclo, id_fase, di, df, "fase sintética"))
for ch in chunked(ciclo_fases, 1000):
    cur.executemany("""
INSERT INTO ciclo_fases (id_ciclo, id_fase, data_inicio, data_fim, observacao)
VALUES (:1, :2, :3, :4, :5)
""", ch)
conn.commit()
print(f"> ciclo_fases: {len(ciclo_fases)}")

ids_ciclo_fases = fetch_ids("ciclo_fases", "id_ciclo_fase")

# ========= 8) SENSORES (>=500) =========
tipos = [("temperatura","DHT22","C"),
         ("umidade","DHT22","%"),
         ("luz","BH1750","lux"),
         ("EC","AtlasEC","mS"),
         ("pH","AtlasPH","pH")]
sensores = []
for i in range(N_MIN):
    id_amb = random.choice(ids_ambientes)
    t,m,u = random.choice(tipos)
    sensores.append((id_amb, t, f"{m}_{i:04d}", u))
for ch in chunked(sensores, 1000):
    cur.executemany("""
INSERT INTO sensores (id_ambiente, tipo, modelo, unidade)
VALUES (:1, :2, :3, :4)
""", ch)
conn.commit()
print(f"> sensores: {len(sensores)}")

ids_sensores = fetch_ids("sensores", "id_sensor")

# ========= 9) LEITURAS (>=500) =========
leituras = []
for i in range(N_MIN):
    id_sensor = random.choice(ids_sensores)
    id_cf = random.choice(ids_ciclo_fases) if random.random() < 0.6 else None
    ts = TS_BASE + dt.timedelta(days=random.randint(0, 300), seconds=random.randint(0,86400))
    # valor coerente com tipo do sensor (descobrir tipo)
    cur.execute("SELECT tipo, unidade FROM sensores WHERE id_sensor = :id", {"id": id_sensor})
    tipo, unidade = cur.fetchone()
    low, high = range_for(tipo)
    if random.random() < 0.15:
        val = random.choice([low - random.uniform(0.2, 0.8), high + random.uniform(0.2, 0.8)])
    else:
        val = random.uniform(low, high)
    leituras.append((id_sensor, id_cf, ts, round(val,3), "ok"))
for ch in chunked(leituras, 500):
    cur.executemany("""
INSERT INTO leituras (id_sensor, id_ciclo_fase, ts_leitura, valor_num, qualidade)
VALUES (:1, :2, :3, :4, :5)
""", ch)
conn.commit()
print(f"> leituras: {len(leituras)}")

ids_leituras = fetch_ids("leituras", "id_leitura")

# ========= 10) CHECKLISTS (>=500) =========
checklists = []
for i in range(N_MIN):
    id_cf = random.choice(ids_ciclo_fases)
    criado_por = random.choice(ids_usuarios)
    ts_c = TS_BASE + dt.timedelta(days=random.randint(0, 300), seconds=random.randint(0,86400))
    status = random.choice(["aberto","aprovado","reprovado"])
    checklists.append((id_cf, criado_por, ts_c, status))
for ch in chunked(checklists, 1000):
    cur.executemany("""
INSERT INTO checklists (id_ciclo_fase, criado_por, ts_criacao, status)
VALUES (:1, :2, :3, :4)
""", ch)
conn.commit()
print(f"> checklists: {len(checklists)}")

ids_checklists = fetch_ids("checklists", "id_checklist")

# ========= 11) CHECKLIST_ITENS (>=500) =========
regras = ["temperatura dentro do ideal","umidade dentro do ideal","EC dentro do ideal",
          "pH dentro do ideal","luz suficiente"]
itens = []
for i in range(N_MIN):
    id_chk = random.choice(ids_checklists)
    regra = random.choice(regras)
    # pegar uma leitura para compor valor/intervalo
    id_le = random.choice(ids_leituras)
    cur.execute("""
SELECT s.tipo, s.unidade, NVL(l.valor_num, 0)
FROM leituras l JOIN sensores s ON s.id_sensor = l.id_sensor
WHERE l.id_leitura = :id
""", {"id": id_le})
    tipo, unidade, v = cur.fetchone()
    low, high = range_for(tipo)
    itens.append((id_chk, regra, f"{v:.2f} {unidade}", f"{low}-{high} {unidade}",
                  "Y" if low <= v <= high else "N", "auto-gerado"))
for ch in chunked(itens, 1000):
    cur.executemany("""
INSERT INTO checklist_itens (id_checklist, regra, valor_medido, faixa_ideal, ok, observacao)
VALUES (:1, :2, :3, :4, :5, :6)
""", ch)
conn.commit()
print(f"> checklist_itens: {len(itens)}")

# ========= 12) ALERTAS (>=500) =========
alertas = []
for i in range(N_MIN):
    # 60% derivados de leitura, 40% de checklist
    if random.random() < 0.6:
        id_le = random.choice(ids_leituras)
        id_chk = None
        tipo = "sensor_fora_faixa"
    else:
        id_le = None
        id_chk = random.choice(ids_checklists)
        tipo = "checklist_reprovado"
    mensagem = "evento gerado sintético"
    severidade = random.choice(["baixa","media","alta","critica"])
    ts_a = TS_BASE + dt.timedelta(days=random.randint(0, 300), seconds=random.randint(0,86400))
    resolvido = random.choice(["Y","N"])
    ts_res = ts_a if resolvido == "Y" else None
    resolvido_por = random.choice(ids_usuarios) if resolvido == "Y" else None
    alertas.append((id_le, id_chk, tipo, mensagem, severidade, ts_a, resolvido, ts_res, resolvido_por))
for ch in chunked(alertas, 1000):
    cur.executemany("""
INSERT INTO alertas (id_leitura, id_checklist, tipo, mensagem, severidade, ts_alerta, resolvido, ts_resolucao, resolvido_por)
VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)
""", ch)
conn.commit()
print(f"> alertas: {len(alertas)}")

ids_alertas = fetch_ids("alertas", "id_alerta")

# ========= 13) AJUSTES (>=500) =========
ajustes = []
for i in range(N_MIN):
    # 70% ligados a alerta, 30% a checklist
    if random.random() < 0.7:
        id_alerta = random.choice(ids_alertas)
        id_check  = None
    else:
        id_alerta = None
        id_check  = random.choice(ids_checklists)
    rec = "Ajustar parâmetro para dentro da faixa"
    exe = random.choice(["Ajuste aplicado","Pendente"])
    tsx = TS_BASE + dt.timedelta(days=random.randint(0, 300), seconds=random.randint(0,86400))
    exec_por = random.choice(ids_usuarios)
    ajustes.append((id_alerta, id_check, rec, exe, tsx, exec_por))
for ch in chunked(ajustes, 1000):
    cur.executemany("""
INSERT INTO ajustes (id_alerta, id_checklist, acao_recomendada, acao_executada, ts_execucao, executado_por)
VALUES (:1, :2, :3, :4, :5, :6)
""", ch)
conn.commit()
print(f"> ajustes: {len(ajustes)}")

# ========= FINAL =========
cur.close()
conn.close()
print("Concluído: todas as tabelas com >=500 registros.")
