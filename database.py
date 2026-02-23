import sqlite3
import os

DB_PATH = "data/database.db"

def get_connection():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Tabela de Vendas e Registros (Atualizada com CPF e Detalhes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendedor TEXT,
        cliente TEXT,
        tipo TEXT, -- 'Venda', 'Não Venda', 'Agendamento'
        produto_vendido TEXT, -- Para 'Venda'
        documento_cliente TEXT, -- CPF/CNPJ
        valor REAL,
        motivo_nao_venda TEXT, -- Para 'Não Venda'
        observacao TEXT,
        data_registro TEXT
    )
    """)

    # 2. Tabela de Agendamentos (Para o sistema de notificações 24h)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendedor TEXT,
        email_vendedor TEXT,
        cliente TEXT,
        data_visita TEXT, -- Formato ISO: YYYY-MM-DD HH:MM:SS
        local_visita TEXT,
        notificado_24h INTEGER DEFAULT 0 -- 0 para não, 1 para sim
    )
    """)

    # 3. Tabela de Usuários (Para controle de acesso e aprovação)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT UNIQUE,
        senha TEXT,
        perfil TEXT, -- 'admin' ou 'vendedor'
        status TEXT DEFAULT 'pendente' -- 'ativo' ou 'pendente'
    )
    """)

    conn.commit()
    conn.close()

# Executa a criação ao importar o arquivo
criar_tabelas()