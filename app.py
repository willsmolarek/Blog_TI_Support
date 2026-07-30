import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------------
# CONFIGURAÇÕES DA PÁGINA
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Gestão de PPM e Qualidade - WEG",
    layout="wide",
)

# ---------------------------------------------------------------
# CARREGAMENTO E TRATAMENTO DOS DADOS
# ---------------------------------------------------------------
@st.cache_data
def carregar_dados():
    # 1. Tabela de Defeitos / Refugos
    df_defeitos = pd.read_csv("EXEMPLO DESIGN DEFEITO.xlsx - Planilha1.csv")
    
    # 2. Tabela de Produção
    df_producao = pd.read_csv("EXEMPLO DESIGN PRODUÇÃO.xlsx - Planilha1.csv")
    
    # Limpeza de espaços nos nomes das colunas
    df_defeitos.columns = df_defeitos.columns.str.strip()
    df_producao.columns = df_producao.columns.str.strip()
    
    # Tratamento de Colunas - Defeitos
    df_defeitos['QTD PÇ'] = pd.to_numeric(df_defeitos['QTD PÇ'], errors='coerce').fillna(0)
    df_defeitos['PESO TOTAL'] = pd.to_numeric(df_defeitos['PESO TOTAL'], errors='coerce').fillna(0)
    df_defeitos['MÊS'] = pd.to_numeric(df_defeitos['MÊS'], errors='coerce')
    
    # Tratamento de Colunas - Produção
    # Usa 'Pç' ou 'Qtd SAP' conforme disponível na tabela de produção
    col_qtd_prod = 'Pç' if 'Pç' in df_producao.columns else 'Qtd SAP'
    df_producao['QTD_PROD'] = pd.to_numeric(df_producao[col_qtd_prod], errors='coerce').fillna(0)
    df_producao['MÊS'] = pd.to_numeric(df_producao['Mês'], errors='coerce') if 'Mês' in df_producao.columns else pd.to_numeric(df_producao['MÊS'], errors='coerce')
    
    # Padronização da coluna de Centro de Trabalho para cruzamento/filtro
    if 'CT Prod Descrição' in df_producao.columns:
        df_producao['CT_PROD_DESC'] = df_producao['CT Prod Descrição']
    elif 'CT PROD DESC' in df_producao.columns:
        df_producao['CT_PROD_DESC'] = df_producao['CT PROD DESC']
    else:
        df_producao['CT_PROD_DESC'] = "Não especificado"
        
    df_defeitos['CT_PROD_DESC'] = df_defeitos['CT PROD DESC'] if 'CT PROD DESC' in df_defeitos.columns else "Não especificado"

    return df_defeitos, df_producao

