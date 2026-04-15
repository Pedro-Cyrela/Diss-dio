from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Dict, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from dissidio_engine import (
    DissidioParams,
    ESSENTIAL_FIELDS,
    FLOOR_FIELDS,
    build_floor_lookup,
    compute_dissidio,
    detect_columns,
    validate_mapping,
)
from storage import load_config, save_config


st.set_page_config(
    page_title="Calculadora de Dissidio",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(16, 185, 129, 0.10), transparent 28%),
                    radial-gradient(circle at top right, rgba(14, 165, 233, 0.10), transparent 26%),
                    linear-gradient(180deg, #f5f7f2 0%, #eef4ef 100%);
                font-family: "Segoe UI Variable", "IBM Plex Sans", "Trebuchet MS", sans-serif;
            }
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0f172a 0%, #16324f 100%);
            }
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] .stMarkdown,
            [data-testid="stSidebar"] .stCaption,
            [data-testid="stSidebar"] .stSubheader,
            [data-testid="stSidebar"] .stRadio label,
            [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] {
                color: #f8fafc;
            }
            [data-testid="stSidebar"] input,
            [data-testid="stSidebar"] textarea,
            [data-testid="stSidebar"] [data-baseweb="input"] input,
            [data-testid="stSidebar"] [data-baseweb="input"] textarea,
            [data-testid="stSidebar"] [data-baseweb="select"] input,
            [data-testid="stSidebar"] [data-baseweb="select"] div,
            [data-testid="stSidebar"] [data-baseweb="select"] span {
                color: #0f172a !important;
                -webkit-text-fill-color: #0f172a !important;
            }
            [data-testid="stSidebar"] [data-baseweb="input"],
            [data-testid="stSidebar"] [data-baseweb="select"] > div,
            [data-testid="stSidebar"] .stDateInput > div > div,
            [data-testid="stSidebar"] .stNumberInput > div > div {
                background: #ffffff;
            }
            [data-testid="stSidebar"] input::placeholder,
            [data-testid="stSidebar"] textarea::placeholder {
                color: #64748b !important;
                -webkit-text-fill-color: #64748b !important;
            }
            [data-testid="stSidebar"] .stRadio label,
            [data-testid="stSidebar"] .stRadio label p,
            [data-testid="stSidebar"] [role="radiogroup"] label,
            [data-testid="stSidebar"] [role="radiogroup"] label p,
            [data-testid="stSidebar"] [role="radiogroup"] span {
                color: #f8fafc !important;
                -webkit-text-fill-color: #f8fafc !important;
            }
            .hero-card {
                padding: 1.25rem 1.4rem;
                border: 1px solid rgba(15, 23, 42, 0.08);
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.88);
                box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
                margin-bottom: 1rem;
            }
            .hero-kicker {
                letter-spacing: 0.08em;
                text-transform: uppercase;
                font-size: 0.74rem;
                color: #0f766e;
                font-weight: 700;
            }
            .hero-title {
                font-size: 2.2rem;
                line-height: 1.1;
                font-weight: 800;
                color: #0f172a;
                margin: 0.25rem 0 0.6rem 0;
            }
            .hero-copy {
                color: #334155;
                font-size: 1rem;
                margin: 0;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_table(uploaded_file, key_prefix: str) -> Optional[pd.DataFrame]:
    if uploaded_file is None:
        return None

    file_bytes = uploaded_file.getvalue()
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        return pd.read_csv(BytesIO(file_bytes), sep=None, engine="python")

    if file_name.endswith((".xlsx", ".xlsm", ".xls")):
        workbook = pd.ExcelFile(BytesIO(file_bytes))
        sheet_name = workbook.sheet_names[0]
        if len(workbook.sheet_names) > 1:
            sheet_name = st.selectbox(
                f"Aba da planilha {key_prefix}",
                workbook.sheet_names,
                key=f"{key_prefix}_sheet",
            )
        return pd.read_excel(BytesIO(file_bytes), sheet_name=sheet_name)

    st.error("Formato nao suportado. Use CSV, XLSX, XLSM ou XLS.")
    return None


def init_state() -> None:
    if "page" not in st.session_state:
        st.session_state["page"] = "Calculo"
    if "resultado_df" not in st.session_state:
        st.session_state["resultado_df"] = None
    if "parametros_salvos" not in st.session_state:
        st.session_state["parametros_salvos"] = load_config()


def format_currency(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(value: Optional[float]) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value:.2f}%"


def dataframe_config() -> Dict[str, object]:
    return {
        "Salario atual": st.column_config.NumberColumn("Salario atual", format="R$ %.2f"),
        "Salario acordo": st.column_config.NumberColumn("Salario acordo", format="R$ %.2f"),
        "Piso categoria": st.column_config.NumberColumn("Piso categoria", format="R$ %.2f"),
        "Novo salario via percentual": st.column_config.NumberColumn("Novo salario via percentual", format="R$ %.2f"),
        "Novo salario via teto": st.column_config.NumberColumn("Novo salario via teto", format="R$ %.2f"),
        "Novo salario via piso": st.column_config.NumberColumn("Novo salario via piso", format="R$ %.2f"),
        "Novo salario pos dissidio": st.column_config.NumberColumn("Novo salario pos dissidio", format="R$ %.2f"),
        "Aumento bruto": st.column_config.NumberColumn("Aumento bruto", format="R$ %.2f"),
        "Aumento via percentual": st.column_config.NumberColumn("Aumento via percentual", format="R$ %.2f"),
        "Aumento via teto": st.column_config.NumberColumn("Aumento via teto", format="R$ %.2f"),
        "Aumento via piso": st.column_config.NumberColumn("Aumento via piso", format="R$ %.2f"),
        "Percentual aplicado": st.column_config.NumberColumn("Percentual aplicado", format="%.2f%%"),
        "Proporcao": st.column_config.NumberColumn("Proporcao", format="%.4f"),
    }


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dissidio")
    return output.getvalue()


def render_mapping_section(df: pd.DataFrame, title: str, field_map: Dict[str, list[str]], key_prefix: str) -> Dict[str, Optional[str]]:
    auto_mapping = detect_columns(df.columns, field_map)
    options = [""] + list(df.columns)

    st.markdown(title)
    columns = st.columns(2)
    mapping: Dict[str, Optional[str]] = {}
    for index, field_name in enumerate(field_map):
        label = field_name.replace("_", " ").title()
        detected = auto_mapping.get(field_name) or ""
        default_index = options.index(detected) if detected in options else 0
        mapping[field_name] = columns[index % 2].selectbox(
            label,
            options,
            index=default_index,
            key=f"{key_prefix}_{field_name}",
        ) or None
    return mapping


def render_filters(df: pd.DataFrame, key_prefix: str) -> pd.DataFrame:
    filtered_df = df.copy()
    with st.expander("Filtros da tabela", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        empresas = col1.multiselect(
            "Empresa",
            sorted(filtered_df["Empresa"].dropna().astype(str).unique().tolist()),
            key=f"{key_prefix}_empresas",
        )
        cargos = col2.multiselect(
            "Cargo",
            sorted(filtered_df["Cargo"].dropna().astype(str).unique().tolist()),
            key=f"{key_prefix}_cargos",
        )
        regras = col3.multiselect(
            "Regra aplicada",
            sorted(filtered_df["Regra aplicada"].dropna().astype(str).unique().tolist()),
            key=f"{key_prefix}_regras",
        )
        nome = col4.text_input("Pesquisar colaborador", key=f"{key_prefix}_nome")

    if empresas:
        filtered_df = filtered_df[filtered_df["Empresa"].astype(str).isin(empresas)]
    if cargos:
        filtered_df = filtered_df[filtered_df["Cargo"].astype(str).isin(cargos)]
    if regras:
        filtered_df = filtered_df[filtered_df["Regra aplicada"].astype(str).isin(regras)]
    if nome:
        filtered_df = filtered_df[
            filtered_df["Colaborador"].astype(str).str.contains(nome, case=False, na=False)
        ]
    return filtered_df


def render_summary_cards(df: pd.DataFrame) -> None:
    total_aumento = df["Aumento bruto"].sum()
    total_folha_atual = df["Salario atual"].sum()
    total_folha_nova = df["Novo salario pos dissidio"].sum()
    media_percentual = df["Percentual aplicado"].mean() if not df.empty else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Colaboradores", f"{len(df)}")
    col2.metric("Aumento total", format_currency(total_aumento))
    col3.metric("Folha atual x nova", f"{format_currency(total_folha_atual)} -> {format_currency(total_folha_nova)}")
    col4.metric("Percentual medio aplicado", format_percent(media_percentual))


def go_to(page_name: str) -> None:
    st.session_state["page"] = page_name
    st.rerun()


def render_calculo_page() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-kicker">Departamento Pessoal</div>
            <div class="hero-title">Calculadora de Dissidio</div>
            <p class="hero-copy">
                Upload da base, mapeamento de colunas, calculo automatico e auditoria da regra aplicada.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "Premissa adotada: para admitidos apos o acordo anterior, a proporcionalidade tambem e aplicada ao valor fixo acima do teto."
    )

    config = st.session_state["parametros_salvos"]

    with st.sidebar:
        st.subheader("Parametros do acordo")
        data_acordo_anterior = st.date_input(
            "Data do acordo anterior",
            value=pd.to_datetime(config.get("data_acordo_anterior")).date()
            if config.get("data_acordo_anterior")
            else date.today().replace(month=3, day=1),
            format="DD/MM/YYYY",
            key="data_acordo_anterior",
        )
        data_acordo_atual = st.date_input(
            "Data do acordo atual",
            value=pd.to_datetime(config.get("data_acordo_atual")).date()
            if config.get("data_acordo_atual")
            else date.today(),
            format="DD/MM/YYYY",
            key="data_acordo_atual",
        )
        percentual_reajuste = st.number_input(
            "Percentual de reajuste",
            min_value=0.0,
            step=0.1,
            value=float(config.get("percentual_reajuste", 0.0)),
            format="%.4f",
            key="percentual_reajuste",
        )
        teto_reajuste = st.number_input(
            "Teto salarial de reajuste",
            min_value=0.0,
            step=100.0,
            value=float(config.get("teto_reajuste", 0.0)),
            format="%.2f",
            key="teto_reajuste",
        )
        valor_fixo_teto = st.number_input(
            "Valor fixo para salarios no teto ou acima",
            min_value=0.0,
            step=10.0,
            value=float(config.get("valor_fixo_teto", 0.0)),
            format="%.2f",
            key="valor_fixo_teto",
        )

    col_upload_1, col_upload_2 = st.columns(2)
    uploaded_main = col_upload_1.file_uploader(
        "Planilha principal de colaboradores",
        type=["csv", "xlsx", "xlsm", "xls"],
        key="uploaded_main",
    )
    uploaded_floor = col_upload_2.file_uploader(
        "Planilha opcional de cargos com piso",
        type=["csv", "xlsx", "xlsm", "xls"],
        key="uploaded_floor",
    )

    df_main = load_table(uploaded_main, "principal")
    df_floor = load_table(uploaded_floor, "piso") if uploaded_floor else None

    if df_main is None:
        st.warning("Anexe a planilha principal para iniciar o calculo.")
        return

    st.subheader("Pre-visualizacao da base")
    st.dataframe(df_main.head(10), use_container_width=True)

    with st.expander("Mapeamento de colunas da base principal", expanded=True):
        mapping = render_mapping_section(
            df_main,
            "Selecione os campos essenciais do calculo.",
            ESSENTIAL_FIELDS,
            "main_map",
        )
        auto_detected = detect_columns(df_main.columns)
        for field_name, detected_column in auto_detected.items():
            if mapping.get(field_name) is None and detected_column:
                mapping[field_name] = detected_column

    floor_lookup = {}
    if df_floor is not None:
        with st.expander("Mapeamento da planilha de piso", expanded=False):
            floor_mapping = render_mapping_section(
                df_floor,
                "Selecione as colunas que representam cargo e piso salarial.",
                FLOOR_FIELDS,
                "floor_map",
            )
        floor_lookup = build_floor_lookup(df_floor, floor_mapping)
        st.caption(f"{len(floor_lookup)} cargos com piso identificados.")

    missing_fields = validate_mapping(mapping)
    if missing_fields:
        st.error(
            "Complete o mapeamento dos campos obrigatorios: "
            + ", ".join(field.replace("_", " ") for field in missing_fields)
        )
        return

    if data_acordo_atual <= data_acordo_anterior:
        st.error("A data do acordo atual precisa ser posterior a data do acordo anterior.")
        return

    if st.button("Calcular dissidio", type="primary", use_container_width=True):
        params = DissidioParams(
            data_acordo_anterior=pd.Timestamp(data_acordo_anterior),
            data_acordo_atual=pd.Timestamp(data_acordo_atual),
            percentual_reajuste=float(percentual_reajuste),
            teto_reajuste=float(teto_reajuste),
            valor_fixo_teto=float(valor_fixo_teto),
        )

        save_config(
            {
                "data_acordo_anterior": params.data_acordo_anterior.date().isoformat(),
                "data_acordo_atual": params.data_acordo_atual.date().isoformat(),
                "percentual_reajuste": params.percentual_reajuste,
                "teto_reajuste": params.teto_reajuste,
                "valor_fixo_teto": params.valor_fixo_teto,
            }
        )
        st.session_state["parametros_salvos"] = load_config()
        st.session_state["resultado_df"] = compute_dissidio(
            df=df_main,
            mapping=mapping,
            params=params,
            floor_lookup=floor_lookup,
        )

    resultado_df = st.session_state.get("resultado_df")
    if resultado_df is None or resultado_df.empty:
        return

    st.divider()
    st.subheader("Resultado do calculo")
    render_summary_cards(resultado_df)
    filtered_df = render_filters(resultado_df, "resultado")
    st.dataframe(filtered_df, use_container_width=True, column_config=dataframe_config(), hide_index=True)

    download_col_1, download_col_2, download_col_3 = st.columns(3)
    download_col_1.download_button(
        "Baixar resultado em Excel",
        data=to_excel_bytes(filtered_df),
        file_name="resultado_dissidio.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    download_col_2.button(
        "Abrir tela de analise",
        on_click=go_to,
        args=("Analise",),
        use_container_width=True,
    )
    download_col_3.button(
        "Abrir auditoria individual",
        on_click=go_to,
        args=("Auditoria",),
        use_container_width=True,
    )


def render_analise_page() -> None:
    st.title("Analise de impacto do dissidio")
    resultado_df = st.session_state.get("resultado_df")
    if resultado_df is None or resultado_df.empty:
        st.warning("Nenhum calculo disponivel. Rode a tela de calculo primeiro.")
        if st.button("Ir para calculo", type="primary"):
            go_to("Calculo")
        return

    filtered_df = render_filters(resultado_df, "analise")
    eixo = st.selectbox(
        "Eixo de analise",
        ["Empresa", "Cargo", "Regra aplicada", "Acima do teto", "Segue piso"],
    )
    metrica = st.selectbox(
        "Metrica principal",
        ["Aumento bruto", "Novo salario pos dissidio", "Salario atual"],
    )

    resumo = (
        filtered_df.groupby(eixo, dropna=False)
        .agg(
            colaboradores=("Colaborador", "count"),
            aumento_total=("Aumento bruto", "sum"),
            folha_atual=("Salario atual", "sum"),
            folha_nova=("Novo salario pos dissidio", "sum"),
            media_percentual=("Percentual aplicado", "mean"),
        )
        .reset_index()
        .sort_values("aumento_total", ascending=False)
    )

    render_summary_cards(filtered_df)

    fig = px.bar(
        resumo,
        x=eixo,
        y="aumento_total" if metrica == "Aumento bruto" else "folha_nova" if metrica == "Novo salario pos dissidio" else "folha_atual",
        color=eixo,
        text_auto=".2s",
        title=f"Impacto por {eixo}",
    )
    fig.update_layout(showlegend=False, xaxis_title=eixo, yaxis_title=metrica)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        resumo,
        use_container_width=True,
        hide_index=True,
        column_config={
            "aumento_total": st.column_config.NumberColumn("Aumento total", format="R$ %.2f"),
            "folha_atual": st.column_config.NumberColumn("Folha atual", format="R$ %.2f"),
            "folha_nova": st.column_config.NumberColumn("Folha nova", format="R$ %.2f"),
            "media_percentual": st.column_config.NumberColumn("Percentual medio", format="%.2f%%"),
        },
    )

    if st.button("Voltar para calculo", use_container_width=True):
        go_to("Calculo")


