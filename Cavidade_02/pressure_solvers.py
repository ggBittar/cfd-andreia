import numpy as np


def _dct2_basis(n):
    i = np.arange(n, dtype=float)[:, None]
    k = np.arange(n, dtype=float)[None, :]
    basis = np.cos(np.pi * (i + 0.5) * k / n)
    basis[:, 0] *= np.sqrt(1.0 / n)
    if n > 1:
        basis[:, 1:] *= np.sqrt(2.0 / n)
    return basis


def _dct_poisson_cache_key(config):
    return (config.nx, config.ny, float(config.dx), float(config.dy))


def obter_estrutura_poisson_dct(config):
    cache = getattr(obter_estrutura_poisson_dct, "_cache", {})
    chave = _dct_poisson_cache_key(config)
    if chave not in cache:
        qx = _dct2_basis(config.nx)
        qy = _dct2_basis(config.ny)

        kx = np.arange(config.nx, dtype=float)
        ky = np.arange(config.ny, dtype=float)
        lambda_x = 2.0 * (1.0 - np.cos(np.pi * kx / config.nx)) / config.dx**2
        lambda_y = 2.0 * (1.0 - np.cos(np.pi * ky / config.ny)) / config.dy**2
        denominador = lambda_y[:, None] + lambda_x[None, :]
        denominador[0, 0] = np.inf

        cache[chave] = qx, qy, denominador
        obter_estrutura_poisson_dct._cache = cache
    return cache[chave]


def obter_estrutura_poisson_fft(config):
    cache = getattr(obter_estrutura_poisson_fft, "_cache", {})
    chave = _dct_poisson_cache_key(config)
    if chave not in cache:
        kx = np.arange(config.nx, dtype=float)
        ky = np.arange(config.ny, dtype=float)
        lambda_x = 2.0 * (1.0 - np.cos(np.pi * kx / config.nx)) / config.dx**2
        lambda_y = 2.0 * (1.0 - np.cos(np.pi * ky / config.ny)) / config.dy**2
        denominador = lambda_y[:, None] + lambda_x[None, :]
        denominador[0, 0] = np.inf

        cache[chave] = denominador
        obter_estrutura_poisson_fft._cache = cache
    return cache[chave]


def _dct_ortho_fft_1d(x):
    x = np.asarray(x, dtype=float)
    n = x.shape[-1]
    extensao = np.concatenate([x, x[..., ::-1]], axis=-1)
    espectro = np.fft.fft(extensao, axis=-1)[..., :n]
    fase = np.exp(-1j * np.pi * np.arange(n) / (2.0 * n))
    coeficientes = (espectro * fase).real

    coeficientes[..., 0] *= 0.5 * np.sqrt(1.0 / n)
    if n > 1:
        coeficientes[..., 1:] *= 0.5 * np.sqrt(2.0 / n)
    return coeficientes


def _idct_ortho_fft_1d(coeficientes):
    coeficientes = np.asarray(coeficientes, dtype=float)
    n = coeficientes.shape[-1]
    dct_sem_escala = coeficientes.copy()

    dct_sem_escala[..., 0] /= 0.5 * np.sqrt(1.0 / n)
    if n > 1:
        dct_sem_escala[..., 1:] /= 0.5 * np.sqrt(2.0 / n)

    espectro = np.zeros(coeficientes.shape[:-1] + (2 * n,), dtype=complex)
    fase = np.exp(1j * np.pi * np.arange(n) / (2.0 * n))
    espectro[..., :n] = dct_sem_escala * fase
    if n > 1:
        espectro[..., n + 1:] = np.conj(espectro[..., 1:n][..., ::-1])

    extensao = np.fft.ifft(espectro, axis=-1).real
    return extensao[..., :n]


def _dct_ortho_fft2(campo):
    coeficientes = _dct_ortho_fft_1d(campo)
    coeficientes = np.swapaxes(coeficientes, -1, -2)
    coeficientes = _dct_ortho_fft_1d(coeficientes)
    return np.swapaxes(coeficientes, -1, -2)


def _idct_ortho_fft2(coeficientes):
    campo = _idct_ortho_fft_1d(coeficientes)
    campo = np.swapaxes(campo, -1, -2)
    campo = _idct_ortho_fft_1d(campo)
    return np.swapaxes(campo, -1, -2)


def resolver_poisson_dct(b_grid, config, p_shape):
    """Resolve A p = b para Poisson com Neumann em malha retangular uniforme.

    A matriz A e o vetor b seguem a mesma convencao do solver SOR: A e um
    laplaciano discreto positivo, com pressao definida a menos de constante.
    O modo medio e fixado em zero.
    """
    qx, qy, denominador = obter_estrutura_poisson_dct(config)

    b = np.asarray(b_grid, dtype=float)
    b = b - b.mean()
    coeficientes = qy.T @ b @ qx
    coeficientes[0, 0] = 0.0

    p_interno = qy @ (coeficientes / denominador) @ qx.T
    p_interno -= p_interno.mean()

    p_corr = np.zeros(p_shape, dtype=float)
    p_corr[1:-1, 1:-1] = p_interno
    p_corr[:, 0] = p_corr[:, 1]
    p_corr[:, -1] = p_corr[:, -2]
    p_corr[0, :] = p_corr[1, :]
    p_corr[-1, :] = p_corr[-2, :]

    return p_corr, 1, 0.0


