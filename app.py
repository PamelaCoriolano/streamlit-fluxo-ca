import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Análise de Fluxo de Loja", layout="wide")

st.title("📊 Análise de Fluxo de Loja - C&A")

st.markdown("Faça upload da planilha com as colunas corretas para iniciar a análise.")

uploaded_file = st.file_uploader("📁 Upload do arquivo Excel", type=["xlsx"])

if uploaded_file:
 # Carrega e prepara os dados
 df = pd.read_excel(uploaded_file)

 # Renomeia coluna para facilitar visualização
 df = df.rename(columns={'[v_calculationGroups]': 'Fluxo loja'})

 # Converte e ordena datas
 df['CDate'] = pd.to_datetime(df['d-Calendar[CDate]'], dayfirst=True)
 df = df.sort_values('CDate')

 # Sidebar: Filtros
 st.sidebar.header("Filtros")

 # Ano
 anos = sorted(df['d-Calendar[Cea Year]'].dropna().unique())
 ano_selecionado = st.sidebar.selectbox("Selecionar Ano", anos)

 # Location Codes
 locais = sorted(df['d-Location[Location Code]'].dropna().unique())
 locais_selecionados = st.sidebar.multiselect("Selecionar Location Code(s)", locais, default=locais[:3])

 # Semanas disponíveis
 semanas = sorted(df['d-Calendar[Short Desc. Week]'].dropna().unique())
 semanas_curtas = st.sidebar.multiselect("Selecionar Semanas Curtas (opcional)", semanas)

 # Filtra base principal
 df_filtrado = df[
     (df['d-Calendar[Cea Year]'] == ano_selecionado) &
     (df['d-Location[Location Code]'].isin(locais_selecionados))
 ]

 # Se filtro de semana curta for aplicado
 if semanas_curtas:
     df_filtrado = df_filtrado[df_filtrado['d-Calendar[Short Desc. Week]'].isin(semanas_curtas)]
     df_filtrado['Semana Curta'] = 'Sim'
 else:
     df_filtrado['Semana Curta'] = 'Não'

 # Verifica se há dados
 if df_filtrado.empty:
     st.warning("Nenhum dado encontrado para os filtros selecionados.")
 else:
     # Seleção do período de campanha
     min_date = df_filtrado['CDate'].min()
     max_date = df_filtrado['CDate'].max()

     st.success(f"Dados filtrados de {min_date.date()} até {max_date.date()} para os códigos selecionados.")

     st.subheader("📅 Configuração dos Períodos")
     
     # Período da campanha
     campaign_range = st.date_input("Selecione o período da campanha", [min_date, max_date], key="campaign_range")

     # Período de comparação
     comparison_range = st.date_input("Selecione o período de comparação", [min_date, max_date], key="comparison_range")

     if len(campaign_range) == 2 and len(comparison_range) == 2:
         campaign_start = pd.Timestamp(campaign_range[0])
         campaign_end = pd.Timestamp(campaign_range[1])
         comparison_start = pd.Timestamp(comparison_range[0])
         comparison_end = pd.Timestamp(comparison_range[1])

         # Define os períodos
         def definir_periodo(data):
             if campaign_start <= data <= campaign_end:
                 return 'Durante Campanha'
             elif comparison_start <= data <= comparison_end:
                 return 'Período de Comparação'
             else:
                 return 'Fora dos Períodos'

         df_filtrado['Período'] = df_filtrado['CDate'].apply(definir_periodo)

         # Filtra apenas os períodos relevantes
         df_relevante = df_filtrado[df_filtrado['Período'].isin(['Durante Campanha', 'Período de Comparação'])]

         # Agrupa por loja e período
         comparativo = df_relevante.groupby(['d-Location[Location Code]', 'Período'])['Fluxo loja'].sum().reset_index()

         # Pivot para gráfico
         pivot = comparativo.pivot(index='d-Location[Location Code]', columns='Período', values='Fluxo loja').fillna(0)

         # Gráfico
         st.subheader("📊 Comparativo de Fluxo por Loja")
         fig, ax = plt.subplots(figsize=(10, 6))
         pivot.plot(kind='bar', ax=ax)
         ax.set_ylabel("Fluxo Total")
         ax.set_xlabel("Location Code")
         ax.set_title("Fluxo por Loja - Comparação de Períodos")
         st.pyplot(fig)

         # Tabela
         st.subheader("📋 Dados detalhados")
         st.dataframe(df_relevante)

         # Download
         csv = df_relevante.to_csv(index=False).encode('utf-8')
         st.download_button("📥 Baixar planilha analisada", data=csv, file_name='fluxo_comparado_por_loja.csv', mime='text/csv')
