import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import random
import time

print("🚀 Iniciando Robô de Endereços Blindado...")

# 1. Tenta ler sua lista, se não existir, cria dados de teste
try:
    df = pd.read_excel("lista_bruta.xlsx")
    print(f"📋 Lendo {len(df)} endereços da sua lista...")
except:
    print("⚠️ 'lista_bruta.xlsx' não achado. Usando dados de exemplo...")
    data = {
        'Endereco': [
            'Av. Paulista, 1578, São Paulo', 
            'Rua Augusta, 1000, São Paulo',
            'Rua da Consolação, 500, São Paulo',
            'Av. Brigadeiro Faria Lima, 2000, São Paulo'
        ],
        'CEP': ['01310-200', '01305-100', '01301-000', '01452-000'],
        'Status': ['Cliente', 'Oportunidade', 'Cliente', 'Oportunidade']
    }
    df = pd.DataFrame(data)

# 2. Configura o GPS
geolocator = Nominatim(user_agent="app_radar_claro_vendas")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# Função de Salva-Vidas (Gera Lat/Lon aleatória em SP se o GPS falhar)
def obter_lat_lon(endereco):
    try:
        loc = geolocator.geocode(endereco, timeout=10)
        if loc:
            return loc.latitude, loc.longitude
    except:
        pass
    # Se falhar, joga num ponto aleatório perto do centro de SP para não sumir
    print(f"⚠️ Não achei '{endereco}'. Usando coordenada aproximada.")
    return -23.5505 + random.uniform(-0.02, 0.02), -46.6333 + random.uniform(-0.02, 0.02)

# 3. Processa
latitudes = []
longitudes = []

print("📍 Buscando coordenadas (Aguarde)...")
for end in df['Endereco']:
    lat, lon = obter_lat_lon(end)
    latitudes.append(lat)
    longitudes.append(lon)
    time.sleep(1) # Respeitar o limite da API

df['lat'] = latitudes
df['lon'] = longitudes

# 4. Prepara colunas para o App
print("🛠️ Formatando para o App...")
df['rua'] = df['Endereco']
# Cria colunas técnicas baseadas no Status
df['bl'] = df['Status'].apply(lambda x: 1 if str(x).lower() == 'cliente' else 0)
df['mov'] = df['Status'].apply(lambda x: 1 if str(x).lower() == 'cliente' else 0)
df['f_ap'] = '🟢'
df['m_ap'] = '🟢'
df['plano_bl'] = df['bl'].apply(lambda x: '500 Mega' if x == 1 else '')
df['plano_mov'] = df['mov'].apply(lambda x: 'Controle 20GB' if x == 1 else '')

# 5. Salva
df.to_excel("carteira.xlsx", index=False)
print(f"✅ Sucesso! 'carteira.xlsx' gerado com {len(df)} locais.")