def resolver_poisson_fft(b_grid, config, p_shape):
    """Resolve a Poisson de Neumann usando DCT calculada por FFT."""
    denominador = obter_estrutura_poisson_fft(config)

    b = np.asarray(b_grid, dtype=float)
    b = b - b.mean()
    coeficientes = _dct_ortho_fft2(b)
    coeficientes[0, 0] = 0.0

    p_interno = _idct_ortho_fft2(coeficientes / denominador)
    p_interno -= p_interno.mean()

    p_corr = np.zeros(p_shape, dtype=float)
    p_corr[1:-1, 1:-1] = p_interno
    p_corr[:, 0] = p_corr[:, 1]
    p_corr[:, -1] = p_corr[:, -2]
    p_corr[0, :] = p_corr[1, :]
    p_corr[-1, :] = p_corr[-2, :]

    return p_corr, 1, 0.0


def _importar_scipy_sparse():
    try:
        from scipy.sparse import csr_matrix
        from scipy.sparse.linalg import LinearOperator, bicgstab, cg
    except ImportError as exc:
        raise ImportError(
            "pressure_solver='scipy_cg' ou 'scipy_bicgstab' requer SciPy. "
            "Instale com: pip install -r Cavidade_02/requirements.txt"
        ) from exc
    return csr_matrix, LinearOperator, cg, bicgstab


def obter_estrutura_poisson_scipy(config):
    csr_matrix, LinearOperator, _, _ = _importar_scipy_sparse()
    cache = getattr(obter_estrutura_poisson_scipy, "_cache", {})
    chave = _dct_poisson_cache_key(config)
    if chave not in cache:
        nx = config.nx
        ny = config.ny
        cx = 1.0 / config.dx**2
        cy = 1.0 / config.dy**2

        linhas = []
        colunas = []
        dados = []
        n_total = nx * ny
        diagonal = np.zeros(n_total - 1, dtype=float)

        for j in range(ny):
            for i in range(nx):
                k = j * nx + i
                diag = 0.0

                if i > 0:
                    if k != 0 and k - 1 != 0:
                        linhas.append(k - 1)
                        colunas.append(k - 2)
                        dados.append(-cx)
                    diag += cx
                if i < nx - 1:
                    if k != 0 and k + 1 != 0:
                        linhas.append(k - 1)
                        colunas.append(k)
                        dados.append(-cx)
                    diag += cx
                if j > 0:
                    if k != 0 and k - nx != 0:
                        linhas.append(k - 1)
                        colunas.append(k - nx - 1)
                        dados.append(-cy)
                    diag += cy
                if j < ny - 1:
                    if k != 0 and k + nx != 0:
                        linhas.append(k - 1)
                        colunas.append(k + nx - 1)
                        dados.append(-cy)
                    diag += cy

                if k != 0:
                    linhas.append(k - 1)
                    colunas.append(k - 1)
                    dados.append(diag)
                    diagonal[k - 1] = diag

        matriz = csr_matrix((dados, (linhas, colunas)), shape=(n_total - 1, n_total - 1))
        diag_inv = np.zeros_like(diagonal)
        np.divide(1.0, diagonal, out=diag_inv, where=diagonal > 0.0)
        precondicionador = LinearOperator(matriz.shape, matvec=lambda x: diag_inv * x)

        cache[chave] = matriz, precondicionador
        obter_estrutura_poisson_scipy._cache = cache
    return cache[chave]


def _resolver_iterativo_scipy(metodo, A, b, x0, M, tolerancia, max_iter):
    _, _, cg, bicgstab = _importar_scipy_sparse()
    iteracoes = 0

    def contar_iteracao(_):
        nonlocal iteracoes
        iteracoes += 1

    solver = cg if metodo == "cg" else bicgstab
    try:
        solucao, info = solver(
            A,
            b,
            x0=x0,
            M=M,
            rtol=tolerancia,
            atol=0.0,
            maxiter=max_iter,
            callback=contar_iteracao,
        )
    except TypeError:
        solucao, info = solver(
            A,
            b,
            x0=x0,
            M=M,
            tol=tolerancia,
            maxiter=max_iter,
            callback=contar_iteracao,
        )

    return solucao, info, iteracoes


def resolver_poisson_scipy(b_grid, config, p_shape, p_inicial=None, metodo="cg"):
    A, precondicionador = obter_estrutura_poisson_scipy(config)

    b = np.asarray(b_grid, dtype=float).reshape(-1)
    b_reduzido = b[1:]

    if p_inicial is None:
        x0 = np.zeros_like(b_reduzido)
    else:
        x0 = np.asarray(p_inicial[1:-1, 1:-1], dtype=float).reshape(-1).copy()[1:]

    p_vec, info, iteracoes = _resolver_iterativo_scipy(
        metodo,
        A,
        b_reduzido,
        x0,
        precondicionador,
        config.sor_tolerance,
        config.sor_max_iter,
    )

    residuo = A @ p_vec - b_reduzido
    erro = float(np.sqrt(np.mean(residuo**2)))

    if info < 0:
        raise FloatingPointError(f"Solver SciPy {metodo} falhou com info={info}.")

    p_corr = np.zeros(p_shape, dtype=float)
    p_interno = np.zeros(config.nx * config.ny, dtype=float)
    p_interno[1:] = p_vec
    p_corr[1:-1, 1:-1] = p_interno.reshape(config.ny, config.nx)
    p_corr[:, 0] = p_corr[:, 1]
    p_corr[:, -1] = p_corr[:, -2]
    p_corr[0, :] = p_corr[1, :]
    p_corr[-1, :] = p_corr[-2, :]

    return p_corr, iteracoes if iteracoes > 0 else config.sor_max_iter, erro
