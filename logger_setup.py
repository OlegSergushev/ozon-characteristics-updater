import sys
import time
import shutil
from pathlib import Path
from datetime import datetime
from loguru import logger
import atexit 

# внутреннее состояние для финализации
_file_sink_id = None
_local_log_path: Path | None = None
_net_log_path: str | None = None
_finalized = False


def _finalize_and_copy():
    """Один раз дописать «конец», закрыть локальный sink и (опц.) скопировать лог на сетевой путь."""
    global _finalized, _file_sink_id, _local_log_path, _net_log_path
    if _finalized:
        return
    try:
        logger.info("=" * 60)
        logger.info(f"=== КОНЕЦ СКРИПТА | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
        logger.info("=" * 60)
    except Exception:
        pass

    # дренируем очередь (актуально при enqueue=True) и закрываем файл
    try:
        logger.complete()
    except Exception:
        pass
    try:
        if _file_sink_id is not None:
            logger.remove(_file_sink_id)
    except Exception:
        pass

    # копируем локальный лог на сетевой путь (если задан)
    if _net_log_path and _local_log_path:
        dst = Path(_net_log_path)
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        last_err = None
        for attempt in range(3):
            try:
                shutil.copy2(str(_local_log_path), str(dst))
                last_err = None
                break
            except Exception as e:
                last_err = e
                if attempt < 2:
                    time.sleep(0.5 * (2 ** attempt))
        if last_err:
            print(f"[log] не удалось скопировать лог на сетевой диск: {last_err}", file=sys.stderr)

    _finalized = True


def setup_logger(log_filename, level_console="INFO", level_file="DEBUG", net_log_path: str | None = None):
    """
    Настраивает логгер: пишет в консоль и ЛОКАЛЬНЫЙ файл log_filename.
    В конце работы (atexit) локальный файл будет скопирован в net_log_path (если задан).
    """
    global _file_sink_id, _local_log_path, _net_log_path

    _local_log_path = Path(log_filename)
    _net_log_path = net_log_path

    logger.remove()

    # --- консольный sink только если stdout реально существует ---
    stdout = getattr(sys, "stdout", None)
    if stdout is not None:
        try:
            logger.add(stdout, level=level_console)
        except TypeError:
            # на всякий случай, если stdout какой-то странный
            pass
        
    # локальный файл: enqueue=True (фоновая запись), catch=True (не падать на ошибке sink)
    _file_sink_id = logger.add(str(_local_log_path), level=level_file, encoding="utf-8",
                               enqueue=True, catch=True)

    # === Старт скрипта ===
    logger.info("=" * 60)
    logger.info(f"=== СТАРТ СКРИПТА {_local_log_path.name} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    logger.info("=" * 60)

    # === Обработчик глобальных ошибок ===
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Закрываем и копируем даже при Ctrl+C
            _finalize_and_copy()
            # делегируем стандартному обработчику (для аккуратного newline и т.п.)
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # 1) логируем стек
        try:
            logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical("Uncaught exception")
        finally:
            # 2) СНАЧАЛА закрываем/копируем лог
            _finalize_and_copy()

        # 3) потом показываем пользователю паузу для скриншота
        try:
            sys.stderr.write(
                f"\n\nПроизошла непредвиденная ошибка.\n"
                f"Подробности сохранены в {_local_log_path}\n"
                f"Пожалуйста, сообщите об этом в поддержку.\n"
            )
            input("\nНажмите Enter чтобы закрыть программу...")
        except Exception:
            pass

        # 4) корректно выходим
        sys.exit(1)

    sys.excepthook = handle_exception

    # === Финализация при штатном выходе ===
    def log_script_end():
        _finalize_and_copy()

    atexit.register(log_script_end)

    return logger
