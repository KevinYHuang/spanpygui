import tqdm.notebook as nb

def is_interactive():
    import __main__ as main
    return not hasattr(main, '__file__')

def tqdm(iter, *args, **kwargs):
    if not is_interactive: return iter
    return nb.tqdm(iter, *args, **kwargs)