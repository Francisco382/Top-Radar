import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import os
import time

def buscar_coordenadas():
    arquivo = 'carteiradistribuicao.xlsx'
    
    if not os.path.exists(arquivo):
        print("❌ Arquivo não encontrado!")
        return

    print("📖 Lendo planilha da empresa...")
    # Lendo a partir da linha 4 (skiprows=3) como no seu app principal
    df = pd.read_excel(arquivo, skiprows=3)
    
    # Configura o buscador (Nominatim é gratuito)
    geolocator = Nominatim(user_agent="top_radar_analytics")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    # Tenta identificar a coluna de endereço
    col_end = next((c for c in df.columns if 'ender' in str(c).lower() or 'rua' in str(c).lower()), None)
    
    if not col_end:
        print("❌ Não encontrei a coluna de endereço. Verifique o nome no Excel.")
        return

    print(f"🌍 Buscando coordenadas para a coluna: {col_end}")
    print("Isso pode demorar um pouco dependendo do número de linhas...")

    # Cria as colunas se não existirem
    if 'Latitude' not in df.columns: df['Latitude'] = None
    if 'Longitude' not in df.columns: df['Longitude'] = None

    for i, row in df.iterrows():
        # Só busca se a célula estiver vazia para não gastar tempo
        if pd.isna(row.get('Latitude')) or row.get('Latitude') == '':
            try:
                # Adicione o nome da sua cidade/estado para ser mais preciso
                endereco_completo = f"{row[col_end]}, São Paulo, Brasil" 
                location = geolocator.geocode(endereco_completo)
                
                if location:
                    df.at[i, 'Latitude'] = location.latitude
                    df.at[i, 'Longitude'] = location.longitude
                    print(f"✅ {i+1}: {row[col_end]} -> Localizado")
                else:
                    print(f"❓ {i+1}: {row[col_end]} -> Não encontrado")
                
                # Respeitar o limite gratuito do servidor
                time.sleep(1) 
            except Exception as e:
                print(f"⚠️ Erro na linha {i+1}: {e}")

    # Salva o resultado mantendo a estrutura original
    with pd.ExcelWriter(arquivo, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, startrow=3)
    
    print(f"\n✨ Pronto! Arquivo '{arquivo}' atualizado com Latitude e Longitude.")

if __name__ == "__main__":
    buscar_coordenadas()