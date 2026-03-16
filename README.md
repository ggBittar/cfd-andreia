# CFD Classes

Este repositório contem tres projetos independentes:

- `Class 1`: aplicação para comparar aproximações numéricas de derivadas
- `Class 2`: aplicação com seleção de funções e visualização gráfica com controle de tempo
- `Class 2 - versao 2`: reproducao do `Class 2` em `PyQt6`, com backend numerico em `Cython`

As instruções abaixo assumem que você está na raiz do repositório:

```powershell
cd C:\Users\gbitt\Documents\Mestrado\CFD\cfd-andreia
```

## Pré-requisitos

No Windows, os dois projetos foram preparados para uso com:

- `CMake`
- `MinGW`
- `Qt 6` para `mingw_64`
- `Qt WebEngine` é opcional no `Class 2` e melhora a renderização das formulações

Exemplo de caminhos usados neste repositório:

- `C:/Qt/6.10.2/mingw_64`
- `C:/Qt/Tools/mingw1310_64/bin/gcc.exe`
- `C:/Qt/Tools/mingw1310_64/bin/g++.exe`

Se seus caminhos forem diferentes, ajuste os comandos abaixo.

## Build e execução do Class 1

### 1. Configurar

```powershell
cd "Class 1"
cmake -S . -B build -G "MinGW Makefiles" `
  -DCMAKE_PREFIX_PATH="C:/Qt/6.10.2/mingw_64" `
  -DCMAKE_MAKE_PROGRAM="C:/Qt/Tools/mingw1310_64/bin/mingw32-make.exe" `
  -DCMAKE_C_COMPILER="C:/Qt/Tools/mingw1310_64/bin/gcc.exe" `
  -DCMAKE_CXX_COMPILER="C:/Qt/Tools/mingw1310_64/bin/g++.exe"
```

### 2. Compilar

```powershell
cmake --build build
```

### 3. Executar

```powershell
& ".\build\avaliador_derivadas.exe"
```

### Observação

No `Class 1`, o `windeployqt` já está configurado como passo pós-build no `CMakeLists.txt`. Em um build bem-sucedido, as DLLs do Qt devem ser copiadas automaticamente para a pasta do executável.

## Build e execução do Class 2

### 1. Configurar

```powershell
cd "Class 2"
cmake -S . -B build -G "MinGW Makefiles" `
  -DCMAKE_PREFIX_PATH="C:/Qt/6.10.2/mingw_64" `
  -DCMAKE_MAKE_PROGRAM="C:/Qt/Tools/mingw1310_64/bin/mingw32-make.exe" `
  -DCMAKE_C_COMPILER="C:/Qt/Tools/mingw1310_64/bin/gcc.exe" `
  -DCMAKE_CXX_COMPILER="C:/Qt/Tools/mingw1310_64/bin/g++.exe"
```

### 2. Compilar

```powershell
cmake --build build
```

### 3. Copiar as DLLs do Qt

O `Class 2` possui um alvo separado para deploy das dependências do Qt:

```powershell
cmake --build build --target deploy_qt
```

Como a primeira aba usa `QWebEngineView` para renderizar fórmulas com MathJax, o kit Qt usado no `Class 2` precisa incluir `WebEngineWidgets`.

Se `WebEngineWidgets` não estiver instalado, o projeto ainda compila e a primeira aba cai automaticamente para um visualizador HTML simples, sem renderização matemática completa.

### 4. Executar

```powershell
& ".\build\Class2App.exe"
```

## Estrutura do repositório

```text
cfd-andreia/
|-- Class 1/
|   |-- CMakeLists.txt
|   |-- src/
|   `-- recursos/
|-- Class 2/
|   |-- CMakeLists.txt
|   |-- src/
|   `-- recursos/
|-- Class 2 - versao 2/
|   |-- pyproject.toml
|   |-- setup.py
|   `-- src/
`-- README.md
```

## Build e execucao do Class 2 - versao 2

### 1. Instalar as dependencias

Em um ambiente Python com `pip`:

```powershell
cd "Class 2 - versao 2"
python -m pip install -e .
```

### 2. Executar

```powershell
class2-versao-2-app
```

Ou:

```powershell
python -m class2_v2_app
```

### Observacao

O `Class 2 - versao 2` foi estruturado para compilar o modulo `src/class2_v2_app/_burgers.pyx` com `Cython`. Se a extensao compilada ainda nao estiver disponivel, a aplicacao cai automaticamente para um backend em Python puro com a mesma formulacao.

## Dicas de troubleshooting

### Erro: `Qt6Core.dll was not found`

Rode o deploy das DLLs no `Class 2`:

```powershell
cmake --build build --target deploy_qt
```

No `Class 1`, esse passo já é automático no pós-build.

### Erro ao encontrar Qt

Confirme que `CMAKE_PREFIX_PATH` aponta para o kit MinGW do Qt:

```text
C:/Qt/6.10.2/mingw_64
```

### Erro ao encontrar compiladores MinGW

Confirme que os compiladores apontam para:

```text
C:/Qt/Tools/mingw1310_64/bin/gcc.exe
C:/Qt/Tools/mingw1310_64/bin/g++.exe
```

### Quando o diretório `build` antigo estiver inconsistente

Apague ou recrie a pasta `build` dentro do projeto e configure novamente:

```powershell
cmake -S . -B build ...
```
