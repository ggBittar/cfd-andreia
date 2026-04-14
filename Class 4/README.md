# Class 4

Aplicacao em `PyQt6` para estudar a discretizacao por volumes finitos da equacao do calor 1D transiente sem termo de geracao, com nucleo numerico em `Cython`.

## O que este projeto faz

- resolve o problema transiente `dT/dt = alpha d²T/dx²` em um dominio 1D
- usa malha uniforme com entrada separada para `x` e `t`, permitindo informar numero de passos ou tamanho do passo
- implementa um modelo de contorno `Dirichlet`, cujos parametros pertencem ao proprio modelo selecionado
- usa condicao inicial uniforme `T0`
- compara a solucao numerica em `tf` com o perfil linear de regime permanente
- permite comparar simultaneamente `volume nulo`, `semivolume` e `elemento fantasma`
- usa o scroll do mouse no grafico para avancar ou retroceder no tempo, mantendo `Ctrl + scroll` para zoom

## Metodos incluidos

- `Dirichlet`: valor prescrito de temperatura nas duas fronteiras
- `Volume nulo`: nos nas fronteiras com imposicao direta de Dirichlet
- `Semivolume`: volumes de contorno com metade do tamanho dos internos
- `Elemento fantasma`: celulas ficticias fora do dominio para impor Dirichlet

Os parametros de contorno exibidos na interface dependem do modelo de contorno selecionado.

## Como instalar

```powershell
cd "Class 4"
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Para habilitar renderizacao matematica mais fiel:

```powershell
python -m pip install -e .[webengine]
```

## Como executar

```powershell
class4-app
```

Ou:

```powershell
python -m class4_app
```
