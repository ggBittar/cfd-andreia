# Class 2 - versao 2

Reproducao do `Class 2` usando `PyQt6` para a interface e `Cython` para o nucleo numerico da formulacao em funcao de `Phi`.

## O que este projeto faz

- mostra as formulacoes da solucao de Burgers em uma aba HTML
- permite configurar a funcao, o dominio em `x`, o tempo final `tf`, um `N` de referencia e um vetor `Nt` com diferentes numeros de passos no tempo
- compara no mesmo grafico a solucao inicial `t = 0`, a solucao exata em `tf` e os metodos temporais selecionados para varios valores de `Nt`
- usa um modulo compilado em Cython para calcular `phi_n`, `phi_x_n`, `phi`, `phi_x` e `u`
- melhora a aba de formulacoes com `MathJax` quando `PyQt6-WebEngine` estiver instalado

## Metodos temporais incluidos

- diferenca adiantada
- diferenca atrasada
- diferenca central

Os metodos estao organizados no arquivo `src/class2_v2_app/time_method_catalog.py`.

## Estrutura

```text
Class 2 - versao 2/
|-- pyproject.toml
|-- setup.py
|-- README.md
`-- src/
    `-- class2_v2_app/
        |-- __init__.py
        |-- __main__.py
        |-- _burgers.pyx
        |-- burgers_fallback.py
        |-- function_catalog.py
        |-- function_selector.py
        |-- graph_widget.py
        |-- latex_widget.py
        |-- main.py
        |-- main_window.py
        `-- time_method_catalog.py
```

## Como instalar

Em um ambiente Python com `pip` disponivel:

```powershell
cd "d:\Users\Directa\Documents\Projetos\pessoal\cfd-andreia\Class 2 - versao 2"
python -m pip install -e .
```

Para habilitar a renderizacao matematica mais fiel na aba `LaTeX Viewer`:

```powershell
python -m pip install -e .[webengine]
```

## Como executar

```powershell
class2-versao-2-app
```

Ou:

```powershell
python -m class2_v2_app
```

## Observacoes

- o projeto foi preparado para funcionar com o modulo Cython compilado
- se o modulo compilado ainda nao estiver disponivel, existe um fallback em Python puro para facilitar testes
- com `PyQt6-WebEngine`, a aba `LaTeX Viewer` usa `MathJax`
- sem `PyQt6-WebEngine`, a aba cai para um HTML enriquecido em `QTextBrowser`
- o painel de selecao agora usa um `N` unico para a solucao exata e um vetor `Nt` para comparar refinamentos temporais
