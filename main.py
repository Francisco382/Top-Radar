import flet as ft
import pandas as pd
import math
import os

# --- LOGICA DE CALCULO ---
def calcular_distancia(lat1, lon1, lat2, lon2):
    try:
        # Raio da Terra em KM
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) * math.sin(dlon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    except:
        return 0.0

def main(page: ft.Page):
    page.title = "Top Radar - Vendas"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400 # Simula tamanho de celular
    
    # Arquivo que você já tem no seu VS Code
    NOME_ARQUIVO_BASE = 'Cliente Fixa sem Móvel - Pontos.csv'

    page.appbar = ft.AppBar(
        title=ft.Text("📡 Radar de Clientes"),
        bgcolor=ft.colors.RED_ACCENT,
        color=ft.colors.WHITE,
        center_title=True,
    )

    lista_clientes = ft.ListView(expand=1, spacing=10, padding=20)

    def carregar_clientes(e):
        lista_clientes.controls.clear()
        
        # Simulando sua posição atual (Sâo Paulo como exemplo)
        # No futuro, usaremos o sensor do celular aqui
        min_lat, min_lon = -23.5505, -46.6333 

        if os.path.exists(NOME_ARQUIVO_BASE):
            try:
                # Lendo seu CSV real
                df = pd.read_csv(NOME_ARQUIVO_BASE, sep=None, engine='python', encoding='utf-8-sig')
                df.columns = [str(c).strip().lower() for c in df.columns]
                
                # Criando os cards para os vendedores
                for _, row in df.head(20).iterrows(): # Mostra os 20 primeiros
                    dist = calcular_distancia(min_lat, min_lon, float(row['latitude']), float(row['longitude']))
                    
                    lista_clientes.controls.append(
                        ft.Card(
                            content=ft.Container(
                                padding=15,
                                content=ft.Column([
                                    ft.ListTile(
                                        leading=ft.Icon(ft.icons.PERSON_PIN_CIRCLE, color="red"),
                                        title=ft.Text(str(row.get('nome', 'Cliente')).upper(), weight="bold"),
                                        subtitle=ft.Text(f"Distância: {dist:.2f} km"),
                                    ),
                                    ft.Row([
                                        ft.TextButton("📍 Rota", icon=ft.icons.MAP),
                                        ft.ElevatedButton("📝 Vender", bgcolor="green", color="white"),
                                    ], alignment=ft.MainAxisAlignment.END)
                                ])
                            )
                        )
                    )
            except Exception as ex:
                lista_clientes.controls.append(ft.Text(f"Erro ao ler dados: {ex}"))
        else:
            lista_clientes.controls.append(ft.Text("⚠️ Arquivo CSV não encontrado no App."))
        
        page.update()

    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.icons.SEARCH, on_click=carregar_clientes, bgcolor="red", tooltip="Buscar Clientes"
    )

    page.add(lista_clientes)

ft.app(target=main)