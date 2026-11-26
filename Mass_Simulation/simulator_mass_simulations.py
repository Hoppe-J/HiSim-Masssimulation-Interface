import hisim.hisim_main
from hisim.simulator import SimulationParameters
from hisim.postprocessingoptions import PostProcessingOptions
import os
import sys
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import shutil
import traceback
import logging
import time
from colorama import Fore, Style
from pathlib import Path
import cProfile
import pstats
import re
from threading import Event, Thread
from multiprocessing import Manager
import psutil


def progress_monitor(progress_dict, config_names, stop_events):
    """
    Überwacht den Fortschritt und gibt Text-Statusmeldungen auf der Konsole aus.
    Ersetzt die tqdm-Progressbars.
    """
    reported_completed = set()

    while True:
        all_stopped = True
        active_status_list = []

        for name in config_names:
            # Prüfen, ob eine Simulation gestoppt (fertig/abgebrochen) ist
            if stop_events[name].is_set():
                if name not in reported_completed:
                    # Einmalige Abschlussmeldung, springt in neue Zeile
                    sys.stdout.write(f"\nSimulation beendet: {name} (100%)\n")
                    reported_completed.add(name)
            else:
                all_stopped = False
                # Fortschritt holen
                prog = progress_dict.get(name, 0)
                if prog > 0:
                    active_status_list.append(f"{name}: {prog:.1f}%")

        if all_stopped:
            break

        # Statuszeile für laufende Simulationen (überschreibt sich selbst mit \r)
        if active_status_list:
            status_line = " | ".join(active_status_list)
            # Breite begrenzen, falls zu viele Configs, oder einfach ausgeben
            sys.stdout.write(f"\rLaufend: {status_line}")
            sys.stdout.flush()

        time.sleep(1)

    sys.stdout.write("\nAlle Simulationen abgeschlossen.\n")
    sys.stdout.flush()

def set_simulation_parameters(simulation_setup, path_simulation_directory, path_simulation_results, export_as_pkl_file):
    """Set up simulation parameters based on the provided configuration."""

    my_simulation_parameters = SimulationParameters(
        start_date=datetime.strptime(simulation_setup.start_date, "%Y-%m-%d"),
        end_date=datetime.strptime(simulation_setup.end_date, "%Y-%m-%d"),
        seconds_per_timestep=simulation_setup.seconds_per_timestep,
        logging_level=simulation_setup.logging_level,
        result_directory=path_simulation_results,
        cache_dir_path=path_simulation_directory
    )
    # Modify post-processing options
    my_simulation_parameters.multiple_buildings = True
    my_simulation_parameters.post_processing_options.extend([
        PostProcessingOptions.WRITE_CONFIGS_FOR_SCENARIO_EVALUATION_TO_JSON,
        PostProcessingOptions.WRITE_COMPONENT_CONFIGS_TO_JSON,
        PostProcessingOptions.EXPORT_RESULTS_IN_ONE_FILE,
        # PostProcessingOptions.MAKE_NETWORK_CHARTS,
        # PostProcessingOptions.GENERATE_PDF_REPORT,
        # PostProcessingOptions.WRITE_COMPONENTS_TO_REPORT,
        # PostProcessingOptions.INCLUDE_CONFIGS_IN_PDF_REPORT,
        #  PostProcessingOptions.PLOT_LINE,
        #  PostProcessingOptions.COMPUTE_OPEX,
        #  PostProcessingOptions.COMPUTE_CAPEX,
        #  PostProcessingOptions.COMPUTE_KPIS,
        #  PostProcessingOptions.WRITE_KPIS_TO_JSON,
    ])

    if export_as_pkl_file:
        my_simulation_parameters.post_processing_options.extend([
            PostProcessingOptions.EXPORT_TO_PKL,
        ])
    else:
        my_simulation_parameters.post_processing_options.extend([
            PostProcessingOptions.EXPORT_TO_CSV,
        ])

    return my_simulation_parameters

