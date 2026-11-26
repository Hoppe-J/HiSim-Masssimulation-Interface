from pathlib import Path
import json

from Mass_Simulation.simulator_mass_simulations import execute_parallel_simulations
from Mass_Simulation.modular_config_parser import (
    read_in_configs,
)

def main():

    current_dir = Path(__file__).resolve().parent

    scenarios_for_simulations_dir = Path(current_dir / "simulation_config_files")

    config_list_paths = sorted(scenarios_for_simulations_dir.rglob("config_list.json"))

    all_configs = []

    for config_list_path in config_list_paths:
        with config_list_path.open("r", encoding="utf-8") as f:
            config_list_data = json.load(f)
        if isinstance(config_list_data, list):
            entries = config_list_data
        elif isinstance(config_list_data, dict):
            entries = config_list_data.get("configs", [])
        else:
            entries = []

        for d in entries:
            loaded = read_in_configs(d)
            if isinstance(loaded, list):
                all_configs.extend(loaded)
            else:
                all_configs.append(loaded)

    num_workers = 1  # max(1, os.cpu_count())

    execute_parallel_simulations(
        path_simulation_directory=current_dir,
        path_simulation_results=current_dir,
        config_list=all_configs,
        delay_between_simulations=5,
        number_of_cpu_for_simulation=num_workers,
        export_as_pkl_file=False)


if __name__ == "__main__":
    main()