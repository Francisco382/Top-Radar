import streamlit as st
import pandas as pd
import os
import plotly.express as px
import time
import numpy as np
import random
import pytz
import folium
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from streamlit_js_eval import get_geolocation
from streamlit_folium import st_folium
import base64

# --- CONFIGURAÇÕES GERAIS ---
ARQUIVO_USUARIOS = 'usuarios.csv'
NOME_ARQUIVO_BASE = 'Cliente Fixa sem Móvel - Pontos.csv'
ARQUIVO_VENDAS = 'vendas.csv'
LIMITE_CLIENTES_LISTA = 500

st.set_page_config(page_title="Analytics Radar Pro", page_icon="📡", layout="wide")

# --- 1. FUNÇÕES DE SUPORTE ---

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

def cabecalho_logo():
    logo_base64 = get_base64_of_bin_file("logoanalytics.png")
    if logo_base64:
        st.markdown(f'<div style="display: flex; justify-content: center; margin-bottom: 10px;" ><img src="data:image/png;base64,{logo_base64}" width="450"></div>', unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='text-align: center; color: #ee2128;' > 📡 Radar Superior</h2>", unsafe_allow_html=True)

def autenticar_usuario(email, senha):
    if not os.path.exists(ARQUIVO_USUARIOS): return None
    try:
        df = pd.read_csv(ARQUIVO_USUARIOS, sep=None, engine='python', encoding='utf-8-sig') 
        df.columns = [c.strip().lower() for c in df.columns]
        user = df[(df['email'].str.strip() == email.strip().lower()) & (df['senha'].astype(str).str.strip() == str(senha).strip())]
        return user.iloc[0].to_dict() if not user.empty else None
    except: return None

def calcular_distancia(lat1, lon1, lat2, lon2):
    try:
        if any(np.isnan([lat1, lon1, lat2, lon2])): return 999.0
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon, dlat = lon2 - lon1, lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return 2 * asin(sqrt(a)) * 6371
    except: return 999.0

def carregar_carteira():
    if not os.path.exists(NOME_ARQUIVO_BASE): return pd.DataFrame()
    try:
        df = pd.read_csv(NOME_ARQUIVO_BASE, sep=None, engine='python', encoding='utf-8-sig')
        df.columns = [str(c).strip().lower() for c in df.columns]
        if 'razao' in df.columns: df = df.rename(columns={'razao': 'nome'})
        for col in ['aprova_na_fixa', 'aprova_na_movel']:
            if col in df.columns: 
                df[col] = df[col].fillna('não').astype(str).str.strip().str.lower().eq('sim')
            else: df[col] = False
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        return df.dropna(subset=['latitude', 'longitude'])
    except: return pd.DataFrame()

def salvar_venda_resiliente(dados):
    try:
        df_nova = pd.DataFrame([dados])
        df_nova.to_csv(ARQUIVO_VENDAS, mode='a', index=False, header=not os.path.exists(ARQUIVO_VENDAS), encoding='utf-8-sig')
        return True
    except: return False

def salvar_novo_usuario(nome, email, senha):
    try:
        df_u = pd.read_csv(ARQUIVO_USUARIOS) if os.path.exists(ARQUIVO_USUARIOS) else pd.DataFrame(columns=['nome', 'email', 'senha', 'perfil'])
        if email.strip().lower() in df_u['email'].str.lower().values: return False
        perfil = 'admin' if df_u.empty else 'vendedor'
        novo = pd.DataFrame([[nome, email.strip().lower(), senha, perfil]], columns=['nome', 'email', 'senha', 'perfil'])
        novo.to_csv(ARQUIVO_USUARIOS, mode='a', index=False, header=not os.path.exists(ARQUIVO_USUARIOS), encoding='utf-8-sig')
        return True
    except: return False

def abrir_rota_gps(lat_destino, lon_destino):
    url = f"https://www.google.com/maps/dir/?api=1&destination={lat_destino},{lon_destino}"
    st.markdown(f"📍 [Abrir no Google Maps]({url})")

# --- 2. TELAS ---

def tela_login():
    cabecalho_logo()
    _, centro, _ = st.columns([1, 2, 1])
    with centro:
        email = st.text_input("📧 E-mail Corporativo")
        senha = st.text_input("🔒 Senha", type="password")
        if st.button("ENTRAR", type="primary", use_container_width=True):
            user = autenticar_usuario(email, senha)
            if user:
                st.session_state.logado = True
                st.session_state.nome, st.session_state.perfil = user['nome'], user['perfil']
                st.session_state.tela_atual = "Radar"
                st.rerun()
            else: st.error("❌ Credenciais inválidas.")
        if st.button("📝 CRIAR CONTA", use_container_width=True):
            st.session_state.tela_atual = "Cadastro"
            st.rerun()

def tela_cadastro():
    cabecalho_logo()
    _, centro, _ = st.columns([1, 2, 1])
    with centro:
        n = st.text_input("Nome completo")
        e = st.text_input("E-mail corporativo")
        s = st.text_input("Senha", type="password")
        if st.button("FINALIZAR CADASTRO", type="primary", use_container_width=True):
            if salvar_novo_usuario(n, e, s):
                st.success("Cadastro realizado!"); time.sleep(1); st.session_state.tela_atual = "Login"; st.rerun()
            else: st.error("E-mail já cadastrado.")
        if st.button("VOLTAR"): st.session_state.tela_atual = "Login"; st.rerun()

def tela_radar():
    st.title("📡 Radar de Vendas")
    
    loc = get_geolocation()
    if loc and 'coords' in loc:
        min_lat, min_lon = loc['coords']['latitude'], loc['coords']['longitude']
    else:
        min_lat, min_lon = -23.5505, -46.6333 

    df = carregar_carteira()
    if df.empty:
        st.warning("⚠️ Base de clientes não encontrada.")
        return

    # Carregar vendas para o set (Otimizado)
    vendas_realizadas = set()
    if os.path.exists(ARQUIVO_VENDAS):
        try:
            df_v = pd.read_csv(ARQUIVO_VENDAS, encoding='utf-8-sig')
            vendas_realizadas = set(df_v['cliente'].astype(str).str.upper().tolist())
        except: pass

    with st.sidebar.expander("📍 Filtros", expanded=True):
        busca = st.text_input("Buscar Nome")
        raio = st.slider("Raio de Atuação (KM)", 0.5, 30.0, 5.0)
    
    with st.sidebar.expander("📖 Legenda do Mapa", expanded=True):
        st.markdown("""
            <div style="font-size: 14px; line-height: 1.8;">
                <span style="color: red;">🚩</span> <b>Flag Vermelha</b>: Já Trabalhado<br>
                <span style="color: #2ecc71;">💰</span> <b>Cifrão Verde</b>: Fixa + Móvel<br>
                <span style="color: #3498db;">🏠</span> <b>Casa Azul</b>: Somente Fixa<br>
                <span style="color: #f39c12;">📱</span> <b>Celular Laranja</b>: Somente Móvel<br>
                <span style="color: blue;">🔵</span> <b>Você</b>
            </div>
        """, unsafe_allow_html=True)

    # Processamento Vetorizado
    df['dist_km'] = df.apply(lambda r: calcular_distancia(min_lat, min_lon, r['latitude'], r['longitude']), axis=1)
    df_f = df[df['dist_km'] <= raio].copy()
    
    if busca:
        df_f = df_f[df_f['nome'].str.contains(busca, case=False, na=False)]

    def definir_status_pme(row):
        af = row.get('aprova_na_fixa', False)
        am = row.get('aprova_na_movel', False)
        if af and am: return "Fixa + Móvel"
        elif af: return "Somente Fixa"
        elif am: return "Somente Móvel"
        return "Sem Oferta"

    df_f['Status_Venda'] = df_f.apply(definir_status_pme, axis=1)
    df_f = df_f.sort_values('dist_km').head(LIMITE_CLIENTES_LISTA)

    tab1, tab2 = st.tabs(["📍 Mapa Inteligente", "📋 Lista de Clientes"])
    
    with tab1:
        if not df_f.empty:
            m = folium.Map(location=[min_lat, min_lon], zoom_start=15)
            folium.Marker([min_lat, min_lon], tooltip="Sua Posição", 
                          icon=folium.Icon(color='blue', icon='user', prefix='fa')).add_to(m)
            
            for _, row in df_f.iterrows():
                # Lógica de marcação corrigida e indentada
                foi_trabalhado = str(row['nome']).upper() in vendas_realizadas
                
                if foi_trabalhado:
                    cor_pino, icone_pino = 'red', 'flag'
                    conteudo_popup = f"<b>{row['nome']}</b><br><span style='color:red;'>✅ JÁ TRABALHADO</span>"
                else:
                    status = row['Status_Venda']
                    if status == "Fixa + Móvel": 
                        cor_pino, icone_pino = 'green', 'usd'
                    elif status == "Somente Fixa": 
                        cor_pino, icone_pino = 'cadetblue', 'home'
                    else: 
                        cor_pino, icone_pino = 'orange', 'phone'
                    conteudo_popup = f"<b>{row['nome']}</b><br>{status}<br>⏳ PENDENTE"

                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=folium.Popup(conteudo_popup, max_width=300),
                    tooltip=row['nome'],
                    icon=folium.Icon(color=cor_pino, icon=icone_pino, prefix='fa')
                ).add_to(m)
            
            st_folium(m, width="100%", height=600)
        else:
            st.warning("Nenhum cliente encontrado no raio.")

    with tab2:
        for i, r in df_f.iterrows():
            trab = str(r['nome']).upper() in vendas_realizadas
            bolinha = "🔴" if trab else "⚪"
            with st.expander(f"{bolinha} {r['nome'].upper()} - {r['dist_km']:.2f} km"):
                st.write(f"**Oferta Disponível:** {r['Status_Venda']}")
                abrir_rota_gps(r['latitude'], r['longitude'])
                if st.button("📝 TABULAR", key=f"btn_list_{i}"):
                    st.session_state.dados_cliente = r.to_dict()
                    st.session_state.tela_atual = "Tabulacao"
                    st.rerun()

