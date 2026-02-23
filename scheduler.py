import time
from datetime import datetime, timedelta
from database import get_connection
from work_notificacoes import enviar_email
from database import get_connection
from datetime import timedelta

def tela_agendamentos_24h():
    st.title("📅 Agendamentos - Próximas 24h")

    conn = get_connection()
    cursor = conn.cursor()

    agora = datetime.now()
    limite = agora + timedelta(hours=24)

    cursor.execute("""
        SELECT *
        FROM agendamentos
    """)

    agendamentos = cursor.fetchall()
    conn.close()

    lista_24h = []

    for ag in agendamentos:
        data_visita = datetime.strptime(ag["data_visita"], "%Y-%m-%d %H:%M:%S")

        if agora <= data_visita <= limite:
            horas_restantes = round((data_visita - agora).total_seconds() / 3600, 1)

            lista_24h.append({
                "Vendedor": ag["vendedor"],
                "Cliente": ag["cliente"],
                "Data Visita": data_visita,
                "Local": ag["local_visita"],
                "Horas Restantes": horas_restantes,
                "Notificado": "🟢 Sim" if ag["notificado_24h"] == 1 else "🔴 Não"
            })

    if not lista_24h:
        st.success("Nenhum agendamento nas próximas 24h.")
        return

    df = pd.DataFrame(lista_24h)

    st.metric("Total nas próximas 24h", len(df))

    st.dataframe(df, use_container_width=True)

def verificar_agendamentos():
    conn = get_connection()
    cursor = conn.cursor()

    agora = datetime.now()
    limite_24h = agora + timedelta(hours=24)

    cursor.execute("""
        SELECT id, vendedor, email_vendedor, cliente, data_visita
        FROM agendamentos
        WHERE notificado_24h = 0
    """)

    agendamentos = cursor.fetchall()

    for ag in agendamentos:
        id_ag = ag["id"]
        email = ag["email_vendedor"]
        cliente = ag["cliente"]
        data_visita = datetime.strptime(ag["data_visita"], "%Y-%m-%d %H:%M:%S")

        if agora <= data_visita <= limite_24h:

            enviar_email(
                email,
                "🔔 Lembrete de Visita - 24h",
                f"""
Cliente: {cliente}
Data da Visita: {data_visita}

Este é um lembrete automático 24h antes da visita.
"""
            )

            cursor.execute("""
                UPDATE agendamentos
                SET notificado_24h = 1
                WHERE id = ?
            """, (id_ag,))

            conn.commit()

    conn.close()


if __name__ == "__main__":
    while True:
        verificar_agendamentos()
        time.sleep(300)  # roda a cada 5 minutos