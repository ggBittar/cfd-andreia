def configurar_matplotlib():
    import matplotlib

    try:
        matplotlib.use("TkAgg")
        matplotlib.rcParams["toolbar"] = "None"

        from matplotlib.backends import _backend_tk

        def criar_com_canvas_sem_pillow(cls, canvas_class, figure, num):
            with _backend_tk._restore_foreground_window_at_end():
                if _backend_tk.cbook._get_running_interactive_framework() is None:
                    _backend_tk.cbook._setup_new_guiapp()
                    _backend_tk._c_internal_utils.Win32_SetProcessDpiAwareness_max()

                window = _backend_tk.tk.Tk(className="matplotlib")
                window.withdraw()

                icon_fname = str(_backend_tk.cbook._get_data_path("images/matplotlib.png"))
                icon_img = _backend_tk.tk.PhotoImage(file=icon_fname, master=window)

                icon_fname_large = str(_backend_tk.cbook._get_data_path("images/matplotlib_large.png"))
                icon_img_large = _backend_tk.tk.PhotoImage(file=icon_fname_large, master=window)

                window.iconphoto(False, icon_img_large, icon_img)

                canvas = canvas_class(figure, master=window)
                manager = cls(canvas, num, window)
                if _backend_tk.mpl.is_interactive():
                    manager.show()
                    canvas.draw_idle()
                return manager

        _backend_tk.FigureManagerTk.create_with_canvas = classmethod(criar_com_canvas_sem_pillow)
    except Exception:
        matplotlib.use("Agg")

    return matplotlib
