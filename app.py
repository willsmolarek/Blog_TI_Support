import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata

# ---------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Painel de Qualidade e PPM - WEG",
    layout="wide"
)

# ---------------------------------------------------------------
# FUNÇÕES DE TRATAMENTO ROBUSTO DE COLUNAS
# ---------------------------------------------------------------
def normalizar_texto(texto):
    """Remove acentos, espaços extras e coloca em minúsculas."""
    if not isinstance(texto, str):
        return ""
    str_norm = unicodedata.normalize('NFD', texto)
    str_sem_acento = "".join([c for c in str_norm if unicodedata.category(c) != 'Mn'])
    return str_sem_acento.lower().strip()

def encontrar_coluna(df, termos_chave):
    """Procura uma coluna no DataFrame baseada em termos chave flexíveis."""
    for col in df.columns:
        col_norm = normalizar_texto(col)
        if any(normalizar_texto(termo) in col_norm for termo in termos_chave):
            return col
    return None

def ler_csv_inteligente(caminho_arquivo):
    """Lê o CSV testando os separadores mais comuns (vírgula e ponto-e-vírgula)."""
    try:
        return pd.read_csv(caminho_arquivo, sep=None, engine='python', encoding='utf-8-sig')
    except Exception:
        try:
            return pd.read_csv(caminho_arquivo, sep=';', encoding='latin1')
        except Exception:
            return pd.read_csv(caminho_arquivo, sep=',', encoding='latin1')

# ---------------------------------------------------------------
# CARREGAMENTO E LEITURA DAS PLANILHAS
# ---------------------------------------------------------------
@st.cache_data
def carregar_dados():
    df_defeitos = ler_csv_inteligente("EXEMPLO DESIGN DEFEITO.xlsx - Planilha1.csv")
    df_producao = ler_csv_inteligente("EXEMPLO DESIGN PRODUÇÃO.xlsx - Planilha1.csv")

    # --- TRATAMENTO TABELA DEFEITOS ---
    col_qtd_def = encontrar_coluna(df_defeitos, ['qtd pc', 'qtd pç', 'quantidade'])
    col_peso_def = encontrar_coluna(df_defeitos, ['peso total', 'peso'])
    col_mes_def = encontrar_coluna(df_defeitos, ['mes', 'mês'])
    col_ct_def = encontrar_coluna(df_defeitos, ['ct prod desc', 'ct prod', 'centro'])
    col_defeito = encontrar_coluna(df_defeitos, ['defeito'])

    df_defeitos['QTD_REFUGO'] = pd.to_numeric(df_defeitos[col_qtd_def], errors='coerce').fillna(0) if col_qtd_def else 0
    df_defeitos['PESO_REFUGO'] = pd.to_numeric(df_defeitos[col_peso_def], errors='coerce').fillna(0) if col_peso_def else 0
    df_defeitos['MES'] = pd.to_numeric(df_defeitos[col_mes_def], errors='coerce') if col_mes_def else 1
    df_defeitos['CT_PROD'] = df_defeitos[col_ct_def].astype(str).str.strip() if col_ct_def else "Sem CT"
    df_defeitos['DEFEITO_NOME'] = df_defeitos[col_defeito].astype(str).str.strip() if col_defeito else "Indefinido"

    # --- TRATAMENTO TABELA PRODUÇÃO ---
    col_qtd_prod = encontrar_coluna(df_producao, ['pc', 'pç', 'qtd sap', 'qtd corr', 'quantidade'])
    col_mes_prod = encontrar_coluna(df_producao, ['mes', 'mês'])
    col_ct_prod = encontrar_coluna(df_producao, ['ct prod descricao', 'ct prod desc', 'ct prod', 'descricao'])

    df_producao['QTD_PROD'] = pd.to_numeric(df_producao[col_qtd_prod], errors='coerce').fillna(0) if col_qtd_prod else 0
    df_producao['MES'] = pd.to_numeric(df_producao[col_mes_prod], errors='coerce') if col_mes_prod else 1
    df_producao['CT_PROD'] = df_producao[col_ct_prod].astype(str).str.strip() if col_ct_prod else "Sem CT"

    return df_defeitos, df_producao


