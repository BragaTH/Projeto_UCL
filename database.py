import sqlite3
from datetime import datetime

DB_PATH = 'estacionamento.db'

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS historico_vagas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            vaga_id     INTEGER NOT NULL,
            entrada     TEXT NOT NULL,
            saida       TEXT,
            duracao_min REAL
        );
    """)
    conn.commit()
    conn.close()
    print("[DB] Banco de dados inicializado.")

def registrar_entrada(vaga_id):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            'INSERT INTO historico_vagas (vaga_id, entrada) VALUES (?, ?)',
            (vaga_id, agora)
        )
        conn.commit()
        conn.close()
        print(f"[DB] Entrada registrada — vaga {vaga_id} às {agora}")
    except Exception as e:
        print(f"[DB] Erro ao registrar entrada: {e}")

def registrar_saida(vaga_id):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        agora = datetime.now()
        agora_str = agora.strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            SELECT id, entrada FROM historico_vagas
            WHERE vaga_id = ? AND saida IS NULL
            ORDER BY id DESC LIMIT 1
        ''', (vaga_id,))
        row = cursor.fetchone()

        if row:
            registro_id, entrada_str = row
            entrada = datetime.strptime(entrada_str, '%Y-%m-%d %H:%M:%S')
            duracao = round((agora - entrada).total_seconds() / 60, 2)
            cursor.execute('''
                UPDATE historico_vagas
                SET saida = ?, duracao_min = ?
                WHERE id = ?
            ''', (agora_str, duracao, registro_id))
            conn.commit()
            print(f"[DB] Saída registrada — vaga {vaga_id} às {agora_str} | duração: {duracao} min")
        else:
            print(f"[DB] Aviso: nenhuma entrada aberta encontrada para vaga {vaga_id}")

        conn.close()
    except Exception as e:
        print(f"[DB] Erro ao registrar saída: {e}")

def buscar_historico(limit=50):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT vaga_id, entrada, saida, duracao_min
            FROM historico_vagas
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB] Erro ao buscar histórico: {e}")
        return []