def run_simulation(path_to_district_file, simulation_parameters, config_json):
    """Run the simulation for the given parameters."""
    hisim.hisim_main.main(
        path_to_module=str(path_to_district_file),
        my_simulation_parameters=simulation_parameters,
        my_module_config=config_json
    )

def main_sim(path_simulation_directory, path_simulation_results, config, export_as_pkl_file):
    """Main function to run the simulation for a given config."""

    simulation_setup = config.simulation_setup
    simulation_parameters = set_simulation_parameters(simulation_setup, path_simulation_directory, path_simulation_results, export_as_pkl_file)

    config_json = config.to_json()

    # Path to the district model file
    current_dir = Path(__file__).resolve().parent
    base_path = current_dir.parent
    path_to_district_file = base_path / "Mass_Simulation" / "building_setup.py"

    # Run the simulation
    run_simulation(path_to_district_file, simulation_parameters, config_json)

    return simulation_parameters.result_directory

def execute_parallel_simulations(
        path_simulation_directory,
        path_simulation_results,
        config_list,
        delay_between_simulations=5,
        profiling_first_simulation=False,
        number_of_cpu_for_simulation=None,
        export_as_pkl_file=False):
    """Execute simulations for a list of configurations in parallel."""

    if not config_list:
        print("Keine Konfigurationen übergeben.")
        return
    number_of_configs = len(config_list)

    manager = Manager()
    progress_dict = manager.dict({config.config_name: 0 for config in config_list})

    stop_events = manager.dict({c.config_name: manager.Event() for c in config_list})

    monitor_thread = Thread(target=progress_monitor,
                            args=(progress_dict, [c.config_name for c in config_list], stop_events))

    monitor_thread.start()

    first_config = config_list[0]
    print("§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§")
    print(f"Starte erste Simulation (allein) für caching von relevanten Daten: {first_config.config_name}")
    try:
        run_simulation_wrapper(args=(path_simulation_directory, path_simulation_results, first_config, progress_dict, stop_events, number_of_configs, export_as_pkl_file), delay_time=0, enable_profiling=profiling_first_simulation)
    except Exception as e:
        print(f"{first_config.config_name} fehlgeschlagen — Abbruch. Fehler: {e}")

    print("§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§§")
    remaining_configs = config_list[1:]
    if not remaining_configs:
        print("Keine weiteren Simulationen zum Ausführen.")
        # Monitor thread beenden, falls nur eine Config existierte
        if monitor_thread.is_alive():
            monitor_thread.join()
        return

    remaining_configs_names_list = []
    for remaining_configs_names in remaining_configs:
        remaining_configs_names_list.append(remaining_configs_names.config_name)

    print(f"Starte restliche Simulationen parallel: {remaining_configs_names_list}")

    num_workers_max = max(1, os.cpu_count() - 2)
    num_workers = min(get_max_parallel_jobs(4), os.cpu_count() - 2)

    if number_of_cpu_for_simulation is None:
        number_of_cpu_for_simulation = num_workers_max
    elif number_of_cpu_for_simulation > num_workers_max:
        print(
            f"vorgebene number_of_cpu_for_simulation {number_of_cpu_for_simulation} ist größer als im system vorhandene Kerne {num_workers_max}")
        number_of_cpu_for_simulation = num_workers_max
    elif number_of_cpu_for_simulation < 1:
        print(f"vorgebene number_of_cpu_for_simulation {number_of_cpu_for_simulation} ist kleiner als 1, setze auf 1.")
        number_of_cpu_for_simulation = 1

    print(f"Anzahl Kerne für Simulation: {number_of_cpu_for_simulation}")

    args_list = [(path_simulation_directory, path_simulation_results, config, progress_dict, stop_events, number_of_configs, export_as_pkl_file) for i, config in enumerate(remaining_configs)]

    with ProcessPoolExecutor(max_workers=number_of_cpu_for_simulation) as executor:
        future_to_config = {
            executor.submit(run_simulation_wrapper, args, delay_between_simulations, enable_profiling=False): args[2]
            for args in args_list
        }
        for future in as_completed(future_to_config):
            config = future_to_config[future]

            try:
                future.result()
            except Exception:
                print(f"{config.config_name} fehlgeschlagen — Details siehe Logfile.")

    monitor_thread.join()

