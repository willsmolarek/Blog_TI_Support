import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------------
# CONFIGURAÇÕES DA PÁGINA
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard de PPM & Defeitos - WEG",
    layout="wide",
)

# ---------------------------------------------------------------
# CARREGAMENTO E TRATAMENTO DOS DADOS (CSVs)
# ---------------------------------------------------------------
@st.cache_data
def carregar_dados():
    # 1. Carrega o primeiro CSV (Dados agregados de Refugo/Design)
    df_design = pd.read_csv("EXEMPLO DESIGN DEFEITO - Copia.xlsx - Planilha1.csv")
    
    # 2. Carrega o segundo CSV (Dados detalhados com Apontamentos)
    df_detalhado = pd.read_csv("EXEMPLO DESIGN DEFEITO.xlsx - Planilha1.csv")
    
    # Limpeza dos nomes das colunas (remove espaços extras)
    df_design.columns = df_design.columns.str.strip()
    df_detalhado.columns = df_detalhado.columns.str.strip()
    
    # Tratamento de Tipos e Datas
    df_design['DATA'] = pd.to_datetime(df_design['DATA'], errors='coerce')
    df_design['QTD PÇ'] = pd.to_numeric(df_design['QTD PÇ'], errors='coerce').fillna(0)
    df_design['PESO TOTAL'] = pd.to_numeric(df_design['PESO TOTAL'], errors='coerce').fillna(0)
    
    return df_design, df_detalhado

# ---------------------------------------------------------------
# INTERFACE PRINCIPAL
# ---------------------------------------------------------------
def main():
    st.title("📊 Painel de Qualidade & Cálculo de PPM")
    st.caption("Análise Integrada das Planilhas de Defeitos e Refugos")

    try:
        df_design, df_detalhado = carregar_dados()
    except Exception as e:
        st.error(f"Erro ao carregar os arquivos CSV/Excel: {e}")
        st.info("Certifique-se de que os arquivos estão na mesma pasta do script app.py")
        return

    # ---------------------------------------------------------------
    # FILTROS LATERAIS
    # ---------------------------------------------------------------
    st.sidebar.header("🔍 Filtros de Análise")
    
    # Filtro de Centro de Trabalho / Moldagem
    cts_disponiveis = ["Todos"] + list(df_design['CT PROD DESC'].dropna().unique())
    ct_selecionado = st.sidebar.selectbox("Centro de Trabalho / Molde", cts_disponiveis)
    
    # Filtro de Tipo de Defeito
    defeitos_disponiveis = ["Todos"] + list(df_design['DEFEITO'].dropna().unique())
    defeito_selecionado = st.sidebar.selectbox("Tipo de Defeito", defeitos_disponiveis)

    # Aplicação dos Filtros
    df_filtrado = df_design.copy()
    if ct_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['CT PROD DESC'] == ct_selecionado]
    if defeito_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['DEFEITO'] == defeito_selecionado]

    # ---------------------------------------------------------------
    # MÉTRICAS E CÁLCULO DO PPM
    # ---------------------------------------------------------------
    total_pecas_refugadas = df_filtrado['QTD PÇ'].sum()
    peso_total_refugado = df_filtrado['PESO TOTAL'].sum()
    
    # Exemplo: Defina ou receba a produção total para o cálculo exato do PPM
    # (Por padrão, usa-se um volume base se não houver coluna de 'Produção Total Boa')
    producao_total_estimada = st.sidebar.number_input(
        "Produção Total do Período (Pçs)", 
        value=100000, 
        step=5000,
        help="Informe o volume total produzido no período para calcular o PPM exato."
    )

    ppm = (total_pecas_refugadas / producao_total_estimada) * 1_000_000 if producao_total_estimada > 0 else 0

    # Exibição dos KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PPM Calculado", f"{ppm:,.2f}")
    c2.metric("Total Peças Refugadas", f"{int(total_pecas_refugadas)} pçs")
    c3.metric("Peso Total Percebido", f"{peso_total_refugado:,.1f} kg")
    c4.metric("Ocorrências Registradas", len(df_filtrado))

    st.divider()

    # ---------------------------------------------------------------
    # GRÁFICOS
    # ---------------------------------------------------------------
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📌 Defeitos por Tipo (Pareto)")
        df_pareto = df_filtrado.groupby('DEFEITO')['QTD PÇ'].sum().reset_index().sort_values(by='QTD PÇ', ascending=False)
        fig_pareto = px.bar(df_pareto, x='DEFEITO', y='QTD PÇ', text='QTD PÇ', color='QTD PÇ', color_continuous_scale='Reds')
        st.plotly_chart(fig_pareto, use_container_width=True)

    with col_g2:
        st.subheader("📅 Evolução Temporal do Refugo")
        df_tempo = df_filtrado.groupby('MÊS')['QTD PÇ'].sum().reset_index()
        fig_tempo = px.line(df_tempo, x='MÊS', y='QTD PÇ', markers=True, title="Peças Refugadas por Mês")
        st.plotly_chart(fig_tempo, use_container_width=True)

    # ---------------------------------------------------------------
    # TABELA COMPLETA DE DADOS
    # ---------------------------------------------------------------
    st.subheader("📋 Detalhamento dos Registros de Refugo")
    st.dataframe(df_filtrado[['DATA', 'DEFEITO', 'QTD PÇ', 'PESO TOTAL', 'CT PROD DESC', 'MAT BRUT DESC']], use_container_width=True)


if __name__ == "__main__":
    main()