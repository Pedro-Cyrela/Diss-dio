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

## Uso interno recomendado

### Primeira instalacao

Opcao 1, clique duplo:

- Execute `instalar_ambiente.bat`

Opcao 2, PowerShell:

```powershell
.\instalar_ambiente.ps1
```

### Abrir o app

Opcao 1, clique duplo:

- Execute `abrir_dissidio.bat`

Opcao 2, PowerShell:

```powershell
.\abrir_dissidio.ps1
```

O app abre localmente no navegador, em `http://localhost:8501`.
Na primeira instalacao, o processo pode levar alguns minutos por causa do download das bibliotecas.

## Fluxo sugerido para distribuir ao time

1. Versione o projeto em repositorio privado no GitHub.
2. Cada analista clona ou recebe uma copia ZIP do projeto.
3. Cada analista roda `instalar_ambiente.bat` uma vez.
4. Depois disso, usa apenas `abrir_dissidio.bat`.

## Execucao manual

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

## Premissa importante

Quando o colaborador foi admitido apos o acordo anterior, a proporcionalidade e aplicada tanto ao reajuste percentual quanto ao valor fixo acima do teto.
