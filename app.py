import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Análise de Fluxo de Loja", layout="wide")

st.title("📊 Análise de Fluxo de Loja - C&A")

st.markdown("Faça upload da planilha com as colunas corretas para iniciar a análise.")

uploaded_file = st.file_uploader("📁 Upload do arquivo Excel", type=["xlsx"])

if uploaded_file:
    # Carrega o dataframe
    df = pd.read_excel(uploaded_file)

    # Converte data
    df['CDate'] = pd.to_datetime(df['d-Calendar[CDate]'], dayfirst=True)
    df = df.sort_values('CDate')

    # Sidebar: Filtros
    st.sidebar.header("Filtros")

    # Filtro por ano
    anos = sorted(df['d-Calendar[Cea Year]'].dropna().unique())
    ano_selecionado = st.sidebar.selectbox("Selecionar Ano", anos)

    # Filtro por Location Code
    locais = sorted(df['d-Location[Location Code]'].dropna().unique())
    local_selecionado = st.sidebar.selectbox("Selecionar Location Code", locais)

    # Filtragem por ano e local
    df_filtrado = df[
        (df['d-Calendar[Cea Year]'] == ano_selecionado) &
        (df['d-Location[Location Code]'] == local_selecionado)
    ]

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        # Range da campanha
        min_date = df_filtrado['CDate'].min()
        max_date = df_filtrado['CDate'].max()

        st.success(f"Dados filtrados: {local_selecionado} - {ano_selecionado} | Período de {min_date.date()} até {max_date.date()}")

        campaign_range = st.date_input("Selecione o período da campanha", [min_date, max_date])

        if len(campaign_range) == 2:
            campaign_start = pd.Timestamp(campaign_range[0])
            campaign_end = pd.Timestamp(campaign_range[1])

            # Classifica o período
            df_filtrado['Período'] = df_filtrado['CDate'].apply(
                lambda x: 'Durante Campanha' if campaign_start <= x <= campaign_end else 'Antes da Campanha'
            )

            # Agrupa por período
            fluxos = df_filtrado.groupby('Período')['Fluxo loja'].sum().reset_index()

            # Gráfico
            st.subheader("📈 Comparativo de Fluxo Total por Período")
            fig, ax = plt.subplots()
            ax.bar(fluxos['Período'], fluxos['Fluxo loja'], color=['gray', 'blue'])
            ax.set_ylabel("Total de Fluxo")
            st.pyplot(fig)

            # Tabela completa
            st.subheader("📋 Tabela com todas as colunas e classificação de período")
            st.dataframe(df_filtrado)

            # Download
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar planilha analisada", data=csv, file_name='fluxo_analisado_completo.csv', mime='text/csv')