def tela_tabulacao():
    st.title("📝 Registro de Atendimento")
    cliente = st.session_state.get('dados_cliente', {})
    nome_cli = str(cliente.get('nome', 'CLIENTE')).upper()
    st.info(f"📍 Cliente: **{nome_cli}**")
    
    tipo = st.radio("Resultado:", ["Venda", "Não Venda", "Agendamento"], horizontal=True)
    
    with st.form("form_registro"):
        detalhes, valor, dt_age = "", 0.0, None
        if tipo == "Venda":
            c1, c2 = st.columns(2)
            prod = c1.selectbox("Solução", ["Banda Larga", "Móvel", "Digital"])
            valor = c2.number_input("Valor (R$)", min_value=0.0)
            doc = st.text_input("CPF ou CNPJ")
            detalhes = f"PROD: {prod} | DOC: {doc}"
        elif tipo == "Não Venda":
            motivo = st.selectbox("Motivo", ["Já é Cliente", "Sem interesse", "Preço"])
            detalhes = f"MOTIVO: {motivo}"
        elif tipo == "Agendamento":
            c1, c2 = st.columns(2)
            d = c1.date_input('Data')
            t = c2.time_input('Hora')
            dt_age = f"{d} {t}"
            detalhes = f"RETORNO: {dt_age}"
        
        obs = st.text_area("Observações")
        if st.form_submit_button("✅ SALVAR"):
            fuso = pytz.timezone('America/Sao_Paulo')
            dados = {
                "vendedor": st.session_state.nome, 
                "cliente": nome_cli, 
                "tipo": tipo,
                "detalhes": detalhes, 
                "valor": valor, 
                "agendamento": dt_age, 
                "observacao": obs,
                "data_registro": datetime.now(fuso).strftime("%d/%m/%Y %H:%M")
            }
            if salvar_venda_resiliente(dados):
                st.success("Salvo!"); time.sleep(1); st.session_state.tela_atual = "Radar"; st.rerun()

    if st.button("🔙 VOLTAR"): 
        st.session_state.tela_atual = "Radar"
        st.rerun()

