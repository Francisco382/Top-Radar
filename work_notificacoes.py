import sqlite3
import smtplib
import os
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- CONFIGURAÇÕES (Devem ser as mesmas do seu app.py) ---
DB_PATH = "data/database.db"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP = os.getenv("SENHA_APP")
EMAIL_SUPERVISOR = "vinicius.franciscosilva@claro.com.br"

def enviar_email(destinatario, assunto, corpo):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(corpo, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_APP)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar para {destinatario}: {e}")
        return False

def processar_agendamentos():
    print(f"[{datetime.now()}] Verificando agendamentos para as próximas 24h...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Define a janela de tempo: exatamente daqui a 24h, com margem de 1h
    agora = datetime.now()
    janela_inicio = (agora + timedelta(days=1) - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    janela_fim = (agora + timedelta(days=1) + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        SELECT * FROM agendamentos 
        WHERE data_visita BETWEEN ? AND ? 
        AND notificado_24h = 0
    """, (janela_inicio, janela_fim))

    agendamentos = cursor.fetchall()

    for ag in agendamentos:
        # Template Vendedor
        corpo_v = f"Olá {ag['vendedor']},\n\nLEMBRETE: Você tem uma visita amanhã às {ag['data_visita']}.\nCliente: {ag['cliente']}\nLocal: {ag['local_visita']}\n\nBoas vendas!"
        
        # Template Supervisor
        corpo_s = f"Aviso de Agenda: O vendedor {ag['vendedor']} tem visita amanhã.\nCliente: {ag['cliente']}\nHorário: {ag['data_visita']}"

        # Disparos
        enviou_v = enviar_email(ag['email_vendedor'], f"🔔 Lembrete 24h: {ag['cliente']}", corpo_v)
        enviou_s = enviar_email(EMAIL_SUPERVISOR, f"📊 Visita Amanhã: {ag['vendedor']}", corpo_s)

        if enviou_v and enviou_s:
            cursor.execute("UPDATE agendamentos SET notificado_24h = 1 WHERE id = ?", (ag['id'],))
            print(f"✅ Notificação enviada para {ag['vendedor']} e supervisor sobre o cliente {ag['cliente']}.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Se rodar manualmente, ele executa uma vez. 
    # Em um servidor, você pode colocar num loop com time.sleep(3600) ou usar um Cron Job.
    processar_agendamentos()