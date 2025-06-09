import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF

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

 # Filtro adicional: d-Location[StCd]
 estados = sorted(df['d-Location[StCd]'].dropna().unique())
 estado_selecionado = st.sidebar.multiselect("Selecionar Estado(s)", estados, default=estados)

 # Semanas disponíveis
 semanas = sorted(df['d-Calendar[Short Desc. Week]'].dropna().unique())
 semanas_curtas = st.sidebar.multiselect("Selecionar Semanas Curtas (opcional)", semanas)

 # Filtra base principal
 df_filtrado = df[
     (df['d-Calendar[Cea Year]'] == ano_selecionado) &
     (df['d-Location[Location Code]'].isin(locais_selecionados)) &
     (df['d-Location[StCd]'].isin(estado_selecionado))
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

         # Calcula a diferença percentual
         if 'Durante Campanha' in pivot.columns and 'Período de Comparação' in pivot.columns:
             pivot['% Diferença'] = ((pivot['Durante Campanha'] - pivot['Período de Comparação']) / pivot['Período de Comparação']) * 100

         # Gráfico de barras com rótulos e diferença percentual
         st.subheader("📊 Comparativo de Fluxo por Loja")
         fig, ax = plt.subplots(figsize=(10, 6))
         bars = pivot[['Durante Campanha', 'Período de Comparação']].plot(kind='bar', ax=ax)

         # Adiciona rótulos nas barras
         for bar in bars.containers:
             ax.bar_label(bar, fmt='%.0f')

         ax.set_ylabel("Fluxo Total")
         ax.set_xlabel("Location Code")
         ax.set_title("Fluxo por Loja - Comparação de Períodos")
         st.pyplot(fig)

         # Tabela
         st.subheader("📋 Dados detalhados")
         st.dataframe(pivot)

         # Download
         csv = pivot.to_csv(index=False).encode('utf-8')
         st.download_button("📥 Baixar planilha analisada", data=csv, file_name='fluxo_comparado_por_loja.csv', mime='text/csv')

         # Função para gerar o PDF
         def gerar_pdf(titulo, texto):
             pdf = FPDF()
             pdf.add_page()
             pdf.set_font("Arial", size=12)

             # Adiciona título
             pdf.set_font("Arial", style="B", size=16)
             pdf.cell(200, 10, txt=titulo, ln=True, align='C')

             # Adiciona texto
             pdf.set_font("Arial", size=12)
             pdf.multi_cell(0, 10, texto)

             # Salva o PDF em memória
             pdf_output = BytesIO()
             pdf.output(pdf_output)
             pdf_output.seek(0)
             return pdf_output

         # Gera o conteúdo do PDF
         titulo = "Relatório de Análise de Fluxo"
         texto = """
         Este relatório contém a análise de fluxo de loja com base nos filtros aplicados.
         Os gráficos e tabelas apresentados refletem os dados processados durante a execução.
         """
         pdf_file = gerar_pdf(titulo, texto)

         # Botão para exportar o PDF
         st.download_button(
             label="📥 Exportar relatório em PDF",
             data=pdf_file,
             file_name="relatorio_fluxo.pdf",
             mime="application/pdf"
         )
