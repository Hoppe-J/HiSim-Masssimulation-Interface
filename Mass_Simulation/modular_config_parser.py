"""Modular household config module."""

# clean
from pathlib import Path
from typing import Optional, Dict, Union
from enum import Enum
from dataclasses import is_dataclass, asdict, fields
from types import MappingProxyType
import json
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from hisim import log
from hisim.system_setup_configuration import SystemSetupConfigBase

from Mass_Simulation.building_setup import BuildingSetup
from Models.Gebaude.generic_building import Generic_Building_Config

@dataclass_json
@dataclass
class SimulationSetup:
    """Configuration of simulation."""
    def __setattr__(self, name, value):
        valid_fields = {f.name for f in fields(self)}
        if name not in valid_fields:
            raise AttributeError(f"'{name}' ist kein gültiges Feld von SimulationSetup")
        super().__setattr__(name, value)
    district_name: str = "District"
    start_geb: int = 1
    end_geb: int = 1
    start_date: str = "2023-01-01"
    end_date: str = "2024-01-01"
    seconds_per_timestep: int = 900
    logging_level: int = 3
    result_directory_name: str = "results"
    further_result_folder_description: str = ""
    variante_simulation: str = ""
    result_folder_sorting_option: str = "MASS_SIMULATION_WITH_HASH_ENUMERATION"
    path_to_weather_directory: Optional[str] = None
    path_to_cache_directory: Optional[str] = None

    read_me: str = "readme in class"


@dataclass_json
@dataclass
class ModularConfig(SystemSetupConfigBase):

    """Modular district Config class."""

    config_name: Optional[str] = None
    simulation_setup: Optional[SimulationSetup] = None
    buildings_setup: Optional[Dict[str, Generic_Building_Config]] = None
    district_setup: Optional[BuildingSetup] = None

    @classmethod
    def get_default_config_for_district(cls):
        """Get default ModularHouseholdConfig."""
        config_name = "Config_1"
        simulation_setup = SimulationSetup()
        buildings_setup = Generic_Building_Config.get_default_generic_building_config()
        district_setup = BuildingSetup.get_default()

        district_config = ModularConfig(
            config_name=config_name,
            simulation_setup=simulation_setup,
            buildings_setup=buildings_setup,
            district_setup=district_setup,
        )
        return district_config

def write_configs_to_json(config_list,config_list_file ):
    """Writes config."""

    config_list_dicts = []

    for config in config_list:
        # Wandelt jedes Config-Objekt in ein JSON-kompatibles Dictionary um
        serializable_dict = make_json_serializable(config.to_dict())
        config_list_dicts.append(serializable_dict)

    # Speichert die Liste von Dictionaries in einer JSON-Datei
    with open(config_list_file, "w", encoding="utf-8") as file:
        json.dump(config_list_dicts, file, indent=4, ensure_ascii=False)

def read_in_configs(config_input: Union[str, dict]) -> ModularConfig:
    """
    Reads in ModularDistrictConfig from:
    - a file path (str or Path)
    - a JSON string
    - a dict
    """
    district_config: Optional[ModularConfig] = None

    # Wenn dict direkt übergeben wird
    if isinstance(config_input, dict):
        config_input_fixed = fix_types(config_input)
        district_config = ModularConfig.from_dict(config_input_fixed)

    # Wenn string übergeben wird
    elif isinstance(config_input, str):
        config_str = config_input.strip()

        # JSON-String erkannt
        if config_str.startswith("{"):
            district_config = ModularConfig.from_json(config_str)

        # Pfad erkannt
        else:
            config_path = Path(config_str)
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")
            with config_path.open(encoding="utf8") as f:
                district_config_dict = json.load(f)
                district_config = ModularConfig.from_dict(district_config_dict)

    else:
        raise TypeError("config_input must be a dict, JSON string, or file path (str/Path)")

    # Validierung
    if (district_config.simulation_setup is None or
        district_config.buildings_setup is None or
        district_config.district_setup is None):
        raise ValueError("Energy system or simulation setup are None.")

    log.information(f"Read modular district config from {district_config.config_name}")
    return district_config

def make_json_serializable(obj, seen=None):
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return None  # oder str(obj) für Debug, aber nicht für int/float/bool

    # Basis-Typen sofort zurückgeben
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj

    seen.add(obj_id)
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    elif isinstance(obj, MappingProxyType):
        return make_json_serializable(dict(obj), seen)
    elif isinstance(obj, dict):
        return {key: make_json_serializable(value, seen) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item, seen) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(make_json_serializable(item, seen) for item in obj)
    elif isinstance(obj, set):
        return [make_json_serializable(item, seen) for item in obj]
    elif is_dataclass(obj):
        return make_json_serializable(asdict(obj), seen)
    elif isinstance(obj, Enum):
        return obj.name
    elif hasattr(obj, "__dict__"):
        return make_json_serializable(vars(obj), seen)
    else:
        return str(obj)  # Fallback für alles andere

def fix_types(obj):
    if isinstance(obj, dict):
        return {k: fix_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fix_types(v) for v in obj]
    elif obj == "None":
        return None
    elif obj == "False":
        return False
    elif obj == "True":
        return True
    else:
        return obj

