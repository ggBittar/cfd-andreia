# Class 3

Aplicacao em `PyQt6` inspirada no `Class 2 - versao 2`, agora com discretizacao em tempo e em espaco para a equacao viscosa de Burgers e nucleo de calculo em `Cython`.

## O que este projeto faz

- apresenta a formulacao continua da solucao de Burgers e os esquemas numericos usados
- permite configurar o dominio em `x`, o tempo final `tf`, um `N` para a solucao exata, um vetor `Nx` de malhas espaciais e um vetor `Nt` de passos no tempo
- compara no grafico a condicao inicial, a solucao exata em `tf` e as solucoes numericas obtidas com avancos em `x` e em `t`
- usa condicao periodica, coerente com a formulacao baseada em `Phi`
- tenta carregar a extensao compilada `class3_app._burgers` e cai para Python puro apenas como fallback

## Metodos incluidos

- `FTBS + difusao central`: conveccao com diferenca atrasada em `x` e difusao central
- `FTCS + difusao central`: conveccao com diferenca central em `x` e difusao central
- `Lax-Friedrichs + difusao central`: media espacial com difusao central

## Como instalar

```powershell
cd "Class 3"
python -m pip install -e .
```

Para habilitar renderizacao matematica mais fiel na aba de formulacoes:

```powershell
python -m pip install -e .[webengine]
```

O build da extensao Cython usa o arquivo `setup.py` do projeto.

## Como executar

```powershell
class3-app
```

Ou:

```powershell
python -m class3_app
```
