from database import get_connection

def salvar_venda(dados):
    conn = get_connection()
    cursor = conn.cursor()

    # Salvamos na tabela 'vendas' (Histórico geral)
    cursor.execute("""
        INSERT INTO vendas 
        (vendedor, cliente, tipo, produto_vendido, documento_cliente, valor, motivo_nao_venda, observacao, data_registro)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        dados.get("vendedor"),
        dados.get("cliente"),
        dados.get("tipo"),
        dados.get("produto_vendido"),    # Novo campo
        dados.get("documento_cliente"),  # Novo campo
        dados.get("valor"),
        dados.get("motivo_nao_venda"),   # Novo campo
        dados.get("observacao"),
        dados.get("data_registro")
    ))

    # Se for um Agendamento, salvamos também na tabela específica para o Worker
    if dados.get("tipo") == "Agendamento":
        cursor.execute("""
            INSERT INTO agendamentos 
            (vendedor, email_vendedor, cliente, data_visita, local_visita)
            VALUES (?, ?, ?, ?, ?)
        """, (
            dados.get("vendedor"),
            dados.get("email_vendedor"),
            dados.get("cliente"),
            dados.get("data_agendamento"), # Formato ISO: YYYY-MM-DD HH:MM:SS
            dados.get("local_visita")
        ))

    conn.commit()
    conn.close()


def listar_vendas():
    conn = get_connection()
    cursor = conn.cursor()
    # Ordenar por data mais recente
    cursor.execute("SELECT * FROM vendas ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Nova função útil para o Supervisor ver os agendamentos futuros
def listar_agendamentos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM agendamentos WHERE notificado_24h = 0")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]