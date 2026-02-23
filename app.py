import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
import time
import numpy as np
import folium
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from streamlit_js_eval import get_geolocation
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from database import get_connection
from datetime import timedelta

from database import criar_tabelas
from vendas_service import salvar_venda, listar_vendas

# ---------------- CONFIGURAÇÃO ----------------

criar_tabelas()

NOME_ARQUIVO_BASE = 'Cliente Fixa sem Móvel - Pontos.csv'

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
SENHA_APP = os.getenv("SENHA_APP")

st.set_page_config(page_title="Analytics Radar Pro",
                   page_icon="📡", layout="wide")

# ---------------- FUNÇÕES ----------------


def exibir_logo():
    caminho_logo = "logoanalytics.png"
    if os.path.exists(caminho_logo):
        with open(caminho_logo, "rb") as img:
            b64 = base64.b64encode(img.read()).decode()
            st.markdown(
                f'<div style="text-align:center"><img src="data:image/png;base64,{b64}" width="300"></div>', unsafe_allow_html=True)
    else:
        st.markdown(
            "<h1 style='text-align:center;'>📡 Analytics Radar Pro</h1>", unsafe_allow_html=True)


def carregar_carteira():
    if not os.path.exists(NOME_ARQUIVO_BASE):
        return pd.DataFrame()

    df = pd.read_csv(NOME_ARQUIVO_BASE, sep=None,
                     engine='python', encoding='utf-8-sig')
    df.columns = [str(c).strip().lower() for c in df.columns]

    mapa = {
        'razao': 'nome',
        'banda larga': 'possui_bl',
        'movel': 'possui_movel'
    }

    df = df.rename(columns=mapa)

    for col in ['possui_bl', 'possui_movel', 'possui_tv', 'aprova_fixa']:
        if col not in df.columns:
            df[col] = 'Não'

    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

    return df.dropna(subset=['latitude', 'longitude'])


def enviar_notificacao(destinatario, assunto, mensagem):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(mensagem, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_APP)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print("Erro envio email:", e)


# ---------------- TELAS ----------------

def tela_login():
    exibir_logo()
    st.title("🔐 Acesso ao Sistema")

    email = st.text_input("E-mail corporativo")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar", type="primary"):
        if not email.endswith("@claro.com.br"):
            st.error("Utilize e-mail corporativo @claro.com.br")
            return

        if email and senha:
            st.session_state.logado = True
            st.session_state.nome = email.split("@")[0].upper()
            st.session_state.email = email
            st.session_state.perfil = "admin" if "admin" in email.lower() else "vendedor"
            st.session_state.tela = "Radar"
            st.rerun()


