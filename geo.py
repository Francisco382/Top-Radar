import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import os
import time

ARQUIVO = 'Cliente Fixa sem Móvel - Pontos.csv'

# 1. Carrega a base
if not os.path.exists(ARQUIVO):
    print("❌ Arquivo não encontrado!")
    exit()

df = pd.read_csv(ARQUIVO, sep=None, engine='python')
df.columns = [c.strip().lower() for c in df.columns]

# Garante que as colunas existam para podermos checar o progresso
if 'latitude' not in df.columns: df['latitude'] = None
if 'longitude' not in df.columns: df['longitude'] = None

# 2. Filtra apenas o que falta (latitude nula)
df_faltante = df[df['latitude'].isnull()].copy()
print(f"📊 Total da base: {len(df)} linhas")
print(f"📍 Linhas sem coordenadas: {len(df_faltante)} linhas")

if len(df_faltante) == 0:
    print("✅ Tudo mapeado com sucesso!")
    exit()

geolocator = Nominatim(user_agent="top_radar_batch")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

print("🚀 Iniciando... Salvando progresso a cada 10 registros.")

# 3. Loop de processamento
contador = 0
for i, row in df_faltante.iterrows():
    # Monta o endereço com as colunas reais da sua planilha
    endereco = f"{row['logr']}, {row['num']} - {row['bairro']}, {row['cidade']} - SP, Brasil"
    
    try:
        location = geocode(endereco)
        if location:
            df.at[i, 'latitude'] = location.latitude
            df.at[i, 'longitude'] = location.longitude
        
        contador += 1
        # Salva no arquivo a cada 10 para não perder progresso se a net cair
        if contador % 10 == 0:
            df.to_csv(ARQUIVO, index=False, encoding='utf-8-sig')
            print(f"💾 {contador} novos endereços salvos...")
            
    except Exception as e:
        print(f"⚠️ Erro na linha {i}: {e}")
        time.sleep(2) # Pausa maior em caso de erro

# Salva o resultado final
df.to_csv(ARQUIVO, index=False, encoding='utf-8-sig')
print("✅ Lote processado!")