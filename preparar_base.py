import pandas as pd
import os
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

# Configurações
ARQUIVO_ENTRADA = 'Cliente Fixa sem Móvel - Pontos.csv'

def processar_base():
    if not os.path.exists(ARQUIVO_ENTRADA):
        print(f"❌ Erro: Arquivo {ARQUIVO_ENTRADA} não encontrado!")
        return

    print("📖 Carregando base de dados...")
    # Lendo o arquivo (detectando separador automaticamente)
    df = pd.read_csv(ARQUIVO_ENTRADA, sep=None, engine='python', encoding='utf-8-sig')
    
    # Padroniza nomes para facilitar a busca
    df.columns = [str(c).strip().upper() for c in df.columns]

    # Verifica se já está processado
    if 'LATITUDE' in df.columns and 'LONGITUDE' in df.columns:
        if df['LATITUDE'].notnull().all():
            print("✅ Esta base já possui coordenadas. Nada a fazer.")
            return

    print("🌍 Iniciando Geolocalização (OpenStreetMap)...")
    geolocator = Nominatim(user_agent="top_radar_preparador")
    # Rate limiter para respeitar o limite de 1 requisição por segundo do serviço gratuito
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.2)

    # Monta o endereço baseado nas colunas da sua planilha de SP
    # CPF_CNPJ,TP_LOGR,LOGR,NUM,BAIRRO,CIDADE,UF
    df['ENDERECO_BUSCA'] = (
        df['TP_LOGR'].astype(str) + " " + 
        df['LOGR'].astype(str) + ", " + 
        df['NUM'].astype(str) + " - " + 
        df['BAIRRO'].astype(str) + ", " + 
        df['CIDADE'].astype(str) + " - " + 
        df['UF'].astype(str) + ", Brasil"
    )

    total = len(df)
    print(f"⏳ Processando {total} linhas. Isso vai levar aprox. {int(total * 1.5 / 60)} minutos.")

    # Executa a busca
    df['location'] = df['ENDERECO_BUSCA'].apply(geocode)
    
    # Extrai lat e lon
    df['LATITUDE'] = df['location'].apply(lambda loc: loc.latitude if loc else None)
    df['LONGITUDE'] = df['location'].apply(lambda loc: loc.longitude if loc else None)

    # Limpeza final
    sucesso = df['LATITUDE'].notnull().sum()
    df_final = df.drop(columns=['location', 'ENDERECO_BUSCA'])
    
    # Salva substituindo o original com as novas colunas
    df_final.to_csv(ARQUIVO_ENTRADA, index=False, encoding='utf-8-sig')
    
    print(f"--- ✅ FIM DO PROCESSO ---")
    print(f"📍 Endereços encontrados: {sucesso} de {total}")
    print(f"💾 Arquivo '{ARQUIVO_ENTRADA}' atualizado e pronto para o App!")

if __name__ == "__main__":
    processar_base()