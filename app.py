# -*- coding: utf-8 -*-
"""
Sistema de Registro e Consulta de Chamados de TI - Regiao 1 (WEG)
Predios: 58, 59, 60 e 62

Como rodar:
    1) pip install streamlit
    2) streamlit run app.py

O banco de dados (chamados.db) e criado automaticamente na primeira
execucao, ja com 2 chamados de exemplo pre-carregados.
"""

import sqlite3
import streamlit as st
from datetime import datetime

# ---------------------------------------------------------------
# CONFIGURACOES FIXAS DO PROJETO
# ---------------------------------------------------------------
PREDIOS_VALIDOS = ["58", "59", "60", "62"]
CATEGORIAS = ["Rede", "SAP", "Hardware", "Permissoes", "Software", "Impressora", "E-mail/Outlook", "Outro"]
URGENCIAS = ["Alta", "Media", "Baixa"]
DB_PATH = "chamados.db"

st.set_page_config(
    page_title="Base de Chamados - Regiao 1 WEG",
    layout="wide",
)

# ---------------------------------------------------------------
# ESTILO (deixa a listagem com cara de blog)
# ---------------------------------------------------------------
st.markdown(
    """
    <style>
    .post-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        background-color: #fafafa;
    }
    .post-meta {
        color: #666;
        font-size: 0.85rem;
        margin-bottom: 0.4rem;
    }
    .post-title {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# BANCO DE DADOS
# ---------------------------------------------------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chamados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            usuario TEXT NOT NULL,
            predio TEXT NOT NULL,
            equipamento TEXT NOT NULL,
            categoria TEXT NOT NULL,
            urgencia TEXT NOT NULL,
            sintoma TEXT NOT NULL,
            causa_raiz TEXT NOT NULL,
            passo_a_passo TEXT NOT NULL,
            dica_prevencao TEXT NOT NULL,
            data_criacao TEXT NOT NULL
        )
        """
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM chamados")
    total = cur.fetchone()[0]
    if total == 0:
        exemplos = [
            (
                "Exemplo de erro (SAP)'",
                "Carlos Menezes",
                "59",
                "Dell Latitude 3420",
                "SAP",
                "Alta",
                "Usuario relatou que ao tentar abrir o SAP GUI, recebe a mensagem "
                "'Nao foi possivel efetuar logon (RFC)' e o sistema nao conecta ao servidor.",
                "Servidor SAPLogon estava com o roteamento de rede apontando para um "
                "Application Server antigo, desativado apos a ultima atualizacao do SAP GUI.",
                "1. Fechar completamente o SAP Logon (verificar na bandeja do sistema).\n"
                "2. Abrir o SAP Logon Pad e ir em 'Editar' > 'Novo item' (ou editar o item existente).\n"
                "3. Atualizar o Application Server para o novo endereco fornecido pela equipe SAP Basis.\n"
                "4. Testar a conexao com 'Conexao de teste'.\n"
                "5. Reabrir o SAP GUI e realizar o logon normalmente.",
                "Sempre validar com a equipe de SAP Basis se houve alteracao de servidor "
                "antes de trocar maquinas de usuarios que usam SAP com frequencia.",
                datetime.now().strftime("%Y-%m-%d %H:%M"),
            ),
        ]
        cur.executemany(
            """
            INSERT INTO chamados
            (titulo, usuario, predio, equipamento, categoria, urgencia,
             sintoma, causa_raiz, passo_a_passo, dica_prevencao, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            exemplos,
        )
        conn.commit()
    conn.close()


def inserir_chamado(dados):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO chamados
        (titulo, usuario, predio, equipamento, categoria, urgencia,
         sintoma, causa_raiz, passo_a_passo, dica_prevencao, data_criacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        dados,
    )
    conn.commit()
    conn.close()


def atualizar_chamado(id_chamado, dados):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE chamados
        SET titulo=?, usuario=?, predio=?, equipamento=?, categoria=?, urgencia=?,
            sintoma=?, causa_raiz=?, passo_a_passo=?, dica_prevencao=?
        WHERE id=?
        """,
        dados + (id_chamado,),
    )
    conn.commit()
    conn.close()


def excluir_chamado(id_chamado):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM chamados WHERE id=?", (id_chamado,))
    conn.commit()
    conn.close()


def buscar_chamados(texto="", predio="Todos", categoria="Todas", urgencia="Todas"):
    conn = get_conn()
    cur = conn.cursor()
    query = "SELECT * FROM chamados WHERE 1=1"
    params = []

    if texto:
        query += " AND (titulo LIKE ? OR sintoma LIKE ? OR causa_raiz LIKE ?)"
        like = f"%{texto}%"
        params += [like, like, like]
    if predio != "Todos":
        query += " AND predio = ?"
        params.append(predio)
    if categoria != "Todas":
        query += " AND categoria = ?"
        params.append(categoria)
    if urgencia != "Todas":
        query += " AND urgencia = ?"
        params.append(urgencia)

    query += " ORDER BY id DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------
# INTERFACE - EDICAO INLINE
# ---------------------------------------------------------------
def form_edicao(row):
    (
        _id, titulo, usuario, predio, equipamento, categoria, urgencia,
        sintoma, causa_raiz, passo_a_passo, dica_prevencao, data_criacao,
    ) = row

    with st.form(f"form_editar_{_id}"):
        novo_titulo = st.text_input("Titulo / Nome do Erro", value=titulo)

        c1, c2, c3 = st.columns(3)
        novo_usuario = c1.text_input("Nome do Usuario", value=usuario)
        novo_predio = c2.selectbox(
            "Predio", PREDIOS_VALIDOS, index=PREDIOS_VALIDOS.index(predio)
        )
        novo_equipamento = c3.text_input("Modelo do PC/Notebook", value=equipamento)

        c4, c5 = st.columns(2)
        nova_categoria = c4.selectbox(
            "Categoria", CATEGORIAS, index=CATEGORIAS.index(categoria) if categoria in CATEGORIAS else 0
        )
        nova_urgencia = c5.selectbox(
            "Urgencia", URGENCIAS, index=URGENCIAS.index(urgencia) if urgencia in URGENCIAS else 0
        )

        novo_sintoma = st.text_area("Sintoma / Relato do Usuario", value=sintoma)
        nova_causa = st.text_area("Causa Raiz", value=causa_raiz)
        novo_passo = st.text_area("Passo a Passo da Resolucao", value=passo_a_passo, height=150)
        nova_dica = st.text_area("Dica de Prevencao", value=dica_prevencao)

        col_salvar, col_cancelar = st.columns(2)
        salvar = col_salvar.form_submit_button("Salvar alteracoes", use_container_width=True)
        cancelar = col_cancelar.form_submit_button("Cancelar", use_container_width=True)

        if salvar:
            campos = [
                novo_titulo, novo_usuario, novo_predio, novo_equipamento,
                nova_categoria, nova_urgencia, novo_sintoma, nova_causa,
                novo_passo, nova_dica,
            ]
            if not all(str(c).strip() for c in campos):
                st.error("Preencha todos os campos antes de salvar.")
            else:
                atualizar_chamado(_id, tuple(campos))
                st.session_state["editando_id"] = None
                st.success("Chamado atualizado com sucesso.")
                st.rerun()

        if cancelar:
            st.session_state["editando_id"] = None
            st.rerun()


def confirmar_exclusao(id_chamado, titulo):
    st.warning(f"Tem certeza que deseja excluir o chamado \"{titulo}\"? Essa acao nao pode ser desfeita.")
    c1, c2 = st.columns(2)
    if c1.button("Sim, excluir", key=f"confirma_excluir_{id_chamado}", use_container_width=True):
        excluir_chamado(id_chamado)
        st.session_state["excluindo_id"] = None
        st.success("Chamado excluido.")
        st.rerun()
    if c2.button("Cancelar", key=f"cancela_excluir_{id_chamado}", use_container_width=True):
        st.session_state["excluindo_id"] = None
        st.rerun()


def exibir_post(row):
    (
        _id, titulo, usuario, predio, equipamento, categoria, urgencia,
        sintoma, causa_raiz, passo_a_passo, dica_prevencao, data_criacao,
    ) = row

    editando = st.session_state.get("editando_id") == _id
    excluindo = st.session_state.get("excluindo_id") == _id

    st.markdown('<div class="post-card">', unsafe_allow_html=True)

    if editando:
        st.markdown(f"**Editando: {titulo}**")
        form_edicao(row)
    else:
        st.markdown(
            f'<div class="post-meta">Predio {predio} &nbsp;|&nbsp; {categoria} &nbsp;|&nbsp; '
            f'Urgencia: {urgencia} &nbsp;|&nbsp; {data_criacao}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="post-title">{titulo}</div>', unsafe_allow_html=True)
        st.markdown(
            f"Usuario: {usuario} &nbsp;&middot;&nbsp; Equipamento: {equipamento}",
            unsafe_allow_html=True,
        )

        with st.expander("Ver detalhes da solucao"):
            st.markdown("**Sintoma / Relato do Usuario**")
            st.write(sintoma)

            st.markdown("**Causa Raiz**")
            st.write(causa_raiz)

            st.markdown("**Passo a Passo da Resolucao**")
            st.write(passo_a_passo)

            st.markdown("**Dica de Prevencao**")
            st.write(dica_prevencao)

        col_a, col_b, col_c = st.columns([1, 1, 6])
        if col_a.button("Editar", key=f"editar_{_id}"):
            st.session_state["editando_id"] = _id
            st.session_state["excluindo_id"] = None
            st.rerun()
        if col_b.button("Excluir", key=f"excluir_{_id}"):
            st.session_state["excluindo_id"] = _id
            st.session_state["editando_id"] = None
            st.rerun()

        if excluindo:
            confirmar_exclusao(_id, titulo)

    st.markdown("</div>", unsafe_allow_html=True)


def pagina_blog():
    st.title("Base de Chamados - Regiao 1")
    st.caption("Predios 58, 59, 60 e 62")

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    texto = col1.text_input("Buscar por palavra-chave (titulo, sintoma, causa)")
    predio = col2.selectbox("Predio", ["Todos"] + PREDIOS_VALIDOS)
    categoria = col3.selectbox("Categoria", ["Todas"] + CATEGORIAS)
    urgencia = col4.selectbox("Urgencia", ["Todas"] + URGENCIAS)

    resultados = buscar_chamados(texto, predio, categoria, urgencia)

    st.markdown(f"**{len(resultados)} chamado(s) encontrado(s)**")
    st.divider()

    if not resultados:
        st.info("Nenhum chamado encontrado com esses filtros.")
        return

    for row in resultados:
        exibir_post(row)


def pagina_novo_registro():
    st.title("Novo Registro de Chamado")
    st.caption("Preencha todos os campos obrigatorios da Regiao 1")

    with st.form("form_novo_chamado", clear_on_submit=True):
        titulo = st.text_input(
            "Titulo / Nome do Erro (ex: mensagem de erro exata) *",
            placeholder="Ex: Erro 'Impressora offline' ao imprimir do SAP",
        )

        col1, col2, col3 = st.columns(3)
        usuario = col1.text_input("Nome do Usuario *")
        predio = col2.selectbox("Predio de Origem * (somente Regiao 1)", PREDIOS_VALIDOS)
        equipamento = col3.text_input("Modelo do PC/Notebook *", placeholder="Ex: Dell Latitude 3420")

        col4, col5 = st.columns(2)
        categoria = col4.selectbox("Categoria *", CATEGORIAS)
        urgencia = col5.selectbox("Urgencia *", URGENCIAS)

        sintoma = st.text_area("Sintoma / Relato do Usuario *")
        causa_raiz = st.text_area("Causa Raiz *")
        passo_a_passo = st.text_area("Passo a Passo da Resolucao *", height=150)
        dica_prevencao = st.text_area("Dica de Prevencao *")

        enviado = st.form_submit_button("Salvar Chamado")

        if enviado:
            campos_obrigatorios = [
                titulo, usuario, predio, equipamento, categoria, urgencia,
                sintoma, causa_raiz, passo_a_passo, dica_prevencao,
            ]
            if not all(str(c).strip() for c in campos_obrigatorios):
                st.error("Preencha todos os campos obrigatorios antes de salvar.")
            elif predio not in PREDIOS_VALIDOS:
                st.error(f"Predio invalido. Voce so pode registrar para: {', '.join(PREDIOS_VALIDOS)}")
            else:
                inserir_chamado((
                    titulo, usuario, predio, equipamento, categoria, urgencia,
                    sintoma, causa_raiz, passo_a_passo, dica_prevencao,
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                ))
                st.success("Chamado registrado com sucesso.")


# ---------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------
def main():
    init_db()

    if "editando_id" not in st.session_state:
        st.session_state["editando_id"] = None
    if "excluindo_id" not in st.session_state:
        st.session_state["excluindo_id"] = None

    st.sidebar.title("Base de Chamados TI")
    st.sidebar.caption("Regiao 1 - Predios 58, 59, 60, 62")
    pagina = st.sidebar.radio(
        "Navegacao",
        ["Blog de Chamados", "Novo Registro"],
    )
    st.sidebar.divider()
    st.sidebar.markdown("**Predios sob sua responsabilidade:**")
    st.sidebar.markdown("58, 59, 60, 62")

    if pagina == "Blog de Chamados":
        pagina_blog()
    else:
        pagina_novo_registro()


if __name__ == "__main__":
    main()