import threading


def run_in_background(target, *args, **kwargs):
    thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    thread.start()

    return thread
