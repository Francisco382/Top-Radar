import pandas as pd

# Criando dados fictícios de exemplo (São Paulo como exemplo)
data = {
    "Cliente": ["João Silva", "Maria Souza", "Loja ABC", "Padaria Central", "Oficina X"],
    "Status": ["Livre", "Livre", "Livre", "Livre", "Livre"],
    "Endereço": ["Rua A, 10", "Av B, 500", "Rua C, 88", "Rua D, 123", "Av E, 1000"],
    "Latitude": [-23.5505, -23.5615, -23.5489, -23.5555, -23.5600],
    "Longitude": [-46.6333, -46.6550, -46.6388, -46.6400, -46.6600],
    "Cluster": ["Cluster 01", "Cluster 01", "Cluster 02", "Cluster 02", "Cluster 03"]
}

df = pd.DataFrame(data)

# Criando um arquivo com 3 linhas vazias no topo para simular o padrão da Claro
with pd.ExcelWriter("carteiradistribuicao.xlsx", engine="xlsxwriter") as writer:
    # O 'startrow=3' faz o pandas começar a escrever na linha 4 (índice 3)
    df.to_excel(writer, index=False, sheet_name="Sheet1", startrow=3)

print("✅ Arquivo 'carteiradistribuicao.xlsx' gerado com sucesso!")
print("Agora rode o seu app com: streamlit run app_v2.py")