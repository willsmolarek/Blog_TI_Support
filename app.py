import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------------
# CONFIGURAÇÕES DA PÁGINA
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Gestão de Refugos e PPM - WEG",
    layout="wide",
)

# ---------------------------------------------------------------
# CARREGAMENTO E TRATAMENTO DOS DADOS (CSVs)
# ---------------------------------------------------------------
@st.cache_data
def carregar_dados():
    # Carregando as duas planilhas enviadas
    df_design = pd.read_csv("EXEMPLO DESIGN DEFEITO - Copia.xlsx - Planilha1.csv")
    df_detalhado = pd.read_csv("EXEMPLO DESIGN DEFEITO.xlsx - Planilha1.csv")
    
    # Padronização e limpeza nos nomes das colunas
    df_design.columns = df_design.columns.str.strip()
    df_detalhado.columns = df_detalhado.columns.str.strip()
    
    # Tratamento de tipos de dados da planilha principal
    df_design['DATA'] = pd.to_datetime(df_design['DATA'], errors='coerce')
    df_design['QTD PÇ'] = pd.to_numeric(df_design['QTD PÇ'], errors='coerce').fillna(0)
    df_design['PESO TOTAL'] = pd.to_numeric(df_design['PESO TOTAL'], errors='coerce').fillna(0)
    df_design['MÊS'] = df_design['MÊS'].astype(str)
    
    return df_design, df_detalhado

# ---------------------------------------------------------------
# APLICAÇÃO PRINCIPAL
# ---------------------------------------------------------------
def main():
    st.title("📊 Painel de Qualidade - Cálculo de PPM & Análise de Defeitos")
    st.caption("Região 1 / Linhas de Moldagem - WEG")

    try:
        df_design, df_detalhado = carregar_dados()
    except Exception as e:
        st.error(f"Erro ao carregar os arquivos CSV: {e}")
        st.info("Garanta que os arquivos CSV das planilhas estejam no mesmo diretório do script.")
        return

    # ---------------------------------------------------------------
    # BARRA LATERAL - FILTROS E PARÂMETROS
    # ---------------------------------------------------------------
    st.sidebar.header("🔍 Filtros de Consulta")
    
    # Filtro por Centro de Trabalho (Molde/Posto)
    cts_disponiveis = ["Todos"] + sorted(list(df_design['CT PROD DESC'].dropna().unique()))
    ct_selecionado = st.sidebar.selectbox("Centro de Trabalho (CT)", cts_disponiveis)
    
    # Filtro por Tipo de Defeito
    defeitos_disponiveis = ["Todas"] + sorted(list(df_design['DEFEITO'].dropna().unique()))
    defeito_selecionado = st.sidebar.selectbox("Tipo de Defeito", defeitos_disponiveis)

    # Parâmetro de Produção Total para o Cálculo do PPM
    st.sidebar.divider()
    st.sidebar.subheader("📐 Parâmetro do PPM")
    producao_total = st.sidebar.number_input(
        "Volume Total Produzido (Pçs)", 
        value=100000, 
        step=5000,
        help="Informe o volume total produzido no período para calcular o PPM real."
    )

    # Aplicação dos filtros na base
    df_filtrado = df_design.copy()
    if ct_selecionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['CT PROD DESC'] == ct_selecionado]
    if defeito_selecionado != "Todas":
        df_filtrado = df_filtrado[df_filtrado['DEFEITO'] == defeito_selecionado]

    # ---------------------------------------------------------------
    # CÁLCULOS DOS KPIS
    # ---------------------------------------------------------------
    total_pecas_refugo = df_filtrado['QTD PÇ'].sum()
    peso_total_refugo = df_filtrado['PESO TOTAL'].sum()
    
    # Cálculo do PPM
    ppm = (total_pecas_refugo / producao_total) * 1_000_000 if producao_total > 0 else 0

    # Exibição dos Cartões Indicadores (KPIs)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("PPM (Partes Por Milhão)", f"{ppm:,.2f}")
    kpi2.metric("Total Refugado (Peças)", f"{int(total_pecas_refugo)} pçs")
    kpi3.metric("Peso Refugado", f"{peso_total_refugo:,.1f} kg")
    kpi4.metric("Ocorrências Registradas", len(df_filtrado))

    st.divider()

    # ---------------------------------------------------------------
    # GRÁFICOS VISUAIS
    # ---------------------------------------------------------------
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📌 Principais Defeitos (Pareto)")
        df_pareto = (
            df_filtrado.groupby('DEFEITO')['QTD PÇ']
            .sum()
            .reset_index()
            .sort_values(by='QTD PÇ', ascending=False)
        )
        fig_pareto = px.bar(
            df_pareto, 
            x='DEFEITO', 
            y='QTD PÇ', 
            text='QTD PÇ', 
            labels={'DEFEITO': 'Defeito', 'QTD PÇ': 'Qtd. Peças Refugadas'},
            color='QTD PÇ', 
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_pareto, use_container_width=True)

    with col_g2:
        st.subheader("📈 Evolução de Refugo por Mês")
        df_tempo = (
            df_filtrado.groupby('MÊS')['QTD PÇ']
            .sum()
            .reset_index()
            .sort_values(by='MÊS')
        )
        fig_tempo = px.line(
            df_tempo, 
            x='MÊS', 
            y='QTD PÇ', 
            markers=True, 
            labels={'MÊS': 'Mês', 'QTD PÇ': 'Qtd. Peças Refugadas'}
        )
        st.plotly_chart(fig_tempo, use_container_width=True)

    # ---------------------------------------------------------------
    # TABELA DE DADOS
    # ---------------------------------------------------------------
    st.subheader("📋 Registros de Defeito Filtrados")
    st.dataframe(
        df_filtrado[['DATA', 'DEFEITO', 'QTD PÇ', 'PESO TOTAL', 'CT PROD DESC', 'MAT BRUT DESC']], 
        use_container_width=True
    )

if __name__ == "__main__":
    main()