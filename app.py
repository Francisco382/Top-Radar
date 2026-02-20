import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime

# --- 1. CONFIGURAÇÃO VISUAL ---
st.set_page_config(page_title="Analytics Radar", page_icon="📡", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Visual Dark Mode */
    .stApp, .main, .block-container { background-color: #000000 !important; }
    h1, h2, h3, h4, p, span, label, .stMarkdown, div[data-testid="stMetricValue"], div[data-testid="stCaptionContainer"] { color: #ffffff !important; }
    
    /* Botão Principal (Vermelho) */
    div.stButton > button[kind="primary"] {
        width: 100%; background-color: #ee2924 !important; color: white !important;
        border-radius: 25px; height: 3.5em; font-weight: bold; border: none;
    }
    /* Botão Secundário (Cinza) */
    div.stButton > button[kind="secondary"] {
        width: 100%; border: 1px solid #555 !important; color: white !important;
        border-radius: 25px; height: 3.5em; background-color: transparent !important;
    }
    /* Inputs */
    .stTextInput>div>div>input {
        background-color: #1a1a1a !important; color: white !important; border: 1px solid #333 !important;
    }
    /* Expander */
    [data-testid="stExpander"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    /* Divisor */
    hr { border-color: #333 !important; }
        [data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BANCO DE DADOS (USUÁRIOS) ---
ARQUIVO_USUARIOS = 'usuarios.xlsx'

def init_usuarios():
    if not os.path.exists(ARQUIVO_USUARIOS):
        # Cria usuário padrão se não existir
        df = pd.DataFrame([{"nome": "Admin", "email": "adm@claro.com.br", "senha": "123456", "perfil": "admin"}])
        df.to_excel(ARQUIVO_USUARIOS, index=False)

def autenticar_usuario(email, senha):
    init_usuarios()
    try:
        df = pd.read_excel(ARQUIVO_USUARIOS)
        user = df[(df['email'] == email) & (df['senha'].astype(str) == str(senha))]
        if not user.empty: return user.iloc[0].to_dict()
    except: pass
    return None

def registrar_usuario(nome, email, senha):
    init_usuarios()
    df = pd.read_excel(ARQUIVO_USUARIOS)
    if email in df['email'].values: return False
    novo = {"nome": nome, "email": email, "senha": senha, "perfil": "vendedor"}
    pd.concat([df, pd.DataFrame([novo])], ignore_index=True).to_excel(ARQUIVO_USUARIOS, index=False)
    return True

def resetar_senha(email, nova_senha):
    init_usuarios()
    df = pd.read_excel(ARQUIVO_USUARIOS)
    if email in df['email'].values:
        df.loc[df['email'] == email, 'senha'] = nova_senha
        df.to_excel(ARQUIVO_USUARIOS, index=False)
        return True
    return False

# --- 3. DADOS DO APP (MAPA E VENDAS) ---
def carregar_carteira():
    if os.path.exists('carteira.xlsx'):
        try: return pd.read_excel('carteira.xlsx').fillna('')
        except: return pd.DataFrame()
    return pd.DataFrame()

def salvar_venda(dados):
    arquivo = 'vendas.csv'
    df = pd.DataFrame([dados])
    df.to_csv(arquivo, mode='a', index=False, header=not os.path.exists(arquivo))

# --- 4. CONTROLE DE TELA ---
if 'logado' not in st.session_state: st.session_state.logado = False
if 'tela' not in st.session_state: st.session_state.tela = "Login"
if 'user' not in st.session_state: st.session_state.user = ""

# --- 5. TELAS DE LOGIN / CADASTRO ---
def cabecalho_logo():
    # Colunas ajustadas para centralizar bem
    c1, c2, c3 = st.columns([1, 1, 1]) 
    
    with c2:
        if os.path.exists("logoanalytics.png"):
            # Ajustei width=180 (um tamanho médio bom)
            st.image("logoanalytics.png", width=180)
        else:
            st.image("logoanalytics.png", width=150)
            
    # O segredo está aqui: 'margin-top: -30px' puxa o texto para cima
    st.markdown(
        "<h2 style='text-align:center; margin-top: -30px; margin-bottom: 30px;'>Analytics Radar</h2>", 
        unsafe_allow_html=True
    )

def tela_login():
    cabecalho_logo()
    _, centro, _ = st.columns([1, 6, 1])
    with centro:
        email = st.text_input("E-mail", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_senha")
        st.write("")
        
        if st.button("ENTRAR", type="primary"):
            user = autenticar_usuario(email, senha)
            if user:
                st.session_state.logado = True
                st.session_state.user = user['email']
                st.session_state.tela = "Consulta"
                st.rerun()
            else:
                st.error("❌ Dados incorretos.")
        
        st.write("")
        st.divider()
        
        # --- SEUS BOTÕES AFASTADOS ---
        # [1, 3, 1] cria um espaço vazio grande no meio
        c1, meio, c2 = st.columns([1, 4, 1])
        
        with c1:
            if st.button("📝 CRIAR CONTA", type="secondary"):
                st.session_state.tela = "Cadastro"
                st.rerun()
        with c2:
            if st.button("🔑 ESQUECI SENHA", type="secondary"):
                st.session_state.tela = "Recuperar"
                st.rerun()

def tela_cadastro():
    cabecalho_logo()
    st.markdown("<h4 style='text-align:center;'>Novo Cadastro</h4>", unsafe_allow_html=True)
    _, centro, _ = st.columns([1, 6, 1])
    with centro:
        nome = st.text_input("Nome")
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        st.write("")
        if st.button("CADASTRAR", type="primary"):
            if registrar_usuario(nome, email, senha):
                st.success("✅ Sucesso! Faça login.")
                st.session_state.tela = "Login"
                st.rerun()
            else: st.error("E-mail já existe.")
        if st.button("VOLTAR", type="secondary"):
            st.session_state.tela = "Login"
            st.rerun()

def tela_recuperar():
    cabecalho_logo()
    st.markdown("<h4 style='text-align:center;'>Redefinir Senha</h4>", unsafe_allow_html=True)
    _, centro, _ = st.columns([1, 6, 1])
    with centro:
        email = st.text_input("Seu E-mail")
        nova = st.text_input("Nova Senha", type="password")
        if st.button("SALVAR", type="primary"):
            if resetar_senha(email, nova):
                st.success("✅ Senha alterada!")
                st.session_state.tela = "Login"
                st.rerun()
            else: st.error("E-mail não encontrado.")
        if st.button("VOLTAR", type="secondary"):
            st.session_state.tela = "Login"
            st.rerun()

# --- 6. TELAS DO SISTEMA (LOGADO) ---
def tela_consulta():
    st.subheader("📍 Radar de Vendas")
    
    # --- FILTROS ---
    c1, c2 = st.columns(2)
    f_bl = c1.checkbox("Sem Banda Larga")
    f_mv = c2.checkbox("Sem Móvel")
    
    # Busca inteligente (converte para string para não dar erro)
    busca = st.text_input("🔍 Buscar Rua, CEP ou Cliente:")
    
    df = carregar_carteira()
    
    if not df.empty:
        # APLICA FILTROS
        if f_bl: df = df[df['bl'] == 0]
        if f_mv: df = df[df['mov'] == 0]
        
        if busca:
            # Busca na Rua OU no Plano (ex: buscar quem tem "500 Mega")
            mask = df['rua'].astype(str).str.contains(busca, case=False) | \
                   df['plano_bl'].astype(str).str.contains(busca, case=False)
            df = df[mask]
        
        # --- MAPA (Agora com zoom automático se filtrar) ---
        if 'lat' in df.columns:
            st.map(df, latitude='lat', longitude='lon', size=20, color='#ee2924')
            
        st.write(f"**{len(df)}** oportunidades encontradas")
        st.divider()

        # --- LISTA DE CARTÕES (CARDS) ---
        for i, row in df.iterrows():
            # O Título do card agora mostra a Rua
            with st.expander(f"🏠 {row['rua']}"):
                
                # COLUNA 1: DETALHES TÉCNICOS
                c_info, c_acao = st.columns([2, 1])
                
                with c_info:
                    st.caption("Situação Atual:")
                    # Banda Larga
                    if row['bl']:
                        st.write(f"🌐 **Net:** ✅ Cliente ({row.get('plano_bl', '-')})")
                    else:
                        st.write(f"🌐 **Net:** ❌ Oportunidade")
                    
                    # Móvel
                    if row['mov']:
                        st.write(f"📱 **Cel:** ✅ Cliente ({row.get('plano_mov', '-')})")
                    else:
                        st.write(f"📱 **Cel:** ❌ Oportunidade")

                # COLUNA 2: AÇÕES (BOTÕES)
                with c_acao:
                    st.write("") # Espaço para alinhar
                    
                    # 1. Botão de Tabular (Vermelho)
                    if st.button("📝 TABULAR", key=f"btn_tab_{i}", type="primary"):
                        st.session_state.endereco_foco = row['rua']
                        st.session_state.tela = "Tabulacao"
                        st.rerun()
                    
                    # 2. Botão de GPS (Link Externo)
                    # Cria link para abrir direto no App de Mapas do celular
                    if 'lat' in row and pd.notnull(row['lat']):
                        link_gps = f"https://www.google.com/maps/search/?api=1&query={row['lat']},{row['lon']}"
                        st.link_button("🗺️ ABRIR GPS", link_gps)
                    else:
                        st.caption("Sem GPS")

    else:
        st.warning("⚠️ Sua carteira está vazia ou o filtro não encontrou nada.")
        st.info("Dica: Verifique se o arquivo 'carteira.xlsx' está na pasta.")

def tela_tabulacao():
    st.subheader(f"📝 Visita: {st.session_state.endereco_foco}")
    res = st.radio("Resultado", ["Venda", "Não Venda", "Agendamento"])
    if st.button("SALVAR DADOS", type="primary"):
        salvar_venda({"data": datetime.now().strftime("%d/%m %H:%M"), "user": st.session_state.user, "local": st.session_state.endereco_foco, "res": res})
        st.success("Salvo!")
        st.session_state.tela = "Consulta"
        st.rerun()
    if st.button("VOLTAR", type="secondary"):
        st.session_state.tela = "Consulta"
        st.rerun()

def tela_relatorios():
    st.title("📊 Dashboard")
    if os.path.exists('vendas.csv'):
        df = pd.read_csv('vendas.csv')
        c1, c2 = st.columns(2)
        c1.metric("Visitas", len(df))
        c2.metric("Vendas", len(df[df['res']=='Venda']))
        fig = px.pie(df, names='res', color_discrete_sequence=['#ee2924', '#fff', '#555'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig)
    else: st.info("Sem vendas ainda.")

# --- 7. NAVEGAÇÃO PRINCIPAL ---
init_usuarios()

if not st.session_state.logado:
    if st.session_state.tela == "Cadastro": tela_cadastro()
    elif st.session_state.tela == "Recuperar": tela_recuperar()
    else: tela_login()
else:
    with st.sidebar:
        if os.path.exists("logoanalytics.png"): st.image("logoanalytics.png", width=100)
        else: st.title("📡")
        
        if st.session_state.user: st.caption(f"Olá, {st.session_state.user}")
        
        menu = st.radio("Menu", ["Radar", "Relatórios"])
        
        st.write("")
        if st.button("SAIR", type="secondary"):
            st.session_state.logado = False
            st.session_state.tela = "Login"
            st.rerun()
            
    if menu == "Relatórios": tela_relatorios()
    elif st.session_state.tela == "Tabulacao": tela_tabulacao()
    else: tela_consulta()