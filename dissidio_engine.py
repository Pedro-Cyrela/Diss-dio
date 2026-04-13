from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd


ESSENTIAL_FIELDS = {
    "colaborador": [
        "colaborador",
        "funcionario",
        "funcionario nome",
        "nome",
        "empregado",
        "colab",
    ],
    "cargo": [
        "cargo",
        "funcao",
        "funcao atual",
        "descricao cargo",
        "titulo cargo",
    ],
    "salario_atual": [
        "salario atual",
        "salario",
        "salario vigente",
        "salario base atual",
        "salario mensal",
    ],
    "salario_acordo": [
        "salario acordo",
        "salario anterior",
        "salario base acordo",
        "salario data base",
        "salario epoca",
        "salario base",
    ],
    "empresa": [
        "empresa",
        "razao social",
        "cnpj",
        "filial",
        "nome empresa",
    ],
    "data_admissao": [
        "data admissao",
        "admissao",
        "dt admissao",
        "data contratacao",
        "data de admissao",
    ],
}


FLOOR_FIELDS = {
    "cargo": [
        "cargo",
        "funcao",
        "descricao cargo",
        "categoria",
    ],
    "piso": [
        "piso",
        "salario",
        "salario piso",
        "piso salarial",
        "valor piso",
    ],
}


@dataclass
class DissidioParams:
    data_acordo_anterior: pd.Timestamp
    data_acordo_atual: pd.Timestamp
    percentual_reajuste: float
    teto_reajuste: float
    valor_fixo_teto: float


def normalize_label(value: object) -> str:
    text = str(value or "").strip().lower()
    replacements = str.maketrans(
        {
            "á": "a",
            "à": "a",
            "ã": "a",
            "â": "a",
            "é": "e",
            "ê": "e",
            "í": "i",
            "ó": "o",
            "ô": "o",
            "õ": "o",
            "ú": "u",
            "ç": "c",
            "_": " ",
            "-": " ",
            "/": " ",
        }
    )
    return " ".join(text.translate(replacements).split())


def detect_columns(columns: pd.Index, field_map: Optional[Dict[str, list[str]]] = None) -> Dict[str, Optional[str]]:
    field_map = field_map or ESSENTIAL_FIELDS
    normalized_columns = {column: normalize_label(column) for column in columns}
    matches: Dict[str, Optional[str]] = {}

    for field_name, aliases in field_map.items():
        detected = None
        alias_set = {normalize_label(alias) for alias in aliases}
        for column, normalized in normalized_columns.items():
            if normalized in alias_set:
                detected = column
                break
        if detected is None:
            for column, normalized in normalized_columns.items():
                if any(alias in normalized for alias in alias_set):
                    detected = column
                    break
        matches[field_name] = detected

    return matches