def tela_radar():
    st.title("📡 Radar de Clientes")

    loc = get_geolocation()

    if loc and 'coords' in loc:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
    else:
        lat, lon = -23.5505, -46.6333
        st.info("Usando localização padrão...")

    df = carregar_carteira()
    vendas = listar_vendas()
    visitados = {str(v['cliente']).upper() for v in vendas}

    df['dist_km'] = np.sqrt((df['latitude']-lat)**2 +
                            (df['longitude']-lon)**2) * 111
    df = df.sort_values('dist_km').head(50)

    mapa = folium.Map(location=[lat, lon], zoom_start=14)
    cluster = MarkerCluster().add_to(mapa)

    for _, r in df.iterrows():
        foi = str(r['nome']).upper() in visitados
        cor = "lightgray" if foi else "blue"
        folium.Marker(
            [r['latitude'], r['longitude']],
            popup=r['nome'],
            icon=folium.Icon(color=cor)
        ).add_to(cluster)

    st_folium(mapa, width="100%", height=400)

    # LISTA DE CLIENTES
    for i, r in df.iterrows():
        nome = str(r['nome']).upper()
        foi = nome in visitados

        with st.expander(f"{nome} {'✅' if foi else ''}"):
            st.write(f"Distância: {r['dist_km']:.2f} km")

            if st.button("Tabular", key=f"tab_{i}"):
                st.session_state["cliente"] = r.to_dict()
                st.session_state["tela"] = "Tabulacao"
                st.rerun()

    st.info(f"Cliente: {cliente.get('nome')}")

    tipo = st.radio("Resultado", ["Venda", "Não Venda", "Agendamento"], horizontal=True)

    with st.form("form_tab"):

        registro = {
            "vendedor": st.session_state.nome,
            "cliente": cliente.get("nome"),
            "tipo": tipo,
            "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # ---------------- VENDA ----------------
        if tipo == "Venda":
            produto = st.selectbox("Produto", ["Dados", "Dados + Voz", "Dados + Voz + TV"])
            cpf = st.text_input("CPF/CNPJ")
            data_venda = st.date_input("Data Venda")
            valor = st.number_input("Valor", min_value=0.0)

            registro.update({
                "produto": produto,
                "cpf_cnpj": cpf,
                "data_venda": str(data_venda),
                "valor": valor
            })

        # ---------------- NÃO VENDA ----------------
        elif tipo == "Não Venda":
            motivo = st.selectbox("Motivo", [
                "Cliente não possui interesse",
                "Casa Vazia, sem morador",
                "Cliente fidelizado a concorrência",
                "Outros"
            ])

            descricao = ""
            if motivo == "Outros":
                descricao = st.text_area("Descreva o motivo")

            registro.update({
                "motivo_nao_venda": motivo,
                "descricao": descricao
            })

        # ---------------- AGENDAMENTO ----------------
        elif tipo == "Agendamento":
            data_ag = st.date_input("Data Agendamento")
            hora_ag = st.time_input("Hora")
            local = st.text_input("Local da Visita")

            data_visita = datetime.combine(data_ag, hora_ag)
            data_visita_str = data_visita.strftime("%Y-%m-%d %H:%M:%S")

            registro.update({
                "data_agendamento": data_visita_str,
                "local_visita": local
            })

        obs = st.text_area("Observações")
        registro["observacao"] = obs

        salvar = st.form_submit_button("Salvar")

        if salvar:
            salvar_venda(registro)

            # salvar também na tabela agendamentos
            if tipo == "Agendamento":
                conn = get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO agendamentos 
                    (vendedor, email_vendedor, cliente, data_visita, local_visita, notificado_24h)
                    VALUES (?, ?, ?, ?, ?, 0)
                """, (
                    st.session_state.nome,
                    st.session_state.email,
                    cliente.get("nome"),
                    data_visita_str,
                    local
                ))

                conn.commit()
                conn.close()

            st.success("Registro salvo com sucesso!")
            time.sleep(1)
            st.session_state.tela = "Radar"
            st.rerun()

    if st.button("Voltar para Radar"):
        st.session_state.tela = "Radar"
        st.rerun()


def tela_supervisor():
    st.title("📊 Painel Supervisor")

    dados = listar_vendas()
    df = pd.DataFrame(dados)

    if df.empty:
        st.info("Sem dados ainda.")
        return

    # Garantir colunas numéricas
    df["valor"] = pd.to_numeric(df.get("valor"), errors="coerce").fillna(0)

    # ---------------- FILTRO ----------------
    vendedores = ["Todos"] + sorted(df["vendedor"].dropna().unique().tolist())
    vendedor_filtro = st.selectbox("Filtrar por vendedor", vendedores)

    if vendedor_filtro != "Todos":
        df = df[df["vendedor"] == vendedor_filtro]

    # ---------------- MÉTRICAS ----------------
    vendas_df = df[df["tipo"] == "Venda"]
    nao_vendas_df = df[df["tipo"] == "Não Venda"]
    agend_df = df[df["tipo"] == "Agendamento"]

    total_vendido = vendas_df["valor"].sum()
    qtd_vendas = len(vendas_df)
    ticket_medio = total_vendido / qtd_vendas if qtd_vendas > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💰 Total Vendido", f"R$ {total_vendido:,.2f}")
    col2.metric("🛒 Qtde Vendas", qtd_vendas)
    col3.metric("🎯 Ticket Médio", f"R$ {ticket_medio:,.2f}")
    col4.metric("📅 Agendamentos", len(agend_df))

    st.divider()

def tela_tabulacao():
    st.title("📝 Tabulação")

    cliente = st.session_state.get("cliente")

    if not cliente:
        st.warning("Nenhum cliente selecionado.")
        if st.button("Voltar"):
            st.session_state.tela = "Radar"
            st.rerun()
        return

    st.info(f"Cliente: {cliente.get('nome')}")

    tipo = st.radio("Resultado", ["Venda", "Não Venda", "Agendamento"], horizontal=True)

    with st.form("form_tab"):

        registro = {
            "vendedor": st.session_state.nome,
            "cliente": cliente.get("nome"),
            "tipo": tipo,
            "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        obs = st.text_area("Observações")
        registro["observacao"] = obs

        salvar = st.form_submit_button("Salvar")

        if salvar:
            salvar_venda(registro)
            st.success("Registro salvo!")
            time.sleep(1)
            st.session_state.tela = "Radar"
            st.rerun()

    if st.button("Voltar para Radar"):
        st.session_state.tela = "Radar"
        st.rerun()

    # ---------------- GRÁFICO NÃO VENDA ----------------
    motivos = nao_vendas_df["motivo_nao_venda"].value_counts()

    if not motivos.empty:
        fig_pizza = go.Figure([go.Pie(
            labels=motivos.index,
            values=motivos.values,
            hole=0.4
        )])
        fig_pizza.update_layout(title="Motivos de Não Venda")
        st.plotly_chart(fig_pizza, use_container_width=True)

    st.divider()

    # ---------------- VENDAS POR DIA ----------------
    if "data_registro" in df.columns:
        df["data_registro"] = pd.to_datetime(
            df["data_registro"], errors="coerce")
        vendas_por_dia = vendas_df.groupby(
            df["data_registro"].dt.date)["valor"].sum()

        if not vendas_por_dia.empty:
            fig_linha = go.Figure()
            fig_linha.add_trace(go.Scatter(
                x=vendas_por_dia.index,
                y=vendas_por_dia.values,
                mode='lines+markers'
            ))
            fig_linha.update_layout(
                title="Vendas por Dia",
                xaxis_title="Data",
                yaxis_title="Valor"
            )
            st.plotly_chart(fig_linha, use_container_width=True)

    st.divider()

    # ---------------- RANKING VENDEDORES ----------------
    ranking = vendas_df.groupby(
        "vendedor")["valor"].sum().sort_values(ascending=False)

    if not ranking.empty:
        st.subheader("🏆 Ranking de Vendedores")
        st.dataframe(ranking.reset_index().rename(columns={
            "vendedor": "Vendedor",
            "valor": "Total Vendido"
        }), use_container_width=True)


def tela_agendamentos_24h():
    st.title("📅 Agendamentos - Próximas 24h")

    conn = get_connection()
    cursor = conn.cursor()

    agora = datetime.now()
    limite = agora + timedelta(hours=24)

    cursor.execute("SELECT * FROM agendamentos")
    dados = cursor.fetchall()
    conn.close()

    lista = []

    for ag in dados:
        try:
            data_visita = datetime.strptime(
                ag["data_visita"], "%Y-%m-%d %H:%M:%S")

            if agora <= data_visita <= limite:
                horas_restantes = round(
                    (data_visita - agora).total_seconds() / 3600, 1)

                lista.append({
                    "Vendedor": ag["vendedor"],
                    "Cliente": ag["cliente"],
                    "Data Visita": data_visita.strftime("%d/%m/%Y %H:%M"),
                    "Local": ag["local_visita"],
                    "Horas Restantes": horas_restantes,
                    "Notificado": "🟢 Sim" if ag["notificado_24h"] == 1 else "🔴 Não"
                })
        except:
            continue

    if not lista:
        st.success("Nenhum agendamento nas próximas 24h.")
        return

    df = pd.DataFrame(lista)

    st.metric("Total nas próximas 24h", len(df))
    st.dataframe(df, use_container_width=True)

# ---------------- ROTEAMENTO ----------------


if "logado" not in st.session_state:
    st.session_state.logado = False
if "tela" not in st.session_state:
    st.session_state.tela = "Login"

if not st.session_state.logado:
    tela_login()

else:
    with st.sidebar:
        st.success(f"Usuário: {st.session_state.nome}")

        menu = st.radio("Menu", [
            "Radar",
            "Supervisor",
            "Agendamentos 24h",
            "Sair"
        ])

        if menu == "Sair":
            st.session_state.clear()
            st.rerun()

        st.session_state.tela = menu

if st.session_state.tela == "Radar":
    tela_radar()

elif st.session_state.tela == "Supervisor":
    tela_supervisor()

elif st.session_state.tela == "Agendamentos 24h":
    tela_agendamentos_24h()

elif st.session_state.tela == "Tabulacao":
    tela_tabulacao()

if st.session_state.tela == "Radar":

    # -------- VERIFICA NOTIFICAÇÕES AUTOMÁTICAS --------
    def verificar_notificacoes_24h():
        ...

# depois da função
if st.session_state.get("logado"):
    verificar_notificacoes_24h()