def render_auditoria_page() -> None:
    st.title("Auditoria individual")
    resultado_df = st.session_state.get("resultado_df")
    if resultado_df is None or resultado_df.empty:
        st.warning("Nenhum calculo disponivel. Rode a tela de calculo primeiro.")
        if st.button("Ir para calculo", type="primary"):
            go_to("Calculo")
        return

    nomes = resultado_df["Colaborador"].fillna("").astype(str).tolist()
    selecionado = st.selectbox("Escolha um colaborador", nomes)
    pessoa = resultado_df[resultado_df["Colaborador"].astype(str) == str(selecionado)].iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Salario atual", format_currency(pessoa["Salario atual"]))
    col2.metric("Novo salario", format_currency(pessoa["Novo salario pos dissidio"]))
    col3.metric("Aumento bruto", format_currency(pessoa["Aumento bruto"]))

    st.subheader("Passo a passo da regra")
    st.write(f"Colaborador: **{pessoa['Colaborador']}**")
    st.write(f"Empresa: **{pessoa['Empresa']}**")
    st.write(f"Cargo: **{pessoa['Cargo']}**")
    st.write(f"Data de admissao: **{pessoa['Data admissao'].strftime('%d/%m/%Y') if pd.notna(pessoa['Data admissao']) else '-'}**")
    st.write(f"Segue piso: **{pessoa['Segue piso']}**")
    st.write(f"Piso da categoria identificado: **{format_currency(pessoa['Piso categoria'])}**")
    st.write(f"Proporcionalidade: **{pessoa['Proporcionalidade']}**")
    st.write(f"Acima do teto: **{pessoa['Acima do teto']}**")
    st.write(f"Novo salario via percentual: **{format_currency(pessoa['Novo salario via percentual'])}**")
    st.write(f"Novo salario via teto: **{format_currency(pessoa['Novo salario via teto'])}**")
    st.write(f"Novo salario via piso: **{format_currency(pessoa['Novo salario via piso'])}**")
    st.write(f"Percentual aplicado: **{format_percent(pessoa['Percentual aplicado'])}**")
    st.write(f"Regra final aplicada: **{pessoa['Regra aplicada']}**")

    if st.button("Voltar para calculo", use_container_width=True):
        go_to("Calculo")


def main() -> None:
    init_state()
    inject_styles()

    with st.sidebar:
        st.divider()
        page = st.radio(
            "Navegacao",
            ["Calculo", "Analise", "Auditoria"],
            index=["Calculo", "Analise", "Auditoria"].index(st.session_state["page"]),
        )
        st.session_state["page"] = page

    if page == "Calculo":
        render_calculo_page()
    elif page == "Analise":
        render_analise_page()
    else:
        render_auditoria_page()


if __name__ == "__main__":
    main()
