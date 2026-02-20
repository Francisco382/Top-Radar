import pandas as pd


# Criando dados fictícios para teste (São Paulo como exemplo)
dados = {
    'rua': ['Av. Paulista, 1000', 'Rua Augusta, 500', 'Rua da Consolação, 10'],
    'bl': [1, 0, 0],
    'mov': [0, 1, 0],
    'plano_bl': ['500 Mega', '', ''],
    'plano_mov': ['', 'Controle 20GB', ''],
    'lat': [-23.5611, -23.5518, -23.5450],
    'lon': [-46.6559, -46.6601, -46.6510]
}

df = pd.DataFrame(dados)

# Salvando como carteira.xlsx (O pandas cuida da parte binária)
try:
    df.to_excel('carteira.xlsx', index=False)
    print("✅ Arquivo 'carteira.xlsx' criado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao criar arquivo: {e}")