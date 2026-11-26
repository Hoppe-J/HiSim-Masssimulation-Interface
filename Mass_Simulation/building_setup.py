from dataclasses import dataclass, fields, field
from dataclasses_json import dataclass_json
from typing import Optional, Any
import shutil
from pathlib import Path
import os
import datetime

from hisim.simulator import SimulationParameters
from hisim.components import weather
from hisim.components.weather import WeatherDataSourceEnum
from hisim.sim_repository_singleton import SingletonSimRepository, SingletonDictKeyEnum
from hisim.postprocessingoptions import PostProcessingOptions
from hisim import loadtypes
from hisim import utils, log
from hisim.components.weather_data_import import WeatherDataImport
from hisim.result_path_provider import ResultPathProviderSingleton, SortingOptionEnum
from hisim.component import ConfigBase

from Models.Gebaude import generic_building

@dataclass_json
@dataclass
class BuildingSetup(ConfigBase):
    """Configuration for District."""

    def __setattr__(self, name, value):
        valid_fields = {f.name for f in fields(self)}
        if name not in valid_fields:
            raise AttributeError(f"'{name}' ist kein gültiges Feld von DistrictSetup")
        super().__setattr__(name, value)

    building_name: Optional[str] = "Default"
    name: Optional[str] = "Default"

    location_quartier: str = "HAMBURG"
    latitude_quartier: float = 53.5299
    longitude_quartier: float = 10.0078

    weather_data_source_quartier: str = "DWD_TRY"
    weather_filename_if_try_or_nsrdb_quartier: str = "TRY_WEATHER_HAMBURG"
    weather_predictive_control_quartier: bool = True
    weather_distance_weatherstations_quartier: int = 30

    @classmethod
    def get_default(cls, building_name=loadtypes.DistrictNames.QUARTIER.value):
        """Get default BuildingPVConfig."""

        return BuildingSetup(
            name="default",
            building_name=building_name,
            location_quartier="AACHEN",
            latitude_quartier=50.775,
            longitude_quartier=6.083,
            weather_data_source_quartier=WeatherDataSourceEnum.DWD_10MIN,
            weather_filename_if_try_or_nsrdb_quartier= "TRY_WEATHER_HAMBURG",
            weather_predictive_control_quartier=True,
            weather_distance_weatherstations_quartier=30,
        )