# ---------------------------------------------------------------
# INTERFACE PRINCIPAL
# ---------------------------------------------------------------
def main():
    st.title("📊 Painel de Qualidade e Cálculo de PPM")
    st.caption("Conexão e Cruzamento: Produção vs. Defeitos")

    try:
        df_defeitos, df_producao = carregar_dados()
    except Exception as e:
        st.error(f"Erro ao carregar os arquivos CSV: {e}")
        st.info("Verifique se os arquivos 'EXEMPLO DESIGN DEFEITO.xlsx - Planilha1.csv' e 'EXEMPLO DESIGN PRODUÇÃO.xlsx - Planilha1.csv' estão na mesma pasta do código.")
        return

    # ---------------------------------------------------------------
    # FILTROS
    # ---------------------------------------------------------------
    st.sidebar.header("🔍 Filtros")

    # Lista unificada de Centros de Trabalho
    cts = sorted(list(set(df_defeitos['CT_PROD'].dropna().unique()).union(set(df_producao['CT_PROD'].dropna().unique()))))
    ct_selecionado = st.sidebar.selectbox("Centro de Trabalho / Molde", ["Todos"] + cts)

    # Lista de Tipos de Defeito
    defeitos = sorted(list(df_defeitos['DEFEITO_NOME'].dropna().unique()))
    defeito_selecionado = st.sidebar.selectbox("Tipo de Defeito", ["Todos"] + defeitos)

    # Filtragem das tabelas
    df_def_filt = df_defeitos.copy()
    df_prod_filt = df_producao.copy()

    if ct_selecionado != "Todos":
        df_def_filt = df_def_filt[df_def_filt['CT_PROD'] == ct_selecionado]
        df_prod_filt = df_prod_filt[df_prod_filt['CT_PROD'] == ct_selecionado]

    if defeito_selecionado != "Todos":
        df_def_filt = df_def_filt[df_def_filt['DEFEITO_NOME'] == defeito_selecionado]

    # ---------------------------------------------------------------
    # CÁLCULOS E MÉTRICAS DE PPM
    # ---------------------------------------------------------------
    total_refugo = df_def_filt['QTD_REFUGO'].sum()
    total_producao = df_prod_filt['QTD_PROD'].sum()
    peso_refugo = df_def_filt['PESO_REFUGO'].sum()

    ppm_geral = (total_refugo / total_producao * 1_000_000) if total_producao > 0 else 0.0

    # Exibição dos Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PPM Real", f"{ppm_geral:,.0f}")
    c2.metric("Total Refugado", f"{int(total_refugo)} pçs")
    c3.metric("Total Produzido", f"{int(total_producao)} pçs")
    c4.metric("Peso Refugado", f"{peso_refugo:,.1f} kg")

    st.divider()

    # ---------------------------------------------------------------
    # VISUALIZAÇÃO GRÁFICA
    # ---------------------------------------------------------------
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("📌 Diagrama de Pareto (Defeitos)")
        if not df_def_filt.empty and total_refugo > 0:
            pareto = df_def_filt.groupby('DEFEITO_NOME')['QTD_REFUGO'].sum().reset_index().sort_values(by='QTD_REFUGO', ascending=False)
            fig_pareto = px.bar(pareto, x='DEFEITO_NOME', y='QTD_REFUGO', text='QTD_REFUGO', color='QTD_REFUGO', color_continuous_scale='Reds', labels={'DEFEITO_NOME': 'Defeito', 'QTD_REFUGO': 'Peças Refugadas'})
            st.plotly_chart(fig_pareto, use_container_width=True)
        else:
            st.info("Nenhum registro de defeito encontrado para este filtro.")

    with g2:
        st.subheader("📈 Evolução do PPM por Mês")
        prod_mes = df_prod_filt.groupby('MES')['QTD_PROD'].sum().reset_index()
        def_mes = df_def_filt.groupby('MES')['QTD_REFUGO'].sum().reset_index()

        df_mes = pd.merge(prod_mes, def_mes, on='MES', how='outer').fillna(0)
        df_mes['PPM'] = df_mes.apply(lambda r: (r['QTD_REFUGO'] / r['QTD_PROD'] * 1_000_000) if r['QTD_PROD'] > 0 else 0, axis=1)
        df_mes = df_mes.sort_values(by='MES')

        if not df_mes.empty and (df_mes['QTD_PROD'].sum() > 0):
            fig_ppm = px.line(df_mes, x='MES', y='PPM', markers=True, labels={'MES': 'Mês', 'PPM': 'PPM Mensal'})
            st.plotly_chart(fig_ppm, use_container_width=True)
        else:
            st.info("Dados de produção/refugo insuficientes para gerar a evolução do PPM.")

    # ---------------------------------------------------------------
    # TABELA DE DADOS
    # ---------------------------------------------------------------
    st.divider()
    st.subheader("📋 Registros de Defeito (Base Filtrada)")
    cols_exibir = [c for c in df_def_filt.columns if c not in ['QTD_REFUGO', 'PESO_REFUGO', 'MES', 'CT_PROD', 'DEFEITO_NOME']]
    st.dataframe(df_def_filt, use_container_width=True)


if __name__ == "__main__":
    main()