def get_log_file_path(path_simulation_directory, config_name):
    log_dir = Path(path_simulation_directory) / "Simulation_Logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / f"{config_name}.log"
    return log_file_path

def run_simulation_wrapper(args, delay_time, enable_profiling=False):
    path_simulation_directory, path_simulation_results, config, progress_dict, stop_events, number_of_configs, export_as_pkl_file = args
    time.sleep(delay_time)

    log_file_path = get_log_file_path(path_simulation_directory, config.config_name)

    file_handler, console_handler, monitor_logger = setup_logger(log_file_path, config.config_name, number_of_configs)

    stop_event = stop_events[config.config_name]
    progress_thread = Thread(target=monitor_progress_updater, args=(log_file_path, config.config_name, progress_dict, stop_event))
    progress_thread.start()

    try:
        logging.info(f"Simulation gestartet")

        if enable_profiling:
            profiler = start_profiler()

        result_directory = main_sim(path_simulation_directory, path_simulation_results, config, export_as_pkl_file)

        if enable_profiling:
            quit_profiler(profiler=profiler, path_simulation_directory=path_simulation_results, config_name=config.config_name)

        stop_event.set()
        progress_thread.join()
        close_monitor_logger(monitor_logger)

        logging.info(f"Simulation erfolgreich beendet und unter {result_directory} gespeichert.")

        wait_for_file_release(log_file_path)
        close_handlers(file_handler, console_handler)

        # Move log file to result folder
        if log_file_path.exists():
            new_log_file_path = Path(result_directory) / f"{config.config_name}.log"
            shutil.move(log_file_path, new_log_file_path)
    except Exception as e:
        stop_event.set()
        progress_thread.join()
        close_monitor_logger(monitor_logger)
        logging.error(f"Fehler bei Simulation '{config.config_name}': {e}")
        logging.error(traceback.format_exc())
        wait_for_file_release(log_file_path)
        close_handlers(file_handler, console_handler)
        raise e
    finally:
        stop_event.set()
        if progress_thread.is_alive():
            progress_thread.join()
        close_monitor_logger(monitor_logger)
        close_handlers(file_handler, console_handler)

def is_file_locked(file_path):
    """Überprüft, ob die Datei von einem anderen Prozess gesperrt ist."""
    try:
        # Versuche, die Datei im Lesemodus zu öffnen
        with open(file_path, 'r'):
            return False  # Die Datei ist nicht gesperrt
    except IOError:
        return True  # Datei ist gesperrt, wird von einem anderen Prozess verwendet

def wait_for_file_release(file_path, max_wait_time=300, check_interval=5):
    """Wartet, bis die Datei nicht mehr von einem anderen Prozess gesperrt ist."""
    wait_time = 0
    while is_file_locked(file_path):
        if wait_time > max_wait_time:
            raise TimeoutError(f"Die Datei '{file_path}' konnte nicht innerhalb der Wartezeit freigegeben werden.")
        time.sleep(check_interval)
        wait_time += check_interval
        logging.info(f"Warte auf Freigabe der Datei: {file_path} (Wartezeit: {wait_time}s)")
    logging.info(f"Die Datei '{file_path}' ist jetzt verfügbar.")

