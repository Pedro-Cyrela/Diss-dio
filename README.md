# Calculadora de Dissidio

Aplicacao Streamlit para calcular reajuste salarial por dissidio com foco operacional em Departamento Pessoal.

## O que a aplicacao cobre

- Upload de planilha principal de colaboradores em CSV ou Excel
- Tentativa de adivinhacao das colunas essenciais com ajuste manual
- Persistencia local dos parametros do acordo
- Regras de percentual, proporcionalidade por admissao, teto com valor fixo e piso da categoria
- Tela de analise de impacto financeiro
- Tela de auditoria individual para validar o calculo colaborador por colaborador

## Campos essenciais esperados

- Colaborador
- Cargo
- Salario atual
- Salario do acordo
- Empresa
- Data de admissao

## Variaveis persistidas

- Data do acordo anterior
- Data do acordo atual
- Percentual de reajuste
- Teto salarial de reajuste
- Valor fixo para salarios iguais ou acima do teto

## Como executar

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

## Premissa importante

Quando o colaborador foi admitido apos o acordo anterior, a proporcionalidade e aplicada tanto ao reajuste percentual quanto ao valor fixo acima do teto.
