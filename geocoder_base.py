import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

def processar_base():
    arquivo = 'carteiradistribuicao.xlsx'
    print("⏳ Carregando planilha...")
    
    # Lê a planilha (ajustado para pular as 3 linhas que você tem no original)
    df = pd.read_excel(arquivo, skiprows=3)
    
    geolocator = Nominatim(user_agent="radar_claro_vendas")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    print("🌍 Convertendo endereços (isso pode demorar dependendo do tamanho)...")
    
    # Criando coluna de endereço completo para facilitar a busca do GPS
    # Ajuste 'endereco_exibir' para o nome exato da sua coluna de endereço
    df['coords'] = df['endereco_exibir'].apply(geocode)
    
    # Extraindo latitude e longitude
    df['latitude'] = df['coords'].apply(lambda loc: loc.latitude if loc else None)
    df['longitude'] = df['coords'].apply(lambda loc: loc.longitude if loc else None)
    
    # Remove a coluna temporária e salva
    df.drop(columns=['coords'], inplace=True)
    df.to_excel(arquivo, index=False)
    print("✅ Planilha atualizada com sucesso!")

if __name__ == "__main__":
    processar_base()