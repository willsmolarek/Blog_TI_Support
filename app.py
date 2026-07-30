import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Painel de Qualidade e PPM - WEG",
    layout="wide"
)

# ---------------------------------------------------------------
# CARREGAMENTO E LEITURA DAS PLANILHAS
# ---------------------------------------------------------------
@st.cache_data
def carregar_dados():
    # Carrega os arquivos CSV gerados das planilhas fornecidas
    df_defeitos = pd.read_csv("EXEMPLO DESIGN DEFEITO.xlsx - Planilha1.csv")
    df_producao = pd.read_csv("EXEMPLO DESIGN PRODUÇÃO.xlsx - Planilha1.csv")

    # Remove espaços extras do nome das colunas
    df_defeitos.columns = df_defeitos.columns.str.strip()
    df_producao.columns = df_producao.columns.str.strip()

    # --- TRATAMENTO TABELA DEFEITOS ---
    df_defeitos['QTD_REFUGO'] = pd.to_numeric(df_defeitos['QTD PÇ'], errors='coerce').fillna(0)
    df_defeitos['PESO_REFUGO'] = pd.to_numeric(df_defeitos['PESO TOTAL'], errors='coerce').fillna(0)
    df_defeitos['MES'] = pd.to_numeric(df_defeitos['MÊS'], errors='coerce')
    df_defeitos['CT_PROD'] = df_defeitos['CT PROD DESC'].astype(str).str.strip()

    # --- TRATAMENTO TABELA PRODUÇÃO ---
    col_prod = 'Pç' if 'Pç' in df_producao.columns else 'Qtd SAP'
    df_producao['QTD_PROD'] = pd.to_numeric(df_producao[col_prod], errors='coerce').fillna(0)
    
    col_mes_prod = 'Mês' if 'Mês' in df_producao.columns else 'MÊS'
    df_producao['MES'] = pd.to_numeric(df_producao[col_mes_prod], errors='coerce')
    
    col_ct_prod = 'CT Prod Descrição' if 'CT Prod Descrição' in df_producao.columns else 'CT PROD DESC'
    df_producao['CT_PROD'] = df_producao[col_ct_prod].astype(str).str.strip()

    return df_defeitos, df_producao


# ---------------------------------------------------------------
# INTERFACE PRINCIPAL
# ---------------------------------------------------------------
def main():
    st.title("📊 Indicadores de Qualidade - Cálculo de PPM")
    st.caption("Cruzamento Automático: Produção vs. Defeitos")

    try:
        df_defeitos, df_producao = carregar_dados()
    except Exception as e:
        st.error(f"Erro ao carregar os arquivos de dados: {e}")
        return

    # ---------------------------------------------------------------
    # FILTROS
    # ---------------------------------------------------------------
    st.sidebar.header("🔍 Filtros")

    # Lista unificada de Centros de Trabalho
    cts = sorted(list(set(df_defeitos['CT_PROD'].dropna().unique()).union(set(df_producao['CT_PROD'].dropna().unique()))))
    ct_selecionado = st.sidebar.selectbox("Centro de Trabalho / Molde", ["Todos"] + cts)

    # Lista de Tipos de Defeito
    defeitos = sorted(list(df_defeitos['DEFEITO'].dropna().unique()))
    defeito_selecionado = st.sidebar.selectbox("Tipo de Defeito", ["Todos"] + defeitos)

    # Filtragem das tabelas
    df_def_filt = df_defeitos.copy()
    df_prod_filt = df_producao.copy()

    if ct_selecionado != "Todos":
        df_def_filt = df_def_filt[df_def_filt['CT_PROD'] == ct_selecionado]
        df_prod_filt = df_prod_filt[df_prod_filt['CT_PROD'] == ct_selecionado]

    if defeito_selecionado != "Todos":
        df_def_filt = df_def_filt[df_def_filt['DEFEITO'] == defeito_selecionado]

    # ---------------------------------------------------------------
    # CÁLCULOS E METRICAS
    # ---------------------------------------------------------------
    total_refugo = df_def_filt['QTD_REFUGO'].sum()
    total_producao = df_prod_filt['QTD_PROD'].sum()
    peso_refugo = df_def_filt['PESO_REFUGO'].sum()

    ppm_geral = (total_refugo / total_producao * 1_000_000) if total_producao > 0 else 0.0

    # Exibição das Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("PPM Geral", f"{ppm_geral:,.0f}")
    col2.metric("Total Refugado", f"{int(total_refugo)} pçs")
    col3.metric("Total Produzido", f"{int(total_producao)} pçs")
    col4.metric("Peso Refugado", f"{peso_refugo:,.1f} kg")

    st.divider()

    # ---------------------------------------------------------------
    # VISUALIZAÇÃO GRÁFICA
    # ---------------------------------------------------------------
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("📌 Defeitos por Quantidade (Pareto)")
        if not df_def_filt.empty:
            pareto = df_def_filt.groupby('DEFEITO')['QTD_REFUGO'].sum().reset_index().sort_values(by='QTD_REFUGO', ascending=False)
            fig_pareto = px.bar(pareto, x='DEFEITO', y='QTD_REFUGO', text='QTD_REFUGO', color='QTD_REFUGO', color_continuous_scale='Reds')
            st.plotly_chart(fig_pareto, use_container_width=True)
        else:
            st.info("Nenhum dado de defeito encontrado com os filtros atuais.")

    with g2:
        st.subheader("📈 Evolução do PPM Mensal")
        # Agrupamento por mês para cálculo do PPM mensal
        prod_mes = df_prod_filt.groupby('MES')['QTD_PROD'].sum().reset_index()
        def_mes = df_def_filt.groupby('MES')['QTD_REFUGO'].sum().reset_index()

        df_mes = pd.merge(prod_mes, def_mes, on='MES', how='outer').fillna(0)
        df_mes['PPM'] = df_mes.apply(lambda r: (r['QTD_REFUGO'] / r['QTD_PROD'] * 1_000_000) if r['QTD_PROD'] > 0 else 0, axis=1)
        df_mes = df_mes.sort_values(by='MES')

        if not df_mes.empty:
            fig_ppm = px.line(df_mes, x='MES', y='PPM', markers=True, labels={'MES': 'Mês', 'PPM': 'PPM'})
            st.plotly_chart(fig_ppm, use_container_width=True)
        else:
            st.info("Sem dados suficientes para exibir a tendência mensal.")

    # ---------------------------------------------------------------
    # TABELA DE DADOS
    # ---------------------------------------------------------------
    st.divider()
    st.subheader("📋 Tabela de Defeitos Filtrada")
    st.dataframe(df_def_filt[['DATA', 'DEFEITO', 'QTD_REFUGO', 'PESO_REFUGO', 'CT_PROD', 'MAT BRUT DESC']], use_container_width=True)


if __name__ == "__main__":
    main()