LATEX_TEXT = r"""
\section*{Cavidade bidimensional com tampa deslizante}

Considere uma caixa retangular de dimensões $L_x \times L_y$, preenchida por um fluido
newtoniano, incompressível e laminar. A tampa superior desliza com velocidade constante
$U$, enquanto as demais paredes permanecem fixas. O escoamento é bidimensional no plano
$(x,y)$.

\subsection*{Equações governantes}

Na forma velocidade-pressão, as equações incompressíveis são:
\[
\frac{\partial u}{\partial x}+\frac{\partial v}{\partial y}=0,
\]
\[
\frac{\partial u}{\partial t}+u\frac{\partial u}{\partial x}+v\frac{\partial u}{\partial y}
= -\frac{1}{\rho}\frac{\partial p}{\partial x}+\nu\left(\frac{\partial^2 u}{\partial x^2}+\frac{\partial^2 u}{\partial y^2}\right),
\]
\[
\frac{\partial v}{\partial t}+u\frac{\partial v}{\partial x}+v\frac{\partial v}{\partial y}
= -\frac{1}{\rho}\frac{\partial p}{\partial y}+\nu\left(\frac{\partial^2 v}{\partial x^2}+\frac{\partial^2 v}{\partial y^2}\right).
\]

No projeto foi adotada a formulação vorticidade-função de corrente, pois ela remove a pressão
para escoamentos 2D incompressíveis:
\[
\omega = \frac{\partial v}{\partial x}-\frac{\partial u}{\partial y},
\qquad
u_x = u = \frac{\partial\psi}{\partial y},
\qquad
u_y = v = -\frac{\partial\psi}{\partial x}.
\]

Assim, resolve-se:
\[
\nabla^2\psi = -\omega,
\]
\[
\frac{\partial\omega}{\partial t} + u\frac{\partial\omega}{\partial x}
+ v\frac{\partial\omega}{\partial y}
= \nu\left(\frac{\partial^2\omega}{\partial x^2}+\frac{\partial^2\omega}{\partial y^2}\right).
\]

\subsection*{Malha node-centered}

A malha possui nós $(i,j)$ com
\[
x_i=i\Delta x,\quad y_j=j\Delta y,
\quad \Delta x=\frac{L_x}{N_x-1},\quad \Delta y=\frac{L_y}{N_y-1}.
\]

Na abordagem node-centered, cada incógnita é armazenada no nó. Para nós internos, o volume de
controle associado ao nó $(i,j)$ possui dimensões $\Delta x\times\Delta y$. Para nós de borda,
o volume é um semi-volume: por exemplo, na parede esquerda a largura é $\Delta x/2$; em cantos,
o volume é um quarto de volume.

\subsection*{Discretização do volume interno}

Integrando a equação de transporte da vorticidade em um volume centrado no nó e usando fluxo
difusivo por diferenças centrais, obtém-se, para nós internos:
\[
\frac{\omega_{i,j}^{n+1}-\omega_{i,j}^{n}}{\Delta t}
+ u_{i,j}\left(\frac{\partial\omega}{\partial x}\right)_{i,j}
+ v_{i,j}\left(\frac{\partial\omega}{\partial y}\right)_{i,j}
= \nu\left[
\frac{\omega_{i+1,j}-2\omega_{i,j}+\omega_{i-1,j}}{\Delta x^2}
+
\frac{\omega_{i,j+1}-2\omega_{i,j}+\omega_{i,j-1}}{\Delta y^2}
\right].
\]

No código, os termos convectivos são aproximados por upwind de primeira ordem:
\[
\left(\frac{\partial\omega}{\partial x}\right)_{i,j}=
\begin{cases}
(\omega_{i,j}-\omega_{i-1,j})/\Delta x, & u_{i,j}\geq 0,\\
(\omega_{i+1,j}-\omega_{i,j})/\Delta x, & u_{i,j}<0,
\end{cases}
\]
\[
\left(\frac{\partial\omega}{\partial y}\right)_{i,j}=
\begin{cases}
(\omega_{i,j}-\omega_{i,j-1})/\Delta y, & v_{i,j}\geq 0,\\
(\omega_{i,j+1}-\omega_{i,j})/\Delta y, & v_{i,j}<0.
\end{cases}
\]

A função de corrente é obtida pela equação de Poisson:
\[
\frac{\psi_{i+1,j}-2\psi_{i,j}+\psi_{i-1,j}}{\Delta x^2}
+
\frac{\psi_{i,j+1}-2\psi_{i,j}+\psi_{i,j-1}}{\Delta y^2}
= -\omega_{i,j}.
\]

Isolando $\psi_{i,j}$:
\[
\psi_{i,j}=
\frac{
\Delta y^2(\psi_{i+1,j}+\psi_{i-1,j})+
\Delta x^2(\psi_{i,j+1}+\psi_{i,j-1})+
\Delta x^2\Delta y^2\omega_{i,j}
}{2(\Delta x^2+\Delta y^2)}.
\]

As velocidades nodais são recuperadas por:
\[
u_{i,j}=\frac{\psi_{i,j+1}-\psi_{i,j-1}}{2\Delta y},
\qquad
v_{i,j}=-\frac{\psi_{i+1,j}-\psi_{i-1,j}}{2\Delta x}.
\]

\subsection*{Semi-volumes nas bordas}

Nos nós sobre uma parede, o volume de controle possui meia espessura na direção normal à parede.
A impermeabilidade impõe fluxo normal nulo. Como as paredes são linhas de corrente, adota-se:
\[
\psi=0 \quad \text{em todas as paredes.}
\]

As condições de não escorregamento são:
\[
\text{parede inferior: } u=0,\;v=0,
\qquad
\text{parede esquerda: } u=0,\;v=0,
\]
\[
\text{parede direita: } u=0,\;v=0,
\qquad
\text{tampa superior: } u=U,\;v=0.
\]

A vorticidade na parede é obtida por uma expansão de Taylor normal à parede, equivalente ao
tratamento do semi-volume. Para uma parede horizontal parada:
\[
\omega_w=-\frac{2\psi_P}{\Delta y^2},
\]
na qual $P$ é o primeiro nó interno adjacente à parede. Para a tampa superior móvel:
\[
\omega_{top}=-\frac{2\psi_P}{\Delta y^2}-\frac{2U}{\Delta y}.
\]

Para paredes verticais paradas:
\[
\omega_{left}=-\frac{2\psi_P}{\Delta x^2},
\qquad
\omega_{right}=-\frac{2\psi_P}{\Delta x^2}.
\]

Nos cantos, onde há singularidade pela mudança brusca de velocidade da parede, o código usa a
média das vorticidades das duas paredes adjacentes.

\subsection*{Critério prático de estabilidade}

Como a integração temporal é explícita para a equação de vorticidade, recomenda-se:
\[
\Delta t \leq \min\left( C_a\frac{h}{U},\; C_d\frac{h^2}{\nu}\right),
\quad h=\min(\Delta x,\Delta y),
\]
com $C_a<1$ e $C_d\lesssim 1/4$. O código escolhe automaticamente um passo conservador quando
$\Delta t$ não é fornecido.
"""
