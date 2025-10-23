import typing


def get_config_path() -> typing.Optional[str]:
    import sys

    if "-c" in sys.argv:
        config_index = sys.argv.index("-c") + 1
        if config_index < len(sys.argv):
            return sys.argv[config_index]

    return None


def get_gunicorn_threads() -> int:
    import importlib.util

    try:
        conf_path = get_config_path()
        if conf_path is not None:
            spec = importlib.util.spec_from_file_location("gunicorn_conf", conf_path)
            if spec and spec.loader:
                gunicorn_conf = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(gunicorn_conf)
                return gunicorn_conf.threads
            return 0
        return 1
    except Exception:
        return 1


def get_thread_id(
    thread_ids: typing.Dict[str, str],
) -> typing.Tuple[str, typing.Dict[str, str]]:
    import secrets, threading

    thread_name = threading.current_thread().name
    if thread_name not in thread_ids:
        thread_ids[thread_name] = secrets.token_hex(4)
    return thread_ids[thread_name], thread_ids


def get_worker_id() -> str:
    import os

    from multiprocessing import current_process

    name = os.environ.get("HOSTNAME")
    if name is None or name == "":
        return str(current_process().pid)

    return name
