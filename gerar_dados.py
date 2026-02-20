import pandas as pd
import random

print("🚀 Gerando dados de teste...")

# Função para criar coordenadas em SP (perto da Av. Paulista)
def gerar_coord():
    return {
        "lat": -23.561684 + random.uniform(-0.005, 0.005),
        "lon": -46.655981 + random.uniform(-0.005, 0.005)
    }

dados = [
    {
        "rua": "Av. Paulista, 1000",
        "bl": 1, "mov": 1, 
        "plano_bl": "500 Mega", "plano_mov": "Pós 50GB",
        "f_ap": "⚪", "m_ap": "⚪", 
        **gerar_coord()
    },
    {
        "rua": "Rua Augusta, 500",
        "bl": 0, "mov": 0, # Oportunidade Total
        "plano_bl": "", "plano_mov": "",
        "f_ap": "🟢", "m_ap": "🟢",
        **gerar_coord()
    },
    {
        "rua": "Rua Haddock Lobo, 300",
        "bl": 1, "mov": 0, # Tem Net, falta Celular
        "plano_bl": "250 Mega", "plano_mov": "",
        "f_ap": "⚪", "m_ap": "🟢",
        **gerar_coord()
    },
    {
        "rua": "Rua da Consolação, 1500",
        "bl": 0, "mov": 1, # Tem Celular, falta Net
        "plano_bl": "", "plano_mov": "Controle 20GB",
        "f_ap": "🟢", "m_ap": "⚪",
        **gerar_coord()
    },
     {
        "rua": "Al. Santos, 800",
        "bl": 0, "mov": 0, 
        "plano_bl": "", "plano_mov": "",
        "f_ap": "🔴", "m_ap": "🟢",
        **gerar_coord()
    }
]

df = pd.DataFrame(dados)
df.to_excel("carteira.xlsx", index=False)
print(f"✅ Sucesso! Arquivo 'carteira.xlsx' criado com {len(df)} clientes.")