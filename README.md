# CFD Classes

Este repositório contém dois projetos Qt/C++ independentes:

- `Class 1`: aplicação para comparar aproximações numéricas de derivadas
- `Class 2`: aplicação com seleção de funções e visualização gráfica com controle de tempo

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

- `C:/ProgramData/mingw64/mingw64/bin/g++.exe`
- `C:/ProgramData/mingw64/mingw64/bin/gcc.exe`
- `C:/ProgramData/mingw64/mingw64/bin/mingw32-make.exe`
- `C:/Qt/6.10.2/mingw_64`

Se seus caminhos forem diferentes, ajuste os comandos abaixo.

## Build e execução do Class 1

### 1. Configurar

```powershell
cmake -S "Class 1" -B "Class 1/build-fresh" -G "MinGW Makefiles" `
  -DCMAKE_MAKE_PROGRAM=C:/ProgramData/mingw64/mingw64/bin/mingw32-make.exe `
  -DCMAKE_CXX_COMPILER=C:/ProgramData/mingw64/mingw64/bin/g++.exe `
  -DCMAKE_C_COMPILER=C:/ProgramData/mingw64/mingw64/bin/gcc.exe `
  -DCMAKE_PREFIX_PATH=C:/Qt/6.10.2/mingw_64
```

Ou, para refazer a configuração do zero na mesma pasta de build:

```powershell
cmake --fresh -S "Class 1" -B "Class 1/build" -G "MinGW Makefiles" `
  -DCMAKE_MAKE_PROGRAM=C:/ProgramData/mingw64/mingw64/bin/mingw32-make.exe `
  -DCMAKE_CXX_COMPILER=C:/ProgramData/mingw64/mingw64/bin/g++.exe `
  -DCMAKE_C_COMPILER=C:/ProgramData/mingw64/mingw64/bin/gcc.exe `
  -DCMAKE_PREFIX_PATH=C:/Qt/6.10.2/mingw_64
```

### 2. Compilar

```powershell
cmake --build "Class 1/build-fresh"
```

### 3. Executar

```powershell
& ".\Class 1\build-fresh\avaliador_derivadas.exe"
```

### Observação

No `Class 1`, o `windeployqt` já está configurado como passo pós-build no `CMakeLists.txt`. Em um build bem-sucedido, as DLLs do Qt devem ser copiadas automaticamente para a pasta do executável.

## Build e execução do Class 2

### 1. Configurar

```powershell
cmake -S "Class 2" -B "Class 2/build-fresh" -G "MinGW Makefiles" `
  -DCMAKE_MAKE_PROGRAM=C:/ProgramData/mingw64/mingw64/bin/mingw32-make.exe `
  -DCMAKE_CXX_COMPILER=C:/ProgramData/mingw64/mingw64/bin/g++.exe `
  -DCMAKE_C_COMPILER=C:/ProgramData/mingw64/mingw64/bin/gcc.exe `
  -DCMAKE_PREFIX_PATH=C:/Qt/6.10.2/mingw_64
```

Ou, para refazer a configuração do zero na mesma pasta de build:

```powershell
cmake --fresh -S "Class 2" -B "Class 2/build" -G "MinGW Makefiles" `
  -DCMAKE_MAKE_PROGRAM=C:/ProgramData/mingw64/mingw64/bin/mingw32-make.exe `
  -DCMAKE_CXX_COMPILER=C:/ProgramData/mingw64/mingw64/bin/g++.exe `
  -DCMAKE_C_COMPILER=C:/ProgramData/mingw64/mingw64/bin/gcc.exe `
  -DCMAKE_PREFIX_PATH=C:/Qt/6.10.2/mingw_64
```

### 2. Compilar

```powershell
cmake --build "Class 2/build-fresh"
```

### 3. Copiar as DLLs do Qt

O `Class 2` possui um alvo separado para deploy das dependências do Qt:

```powershell
cmake --build "Class 2/build-fresh" --target deploy_qt
```

Como a primeira aba usa `QWebEngineView` para renderizar fórmulas com MathJax, o kit Qt usado no `Class 2` precisa incluir `WebEngineWidgets`.

Se `WebEngineWidgets` não estiver instalado, o projeto ainda compila e a primeira aba cai automaticamente para um visualizador HTML simples, sem renderização matemática completa.

### 4. Executar

```powershell
& ".\Class 2\build-fresh\Class2App.exe"
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
`-- README.md
```

## Dicas de troubleshooting

### Erro: `Qt6Core.dll was not found`

Rode o deploy das DLLs no `Class 2`:

```powershell
cmake --build "Class 2/build-fresh" --target deploy_qt
```

No `Class 1`, esse passo já é automático no pós-build.

### Erro de configure com `no such file or directory`

Verifique se `mingw32-make.exe` aponta para o caminho real do MinGW. Neste ambiente, o caminho correto é:

```text
C:/ProgramData/mingw64/mingw64/bin/mingw32-make.exe
```

### Erro ao encontrar Qt

Confirme que `CMAKE_PREFIX_PATH` aponta para o kit MinGW do Qt:

```text
C:/Qt/6.10.2/mingw_64
```

### Quando o diretório `build` antigo estiver inconsistente

Prefira gerar em uma pasta nova como `build-fresh`, em vez de reaproveitar um build antigo:

```powershell
cmake -S "Class 2" -B "Class 2/build-fresh" ...
```
