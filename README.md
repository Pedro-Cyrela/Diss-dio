# Calculadora de Dissidio

Aplicacao Streamlit para calcular reajuste salarial por dissidio com foco operacional em Departamento Pessoal.

## O que a aplicacao cobre

- Upload de planilha principal de colaboradores em CSV ou Excel
- Tentativa de adivinhacao das colunas essenciais com ajuste manual
- Persistencia local dos parametros do acordo por usuario da maquina
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

Os parametros ficam em `AppData\Roaming\CalculadoraDissidio\config.json`, separados por usuario da maquina.

## Novo fluxo de uso

### Pre-requisito unico

- Ter Python 3.10 ou superior instalado na maquina e acessivel pelo comando `python`

### Como abrir o app

No proprio diretorio do projeto, execute:

```powershell
python app.py
```

O `app.py` agora faz sozinho o bootstrap local:

- cria a pasta `.venv` se ela ainda nao existir
- verifica se `streamlit`, `pandas`, `openpyxl` e `plotly` estao disponiveis
- instala o que faltar com base no `requirements.txt`
- inicia o Streamlit localmente
- abre o navegador automaticamente

O app tenta usar `http://localhost:8501`. Se essa porta estiver ocupada, ele escolhe a proxima livre.

### Distribuicao para o time

1. Entregue a pasta do projeto por GitHub ou ZIP.
2. Oriente o usuario a abrir um terminal dentro da pasta.
3. Oriente o usuario a executar apenas `python app.py`.

Nao ha mais dependencia operacional de `.bat`, `.ps1` ou arquivos temporarios para subir a aplicacao.

## Execucao alternativa

Se alguem ja estiver com o ambiente pronto e quiser rodar o Streamlit manualmente:

```powershell
.venv\Scripts\python -m streamlit run dissidio_ui.py
```

## Premissa importante

Quando o colaborador foi admitido apos o acordo anterior, a proporcionalidade e aplicada tanto ao reajuste percentual quanto ao valor fixo acima do teto.