def month_start(value: pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(year=value.year, month=value.month, day=1)


def add_months(value: pd.Timestamp, months: int) -> pd.Timestamp:
    return value + pd.DateOffset(months=months)


def months_between(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return max(0, (end.year - start.year) * 12 + (end.month - start.month))


def compute_proportionality(
    data_admissao: pd.Timestamp,
    data_acordo_anterior: pd.Timestamp,
    data_acordo_atual: pd.Timestamp,
) -> tuple[float, int, int]:
    acordo_anterior_mes = month_start(data_acordo_anterior)
    acordo_atual_mes = month_start(data_acordo_atual)
    total_meses = months_between(acordo_anterior_mes, acordo_atual_mes)
    total_meses = max(total_meses, 1)

    if pd.isna(data_admissao) or data_admissao <= data_acordo_anterior:
        return 1.0, total_meses, total_meses

    mes_efetivo = month_start(data_admissao)
    if data_admissao.day > 15:
        mes_efetivo = add_months(mes_efetivo, 1)

    meses_elegiveis = months_between(mes_efetivo, acordo_atual_mes)
    meses_elegiveis = min(max(meses_elegiveis, 0), total_meses)
    return meses_elegiveis / total_meses, meses_elegiveis, total_meses


def build_floor_lookup(df_piso: Optional[pd.DataFrame], mapping: Optional[Dict[str, str]] = None) -> Dict[str, float]:
    if df_piso is None or df_piso.empty:
        return {}

    mapping = mapping or detect_columns(df_piso.columns, FLOOR_FIELDS)
    cargo_col = mapping.get("cargo")
    piso_col = mapping.get("piso")
    if not cargo_col or not piso_col:
        return {}

    piso_df = df_piso[[cargo_col, piso_col]].copy()
    piso_df.columns = ["cargo", "piso"]
    piso_df["cargo"] = piso_df["cargo"].map(normalize_label)
    piso_df["piso"] = pd.to_numeric(piso_df["piso"], errors="coerce")
    piso_df = piso_df.dropna(subset=["cargo", "piso"])

    return {
        str(row["cargo"]): float(row["piso"])
        for _, row in piso_df.drop_duplicates(subset=["cargo"], keep="last").iterrows()
    }


def validate_mapping(mapping: Dict[str, Optional[str]]) -> list[str]:
    missing = [field for field, column in mapping.items() if not column]
    return missing


def parse_date_series(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=True)
    if parsed.notna().any():
        return parsed
    return pd.to_datetime(series, errors="coerce")


def compute_dissidio(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    params: DissidioParams,
    floor_lookup: Optional[Dict[str, float]] = None,
) -> pd.DataFrame:
    floor_lookup = floor_lookup or {}
    working_df = df.copy()

    rename_map = {original: field for field, original in mapping.items()}
    working_df = working_df.rename(columns=rename_map)

    working_df["salario_atual"] = pd.to_numeric(working_df["salario_atual"], errors="coerce")
    working_df["salario_acordo"] = pd.to_numeric(working_df["salario_acordo"], errors="coerce")
    working_df["data_admissao"] = parse_date_series(working_df["data_admissao"])

    percentage_rate = params.percentual_reajuste / 100
    result_rows = []

    for _, row in working_df.iterrows():
        salario_atual = float(row.get("salario_atual") or 0)
        salario_acordo = float(row.get("salario_acordo") or 0)
        data_admissao = row.get("data_admissao")
        cargo = str(row.get("cargo") or "")
        cargo_normalizado = normalize_label(cargo)

        proporcao, meses_elegiveis, meses_totais = compute_proportionality(
            data_admissao=data_admissao,
            data_acordo_anterior=params.data_acordo_anterior,
            data_acordo_atual=params.data_acordo_atual,
        )

        acima_teto = salario_acordo >= params.teto_reajuste if params.teto_reajuste > 0 else False
        aumento_percentual = salario_acordo * percentage_rate * proporcao
        novo_salario_percentual = salario_atual + aumento_percentual

        aumento_teto = params.valor_fixo_teto * proporcao if acima_teto else 0.0
        novo_salario_teto = salario_atual + aumento_teto if acima_teto else novo_salario_percentual

        piso_categoria = floor_lookup.get(cargo_normalizado)
        segue_piso = piso_categoria is not None
        novo_salario_piso = max(salario_atual, float(piso_categoria)) if segue_piso else None
        aumento_piso = max(0.0, (novo_salario_piso or salario_atual) - salario_atual) if segue_piso else 0.0

        if acima_teto:
            novo_salario_base = novo_salario_teto
            aumento_base = aumento_teto
            regra_base = "Teto com valor fixo"
        else:
            novo_salario_base = novo_salario_percentual
            aumento_base = aumento_percentual
            regra_base = "Percentual"

        regra_aplicada = regra_base
        if proporcao < 1:
            regra_aplicada = f"{regra_aplicada} proporcional"

        if segue_piso and (novo_salario_piso or 0) > novo_salario_base:
            novo_salario_final = float(novo_salario_piso)
            aumento_final = aumento_piso
            regra_aplicada = "Piso da categoria"
            if proporcao < 1:
                regra_aplicada = f"{regra_aplicada} com comparacao ao proporcional"
        else:
            novo_salario_final = novo_salario_base
            aumento_final = aumento_base

        percentual_aplicado = (aumento_final / salario_acordo * 100) if salario_acordo else 0.0

        result_rows.append(
            {
                "Colaborador": row.get("colaborador"),
                "Empresa": row.get("empresa"),
                "Cargo": cargo,
                "Data admissao": data_admissao,
                "Salario atual": salario_atual,
                "Salario acordo": salario_acordo,
                "Proporcao": proporcao,
                "Meses elegiveis": meses_elegiveis,
                "Meses acordo": meses_totais,
                "Proporcionalidade": f"{meses_elegiveis}/{meses_totais}",
                "Acima do teto": "Sim" if acima_teto else "Nao",
                "Segue piso": "Sim" if segue_piso else "Nao",
                "Piso categoria": piso_categoria,
                "Novo salario via percentual": novo_salario_percentual,
                "Novo salario via teto": novo_salario_teto if acima_teto else None,
                "Novo salario via piso": novo_salario_piso,
                "Aumento via percentual": aumento_percentual,
                "Aumento via teto": aumento_teto if acima_teto else None,
                "Aumento via piso": aumento_piso if segue_piso else None,
                "Novo salario pos dissidio": novo_salario_final,
                "Aumento bruto": aumento_final,
                "Percentual aplicado": percentual_aplicado,
                "Regra aplicada": regra_aplicada,
            }
        )

    result_df = pd.DataFrame(result_rows)
    if not result_df.empty:
        result_df = result_df.sort_values(["Empresa", "Colaborador"], kind="stable").reset_index(drop=True)
    return result_df
