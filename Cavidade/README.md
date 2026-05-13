# Cavidade com Tampa Deslizante — PyQt + Simulação 2D

Este projeto implementa uma interface em **PyQt6** com duas abas:

1. **Discretização em LaTeX**: apresenta a formulação do problema da cavidade com tampa deslizante, a malha `node-centered`, os semi-volumes nas bordas e as condições de contorno.
2. **Simulação temporal**: executa uma simulação 2D do escoamento usando a formulação vorticidade-função de corrente.

O caso físico é a clássica **lid-driven cavity**: uma caixa fechada com a tampa superior deslizando com velocidade constante `U`, enquanto as outras paredes permanecem fixas.

## Estrutura do projeto

```text
cavidade_tampa_deslizante_pyqt/
├── README.md
├── requirements.txt
├── run.ps1
├── docs/
│   └── discretizacao.tex
└── src/
    ├── __init__.py
    ├── cavity_solver.py
    ├── latex_content.py
    ├── latex_widget.py
    ├── main.py
    └── simulation_widget.py
```

## Modelo numérico

A simulação usa a formulação vorticidade-função de corrente:

```math
\nabla^2\psi=-\omega
```

```math
\frac{\partial\omega}{\partial t}
+u\frac{\partial\omega}{\partial x}
+v\frac{\partial\omega}{\partial y}
=\nu\nabla^2\omega
```

com:

```math
u_x=u=\frac{\partial\psi}{\partial y},
\qquad
u_y=v=-\frac{\partial\psi}{\partial x}
```

As condições de contorno são:

- parede inferior: `u = 0`, `v = 0`;
- parede esquerda: `u = 0`, `v = 0`;
- parede direita: `u = 0`, `v = 0`;
- tampa superior: `u = U`, `v = 0`;
- função de corrente: `ψ = 0` nas paredes impermeáveis;
- vorticidade de parede calculada pela aproximação de Thom.

A malha é **node-centered**. Nas bordas, os volumes de controle são tratados como **semi-volumes**, e nos cantos como quartos de volume.

## Como rodar no Windows com PowerShell

Dentro da pasta do projeto, execute:

```powershell
.\run.ps1
```

O script `run.ps1` faz automaticamente:

1. entra na pasta do projeto;
2. cria o ambiente virtual `.venv`, se ele ainda não existir;
3. ativa o ambiente virtual;
4. atualiza o `pip`;
5. instala as dependências de `requirements.txt`;
6. executa a aplicação com `python src\main.py`.

Caso o PowerShell bloqueie a execução do próprio `run.ps1`, rode uma vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Depois execute novamente:

```powershell
.\run.ps1
```

## Como rodar manualmente

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python src\main.py
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python src/main.py
```

## Como usar a simulação

Na aba **Simulação temporal**:

- ajuste o número de Reynolds em `Re`;
- ajuste a malha em `Nós N×N`;
- clique em **Resetar** para reconstruir o caso com os novos parâmetros;
- clique em **Iniciar** para evoluir no tempo;
- clique em **Pausar** para interromper;
- use **Avançar 20 passos** para evoluir manualmente;
- alterne entre os campos `Velocidade |V|`, `Vorticidade` e `Função de corrente`.

## Observações importantes

- Para `Re` muito alto e malha grosseira, a simulação explícita pode ficar instável.
- Para começar, use `Re = 100` e malha `41 × 41`.
- A simulação tem objetivo didático: ela mostra a formação do vórtice principal e o desenvolvimento do campo de velocidades ao longo do tempo.
- O arquivo `docs/discretizacao.tex` contém a formulação em LaTeX em formato compilável.

## Compilar o LaTeX separadamente

Se você tiver uma distribuição LaTeX instalada, pode gerar um PDF da formulação com:

```bash
cd docs
pdflatex discretizacao.tex
```


## Correção da guia LaTeX

A aba **Discretização em LaTeX** usa um renderizador interno em PyQt com cores fixas para evitar o problema de equações ilegíveis em tema escuro do Windows/Qt. O arquivo LaTeX completo continua disponível em `docs/discretizacao.tex`.
