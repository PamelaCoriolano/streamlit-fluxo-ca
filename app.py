import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Análise de Fluxo de Loja", layout="centered")

st.title("📊 Análise de Fluxo de Loja - C&A")

st.markdown("Faça upload da planilha com as colunas `CDate` e `Fluxo loja` para começar.")

uploaded_file = st.file_uploader("Upload do arquivo Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    df['CDate'] = pd.to_datetime(df['d-Calendar[CDate]'], dayfirst=True)
    df = df.sort_values('CDate')

    min_date = df['CDate'].min()
    max_date = df['CDate'].max()

    st.success(f"Dados carregados de {min_date.date()} até {max_date.date()}.")

    campaign_range = st.date_input("Selecione o período da campanha", [min_date, max_date])

    if len(campaign_range) == 2:
        campaign_start, campaign_end = campaign_range

        df['Período'] = df['CDate'].apply(
            lambda x: 'Durante Campanha' if campaign_start <= x <= campaign_end else 'Antes da Campanha'
        )

        fluxos = df.groupby('Período')['Fluxo loja'].sum().reset_index()

        st.subheader("📈 Comparativo de Fluxo Total")
        fig, ax = plt.subplots()
        ax.bar(fluxos['Período'], fluxos['Fluxo loja'], color=['gray', 'blue'])
        ax.set_ylabel("Total de Fluxo")
        st.pyplot(fig)

        st.subheader("📁 Planilha com período classificado")
        st.dataframe(df[['CDate', 'Fluxo loja', 'Período']])

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar planilha analisada", data=csv, file_name='fluxo_analisado.csv', mime='text/csv')