def tela_supervisor():
    st.title("📊 BI & Gestão Estratégica")
    if not os.path.exists(ARQUIVO_VENDAS):
        st.info("ℹ️ Aguardando registros para gerar indicadores."); return
    
    vendas = pd.read_csv(ARQUIVO_VENDAS)
    st.metric("Total de Atendimentos", len(vendas))
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Tipos de Atendimento")
        fig_pie = px.pie(vendas, names='tipo', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
    with c2:
        st.subheader("Vendas por Vendedor")
        vendas_v = vendas[vendas['tipo'] == 'Venda']
        if not vendas_v.empty:
            fig_bar = px.bar(vendas_v.groupby('vendedor').size().reset_index(name='qtd'), x='vendedor', y='qtd')
            st.plotly_chart(fig_bar, use_container_width=True)
    
    st.subheader("📋 Auditoria Completa")
    st.dataframe(vendas, use_container_width=True)

# --- 4. NAVEGAÇÃO FINAL ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'tela_atual' not in st.session_state: st.session_state.tela_atual = "Login"

if not st.session_state.logado:
    if st.session_state.tela_atual == "Cadastro": tela_cadastro()
    else: tela_login()
else:
    if st.session_state.tela_atual == "Tabulacao":
        tela_tabulacao()
    else:
        with st.sidebar:
            st.write(f"👤 **{st.session_state.nome}**")
            opcao = st.radio("Navegação", ["Radar", "Supervisor"] if st.session_state.perfil == "admin" else ["Radar"])
            st.divider()
            if st.button("Sair", use_container_width=True):
                st.session_state.logado = False
                st.session_state.tela_atual = "Login"
                st.rerun()
        
        if opcao == "Supervisor":
            tela_supervisor()
        else:
            tela_radar()