# ---------------------------------------------------------------
# APLICAÇÃO PRINCIPAL
# ---------------------------------------------------------------
def main():
    st.title("📊 Painel de Qualidade & Cálculo Automático de PPM")
    st.caption("Análise integrada entre Produção e Refugos/Defeitos")

    try:
        df_defeitos, df_producao = carregar_dados()
    except Exception as e:
        st.error(f"Erro ao carregar os arquivos CSV: {e}")
        st.info("Certifique-se de que os arquivos 'EXEMPLO DESIGN DEFEITO.xlsx - Planilha1.csv' e 'EXEMPLO DESIGN PRODUÇÃO.xlsx - Planilha1.csv' estão no mesmo diretório.")
        return

    # ---------------------------------------------------------------
    # BARRA LATERAL - FILTROS DINÂMICOS
    # ---------------------------------------------------------------
    st.sidebar.header("🔍 Filtros de Consulta")
    
    # Filtro de Centro de Trabalho (Moldagem)
    cts_defeitos = set(df_defeitos['CT_PROD_DESC'].dropna().unique())
    cts_producao = set(df_producao['CT_PROD_DESC'].dropna().unique())
    cts_todos = ["Todos"] + sorted(list(cts_defeitos.union(cts_producao)))
    
    ct_selecionado = st.sidebar.selectbox("Centro de Trabalho / Molde", cts_todos)
    
    # Filtro de Tipo de Defeito
    defeitos_disponiveis = ["Todos"] + sorted(list(df_defeitos['DEFEITO'].dropna().unique()))
    defeito_selecionado = st.sidebar.selectbox("Tipo de Defeito", defeitos_disponiveis)

    # Aplicação dos Filtros nas duas tabelas
    df_def_filt = df_defeitos.copy()
    df_prod_filt = df_producao.copy()

    if ct_selecionado != "Todos":
        df_def_filt = df_def_filt[df_def_filt['CT_PROD_DESC'] == ct_selecionado]
        df_prod_filt = df_prod_filt[df_prod_filt['CT_PROD_DESC'] == ct_selecionado]

    if defeito_selecionado != "Todos":
        df_def_filt = df_def_filt[df_def_filt['DEFEITO'] == defeito_selecionado]

    # ---------------------------------------------------------------
    # CÁLCULO DO PPM REAL
    # ---------------------------------------------------------------
    total_refugado = df_def_filt['QTD PÇ'].sum()
    total_produzido = df_prod_filt['QTD_PROD'].sum()
    peso_refugado = df_def_filt['PESO TOTAL'].sum()

    # Fórmula do PPM
    if total_produzido > 0:
        ppm = (total_refugado / total_produzido) * 1_000_000
    else:
        ppm = 0.0

    # ---------------------------------------------------------------
    # KPIS PRINCIPAIS
    # ---------------------------------------------------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PPM Real Calculado", f"{ppm:,.0f}")
    c2.metric("Total Refugado (Pçs)", f"{int(total_refugado)} pçs")
    c3.metric("Total Produzido (Pçs)", f"{int(total_produzido)} pçs")
    c4.metric("Peso Refugado Total", f"{peso_refugado:,.1f} kg")

    st.divider()

    # ---------------------------------------------------------------
    # GRÁFICOS INTERATIVOS
    # ---------------------------------------------------------------
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📌 Diagrama de Pareto - Principais Defeitos")
        if not df_def_filt.empty:
            df_pareto = (
                df_def_filt.groupby('DEFEITO')['QTD PÇ']
                .sum()
                .reset_index()
                .sort_values(by='QTD PÇ', ascending=False)
            )
            fig_pareto = px.bar(
                df_pareto, 
                x='DEFEITO', 
                y='QTD PÇ', 
                text='QTD PÇ',
                color='QTD PÇ', 
                color_continuous_scale='Reds',
                labels={'DEFEITO': 'Defeito', 'QTD PÇ': 'Qtd Refugada'}
            )
            st.plotly_chart(fig_pareto, use_container_width=True)
        else:
            st.info("Nenhum defeito registrado para os filtros selecionados.")

    with col_g2:
        st.subheader("📈 PPM por Mês")
        # Agrupamento Mensal para calcular o PPM do Mês
        prod_mes = df_prod_filt.groupby('MÊS')['QTD_PROD'].sum().reset_index()
        def_mes = df_def_filt.groupby('MÊS')['QTD PÇ'].sum().reset_index()

        df_mes = pd.merge(prod_mes, def_mes, on='MÊS', how='outer').fillna(0)
        df_mes['PPM_MES'] = df_mes.apply(
            lambda r: (r['QTD PÇ'] / r['QTD_PROD'] * 1_000_000) if r['QTD_PROD'] > 0 else 0, axis=1
        )
        df_mes = df_mes.sort_values(by='MÊS')

        if not df_mes.empty:
            fig_ppm_mes = px.line(
                df_mes, 
                x='MÊS', 
                y='PPM_MES', 
                markers=True, 
                labels={'MÊS': 'Mês', 'PPM_MES': 'PPM'},
                title="Evolução Mensal do PPM"
            )
            st.plotly_chart(fig_ppm_mes, use_container_width=True)
        else:
            st.info("Sem dados suficientes para gerar o gráfico mensal.")

    # ---------------------------------------------------------------
    # VISUALIZAÇÃO DAS TABELAS
    # ---------------------------------------------------------------
    st.divider()
    tab1, tab2 = st.tabs(["📋 Detalhes dos Defeitos", "🏭 Detalhes da Produção"])

    with tab1:
        st.dataframe(
            df_def_filt[['DATA', 'DEFEITO', 'QTD PÇ', 'PESO TOTAL', 'CT_PROD_DESC', 'MAT BRUT DESC']], 
            use_container_width=True
        )

    with tab2:
        cols_prod = [c for c in ['Data2', 'Denominação', 'QTD_PROD', 'Peso Total', 'CT_PROD_DESC'] if c in df_prod_filt.columns]
        st.dataframe(df_prod_filt[cols_prod], use_container_width=True)

if __name__ == "__main__":
    main()