def setup_function(my_sim: Any, my_simulation_parameters: Optional[SimulationParameters] = None) -> None:  # noqa: too-many-statements
    from Mass_Simulation.modular_config_parser import read_in_configs

    config_filename = my_sim.my_module_config

    if isinstance(config_filename, str):
        config = read_in_configs(config_filename)  # type: ignore
    else:
        raise ValueError("No module config path from the simulator was given. Use default config.")

    config_name = config.config_name
    simulation_setup = config.simulation_setup
    district_config = config.district_setup
    buildings_setup = config.buildings_setup

    hisim_logging_level = my_simulation_parameters.logging_level

    pfad_result_directory = my_simulation_parameters.result_directory
    post_processing_options = my_simulation_parameters.post_processing_options
    ergebnis_ordner_name = simulation_setup.result_directory_name
    further_result_folder_description = simulation_setup.further_result_folder_description
    variante_simulation = simulation_setup.variante_simulation
    scenario_hash_string = config_name
    result_folder_sorting_option = SortingOptionEnum[simulation_setup.result_folder_sorting_option]

    current_dir = Path(__file__).resolve().parent

    if simulation_setup.path_to_weather_directory is None:
        path_to_weather_directory = str(
            current_dir.parents[1] / "weather_data")

    else:
        path_to_weather_directory = simulation_setup.path_to_weather_directory

    if simulation_setup.path_to_cache_directory is None:
        path_to_cache_directory = str(
                current_dir.parents[1] / "simulation_cache")
    else:
        path_to_cache_directory = simulation_setup.path_to_cache_directory

    path_simulation_directory = my_simulation_parameters.cache_dir_path

    if path_to_cache_directory is None:
        cache_dir_path_simuparams = os.path.join(pfad_result_directory,"inputs", "inputs_cache")
    else:
        cache_dir_path_simuparams = path_to_cache_directory

    if not os.path.exists(cache_dir_path_simuparams):
        os.makedirs(cache_dir_path_simuparams)

    ResultPathProviderSingleton().set_important_result_path_information(
        module_directory=pfad_result_directory,
        model_name=ergebnis_ordner_name,
        further_result_folder_description=further_result_folder_description,
        variant_name=variante_simulation,
        scenario_hash_string=scenario_hash_string,
        sorting_option=result_folder_sorting_option,
    )

    pfad_result_directory = ResultPathProviderSingleton().get_result_directory_name()

    # Überprüfen, ob der Verzeichnispfad existiert
    if not os.path.exists(pfad_result_directory):
        # Wenn nicht, erstelle das Verzeichnis
        os.makedirs(pfad_result_directory)
        print(f"Das Verzeichnis {pfad_result_directory} wurde erstellt.")
    else:
        print(f"Das Verzeichnis {pfad_result_directory} existiert bereits.")
        # Überprüfen, ob das Verzeichnis nicht leer ist
        if os.listdir(pfad_result_directory) and not hisim_logging_level == 4:
            finished_flag_file = os.path.join(pfad_result_directory, "finished.flag")
            if os.path.exists(finished_flag_file):
                # Falls finished.flag existiert → Simulation abgeschlossen → abbrechen
                raise KeyError(
                    f"Der Resultpfad Ordner {pfad_result_directory} enthält bereits Daten und finished.flag ist vorhanden.")
            else:
                print(
                    f"Achtung: {pfad_result_directory} enthält bereits Daten, aber keine finished.flag – es wird fortgesetzt.")
        elif os.listdir(pfad_result_directory) and hisim_logging_level == 4:
            # Nachfrage im Terminal für Bestätigung
            response = input(
                f"HISIM LOGGING LEVEL: DEBUG MODUS: Der Resultpfad Ordner {pfad_result_directory} enthält bereits Daten. Möchten Sie diese überschreiben? (j/n): ")
            if response.lower() == 'j':
                print("Daten werden überschrieben.")
            else:
                raise KeyError("Überschreiben abgebrochen.")
        else:
            print(f"Das Verzeichnis {pfad_result_directory} ist leer und wird als result Ordner verwendet.")

    if my_simulation_parameters is None:
        my_simulation_parameters = SimulationParameters(
            start_date=datetime.datetime(2020, 1, 1),
            end_date=datetime.datetime(2021, 1, 1),
            seconds_per_timestep=900,
            post_processing_options=post_processing_options,
            logging_level=hisim_logging_level,
        )

    my_simulation_parameters.result_directory = pfad_result_directory
    my_simulation_parameters.cache_dir_path = cache_dir_path_simuparams
    my_simulation_parameters.multiple_buildings = True
    my_simulation_parameters.post_processing_options.extend([
        PostProcessingOptions.WRITE_CONFIGS_FOR_SCENARIO_EVALUATION_TO_JSON,
        PostProcessingOptions.WRITE_COMPONENT_CONFIGS_TO_JSON,
    ])
    if not any(opt in my_simulation_parameters.post_processing_options for opt in [
        PostProcessingOptions.EXPORT_TO_CSV,
        PostProcessingOptions.EXPORT_TO_PKL
    ]):
        my_simulation_parameters.post_processing_options.extend([PostProcessingOptions.EXPORT_TO_CSV])

    my_sim.set_simulation_parameters(my_simulation_parameters)

    # =================================================================================================================================
    # SETUP
    district_name = loadtypes.DistrictNames[simulation_setup.district_name.upper()].value

    district_config.building_name = district_name
    district_config.name = district_name

    read_me = simulation_setup.read_me
    location_quartier = district_config.location_quartier
    latitude_quartier = district_config.latitude_quartier
    longitude_quartier = district_config.longitude_quartier

    weather_data_source_quartier = WeatherDataSourceEnum[district_config.weather_data_source_quartier]
    weather_filename_if_try_or_nsrdb_quartier = district_config.weather_filename_if_try_or_nsrdb_quartier
    weather_predictive_control_quartier = district_config.weather_predictive_control_quartier
    weather_distance_weatherstations_quartier = district_config.weather_distance_weatherstations_quartier
    start_geb = simulation_setup.start_geb
    end_geb = simulation_setup.end_geb

    # =================================================================================================================================
    # Erstellen von Gebäuden
    # =================================================================================================================================

    district_list_bui_names = []
    for i in range(start_geb, end_geb + 1):
        district_list_bui_names.append("Bui" + str(i))

    # =================================================================================================================================
    # Ordner Erstellen Analog zu Scenarien Analyse
    # =================================================================================================================================

    # für scenario analyse
    SingletonSimRepository().set_entry(
        key=SingletonDictKeyEnum.RESULT_SCENARIO_NAME, entry=f"{scenario_hash_string}",
    )

    my_sim.my_module_config = {elem: {} for elem in district_list_bui_names}
    my_sim.my_module_config.update({district_name: {}})

    my_sim.my_module_config[district_name] = district_config.to_dict()

    # =================================================================================================================================
    # ReadMe erstellen
    # =================================================================================================================================
    read_me_path=os.path.join(pfad_result_directory,"00_readme.txt")
    with open(read_me_path, 'w', encoding='utf-8') as datei:
        datei.write(read_me)
    print(f"INFO: README-Datei wurde erfolgreich erstellt unter: {pfad_result_directory}")


    # =================================================================================================================================
    # Import von Input Daten
    # =================================================================================================================================
    pfad_zu_input_ordner = os.path.join(path_simulation_directory, "inputs")

    # =================================================================================================================================
    # Build Weather building_setup
    # =================================================================================================================================
    if weather_data_source_quartier == WeatherDataSourceEnum.DWD_TRY or weather_data_source_quartier == WeatherDataSourceEnum.NSRDB or weather_data_source_quartier ==WeatherDataSourceEnum.NSRDB_15MIN:
        data_format = [".csv", ".dat"]
        if weather_filename_if_try_or_nsrdb_quartier.endswith(data_format[0]):
            weather_filename_if_try_or_nsrdb_quartier_without_format =  weather_filename_if_try_or_nsrdb_quartier[:-4]
        elif weather_filename_if_try_or_nsrdb_quartier.endswith(data_format[1]):
            weather_filename_if_try_or_nsrdb_quartier_without_format =  weather_filename_if_try_or_nsrdb_quartier[:-4]
        else:
            weather_filename_if_try_or_nsrdb_quartier_without_format =  weather_filename_if_try_or_nsrdb_quartier

        if weather_data_source_quartier == WeatherDataSourceEnum.DWD_TRY:
            subfolder = os.path.join("weather", "test-reference-years_2015-2045", "data_processed")
        elif weather_data_source_quartier == WeatherDataSourceEnum.NSRDB_15MIN:
            subfolder = os.path.join("weather", "NSRDB_15min")
        elif weather_data_source_quartier == WeatherDataSourceEnum.NSRDB:
            subfolder = os.path.join("weather", "NSRDB")
        else:
            raise KeyError("Fehlerhafte Wetterdatenquelle für building_setup: Ungültige Wetterdatenquelle.")

        for format in data_format:
            # Pfad im Cache
            cache_weather_path = os.path.join(path_to_weather_directory, subfolder,
                                              weather_filename_if_try_or_nsrdb_quartier_without_format + format)
            cache_weather_path_without_format = os.path.join(path_to_weather_directory, subfolder,
                                              weather_filename_if_try_or_nsrdb_quartier_without_format)
            # Pfad im Input-Ordner
            input_weather_path = os.path.join(pfad_zu_input_ordner, subfolder,
                                              weather_filename_if_try_or_nsrdb_quartier_without_format + format)

            # Prüfen ob Datei im Cache existiert
            if os.path.exists(cache_weather_path):
                break

            elif os.path.exists(input_weather_path):
                # Datei im Input Ordner gefunden -> in Cache verschieben (inkl. Unterordner anlegen)
                os.makedirs(os.path.dirname(cache_weather_path), exist_ok=True)
                shutil.move(input_weather_path, cache_weather_path)
                break
        else:
            raise FileNotFoundError(
                f"Wetterdatei {weather_filename_if_try_or_nsrdb_quartier_without_format} weder im Cache {cache_weather_path} noch im Input-Ordner {input_weather_path} gefunden.")

        my_weather_config_quartier = weather.WeatherConfig(
            building_name=district_name,
            name="Weather",
            location=location_quartier,
            source_path=cache_weather_path_without_format,
            data_source=weather_data_source_quartier,
            predictive_control=True,#weather_predictive_control_quartier,
        )
    elif weather_data_source_quartier == WeatherDataSourceEnum.DWD_10MIN or weather_data_source_quartier == WeatherDataSourceEnum.DWD_15MIN or weather_data_source_quartier == WeatherDataSourceEnum.ERA5:
        my_weather_data_quartier = WeatherDataImport(start_date=my_simulation_parameters.start_date,
                                                     end_date=my_simulation_parameters.end_date,
                                                     location=location_quartier,
                                                     latitude=latitude_quartier,
                                                     longitude=longitude_quartier,
                                                     distance_weather_stations=weather_distance_weatherstations_quartier,
                                                     path_input_folder=path_to_weather_directory,
                                                     weather_data_source=weather_data_source_quartier)
        # funktion ruft daten vom dwd/era5 ab, speichert als csv und gibt pfad zur csv zurück
        my_weather_config_quartier = weather.WeatherConfig(
            building_name=district_name,
            # nur für eigene Wetterdaten, sonst unten config nutzen und normal csv oder try über wettermodell einbinden
            name="Weather",
            location=location_quartier,
            source_path=my_weather_data_quartier.csv_path,
            data_source=weather_data_source_quartier,
            predictive_control=True,#weather_predictive_control_quartier,
        )
    else:
        raise KeyError("Fehlerhafte Wetterdatenquelle für building_setup: Derzeit nur DWD_TRY, NSRDB, NSRDB_15MIN, DWD_10MIN und ERA5 möglich")

    my_weather_quartier = weather.Weather(config=my_weather_config_quartier, my_simulation_parameters=my_simulation_parameters)
    my_sim.add_component(my_weather_quartier)

    # für scenarien analyse
    SingletonSimRepository().set_entry(key=SingletonDictKeyEnum.LOCATION, entry=my_weather_config_quartier.location)

    # =================================================================================================================================
    #Löschen alter Lastproile die mit LPG erzeugt wurden
    # =================================================================================================================================
    # cleanup old lpg requests, mandatory to change number of cars
    """HINWEIS: LPG Results werden in path_simulation_directory (Ergebnis Ordner) gespeichert und in originalen HiSim result Ordner KOPIERT
     alte LPG-Ergebnisse in path_simulation_directory werden über Generic_Building Modell aus Ordner gelöscht
      hier wird original HiSim result ordner geleert 
      --> wird so gemacht, damit originales car modell genutzt werden kann, welches auf Fahrprofile in oroiginalen hisim pfad referenziert"""

    if os.path.exists(utils.HISIMPATH["utsp_results"]):
        files_in_folder = os.listdir(utils.HISIMPATH["utsp_results"])
        for file in files_in_folder:
            full_path = os.path.join(utils.HISIMPATH["utsp_results"], file)
            os.remove(full_path)
            print("INFO: HiSim original LPG Result Ordner wird für neue Simulation gelöscht ")

    # =================================================================================================================================
    # Build building_setup Gebäude
    # =================================================================================================================================

    building_names_with_config = (list(buildings_setup.keys()))

    missing_buildings_in_config_list = [bui for bui in district_list_bui_names if bui not in building_names_with_config]

    if missing_buildings_in_config_list:
        raise KeyError(f"Fehler: Folgende Gebäude fehlen in buildings_setups: {missing_buildings_in_config_list}")

    print("INFO: Anzahl der Geb. im building_setup: " + str(len(district_list_bui_names)))

    geb_config = generic_building.Generic_Building_Config.get_default_generic_building_config()
    district_list = []

    for i in range(len(district_list_bui_names)):
        building_name = district_list_bui_names[i]

        print("INFO: ------------------------ Parametrierung von " + str(
            building_name) + "------------------------")
        single_building_config = buildings_setup[building_name]

      #  for components_configs in single_building_config:
        for parameter, wert in vars(single_building_config).items():
            if hasattr(geb_config, parameter):
                aktueller_wert = getattr(geb_config, parameter)
                if aktueller_wert != wert:
                    setattr(geb_config, parameter, wert)

        district_list.append(generic_building.Generic_Building(my_sim=my_sim,
                                                               my_simulation_parameters=my_simulation_parameters,
                                                               path_simulation_directory=path_simulation_directory,
                                                               my_weather=my_weather_quartier,
                                                               config=geb_config,
                                                               location=location_quartier,
                                                               district_name=district_name,
                                                               config_name=config_name))

        district_list[i].generic_building()