def setup_logger(log_file_path, config_name, number_of_configs):

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    formatter_file = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter_file)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter_console = logging.Formatter(f'{config_name} [%(levelname)s] %(message)s')
    console_handler.setFormatter(formatter_console)

    # Filter für Konsole — nur INFO und ERROR
    class InfoOrErrorFilter(logging.Filter):

        def filter(self, record):
            if record.levelno == logging.ERROR:
                record.msg = f"{Fore.RED}{record.msg}{Style.RESET_ALL}"
            elif record.levelno == logging.WARNING:
                record.msg = f"{Fore.YELLOW}{record.msg}{Style.RESET_ALL}"
            return record.levelno in (logging.INFO, logging.ERROR)

    console_handler.addFilter(InfoOrErrorFilter())

    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    monitor_logger = setup_monitor_logger(config_name)

    if number_of_configs > 3 and config_name != "Config_0":
        sys.stdout = open(log_file_path, 'a', encoding='utf-8', buffering=1)
        sys.stderr = sys.stdout

    return file_handler, console_handler, monitor_logger

def close_handlers(file_handler, console_handler):
    """Schließe die Handler explizit."""
    try:
        file_handler.close()
    except Exception as e:
        print(f"Fehler beim Schließen des file_handler: {e}")

    try:
        console_handler.close()
    except Exception as e:
        print(f"Fehler beim Schließen des console_handler: {e}")

    logging.shutdown()

    if sys.stdout != sys.__stdout__:
        try:
            sys.stdout.close()
        except Exception as e:
            print(f"Fehler beim Schließen von sys.stdout: {e}")
        sys.stdout = sys.__stdout__

    if sys.stderr != sys.__stderr__:
        try:
            sys.stderr.close()
        except Exception as e:
            print(f"Fehler beim Schließen von sys.stderr: {e}")
        sys.stderr = sys.__stderr__

    time.sleep(1)

def start_profiler():
    profiler = cProfile.Profile()
    profiler.enable()
    logging.info("starting profiling of simulation")
    return profiler

def quit_profiler(profiler, path_simulation_directory, config_name):
    profiler.disable()
    profiler_results_path = Path(path_simulation_directory) / "Profileroutputs"
    profiler_results_path.mkdir(parents=True, exist_ok=True)

    stats_path = profiler_results_path / f"profile_{config_name}.prof"
    profiler.dump_stats(stats_path)
    logging.info(f"Profiler-Daten gespeichert unter: {stats_path}")

def setup_monitor_logger(config_name):
    monitor_logger = logging.getLogger(f"{config_name}_monitor")
    monitor_logger.setLevel(logging.DEBUG)
    monitor_logger.propagate = False  # Verhindert Weitergabe an Root-Logger

    if not monitor_logger.handlers:
        monitor_console_handler = logging.StreamHandler(sys.stdout)
        monitor_formatter = logging.Formatter(f'{config_name} [MONITOR] %(message)s')
        monitor_console_handler.setFormatter(monitor_formatter)
        monitor_logger.addHandler(monitor_console_handler)

    return monitor_logger

def close_monitor_logger(monitor_logger):
    handlers = monitor_logger.handlers[:]
    for handler in handlers:
        try:
            handler.flush()
            handler.close()
        except Exception as e:
            print(f"Fehler beim Schließen von Monitor-Handler: {e}")
        monitor_logger.removeHandler(handler)

def parse_progress_from_line(line):
    # ANSI-Farbcodes entfernen
    clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
    match = re.search(r'Simulating\.\.\.\s*([\d.]+)\s*%', clean_line)
    if match:
        return round(float(match.group(1)), 2)
    return None

def monitor_progress_updater(log_file_path, config_name, progress_dict, stop_event):
    with open(log_file_path, 'r', encoding='utf-8') as f:
        f.seek(0, os.SEEK_END)  # Am Ende der Datei starten
        last_progress = 0
        while True:
            if stop_event.is_set():
                break
            line = f.readline()
            if not line:
                time.sleep(1)
                continue
            progress = parse_progress_from_line(line)
            if progress is not None:
                last_progress = progress
                progress_dict[config_name] = progress

def get_max_parallel_jobs(ram_per_job_gb=4):
    total_gb = psutil.virtual_memory().total / (1024**3)
    return max(1, int(total_gb // ram_per_job_gb))