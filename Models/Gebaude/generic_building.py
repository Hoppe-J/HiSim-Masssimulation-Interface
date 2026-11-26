"""
Universelles Gebäude Modell mit allen "typischen" Komponenten

OHNE Kühlung derzeit

SIEHE BILD zu "generic_building_system" für Aufbau

"""
from hisim.components import more_advanced_heat_pump_hplib
from hisim.components import heat_distribution_system
from hisim.components import building
from hisim.components import simple_water_storage
#from hisim.components import simple_dhw_storage
from hisim.components import generic_pv_system
from hisim.components import advanced_battery_bslib
from hisim.components import controller_l2_district_energy_management_system
from hisim.components import electricity_meter
from hisim.components import generic_car
from hisim.components import advanced_ev_battery_bslib
from hisim.components import controller_l1_generic_ev_charge
from hisim.components import loadprofilegenerator_utsp_connector
from hisim.components import heating_meter
from hisim.components import simple_heat_source
from hisim.components import solar_thermal_system
from hisim.components import generic_boiler
from hisim.components import gas_meter
from hisim.components.generic_boiler import BoilerType
from hisim.components.loadprofilegenerator_utsp_connector import LpgDataAcquisitionMode
from hisim import loadtypes
from hisim import loadtypes as lt
from hisim import component as cp
from hisim.component import (ConfigBase,
                             DisplayConfig,
                             Coordinates,)
from dataclasses import dataclass, fields
from dataclasses_json import dataclass_json

from utspclient.helpers.lpgdata import (
    ChargingStationSets,
    Households,
    TransportationDeviceSets,
    TravelRouteSets,
    EnergyIntensityType,
)

import os
import re
import enum
from pathlib import Path
from typing import List, Optional, Any, Union

import pygfunction as gt

from ..Erdsonde import borehole_heat_exchanger


class Conventional_Fuel(enum.Enum):
    """Heat sources."""
    GAS = "GAS"
    GREEN_HYDROGEN = "GREEN_HYDROGEN"
    OXYGEN = "OXYGEN"
    DIESEL = "DIESEL"
    OIL = "OIL"
    PELLETS = "PELLETS"
    WOOD_CHIPS = "WOOD_CHIPS"
    DISTRICTHEATING = "DISTRICTHEATING"

class Solar_Thermal_Collector_Type(enum.Enum):
    """Heat sources."""
    FLAT_PLATE = "FLAT_PLATE"
    VACUUM_TUBE = "VACUUM_TUBE"

class Heat_Source_For_Brine_Heat_Pumps(enum.Enum):
    """Heat sources."""

    CONSTANT_THERMAL_POWER = "CONSTANT_THERMAL_POWER"
    CONSTANT_TEMPERATURE = "CONSTANT_TEMPERATURE"
    NEAR_SURFACE_BRINE_TEMPERATURE = "NEAR_SURFACE_BRINE_TEMPERATURE"
    GROUND_PROBE = "GROUND_PROBE"
    DISTRICT_HEATING = "DISTRICT_HEATING"

@dataclass_json
@dataclass
class Generic_Building_Config(ConfigBase):

    """Generic Building Config Class"""

    @classmethod
    def get_main_classname(cls):
        """Returns the full class name of the base class."""
        return Generic_Building.get_full_classname()

    def __setattr__(self, name, value):
        valid_fields = {f.name for f in fields(self)}
        if name not in valid_fields:
            raise AttributeError(f"'{name}' ist kein gültiges Feld von Generic_Building_Config")
        super().__setattr__(name, value)

    name: str
    building_name:str

    ethos_builda_dev_client: Optional[bool]
    ethos_builda_id: Optional[str]
    ethos_builda_address: Optional[dict]
    ethos_builda_construction_year: Optional[int]
    ethos_builda_roof_geometry: Optional[list[dict]]

    building_latitude: Union[float,None]
    building_longitude: Union[float, None]

    building_existing: bool
    building_code:str
    building_heat_capacity_class:str
    building_initial_internal_temperature_in_celsius: float
    building_heating_reference_temperature_in_celsius: float
    building_absolute_conditioned_floor_area_in_m2:float
    building_number_of_apartments:int
    building_predictive_control: bool
    building_enable_opening_windows: bool
    building_floor_u_value_in_watt_per_m2_per_kelvin: Optional[float]
    building_floor_area_in_m2: Optional[float]
    building_facade_u_value_in_watt_per_m2_per_kelvin: Optional[float]
    building_facade_area_in_m2: Optional[float]
    building_roof_u_value_in_watt_per_m2_per_kelvin: Optional[float]
    building_roof_area_in_m2: Optional[float]
    building_window_u_value_in_watt_per_m2_per_kelvin: Optional[float]
    building_window_area_in_m2: Optional[float]
    building_door_u_value_in_watt_per_m2_per_kelvin: Optional[float]
    building_door_area_in_m2: Optional[float]
    building_window_co2_footprint: Optional[float]
    building_window_cost: Optional[float]
    building_window_lifetime: Optional[float]
    building_window_maintenance_cost_as_percentage_of_investment: Optional[float]
    building_window_maintenance_costs_in_euro_per_year: Optional[float]
    building_roof_co2_footprint: Optional[float]
    building_roof_cost: Optional[float]
    building_roof_lifetime: Optional[float]
    building_roof_maintenance_cost_as_percentage_of_investment: Optional[float]
    building_roof_maintenance_costs_in_euro_per_year: Optional[float]
    building_floor_co2_footprint: Optional[float]
    building_floor_cost: Optional[float]
    building_floor_lifetime: Optional[float]
    building_floor_maintenance_cost_as_percentage_of_investment: Optional[float]
    building_floor_maintenance_costs_in_euro_per_year: Optional[float]
    building_facade_co2_footprint: Optional[float]
    building_facade_cost: Optional[float]
    building_facade_lifetime: Optional[float]
    building_facade_maintenance_cost_as_percentage_of_investment: Optional[float]
    building_facade_maintenance_costs_in_euro_per_year: Optional[float]
    building_door_co2_footprint: Optional[float]
    building_door_cost: Optional[float]
    building_door_lifetime: Optional[float]
    building_door_maintenance_cost_as_percentage_of_investment: Optional[float]
    building_door_maintenance_costs_in_euro_per_year: Optional[float]

    heat_distribution_system_existing: bool
    heat_distribution_system_heating_system:int
    heat_distribution_system_nominal_water_mass_flow_rate_in_kg_per_second:float
    heat_distribution_system_set_heating_threshold_outside_temperature_in_celsius:float
    heat_distribution_system_set_cooling_threshold_outside_temperature_in_celsius: float
    heat_distribution_system_heating_reference_temperature_in_celsius:float
    heat_distribution_system_set_heating_temperature_for_building_in_celsius:float
    heat_distribution_system_set_cooling_temperature_for_building_in_celsius:float
    heat_distribution_system_co2_footprint: float
    heat_distribution_system_cost: float
    heat_distribution_system_lifetime: float
    heat_distribution_system_maintenance_costs_in_euro_per_year:float
    heat_distribution_system_maintenance_cost_as_percentage_of_investment: float

    sh_storage_existing:bool
    sh_storage_volume_in_liter:float
    sh_storage_position: int
    sh_storage_heat_transfer_coefficient_in_watt_per_m2_per_kelvin:float
    sh_storage_heat_exchanger_is_present:bool
    sh_storage_co2_footprint: float
    sh_storage_cost: float
    sh_storage_lifetime: float
    sh_storage_maintenance_cost_as_percentage_of_investment: float
    sh_storage_maintenance_costs_in_euro_per_year: float

    dhw_storage_existing:bool
    dhw_storage_t_min_in_celsius: float
    dhw_storage_t_max_in_celsius: float
    dhw_storage_freshwater_temperature: float
    dhw_storage_ww_temperature_demand: float
    dhw_storage_volume_in_liter: float
    dhw_storage_heat_transfer_coefficient_in_watt_per_m2_per_kelvin: float
    dhw_storage_co2_footprint: float
    dhw_storage_cost: float
    dhw_storage_lifetime: float
    dhw_storage_maintenance_cost_as_percentage_of_investment: float
    dhw_storage_maintenance_costs_in_euro_per_year: float

    loadprofile_existing: bool
    loadprofile_data_acquisition_mode: str
    loadprofile_household_utsp: Optional[str]#Union[JsonReference, List[JsonReference]]
    loadprofile_number_of_persons: Optional[int]
    loadprofile_energy_intensity_utsp: Optional[str]#EnergyIntensityType
    loadprofile_travel_route_set_utsp: Optional[str]#JsonReference
    loadprofile_transportation_device_set_utsp: Optional[str]#JsonReference
    loadprofile_charging_station_set_utsp: Optional[str]#JsonReference
    loadprofile_profile_with_washing_machine_and_dishwasher_utsp: bool
    loadprofile_predictive_control_utsp: bool
    loadprofile_predefined_profile_name:Optional[str]
    loadprofile_predefined_loadprofile_filepaths:Optional[Union[str, Path]]
    loadprofile_predictive_occupancy:Optional[bool]

    heatpump_existing:bool
    heatpump_spaceheating_mode: int
    heatpump_thermalPower_is_constant_for_dhw:bool
    heatpump_p_th_max_dhw_in_watt:float
    heatpump_model:str
    heatpump_fluid_primary_side: str
    heatpump_heat_source_if_not_air: Optional[str]
    heatpump_minimum_running_time_in_seconds:int
    heatpump_minimum_idle_time_in_seconds:int
    heatpump_group_id: int
    heatpump_heating_reference_temperature_in_celsius: float
    heatpump_flow_temperature_in_celsius: float
    heatpump_set_thermal_output_power_in_watt: float
    heatpump_cycling_mode: bool
    heatpump_massflow_nominal_secondary_in_kg_per_s:float
    heatpump_minimum_thermal_output_power_in_watt: float
    heatpump_massflow_nominal_primary_side_in_kg_per_s: Optional[float]
    heatpump_upper_temperature_offset_for_state_conditions_in_celsius:float
    heatpump_lower_temperature_offset_for_state_conditions_in_celsius: float
    heatpump_with_domestic_hot_water_preparation: bool
    heatpump_passive_cooling_with_brine: bool
    heatpump_electrical_input_power_brine_pump_in_watt: float
    heatpump_for_dhw_is_indoor: bool
    heatpump_with_space_heating: bool
    heatpump_co2_footprint: float
    heatpump_cost: float
    heatpump_lifetime: float
    heatpump_maintenance_cost_as_percentage_of_investment: float
    heatpump_maintenance_costs_in_euro_per_year: float

    heatpump_heat_source_fluid_type_primary_side: str
    heatpump_heat_source_mass_fraction_of_fluid_mixed_in_water: float
    heatpump_heat_source_fluid_primary_side_specific_heat_capacity: float

    simple_heatsource_const_value_of_const_heat_source: Optional[
        float]  # Wert aus Eingabeexcel wird hier zwischen gespeichert und in Quartiermodell aufgerufen
    simple_heatsource_co2_footprint: float
    simple_heatsource_cost: float
    simple_heatsource_lifetime: float
    simple_heatsource_maintenance_cost_as_percentage_of_investment: float
    simple_heatsource_maintenance_costs_in_euro_per_year:float

    ground_probe_sort_of_pipe: str
    ground_probe_bore_field_geometry: str
    ground_probe_buried_depth_of_pipe: float
    ground_probe_length_of_borehole: float
    ground_probe_radius_of_borehole: float
    ground_probe_number_of_boreholes_in_x_direction: int
    ground_probe_number_of_boreholes_in_y_direction: int
    ground_probe_borehole_spacing_both_directions: float
    ground_probe_outer_pipe_radius: float
    ground_probe_inner_pipe_radius: float
    ground_probe_shank_spacing: float
    ground_probe_pipe_roughness: float
    ground_probe_thermal_diffusivity_ground_in_sqm_per_s: float
    ground_probe_thermal_conductivity_ground: float
    ground_probe_thermal_conductivity_grout: float
    ground_probe_thermal_conductivity_pipe: float
    ground_probe_co2_footprint: float
    ground_probe_cost: float
    ground_probe_lifetime: float
    ground_probe_maintenance_cost_as_percentage_of_investment: float
    ground_probe_maintenance_costs_in_euro_per_year:float

    conventional_heater_existing: bool
    conventional_heater_with_domestic_hot_water_preparation: bool
    conventional_heater_fuel_type: Union[Conventional_Fuel, str]
    conventional_heater_boiler_type: Union[BoilerType, int]
    conventional_heater_boiler_is_modulating: bool
    conventional_heater_set_heating_threshold_outside_temperature_in_celsius_for_bivalent_use:float
    conventional_heater_minimal_thermal_power_in_watt: float
    conventional_heater_maximal_thermal_power_in_watt: float
    conventional_heater_set_temperature_difference_for_full_power: float
    conventional_heater_minimum_running_time_in_seconds: float
    conventional_heater_minimum_resting_time_in_seconds: float
    conventional_heater_temperature_delta_in_celsius: float
    conventional_heater_eff_th_min: float
    conventional_heater_eff_th_max: float
    conventional_heater_co2_footprint: float
    conventional_heater_cost: float
    conventional_heater_lifetime: float
    conventional_heater_maintenance_cost_as_percentage_of_investment: float
    conventional_heater_maintenance_costs_in_euro_per_year: float

    pv_existing:bool
    pv_power:float
    pv_load_module_data:bool
    pv_module_database: int
    pv_inverter_database: int
    pv_module_name:str
    pv_integrate_inverter:bool
    pv_inverter_name:str
    pv_share_of_maximum_pv_potential: float
    pv_azimuth:float
    pv_tilt:float
    pv_area: float
    pv_prediction_horizon:Optional[int]
    pv_predictive:  bool
    pv_predictive_control: bool
    pv_co2_footprint: float
    pv_cost: float
    pv_lifetime: float
    pv_maintenance_cost_as_percentage_of_investment: float
    pv_maintenance_costs_in_euro_per_year: float

    battery_existing:bool
    battery_capacity_generic_in_kilowatt_hour:float
    battery_c_rate: Optional[float]
    battery_inverter_power_generic_in_watt:float
    battery_system_id:str
    battery_charge_in_kwh:float
    battery_discharge_in_kwh:float
    battery_co2_footprint: float
    battery_cost: float
    battery_lifetime: float
    battery_lifetime_in_cycles: float
    battery_maintenance_cost_as_percentage_of_investment: float
    battery_maintenance_costs_in_euro_per_year: float

    solar_thermal_collector_for_dhw_existing: bool
    solar_thermal_collector_for_dhw_type: Union[Solar_Thermal_Collector_Type, str]
    solar_thermal_collector_for_dhw_set_temperature_difference_for_on:float
    solar_thermal_collector_for_dhw_azimuth: float
    solar_thermal_collector_for_dhw_tilt: float
    solar_thermal_collector_for_dhw_area_m2: float
    solar_thermal_collector_roof_index: int
    solar_thermal_collector_for_dhw_eta_0: float
    solar_thermal_collector_for_dhw_a_1_w_m2_k: float
    solar_thermal_collector_for_dhw_a_2_w_m2_k: float
    solar_thermal_collector_for_dhw_old_solar_pump: bool
    solar_thermal_collector_for_dhw_co2_footprint: float
    solar_thermal_collector_for_dhw_investment_cost: float
    solar_thermal_collector_for_dhw_maintenance_cost_as_percentage_of_investment: float
    solar_thermal_collector_for_dhw_maintenance_costs_eur_per_y: float
    solar_thermal_collector_for_dhw_lifetime: float
    solar_thermal_collector_for_dhw_source_weight: int

    car_existing: bool
    car_number_of_electric: int
    car_consumption_per_km_electric: float
    car_battery_system_id_electric:str
    car_battery_capacity_in_kwh:float
    car_battery_setpoint_state_of_charge:float
    car_co2_footprint: float
    car_cost: float
    car_lifetime: float
    car_maintenance_cost_as_percentage_of_investment: float
    car_maintenance_costs_in_euro_per_year: float
    car_battery_co2_footprint: float
    car_battery_cost: float
    car_battery_lifetime: float
    car_battery_maintenance_cost_as_percentage_of_investment: float
    car_battery_maintenance_costs_in_euro_per_year: float


    ems_existing:bool
    ems_strategy:int
    ems_limit_to_shave:float
    ems_building_temperature_offset_value:float
    ems_dhw_storage_temperature_offset_value:float
    ems_sh_storage_temperature_offset_value:float
    ems_source_weight_occupancy:int
    ems_source_weight_heatpump_DHW:int
    ems_source_weight_heatpump_hotwater:int
    ems_source_weight_battery:int
    ems_source_weight_car: int


    @classmethod
    def get_default_generic_building_config(cls):
        return Generic_Building_Config(
            name="default",
            building_name="default_building",
            heat_distribution_system_heating_system = 1,
            heat_distribution_system_nominal_water_mass_flow_rate_in_kg_per_second=1,
            heat_distribution_system_set_heating_threshold_outside_temperature_in_celsius = 10,
            heat_distribution_system_set_cooling_threshold_outside_temperature_in_celsius = 30,
            heat_distribution_system_heating_reference_temperature_in_celsius = -11,
            heat_distribution_system_set_heating_temperature_for_building_in_celsius = 20,
            heat_distribution_system_set_cooling_temperature_for_building_in_celsius = 40,
            building_latitude=None,
            building_longitude=None,
            building_code = "DE.N.SFH.12.Gen.ReEx.001.023",
            building_heat_capacity_class = "very heavy",
            building_initial_internal_temperature_in_celsius=22.0,
            building_heating_reference_temperature_in_celsius=-11,
            building_absolute_conditioned_floor_area_in_m2 = 120,
            building_floor_u_value_in_watt_per_m2_per_kelvin=None,
            building_floor_area_in_m2=None,
            building_facade_u_value_in_watt_per_m2_per_kelvin=None,
            building_facade_area_in_m2 = None,
            building_roof_u_value_in_watt_per_m2_per_kelvin = None,
            building_roof_area_in_m2 = None,
            building_window_u_value_in_watt_per_m2_per_kelvin = None,
            building_window_area_in_m2 = None,
            building_door_u_value_in_watt_per_m2_per_kelvin = None,
            building_door_area_in_m2 = None,
            building_number_of_apartments = 1,
            building_predictive_control = False,
            building_enable_opening_windows = False,
            building_window_co2_footprint = None,
            building_window_cost = None,
            building_window_lifetime = None,
            building_window_maintenance_cost_as_percentage_of_investment = None,
            building_roof_co2_footprint = None,
            building_roof_cost = None,
            building_roof_lifetime = None,
            building_roof_maintenance_cost_as_percentage_of_investment = None,
            building_floor_co2_footprint = None,
            building_floor_cost = None,
            building_floor_lifetime = None,
            building_floor_maintenance_cost_as_percentage_of_investment =None,
            building_facade_co2_footprint = None,
            building_facade_cost = None,
            building_facade_lifetime = None,
            building_facade_maintenance_cost_as_percentage_of_investment = None,
            building_door_co2_footprint = None,
            building_door_cost = None,
            building_door_lifetime = None,
            building_door_maintenance_cost_as_percentage_of_investment = None,
            building_door_maintenance_costs_in_euro_per_year = None,
            building_window_maintenance_costs_in_euro_per_year = None,
            building_roof_maintenance_costs_in_euro_per_year = None,
            building_facade_maintenance_costs_in_euro_per_year = None,
            building_floor_maintenance_costs_in_euro_per_year = None,

            loadprofile_data_acquisition_mode = "use_utsp",
            loadprofile_household_utsp="CHR01_Couple_both_at_Work",
            loadprofile_number_of_persons=2,
            loadprofile_energy_intensity_utsp="EnergySaving",
            loadprofile_travel_route_set_utsp="Travel_Route_Set_for_10km_Commuting_Distance",
            loadprofile_transportation_device_set_utsp="Bus_and_one_30_km_h_Car",
            loadprofile_charging_station_set_utsp="Charging_At_Home_with_03_7_kW",
            loadprofile_profile_with_washing_machine_and_dishwasher_utsp=True,
            loadprofile_predictive_control_utsp=False,
            loadprofile_predefined_profile_name = "CHR01 Couple both at Work",
            loadprofile_predefined_loadprofile_filepaths = None,
            loadprofile_predictive_occupancy = False,
            heatpump_spaceheating_mode = 1,
            dhw_storage_t_min_in_celsius = 40,
            dhw_storage_t_max_in_celsius = 65,
            heatpump_thermalPower_is_constant_for_dhw = False,
            heatpump_p_th_max_dhw_in_watt = 9500,
            heatpump_model = "WPL 25 A",
            heatpump_fluid_primary_side = "Air",
            heatpump_heat_source_if_not_air = None,
            simple_heatsource_const_value_of_const_heat_source = 0,
            heatpump_cycling_mode = True,
            heatpump_minimum_running_time_in_seconds = 5*60,
            heatpump_minimum_idle_time_in_seconds = 5*60,
            heatpump_massflow_nominal_secondary_in_kg_per_s=1400/3600,
            heatpump_massflow_nominal_primary_side_in_kg_per_s=None,
            heatpump_minimum_thermal_output_power_in_watt = 3800,
            heatpump_group_id = 0,
            heatpump_heating_reference_temperature_in_celsius = 0,
            heatpump_flow_temperature_in_celsius = 0,
            heatpump_set_thermal_output_power_in_watt = 0,
            heatpump_upper_temperature_offset_for_state_conditions_in_celsius=20,
            heatpump_lower_temperature_offset_for_state_conditions_in_celsius =5,
            sh_storage_volume_in_liter = 400,
            sh_storage_position = 1,
            heatpump_with_domestic_hot_water_preparation=True,
            heatpump_passive_cooling_with_brine=False,
            heatpump_electrical_input_power_brine_pump_in_watt=0,
            heatpump_for_dhw_is_indoor=False,
            heatpump_with_space_heating = True,
            sh_storage_heat_transfer_coefficient_in_watt_per_m2_per_kelvin = 2.0,
            sh_storage_heat_exchanger_is_present = True,
            dhw_storage_freshwater_temperature = 10,
            dhw_storage_ww_temperature_demand = 65,
            dhw_storage_volume_in_liter = 300,
            dhw_storage_heat_transfer_coefficient_in_watt_per_m2_per_kelvin = 0.9,
            pv_power = 1000,
            pv_load_module_data = False,
            pv_module_name = "Hanwha_HSL60P6_PA_4_250T__2013_",
            pv_module_database = 1,
            pv_integrate_inverter = True,
            pv_inverter_database = 2,
            pv_inverter_name = "ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_",
            pv_azimuth = 180,
            pv_tilt = 30,
            pv_area =10,
            pv_share_of_maximum_pv_potential = 1,
            pv_prediction_horizon = None,
            pv_predictive = False,
            pv_predictive_control = False,
            battery_capacity_generic_in_kilowatt_hour = 10,
            battery_c_rate = 0.5,
            battery_inverter_power_generic_in_watt = 10*0.5*1000,  #c.rate: hier 0.5 (*1000 von kW auf W)
            battery_system_id = "SG1",
            battery_charge_in_kwh = 0,
            battery_discharge_in_kwh = 0,
            ems_strategy = 1, #"optimize_own_consumption",
            ems_limit_to_shave = 0,
            ems_building_temperature_offset_value = 2,
            ems_dhw_storage_temperature_offset_value = 10,
            ems_sh_storage_temperature_offset_value=10,
            ems_source_weight_occupancy = 999,
            ems_source_weight_heatpump_DHW = 999,
            ems_source_weight_heatpump_hotwater = 1,
            ems_source_weight_battery = 2,
            ems_source_weight_car = 3,

            heat_distribution_system_existing=True,
            building_existing=True,
            ethos_builda_dev_client=None,
            ethos_builda_id=None,
            ethos_builda_address=None,
            ethos_builda_construction_year=None,
            ethos_builda_roof_geometry=None,
            heatpump_existing=True,
            sh_storage_existing=True,
            dhw_storage_existing=True,
            pv_existing=True,
            battery_existing=True,
            ems_existing=True,
            car_existing= True,
            loadprofile_existing = True,
            car_number_of_electric=1,
            car_consumption_per_km_electric=0.15,
            car_battery_system_id_electric="SG1",
            car_battery_capacity_in_kwh=30,
            car_battery_setpoint_state_of_charge=0.4,

            heat_distribution_system_co2_footprint=1,
            heat_distribution_system_cost=1,
            heat_distribution_system_lifetime=1,
            heat_distribution_system_maintenance_costs_in_euro_per_year=1,
            heat_distribution_system_maintenance_cost_as_percentage_of_investment=1,
            heatpump_co2_footprint=1,
            heatpump_cost=1,
            heatpump_lifetime=1,
            heatpump_maintenance_cost_as_percentage_of_investment=1,
            heatpump_maintenance_costs_in_euro_per_year=1,
            sh_storage_co2_footprint=1,
            sh_storage_cost=1,
            sh_storage_lifetime=1,
            sh_storage_maintenance_cost_as_percentage_of_investment=1,
            sh_storage_maintenance_costs_in_euro_per_year=1,
            dhw_storage_co2_footprint=1,
            dhw_storage_cost=1,
            dhw_storage_lifetime=1,
            dhw_storage_maintenance_cost_as_percentage_of_investment=1,
            dhw_storage_maintenance_costs_in_euro_per_year=1,
            pv_co2_footprint=1,
            pv_cost=1,
            pv_lifetime=1,
            pv_maintenance_cost_as_percentage_of_investment=1,
            pv_maintenance_costs_in_euro_per_year=1,
            battery_co2_footprint=1,
            battery_cost=1,
            battery_lifetime=1,
            battery_lifetime_in_cycles=1,
            battery_maintenance_cost_as_percentage_of_investment=1,
            battery_maintenance_costs_in_euro_per_year=1,
            car_co2_footprint=1,
            car_cost=1,
            car_lifetime=1,
            car_maintenance_cost_as_percentage_of_investment=1,
            car_maintenance_costs_in_euro_per_year=1,
            car_battery_co2_footprint=1,
            car_battery_cost=1,
            car_battery_lifetime=1,
            car_battery_maintenance_cost_as_percentage_of_investment=1,
            car_battery_maintenance_costs_in_euro_per_year=1,
            simple_heatsource_co2_footprint=1,
            simple_heatsource_cost=1,
            simple_heatsource_lifetime=1,
            simple_heatsource_maintenance_cost_as_percentage_of_investment=1,
            simple_heatsource_maintenance_costs_in_euro_per_year=1,
            ground_probe_co2_footprint=1,
            ground_probe_cost=1,
            ground_probe_lifetime=1,
            ground_probe_maintenance_cost_as_percentage_of_investment=1,
            ground_probe_maintenance_costs_in_euro_per_year=1,

            conventional_heater_existing=False,
            conventional_heater_with_domestic_hot_water_preparation=False,
            conventional_heater_fuel_type=Conventional_Fuel.GAS,
            conventional_heater_boiler_type="CONDENSING",
            conventional_heater_boiler_is_modulating = True,
            conventional_heater_set_heating_threshold_outside_temperature_in_celsius_for_bivalent_use=15,
            conventional_heater_minimal_thermal_power_in_watt=1,
            conventional_heater_maximal_thermal_power_in_watt=1,
            conventional_heater_set_temperature_difference_for_full_power=1,
            conventional_heater_minimum_running_time_in_seconds=1,
            conventional_heater_minimum_resting_time_in_seconds=1,
            conventional_heater_temperature_delta_in_celsius=1,
            conventional_heater_eff_th_min=1,
            conventional_heater_eff_th_max=1,
            conventional_heater_co2_footprint=1,
            conventional_heater_cost=1,
            conventional_heater_lifetime=1,
            conventional_heater_maintenance_cost_as_percentage_of_investment=1,
            conventional_heater_maintenance_costs_in_euro_per_year=1,

            ground_probe_sort_of_pipe="SINGLE_U_TUBE",
            heatpump_heat_source_fluid_type_primary_side="PROPYLEN_GLYCOL",
            heatpump_heat_source_fluid_primary_side_specific_heat_capacity = 0,
            heatpump_heat_source_mass_fraction_of_fluid_mixed_in_water=0.20,
            ground_probe_bore_field_geometry="L_SHAPED_FIELD",
            ground_probe_buried_depth_of_pipe=4,
            ground_probe_length_of_borehole=190,
            ground_probe_radius_of_borehole=0.075,
            ground_probe_number_of_boreholes_in_x_direction=1,
            ground_probe_number_of_boreholes_in_y_direction=1,
            ground_probe_borehole_spacing_both_directions=7.5,
            ground_probe_outer_pipe_radius=0.0211,
            ground_probe_inner_pipe_radius=0.0147,
            ground_probe_shank_spacing=0.052,
            ground_probe_pipe_roughness=1.0e-6,
            ground_probe_thermal_diffusivity_ground_in_sqm_per_s=1.0e-6,
            ground_probe_thermal_conductivity_ground=2,
            ground_probe_thermal_conductivity_grout=1,
            ground_probe_thermal_conductivity_pipe=0.4,

            solar_thermal_collector_for_dhw_existing=False,
            solar_thermal_collector_for_dhw_type=Solar_Thermal_Collector_Type.FLAT_PLATE,
            solar_thermal_collector_for_dhw_set_temperature_difference_for_on=10,
            solar_thermal_collector_for_dhw_azimuth=0,
            solar_thermal_collector_for_dhw_tilt=0,
            solar_thermal_collector_for_dhw_area_m2=0,
            solar_thermal_collector_roof_index=0,
            solar_thermal_collector_for_dhw_eta_0=0,
            solar_thermal_collector_for_dhw_a_1_w_m2_k=0,
            solar_thermal_collector_for_dhw_a_2_w_m2_k=0,
            solar_thermal_collector_for_dhw_old_solar_pump=False,
            solar_thermal_collector_for_dhw_co2_footprint=0,
            solar_thermal_collector_for_dhw_investment_cost=0,
            solar_thermal_collector_for_dhw_maintenance_cost_as_percentage_of_investment=0,
            solar_thermal_collector_for_dhw_maintenance_costs_eur_per_y=0,
            solar_thermal_collector_for_dhw_lifetime=0,
            solar_thermal_collector_for_dhw_source_weight=0,
        )


class Generic_Building(cp.Component):

    # Outputs

    electricity_meter_geb:Any

    heatpump_geb: Any

    building_parameter: Any

    quartier_ems: Any

    my_gas_meter_geb: Any

    def __init__(self,my_sim,my_simulation_parameters,path_simulation_directory, my_weather,config:Generic_Building_Config, location, district_name, config_name)->None:
        self.config_name=config_name
        building_config = config
        building_config.name = building_config.building_name

        self.my_simulation_parameters = my_simulation_parameters

        super().__init__(
            name=building_config.building_name,
            my_simulation_parameters=my_simulation_parameters,
            my_config=config,
            my_display_config=DisplayConfig(display_in_webtool=False),
        )

        for key, value in my_sim.my_module_config.items():
            if building_config.building_name == key:
                my_sim.my_module_config[key] = building_config.to_dict()

        # Parameter building_setup
        self.my_sim = my_sim
        self.path_simulation_directory=path_simulation_directory
        self.location = location
        self.my_weather = my_weather
        self.district_name = district_name
        self.building_name = building_config.building_name
        self.name = building_config.building_name

        # Parameter Building
        self.building_existing = building_config.building_existing

        self.ethos_builda_dev_client = building_config.ethos_builda_dev_client
        self.ethos_builda_id = building_config.ethos_builda_id
        self.ethos_builda_address = building_config.ethos_builda_address
        self.ethos_builda_construction_year = building_config.ethos_builda_construction_year
        self.ethos_builda_roof_geometry=building_config.ethos_builda_roof_geometry

        self.building_latitude = building_config.building_latitude
        self.building_longitude = building_config.building_longitude

        self.building_code = building_config.building_code
        self.building_heat_capacity_class = building_config.building_heat_capacity_class
        self.building_initial_internal_temperature_in_celsius = building_config.building_initial_internal_temperature_in_celsius
        self.building_heating_reference_temperature_in_celsius = building_config.building_heating_reference_temperature_in_celsius
        self.building_absolute_conditioned_floor_area_in_m2 = building_config.building_absolute_conditioned_floor_area_in_m2
        self.building_floor_u_value_in_watt_per_m2_per_kelvin = building_config.building_floor_u_value_in_watt_per_m2_per_kelvin
        self.building_floor_area_in_m2 = building_config.building_floor_area_in_m2
        self.building_facade_u_value_in_watt_per_m2_per_kelvin = building_config.building_facade_u_value_in_watt_per_m2_per_kelvin
        self.building_facade_area_in_m2 = building_config.building_facade_area_in_m2
        self.building_roof_u_value_in_watt_per_m2_per_kelvin = building_config.building_roof_u_value_in_watt_per_m2_per_kelvin
        self.building_roof_area_in_m2 = building_config.building_roof_area_in_m2
        self.building_window_u_value_in_watt_per_m2_per_kelvin = building_config.building_window_u_value_in_watt_per_m2_per_kelvin
        self.building_window_area_in_m2 = building_config.building_window_area_in_m2
        self.building_door_u_value_in_watt_per_m2_per_kelvin = building_config.building_door_u_value_in_watt_per_m2_per_kelvin
        self.building_door_area_in_m2 = building_config.building_door_area_in_m2
        self.building_number_of_apartments = building_config.building_number_of_apartments
        self.building_predictive_control = building_config.building_predictive_control
        self.building_enable_opening_windows = building_config.building_enable_opening_windows
        self.building_window_co2_footprint = building_config.building_window_co2_footprint
        self.building_window_cost = building_config.building_window_cost
        self.building_window_lifetime =  building_config.building_window_lifetime
        self.building_window_maintenance_cost_as_percentage_of_investment =  building_config.building_window_maintenance_cost_as_percentage_of_investment
        self.building_roof_co2_footprint = building_config.building_roof_co2_footprint
        self.building_roof_cost = building_config.building_roof_cost
        self.building_roof_lifetime = building_config.building_roof_lifetime
        self.building_roof_maintenance_cost_as_percentage_of_investment = building_config.building_roof_maintenance_cost_as_percentage_of_investment
        self.building_floor_co2_footprint = building_config.building_floor_co2_footprint
        self.building_floor_cost = building_config.building_floor_cost
        self.building_floor_lifetime = building_config.building_floor_lifetime
        self.building_floor_maintenance_cost_as_percentage_of_investment = building_config.building_floor_maintenance_cost_as_percentage_of_investment
        self.building_facade_co2_footprint = building_config.building_facade_co2_footprint
        self.building_facade_cost = building_config.building_facade_cost
        self.building_facade_lifetime = building_config.building_facade_lifetime
        self.building_facade_maintenance_cost_as_percentage_of_investment = building_config.building_facade_maintenance_cost_as_percentage_of_investment
        self.building_door_co2_footprint = building_config.building_door_co2_footprint
        self.building_door_cost = building_config.building_door_cost
        self.building_door_lifetime = building_config.building_door_lifetime
        self.building_door_maintenance_cost_as_percentage_of_investment = building_config.building_door_maintenance_cost_as_percentage_of_investment
        self.building_door_maintenance_costs_in_euro_per_year = building_config.building_door_maintenance_costs_in_euro_per_year
        self.building_window_maintenance_costs_in_euro_per_year = building_config.building_window_maintenance_costs_in_euro_per_year
        self.building_roof_maintenance_costs_in_euro_per_year = building_config.building_roof_maintenance_costs_in_euro_per_year
        self.building_facade_maintenance_costs_in_euro_per_year = building_config.building_facade_maintenance_costs_in_euro_per_year
        self.building_floor_maintenance_costs_in_euro_per_year = building_config.building_floor_maintenance_costs_in_euro_per_year

        # Parameter Heat Distribution
        self.heat_distribution_system_existing = building_config.heat_distribution_system_existing
        self.heat_distribution_system_heating_system=building_config.heat_distribution_system_heating_system
        self.heat_distribution_system_nominal_water_mass_flow_rate_in_kg_per_second=(building_config
                                                                         .heat_distribution_system_nominal_water_mass_flow_rate_in_kg_per_second)
        self.heat_distribution_system_heating_reference_temperature_in_celsius = building_config.heat_distribution_system_heating_reference_temperature_in_celsius
        self.heat_distribution_system_set_heating_temperature_for_building_in_celsius=building_config.heat_distribution_system_set_heating_temperature_for_building_in_celsius
        self.heat_distribution_system_set_cooling_temperature_for_building_in_celsius=building_config.heat_distribution_system_set_cooling_temperature_for_building_in_celsius

        # Parameter Heat Pump
        self.heatpump_existing = building_config.heatpump_existing
        self.heatpump_spaceheating_mode = building_config.heatpump_spaceheating_mode
        self.heat_distribution_system_set_heating_threshold_outside_temperature_in_celsius = building_config.heat_distribution_system_set_heating_threshold_outside_temperature_in_celsius
        self.heat_distribution_system_set_cooling_threshold_outside_temperature_in_celsius = building_config.heat_distribution_system_set_cooling_threshold_outside_temperature_in_celsius
        self.heatpump_with_domestic_hot_water_preparation = building_config.heatpump_with_domestic_hot_water_preparation
        self.heatpump_passive_cooling_with_brine = building_config.heatpump_passive_cooling_with_brine
        self.heatpump_electrical_input_power_brine_pump_in_watt = building_config.heatpump_electrical_input_power_brine_pump_in_watt
        self.heatpump_for_dhw_is_indoor = building_config.heatpump_for_dhw_is_indoor
        self.heatpump_with_space_heating = building_config.heatpump_with_space_heating
        self.dhw_storage_t_min_in_celsius = building_config.dhw_storage_t_min_in_celsius
        self.dhw_storage_t_max_in_celsius = building_config.dhw_storage_t_max_in_celsius
        self.heatpump_thermalPower_is_constant_for_dhw = building_config.heatpump_thermalPower_is_constant_for_dhw
        self.heatpump_p_th_max_dhw_in_watt = building_config.heatpump_p_th_max_dhw_in_watt
        self.model = building_config.heatpump_model
        self.heatpump_fluid_primary_side = building_config.heatpump_fluid_primary_side
        self.heatpump_heat_source_if_not_air = building_config.heatpump_heat_source_if_not_air
        self.simple_heatsource_const_value_of_const_heat_source = building_config.simple_heatsource_const_value_of_const_heat_source
        self.heatpump_cycling_mode = building_config.heatpump_cycling_mode
        self.heatpump_minimum_running_time_in_seconds = building_config.heatpump_minimum_running_time_in_seconds
        self.heatpump_minimum_idle_time_in_seconds = building_config.heatpump_minimum_idle_time_in_seconds
        self.heatpump_massflow_nominal_secondary_in_kg_per_s = building_config.heatpump_massflow_nominal_secondary_in_kg_per_s
        self.heatpump_minimum_thermal_output_power_in_watt = building_config.heatpump_minimum_thermal_output_power_in_watt
        self.heatpump_massflow_nominal_primary_side_in_kg_per_s = building_config.heatpump_massflow_nominal_primary_side_in_kg_per_s
        self.heatpump_upper_temperature_offset_for_state_conditions_in_celsius = building_config.heatpump_upper_temperature_offset_for_state_conditions_in_celsius
        self.heatpump_lower_temperature_offset_for_state_conditions_in_celsius = building_config.heatpump_lower_temperature_offset_for_state_conditions_in_celsius
        self.heatpump_group_id = building_config.heatpump_group_id
        self.heatpump_heating_reference_temperature_in_celsius = building_config.heatpump_heating_reference_temperature_in_celsius
        self.heatpump_flow_temperature_in_celsius = building_config.heatpump_flow_temperature_in_celsius
        self.heatpump_set_thermal_output_power_in_watt = building_config.heatpump_set_thermal_output_power_in_watt

        # Parameter Ground Probe
        self.ground_probe_sort_of_pipe = building_config.ground_probe_sort_of_pipe
        self.heatpump_heat_source_fluid_type_primary_side = building_config.heatpump_heat_source_fluid_type_primary_side
        self.heatpump_heat_source_fluid_primary_side_specific_heat_capacity = building_config.heatpump_heat_source_fluid_primary_side_specific_heat_capacity
        self.heatpump_heat_source_mass_fraction_of_fluid_mixed_in_water = building_config.heatpump_heat_source_mass_fraction_of_fluid_mixed_in_water
        self.ground_probe_bore_field_geometry = building_config.ground_probe_bore_field_geometry
        self.ground_probe_buried_depth_of_pipe = building_config.ground_probe_buried_depth_of_pipe
        self.ground_probe_length_of_borehole = building_config.ground_probe_length_of_borehole
        self.ground_probe_radius_of_borehole = building_config.ground_probe_radius_of_borehole
        self.ground_probe_number_of_boreholes_in_x_direction = building_config.ground_probe_number_of_boreholes_in_x_direction
        self.ground_probe_number_of_boreholes_in_y_direction = building_config.ground_probe_number_of_boreholes_in_y_direction
        self.ground_probe_borehole_spacing_both_directions = building_config.ground_probe_borehole_spacing_both_directions
        self.ground_probe_outer_pipe_radius = building_config.ground_probe_outer_pipe_radius
        self.ground_probe_inner_pipe_radius = building_config.ground_probe_inner_pipe_radius
        self.ground_probe_shank_spacing = building_config.ground_probe_shank_spacing
        self.ground_probe_pipe_roughness = building_config.ground_probe_pipe_roughness
        self.ground_probe_thermal_diffusivity_ground_in_sqm_per_s = building_config.ground_probe_thermal_diffusivity_ground_in_sqm_per_s
        self.ground_probe_thermal_conductivity_ground = building_config.ground_probe_thermal_conductivity_ground
        self.ground_probe_thermal_conductivity_grout = building_config.ground_probe_thermal_conductivity_grout
        self.ground_probe_thermal_conductivity_pipe = building_config.ground_probe_thermal_conductivity_pipe

        # Parameter Hot Water Storage (Space Heating)
        self.sh_storage_existing = building_config.sh_storage_existing
        self.sh_storage_position = building_config.sh_storage_position
        self.sh_storage_volume_in_liter = building_config.sh_storage_volume_in_liter
        self.sh_storage_heat_transfer_coefficient_in_watt_per_m2_per_kelvin = building_config.sh_storage_heat_transfer_coefficient_in_watt_per_m2_per_kelvin
        self.sh_storage_heat_exchanger_is_present = building_config.sh_storage_heat_exchanger_is_present

        # Parameter DHW Storage
        self.dhw_storage_existing = building_config.dhw_storage_existing
        self.freshwater_temperature = building_config.dhw_storage_freshwater_temperature
        self.ww_temperature_demand = building_config.dhw_storage_ww_temperature_demand
        self.dhw_storage_volume_in_liter = building_config.dhw_storage_volume_in_liter
        self.dhw_storage_heat_transfer_coefficient_in_watt_per_m2_per_kelvin = building_config.dhw_storage_heat_transfer_coefficient_in_watt_per_m2_per_kelvin

        # Parameter PV
        self.pv_existing = building_config.pv_existing
        self.pv_power = building_config.pv_power
        self.pv_load_module_data = building_config.pv_load_module_data
        self.pv_module_name = building_config.pv_module_name
        self.pv_module_database = building_config.pv_module_database
        self.pv_integrate_inverter = building_config.pv_integrate_inverter
        self.pv_inverter_database = building_config.pv_inverter_database
        self.pv_inverter_name = building_config.pv_inverter_name
        self.pv_share_of_maximum_pv_potential = building_config.pv_share_of_maximum_pv_potential
        self.pv_azimuth = building_config.pv_azimuth
        self.pv_tilt = building_config.pv_tilt
        self.pv_area = building_config.pv_area
        self.pv_prediction_horizon = building_config.pv_prediction_horizon
        self.pv_predictive = building_config.pv_predictive
        self.pv_predictive_control = building_config.pv_predictive_control

        # Parameter Battery
        self.battery_existing = building_config.battery_existing
        self.battery_capacity_generic_in_kilowatt_hour = building_config.battery_capacity_generic_in_kilowatt_hour
        self.battery_c_rate = building_config.battery_c_rate
        self.battery_inverter_power_generic_in_watt = building_config.battery_inverter_power_generic_in_watt
        self.battery_system_id = building_config.battery_system_id
        self.battery_charge_in_kwh = building_config.battery_charge_in_kwh
        self.battery_discharge_in_kwh = building_config.battery_discharge_in_kwh

        # Parameter Loadprofiles
        self.loadprofile_existing = building_config.loadprofile_existing
        self.loadprofile_data_acquisition_mode = building_config.loadprofile_data_acquisition_mode
        self.loadprofile_predefined_profile_name=building_config.loadprofile_predefined_profile_name
        self.loadprofile_predefined_loadprofile_filepaths=building_config.loadprofile_predefined_loadprofile_filepaths
        self.loadprofile_household_utsp = building_config.loadprofile_household_utsp
        self.loadprofile_number_of_persons = building_config.loadprofile_number_of_persons
        self.loadprofile_energy_intensity_utsp = building_config.loadprofile_energy_intensity_utsp
        self.loadprofile_travel_route_set_utsp = building_config.loadprofile_travel_route_set_utsp
        self.loadprofile_transportation_device_set_utsp = building_config.loadprofile_transportation_device_set_utsp
        self.loadprofile_charging_station_set_utsp = building_config.loadprofile_charging_station_set_utsp
        self.loadprofile_profile_with_washing_machine_and_dishwasher_utsp = building_config.loadprofile_profile_with_washing_machine_and_dishwasher_utsp
        self.loadprofile_predictive_control_utsp = building_config.loadprofile_predictive_control_utsp
        self.loadprofile_predictive_occupancy = building_config.loadprofile_predictive_occupancy

        # Parameter Mobility
        self.car_existing = building_config.car_existing
        self.car_number_of_electric = building_config.car_number_of_electric
        self.car_consumption_per_km_electric = building_config.car_consumption_per_km_electric
        self.car_battery_system_id_electric = building_config.car_battery_system_id_electric
        self.car_battery_capacity_in_kwh = building_config.car_battery_capacity_in_kwh
        self.car_battery_setpoint_state_of_charge = building_config.car_battery_setpoint_state_of_charge

        # Parameter Energiemanagementsystem Gebäude
        self.ems_existing = building_config.ems_existing
        self.ems_strategy=building_config.ems_strategy
        self.ems_limit_to_shave=building_config.ems_limit_to_shave
        self.ems_building_temperature_offset_value=building_config.ems_building_temperature_offset_value
        self.ems_dhw_storage_temperature_offset_value=building_config.ems_dhw_storage_temperature_offset_value
        self.sh_simple_ems_sh_storage_temperature_offset_value=building_config.ems_sh_storage_temperature_offset_value
        self.ems_source_weight_occupancy=building_config.ems_source_weight_occupancy
        self.ems_source_weight_heatpump_DHW=building_config.ems_source_weight_heatpump_DHW
        self.ems_source_weight_heatpump_hotwater=building_config.ems_source_weight_heatpump_hotwater
        self.ems_source_weight_battery=building_config.ems_source_weight_battery
        self.ems_source_weight_car = building_config.ems_source_weight_car

        # Parameter Cost and Emissions
        self.heat_distribution_system_co2_footprint=building_config.heat_distribution_system_co2_footprint
        self.heat_distribution_system_cost=building_config.heat_distribution_system_cost
        self.heat_distribution_system_lifetime=building_config.heat_distribution_system_lifetime
        self.heat_distribution_system_maintenance_costs_in_euro_per_year=building_config.heat_distribution_system_maintenance_costs_in_euro_per_year
        self.heat_distribution_system_maintenance_cost_as_percentage_of_investment=building_config.heat_distribution_system_maintenance_cost_as_percentage_of_investment
        self.heatpump_co2_footprint=building_config.heatpump_co2_footprint
        self.heatpump_cost=building_config.heatpump_cost
        self.heatpump_lifetime=building_config.heatpump_lifetime
        self.heatpump_maintenance_costs_in_euro_per_year=building_config.heatpump_maintenance_costs_in_euro_per_year
        self.heatpump_maintenance_cost_as_percentage_of_investment=building_config.heatpump_maintenance_cost_as_percentage_of_investment
        self.sh_storage_co2_footprint=building_config.sh_storage_co2_footprint
        self.sh_storage_cost=building_config.sh_storage_cost
        self.sh_storage_lifetime=building_config.sh_storage_lifetime
        self.sh_storage_maintenance_costs_in_euro_per_year=building_config.sh_storage_maintenance_costs_in_euro_per_year
        self.sh_storage_maintenance_cost_as_percentage_of_investment=building_config.sh_storage_maintenance_cost_as_percentage_of_investment
        self.dhw_storage_co2_footprint=building_config.dhw_storage_co2_footprint
        self.dhw_storage_cost=building_config.dhw_storage_cost
        self.dhw_storage_lifetime=building_config.dhw_storage_lifetime
        self.dhw_storage_maintenance_cost_as_percentage_of_investment=building_config.dhw_storage_maintenance_cost_as_percentage_of_investment
        self.dhw_storage_maintenance_costs_in_euro_per_year=building_config.dhw_storage_maintenance_costs_in_euro_per_year
        self.pv_co2_footprint=building_config.pv_co2_footprint
        self.pv_cost=building_config.pv_cost
        self.pv_lifetime=building_config.pv_lifetime
        self.pv_maintenance_cost_as_percentage_of_investment=building_config.pv_maintenance_cost_as_percentage_of_investment
        self.pv_maintenance_costs_in_euro_per_year=building_config.pv_maintenance_costs_in_euro_per_year
        self.battery_co2_footprint=building_config.battery_co2_footprint
        self.battery_cost=building_config.battery_cost
        self.battery_lifetime=building_config.battery_lifetime
        self.battery_lifetime_in_cycles=building_config.battery_lifetime_in_cycles
        self.battery_maintenance_cost_as_percentage_of_investment=building_config.battery_maintenance_cost_as_percentage_of_investment
        self.battery_maintenance_costs_in_euro_per_year=building_config.battery_maintenance_costs_in_euro_per_year
        self.car_co2_footprint=building_config.car_co2_footprint
        self.car_cost=building_config.car_cost
        self.car_lifetime=building_config.car_lifetime
        self.car_maintenance_cost_as_percentage_of_investment=building_config.car_maintenance_cost_as_percentage_of_investment
        self.car_maintenance_costs_in_euro_per_year=building_config.car_maintenance_costs_in_euro_per_year
        self.car_battery_co2_footprint=building_config.car_battery_co2_footprint
        self.car_battery_cost=building_config.car_battery_cost
        self.car_battery_lifetime=building_config.car_battery_lifetime
        self.car_battery_maintenance_cost_as_percentage_of_investment=building_config.car_battery_maintenance_cost_as_percentage_of_investment
        self.car_battery_maintenance_costs_in_euro_per_year=building_config.car_battery_maintenance_costs_in_euro_per_year
        self.simple_heatsource_co2_footprint=building_config.simple_heatsource_co2_footprint
        self.simple_heatsource_cost=building_config.simple_heatsource_cost
        self.simple_heatsource_lifetime=building_config.simple_heatsource_lifetime
        self.simple_heatsource_maintenance_cost_as_percentage_of_investment=building_config.simple_heatsource_maintenance_cost_as_percentage_of_investment
        self.simple_heatsource_maintenance_costs_in_euro_per_year=building_config.simple_heatsource_maintenance_costs_in_euro_per_year
        self.ground_probe_co2_footprint=building_config.ground_probe_co2_footprint
        self.ground_probe_cost=building_config.ground_probe_cost
        self.ground_probe_lifetime=building_config.ground_probe_lifetime
        self.ground_probe_maintenance_cost_as_percentage_of_investment=building_config.ground_probe_maintenance_cost_as_percentage_of_investment
        self.ground_probe_maintenance_costs_in_euro_per_year=building_config.ground_probe_maintenance_costs_in_euro_per_year

        # parameter conventional heater
        self.conventional_heater_existing = building_config.conventional_heater_existing
        self.conventional_heater_with_domestic_hot_water_preparation = building_config.conventional_heater_with_domestic_hot_water_preparation
        self.conventional_heater_fuel_type = building_config.conventional_heater_fuel_type
        self.conventional_heater_boiler_type = building_config.conventional_heater_boiler_type
        self.conventional_heater_boiler_is_modulating = building_config.conventional_heater_boiler_is_modulating
        self.conventional_heater_set_heating_threshold_outside_temperature_in_celsius_for_bivalent_use = building_config.conventional_heater_set_heating_threshold_outside_temperature_in_celsius_for_bivalent_use
        self.conventional_heater_minimal_thermal_power_in_watt = building_config.conventional_heater_minimal_thermal_power_in_watt
        self.conventional_heater_maximal_thermal_power_in_watt = building_config.conventional_heater_maximal_thermal_power_in_watt
        self.conventional_heater_set_temperature_difference_for_full_power = building_config.conventional_heater_set_temperature_difference_for_full_power
        self.conventional_heater_minimum_running_time_in_seconds = building_config.conventional_heater_minimum_running_time_in_seconds
        self.conventional_heater_minimum_resting_time_in_seconds = building_config.conventional_heater_minimum_resting_time_in_seconds
        self.conventional_heater_temperature_delta_in_celsius = building_config.conventional_heater_temperature_delta_in_celsius
        self.conventional_heater_eff_th_min = building_config.conventional_heater_eff_th_min
        self.conventional_heater_eff_th_max = building_config.conventional_heater_eff_th_max
        self.conventional_heater_co2_footprint =building_config.conventional_heater_co2_footprint
        self.conventional_heater_cost=building_config.conventional_heater_cost
        self.conventional_heater_lifetime =building_config.conventional_heater_lifetime
        self.conventional_heater_maintenance_cost_as_percentage_of_investment=building_config.conventional_heater_maintenance_cost_as_percentage_of_investment
        self.conventional_heater_maintenance_costs_in_euro_per_year=building_config.conventional_heater_maintenance_costs_in_euro_per_year

        # parametrierung solar thermie collector
        self.solar_thermal_collector_for_dhw_existing=building_config.solar_thermal_collector_for_dhw_existing
        self.solar_thermal_collector_for_dhw_type=building_config.solar_thermal_collector_for_dhw_type
        self.solar_thermal_collector_for_dhw_set_temperature_difference_for_on=building_config.solar_thermal_collector_for_dhw_set_temperature_difference_for_on
        self.solar_thermal_collector_for_dhw_azimuth=building_config.solar_thermal_collector_for_dhw_azimuth
        self.solar_thermal_collector_for_dhw_tilt=building_config.solar_thermal_collector_for_dhw_tilt
        self.solar_thermal_collector_for_dhw_area_m2=building_config.solar_thermal_collector_for_dhw_area_m2
        self.solar_thermal_collector_roof_index=building_config.solar_thermal_collector_roof_index
        self.solar_thermal_collector_for_dhw_eta_0=building_config.solar_thermal_collector_for_dhw_eta_0
        self.solar_thermal_collector_for_dhw_a_1_w_m2_k=building_config.solar_thermal_collector_for_dhw_a_1_w_m2_k
        self.solar_thermal_collector_for_dhw_a_2_w_m2_k=building_config.solar_thermal_collector_for_dhw_a_2_w_m2_k
        self.solar_thermal_collector_for_dhw_old_solar_pump=building_config.solar_thermal_collector_for_dhw_old_solar_pump
        self.solar_thermal_collector_for_dhw_co2_footprint=building_config.solar_thermal_collector_for_dhw_co2_footprint
        self.solar_thermal_collector_for_dhw_investment_cost=building_config.solar_thermal_collector_for_dhw_investment_cost
        self.solar_thermal_collector_for_dhw_maintenance_cost_as_percentage_of_investment=building_config.solar_thermal_collector_for_dhw_maintenance_cost_as_percentage_of_investment
        self.solar_thermal_collector_for_dhw_maintenance_costs_eur_per_y=building_config.solar_thermal_collector_for_dhw_maintenance_costs_eur_per_y
        self.solar_thermal_collector_for_dhw_lifetime=building_config.solar_thermal_collector_for_dhw_lifetime
        self.solar_thermal_collector_for_dhw_source_weight=building_config.solar_thermal_collector_for_dhw_source_weight

    def generic_building(self):
        # =================================================================================================================================
        # Build Components

        if self.sh_storage_existing == False:
            self.sh_storage_position = 3

        if self.heatpump_with_space_heating == False and self.conventional_heater_existing == False:
            raise KeyError("Kein Wärmeerzeuger für Spaceheating angeschlossen")
        if self.heatpump_with_domestic_hot_water_preparation == False and self.conventional_heater_with_domestic_hot_water_preparation == False:
            raise KeyError("Kein Wärmeerzeuger für DHW angeschlossen")

        if self.conventional_heater_existing == True:
            self.sh_storage_position = 1
            self.ems_source_weight_heatpump_hotwater = 999
            if self.conventional_heater_with_domestic_hot_water_preparation == True:
                self.ems_source_weight_heatpump_DHW = 999

        if self.battery_existing == False:
            self.ems_source_weight_battery = 999

        if self.car_existing == False:
            self.ems_source_weight_car = 999

        if self.battery_existing and not self.ems_existing:
            raise KeyError("Battery needs ems but ems not existing")

        if self.car_existing and not self.ems_existing:
            raise KeyError("car needs ems but ems not existing")

        if self.heatpump_existing == False:
            self.ems_source_weight_heatpump_hotwater = 999
            self.ems_source_weight_heatpump_DHW = 999

        if self.ems_existing==True:
            source_weights_set = {value for name, value in self.__dict__.items() if 'weight' in name}
            if len(list(source_weights_set)) == 1 and list(source_weights_set)[0] == 999:
                self.ems_existing = False
                print("\n" + "*************INFO: ALLE SOURCE WEIGHTS FÜR EMS SIND 999 --> EMS WIRD ENTFERNT!*************" + "\n")


        if self.heat_distribution_system_set_cooling_threshold_outside_temperature_in_celsius <= self.heat_distribution_system_set_heating_temperature_for_building_in_celsius:
            raise KeyError("heat_distribution_system_set_cooling_threshold_outside_temperature_in_celsius muss größer als Raumsolltemepratur (heat_distribution_system_set_heating_temperature_for_building_in_celsius) sein!!!")

        # Build Building

        building_cost = self.building_door_cost + self.building_window_cost + self.building_roof_cost + self.building_facade_cost + self.building_floor_cost

        building_co2_footprint = self.building_door_co2_footprint + self.building_window_co2_footprint + self.building_roof_co2_footprint + self.building_facade_co2_footprint + self.building_floor_co2_footprint

        building_lifetime = (self.building_door_lifetime + self.building_window_lifetime + self.building_roof_lifetime + self.building_facade_lifetime + self.building_floor_lifetime) / 5

        building_maintenance_costs_in_euro_per_year = self.building_door_maintenance_costs_in_euro_per_year + self.building_window_maintenance_costs_in_euro_per_year + self.building_roof_maintenance_costs_in_euro_per_year + self.building_facade_maintenance_costs_in_euro_per_year + self.building_floor_maintenance_costs_in_euro_per_year

        my_building_config = building.BuildingConfig(
            building_name=self.building_name,
            name="Building",
            building_code=self.building_code,
            building_heat_capacity_class=self.building_heat_capacity_class,
            initial_internal_temperature_in_celsius=self.building_initial_internal_temperature_in_celsius,
            heating_reference_temperature_in_celsius=self.building_heating_reference_temperature_in_celsius,
            absolute_conditioned_floor_area_in_m2=self.building_absolute_conditioned_floor_area_in_m2,
            max_thermal_building_demand_in_watt=None,
            floor_u_value_in_watt_per_m2_per_kelvin=self.building_floor_u_value_in_watt_per_m2_per_kelvin,
            floor_area_in_m2=self.building_floor_area_in_m2,
            facade_u_value_in_watt_per_m2_per_kelvin=self.building_facade_u_value_in_watt_per_m2_per_kelvin,
            facade_area_in_m2=self.building_facade_area_in_m2,
            roof_u_value_in_watt_per_m2_per_kelvin=self.building_roof_u_value_in_watt_per_m2_per_kelvin,
            roof_area_in_m2=self.building_roof_area_in_m2,
            window_u_value_in_watt_per_m2_per_kelvin=self.building_window_u_value_in_watt_per_m2_per_kelvin,
            window_area_in_m2=self.building_window_area_in_m2,
            door_u_value_in_watt_per_m2_per_kelvin=self.building_door_u_value_in_watt_per_m2_per_kelvin,
            door_area_in_m2=self.building_door_area_in_m2,
            total_base_area_in_m2=None,
            set_heating_temperature_in_celsius=self.heat_distribution_system_set_heating_temperature_for_building_in_celsius,  # Solltemperatur Gebäude Heizbetrieb,
            set_cooling_temperature_in_celsius=self.heat_distribution_system_set_cooling_temperature_for_building_in_celsius,
            number_of_apartments=self.building_number_of_apartments,
            predictive=self.building_predictive_control,
            enable_opening_windows=self.building_enable_opening_windows,
            device_co2_footprint_in_kg=building_co2_footprint,
            investment_costs_in_euro=building_cost,
            maintenance_costs_in_euro_per_year=building_maintenance_costs_in_euro_per_year,  # noqa: E501 #
            lifetime_in_years=building_lifetime,
            subsidy_as_percentage_of_investment_costs=None,
        )
        my_building_information = building.BuildingInformation(config=my_building_config)

        my_building = building.Building(
            config=my_building_config, my_simulation_parameters=self.my_simulation_parameters
        )
        my_heat_distribution_controller_config = heat_distribution_system.HeatDistributionControllerConfig(
            building_name=self.building_name,
            name="HeatDistributionController",
            heating_system=self.heat_distribution_system_heating_system,  # HeatingSystemType.FLOORHEATING,
            set_heating_threshold_outside_temperature_in_celsius=self.heat_distribution_system_set_heating_threshold_outside_temperature_in_celsius,  # Heizgrenztemperatur
            heating_reference_temperature_in_celsius=self.heat_distribution_system_heating_reference_temperature_in_celsius,
            set_heating_temperature_for_building_in_celsius=self.heat_distribution_system_set_heating_temperature_for_building_in_celsius,  # Solltemperatur Gebäude Heizbetrieb
            set_cooling_temperature_for_building_in_celsius=self.heat_distribution_system_set_cooling_temperature_for_building_in_celsius,
            heating_load_of_building_in_watt=my_building_information.max_thermal_building_demand_in_watt,
            specific_heating_load_of_building_in_watt_per_m2=my_building_information
                                                             .max_thermal_building_demand_in_watt/self.building_absolute_conditioned_floor_area_in_m2,
        )

        my_heat_distribution_controller = heat_distribution_system.HeatDistributionController(
            config=my_heat_distribution_controller_config,
            my_simulation_parameters=self.my_simulation_parameters
        )

        my_heat_distribution_controller_information = (
            heat_distribution_system.HeatDistributionControllerInformation(
                config=my_heat_distribution_controller.hsd_controller_config
            )
        )


        # Build Occupancy
        household_name = self.loadprofile_household_utsp
        energy_intensity_name = self.loadprofile_energy_intensity_utsp
        travel_route_set_name = self.loadprofile_travel_route_set_utsp
        transportation_device_set_name = self.loadprofile_transportation_device_set_utsp
        charging_station_set_name = self.loadprofile_charging_station_set_utsp

        # Versuche, das entsprechende Attribut in lpgdata.py zu finden
        # Wenn das Attribut gefunden wurde, weise es einer anderen Variable zu
        household = getattr(Households, household_name, None)
        energy_intensity = getattr(EnergyIntensityType, energy_intensity_name, None)
        travel_route_set = getattr(TravelRouteSets, travel_route_set_name, None)
        transportation_device_set = getattr(TransportationDeviceSets, transportation_device_set_name, None)
        charging_station_set = getattr(ChargingStationSets, charging_station_set_name, None)  #

        if household is None:
            raise KeyError("Ungültiger Wert in Eingabeexcel Loadprofile für household")
        if energy_intensity is None:
            raise KeyError("Ungültiger Wert in Eingabeexcel Loadprofile für energy_intensity")
        if travel_route_set is None:
            raise KeyError("Ungültiger Wert in Eingabeexcel Loadprofile für loadprofile_travel_route_set_utsp")
        if transportation_device_set is None:
            raise KeyError("Ungültiger Wert in Eingabeexcel Loadprofile für transportation_device_set")
        if charging_station_set is None:
            raise KeyError("Ungültiger Wert in Eingabeexcel Loadprofile für charging_station_set")

        predefined_load_profile_name = None
        loadprofile_predefined_loadprofile_filepaths = None

        # Removes old results of loadprofilegenerator_connector_utsp.
        ordner_pfad_lpg_result_single_building = os.path.join(self.path_simulation_directory,"inputs", "LPG_Result","Results")

        if not os.path.exists(ordner_pfad_lpg_result_single_building):
            # Erstelle den Ordner, falls er nicht existiert
            os.makedirs(ordner_pfad_lpg_result_single_building)
            # os.makedirs(ordner_pfad_result_lpg)
            # os.makedirs(ordner_pfad_cache_lpg)
            print("INFO: LPG-Result Ordner für " + str(self.building_name)+ " erstelt " + str(ordner_pfad_lpg_result_single_building))

        if self.my_simulation_parameters.logging_level == 4:
            utsp_data_acquisition_mode = LpgDataAcquisitionMode.USE_PREDEFINED_PROFILE

        else:
            if isinstance(self.loadprofile_data_acquisition_mode, str):
                utsp_data_acquisition_mode = LpgDataAcquisitionMode[str(self.loadprofile_data_acquisition_mode.upper())]
            elif isinstance(self.loadprofile_data_acquisition_mode, LpgDataAcquisitionMode):
                utsp_data_acquisition_mode = self.loadprofile_data_acquisition_mode
            else:
                raise ValueError("Unknown data acquisition mode for lpg")

        if utsp_data_acquisition_mode == LpgDataAcquisitionMode.USE_PREDEFINED_PROFILE:
            household = None
            energy_intensity = None
            travel_route_set = None
            transportation_device_set = None
            charging_station_set = None

            if self.my_simulation_parameters.logging_level == 4:
                predefined_load_profile_name = "CHR01 Couple both at Work"
                loadprofile_predefined_loadprofile_filepaths = None
                print("INFO:utsp_data_acquisition_mode = predefined_profile")
            else:
                project_root =  Path(__file__).resolve().parents[4]
                predefined_load_profile_name = self.loadprofile_predefined_profile_name
                loadprofile_predefined_loadprofile_filepaths = str(project_root / Path(
                    self.loadprofile_predefined_loadprofile_filepaths))


        if utsp_data_acquisition_mode == LpgDataAcquisitionMode.USE_UTSP or utsp_data_acquisition_mode == LpgDataAcquisitionMode.USE_LOCAL_LPG:
            predefined_load_profile_name = None
            loadprofile_predefined_loadprofile_filepaths = None
            if self.car_existing == False:
                travel_route_set = None
                transportation_device_set = None
                charging_station_set = None

        config_index = re.search(r'\d+', self.config_name)

        if config_index:
            calculation_index_for_local_lpg = config_index.group(0)  # Gibt den gefundenen String zurück
            calculation_index_for_local_lpg = int(calculation_index_for_local_lpg)
        else:
            print(f"Kein Index für {self.config_name} gefunden... Nutze 1 als default index")
            calculation_index_for_local_lpg = 1

        my_occupancy_config = loadprofilegenerator_utsp_connector.UtspLpgConnectorConfig(
            building_name=self.building_name,
            name="Occupancy",
            data_acquisition_mode = utsp_data_acquisition_mode,
            name_of_predefined_loadprofile=predefined_load_profile_name,
            predefined_loadprofile_filepaths=loadprofile_predefined_loadprofile_filepaths,
            household=household,
            energy_intensity=energy_intensity,
            travel_route_set=travel_route_set,
            transportation_device_set=transportation_device_set,
            charging_station_set=charging_station_set,
            profile_with_washing_machine_and_dishwasher=self.loadprofile_profile_with_washing_machine_and_dishwasher_utsp,
            predictive_control=self.loadprofile_predictive_control_utsp,
            predictive=self.loadprofile_predictive_occupancy,
            result_dir_path=ordner_pfad_lpg_result_single_building,
            cache_dir_path=self.my_simulation_parameters.cache_dir_path,#ordner_pfad_cache_lpg,
            guid="",
            calculation_index_for_local_lpg=calculation_index_for_local_lpg
        )

        my_occupancy = loadprofilegenerator_utsp_connector.UtspLpgConnector(
            config=my_occupancy_config, my_simulation_parameters=self.my_simulation_parameters
        )

        # Build Heat Distribution System
        my_heat_distribution_config = heat_distribution_system.HeatDistributionConfig(
            building_name=self.building_name,
            name="HeatDistribution",
            heating_system=self.heat_distribution_system_heating_system,
            water_mass_flow_rate_in_kg_per_second=self.heat_distribution_system_nominal_water_mass_flow_rate_in_kg_per_second,
            absolute_conditioned_floor_area_in_m2 = self.building_absolute_conditioned_floor_area_in_m2,
            position_hot_water_storage_in_system = self.sh_storage_position,
            device_co2_footprint_in_kg=self.heat_distribution_system_co2_footprint,
            investment_costs_in_euro=self.heat_distribution_system_cost,
            lifetime_in_years=self.heat_distribution_system_lifetime,
            maintenance_costs_in_euro_per_year=self.heat_distribution_system_maintenance_costs_in_euro_per_year,
            subsidy_as_percentage_of_investment_costs=None,
        )

        my_heat_distribution = heat_distribution_system.HeatDistribution(
            my_simulation_parameters=self.my_simulation_parameters, config=my_heat_distribution_config
        )

        if self.heatpump_existing == True:
            # Build Heat Pump
            if self.heatpump_group_id not in [1.0,4.0]:
                specific_heat_capacity_of_primary_fluid = gt.media.Fluid(
                    borehole_heat_exchanger.FluidMediaType[self.heatpump_heat_source_fluid_type_primary_side].value,
                    self.heatpump_heat_source_mass_fraction_of_fluid_mixed_in_water * 100).cp
            else:
                specific_heat_capacity_of_primary_fluid=0


            my_heatpump_config = more_advanced_heat_pump_hplib.MoreAdvancedHeatPumpHPLibConfig(
                building_name=self.building_name,
                name="HeatPump",
                model=self.model,  # ""Generic
                fluid_primary_side=self.heatpump_fluid_primary_side,
                group_id=self.heatpump_group_id,  # bestimmt WP Art (W/W,L/W,etc) --> siehe Doku zu Bib
                heating_reference_temperature_in_celsius=self.heatpump_heating_reference_temperature_in_celsius,
                flow_temperature_in_celsius=self.heatpump_flow_temperature_in_celsius, # bei on/off regelung sollwert für Austrittstemperatur, bei modulierend regelung entspricht wert hds Flow Temp, nur bei "generic" Modlel von bedeutung
                set_thermal_output_power_in_watt=self.heatpump_set_thermal_output_power_in_watt,
                cycling_mode=self.heatpump_cycling_mode,
                minimum_running_time_in_seconds = self.heatpump_minimum_running_time_in_seconds,
                minimum_idle_time_in_seconds = self.heatpump_minimum_idle_time_in_seconds,
                position_hot_water_storage_in_system = self.sh_storage_position,
                with_domestic_hot_water_preparation=self.heatpump_with_domestic_hot_water_preparation,
                passive_cooling_with_brine=self.heatpump_passive_cooling_with_brine,
                electrical_input_power_brine_pump_in_watt=self.heatpump_electrical_input_power_brine_pump_in_watt,
                massflow_nominal_secondary_side_in_kg_per_s = self.heatpump_massflow_nominal_secondary_in_kg_per_s,
                specific_heat_capacity_of_primary_fluid=specific_heat_capacity_of_primary_fluid,
                minimum_thermal_output_power_in_watt = self.heatpump_minimum_thermal_output_power_in_watt,
                device_co2_footprint_in_kg=self.heatpump_co2_footprint,
                # value from emission_factors_and_costs_devices.csv
                investment_costs_in_euro=self.heatpump_cost,
                lifetime_in_years=self.heatpump_lifetime,  # value from emission_factors_and_costs_devices.csv
                maintenance_costs_in_euro_per_year=self.heatpump_maintenance_costs_in_euro_per_year,  # source:  VDI2067-1
                subsidy_as_percentage_of_investment_costs=None,
            )

            my_heatpump = more_advanced_heat_pump_hplib.MoreAdvancedHeatPumpHPLib(
                config=my_heatpump_config,
                my_simulation_parameters=self.my_simulation_parameters,
            )

            if self. heatpump_with_space_heating == True:
                my_heatpump_controller_space_heating_config = more_advanced_heat_pump_hplib.MoreAdvancedHeatPumpHPLibControllerSpaceHeatingConfig(
                    building_name=self.building_name,
                    name="HPControllerSH",
                    mode=self.heatpump_spaceheating_mode,  # 1: on/off controller modulierend, 2: regulated Controller inkl. kühlung
                    set_heating_threshold_outside_temperature_in_celsius=self.heat_distribution_system_set_heating_threshold_outside_temperature_in_celsius,
                    set_cooling_threshold_outside_temperature_in_celsius=self.heat_distribution_system_set_cooling_threshold_outside_temperature_in_celsius,
                  #  temperature_offset_for_state_conditions_in_celsius=20,#self.temperature_offset_for_state_conditions_in_celsius_hp,
                    upper_temperature_offset_for_state_conditions_in_celsius=self.heatpump_upper_temperature_offset_for_state_conditions_in_celsius,
                    lower_temperature_offset_for_state_conditions_in_celsius=self.heatpump_lower_temperature_offset_for_state_conditions_in_celsius,
                    heat_distribution_system_type=my_heat_distribution_controller_information.heat_distribution_system_type,
                )

                my_heatpump_controller_space_heating = more_advanced_heat_pump_hplib.MoreAdvancedHeatPumpHPLibControllerSpaceHeating(
                    config=my_heatpump_controller_space_heating_config,
                    my_simulation_parameters=self.my_simulation_parameters
                )
            if self.heatpump_with_domestic_hot_water_preparation == True:
                my_heatpump_controller_dhw_config = more_advanced_heat_pump_hplib.MoreAdvancedHeatPumpHPLibControllerDHWConfig(
                    building_name=self.building_name,
                    name="HPControllerDHW",
                    t_min_dhw_storage_in_celsius=self.dhw_storage_t_min_in_celsius,
                    t_max_dhw_storage_in_celsius=self.dhw_storage_t_max_in_celsius,
                    thermalpower_dhw_is_constant=self.heatpump_thermalPower_is_constant_for_dhw,
                    p_th_max_dhw_in_watt=self.heatpump_p_th_max_dhw_in_watt,
                )

                my_heatpump_controller_dhw = more_advanced_heat_pump_hplib.MoreAdvancedHeatPumpHPLibControllerDHW(
                    config=my_heatpump_controller_dhw_config,
                    my_simulation_parameters=self.my_simulation_parameters
                )

        if self.solar_thermal_collector_for_dhw_existing == True:
            # Build Solar Thermal Collector
            
            my_solar_thermal_collector_controller_config = solar_thermal_system.SolarThermalSystemControllerConfig(
                building_name=self.building_name,
                name="SolarThermalSystemController",
                set_temperature_difference_for_on=self.solar_thermal_collector_for_dhw_set_temperature_difference_for_on
            )

            my_solar_thermal_collector_controller = solar_thermal_system.SolarThermalSystemController(
                config=my_solar_thermal_collector_controller_config, my_simulation_parameters=self.my_simulation_parameters
            )

            my_solar_thermal_collector_config = solar_thermal_system.SolarThermalSystemConfig(
                building_name=self.building_name,
                coordinates=Coordinates(latitude=self.building_latitude, longitude=self.building_longitude),
                name="SolarThermalSystem",
                azimuth=self.solar_thermal_collector_for_dhw_azimuth,
                tilt=self.solar_thermal_collector_for_dhw_tilt,
                area_m2=self.solar_thermal_collector_for_dhw_area_m2,  # m2
                eta_0=self.solar_thermal_collector_for_dhw_eta_0,
                a_1_w_m2_k=self.solar_thermal_collector_for_dhw_a_1_w_m2_k,  # W/(m2*K)
                a_2_w_m2_k=self.solar_thermal_collector_for_dhw_a_2_w_m2_k,  # W/(m2*K2)
                old_solar_pump=self.solar_thermal_collector_for_dhw_old_solar_pump,
                device_co2_footprint_in_kg=self.solar_thermal_collector_for_dhw_co2_footprint,
                investment_costs_in_euro=self.solar_thermal_collector_for_dhw_investment_cost,
                maintenance_costs_in_euro_per_year=self.solar_thermal_collector_for_dhw_maintenance_costs_eur_per_y,
                lifetime_in_years=self.solar_thermal_collector_for_dhw_lifetime,
                subsidy_as_percentage_of_investment_costs=None,
                source_weight=self.solar_thermal_collector_for_dhw_source_weight,
            )

            my_solar_thermal_collector = solar_thermal_system.SolarThermalSystem(
                config=my_solar_thermal_collector_config, my_simulation_parameters=self.my_simulation_parameters
            )


        if self.conventional_heater_existing == True:

            self.conventional_heater_fuel = Conventional_Fuel[str(self.conventional_heater_fuel_type).upper()].name

            if self.heatpump_existing == False:
                self.conventional_heater_set_heating_threshold_outside_temperature_in_celsius_for_bivalent_use=self.heat_distribution_system_set_heating_threshold_outside_temperature_in_celsius

            if self.sh_storage_existing == False:
                raise KeyError("conventional heater only works with Hot Water Storage for Space heating! - No Hot Water Storage Exist in Excel")

            if self.heatpump_existing and self.heatpump_with_domestic_hot_water_preparation:
                secondary_mode_of_conventional_heater_for_dhw = True
            else:
                secondary_mode_of_conventional_heater_for_dhw = False

            my_conventional_heater_controller_config = generic_boiler.GenericBoilerControllerConfig(
                building_name=self.building_name,
                name="ConventionalHeaterController",
                is_modulating=self.conventional_heater_boiler_is_modulating,
                set_heating_threshold_outside_temperature_in_celsius=self.conventional_heater_set_heating_threshold_outside_temperature_in_celsius_for_bivalent_use,
                minimal_thermal_power_in_watt=self.conventional_heater_minimal_thermal_power_in_watt,
                maximal_thermal_power_in_watt=self.conventional_heater_maximal_thermal_power_in_watt,
                set_temperature_difference_for_full_power=self.conventional_heater_set_temperature_difference_for_full_power,
                minimum_runtime_in_seconds=self.conventional_heater_minimum_running_time_in_seconds,
                minimum_resting_time_in_seconds=self.conventional_heater_minimum_resting_time_in_seconds,
                hysteresis_water_temperature_offset=10,
                with_domestic_hot_water_preparation=self.conventional_heater_with_domestic_hot_water_preparation,
                secondary_mode=secondary_mode_of_conventional_heater_for_dhw
            )

            my_conventional_heater_controller = generic_boiler.GenericBoilerController(
                my_simulation_parameters=self.my_simulation_parameters, config=my_conventional_heater_controller_config,
            )

            if isinstance(self.conventional_heater_boiler_type, (int, float)):
                conventional_heater_boiler_type = generic_boiler.BoilerType(int(self.conventional_heater_boiler_type))
            elif isinstance(self.conventional_heater_boiler_type, str):
                conventional_heater_boiler_type = generic_boiler.BoilerType[self.conventional_heater_boiler_type.upper()]
            elif isinstance(self.conventional_heater_boiler_type, generic_boiler.BoilerType):
                conventional_heater_boiler_type = self.conventional_heater_boiler_type
            else:
                raise TypeError(
                    f"conventional_heater_boiler_type muss entweder ein int, float oder eine Instanz von generic_boiler.BoilerType sein. Type aktuell: {type(self.conventional_heater_boiler_type)}")

            if isinstance(self.conventional_heater_fuel, str):
                conventional_heater_fuel = lt.LoadTypes[str(self.conventional_heater_fuel.upper())]
            elif isinstance(self.conventional_heater_fuel, lt.LoadTypes):
                conventional_heater_fuel = self.conventional_heater_fuel
            else:
                raise TypeError(
                    f"conventional_heater_fuel muss entweder ein str oder eine Instanz von lt.LoadTypes sein. Type aktuell: {type(self.conventional_heater_fuel)}")

            # Build Gas heater For Space Heating
            my_conventional_heater_config = generic_boiler.GenericBoilerConfig(
                building_name=self.building_name,
                name="ConventionalHeater",
                boiler_type=conventional_heater_boiler_type,
                energy_carrier=conventional_heater_fuel,
                temperature_delta_in_celsius=self.conventional_heater_temperature_delta_in_celsius,
                minimal_thermal_power_in_watt=self.conventional_heater_minimal_thermal_power_in_watt,
                maximal_thermal_power_in_watt=self.conventional_heater_maximal_thermal_power_in_watt,
                eff_th_min=self.conventional_heater_eff_th_min,
                eff_th_max=self.conventional_heater_eff_th_max,
                device_co2_footprint_in_kg=self.conventional_heater_co2_footprint, # nur einmal in config excel vorgegeben, darum teilt sich auf auf sh und dhw
                investment_costs_in_euro=self.conventional_heater_cost, # nur einmal in config excel vorgegeben, darum teilt sich auf auf sh und dhw
                lifetime_in_years=self.conventional_heater_lifetime,
                maintenance_costs_in_euro_per_year=self.conventional_heater_maintenance_costs_in_euro_per_year,
                subsidy_as_percentage_of_investment_costs=None,
                consumption_in_kilowatt_hour=0,
            )

            my_conventional_heater = generic_boiler.GenericBoiler(
                config=my_conventional_heater_config, my_simulation_parameters=self.my_simulation_parameters,
            )

            if  self.conventional_heater_fuel is Conventional_Fuel.GAS.name:
                my_gas_meter_config = gas_meter.GasMeterConfig(
                    building_name=self.building_name,
                    name="GasMeter",
                    total_energy_from_grid_in_kwh=0.0,
                    gas_loadtype=lt.LoadTypes.GAS,
                    device_co2_footprint_in_kg=None,
                    investment_costs_in_euro=None,
                    lifetime_in_years=None,
                    maintenance_costs_in_euro_per_year=None,
                    subsidy_as_percentage_of_investment_costs=None,
                )

                my_gas_meter = gas_meter.GasMeter(
                    my_simulation_parameters=self.my_simulation_parameters,
                    config=my_gas_meter_config,
                )

        # Build Heat Water Storage
        if self.sh_storage_existing == True:
            my_sh_storage_config = simple_water_storage.SimpleHotWaterStorageConfig(
                building_name=self.building_name,
                name="SHStorage",
                volume_heating_water_storage_in_liter=self.sh_storage_volume_in_liter,
                heat_transfer_coefficient_in_watt_per_m2_per_kelvin=self.sh_storage_heat_transfer_coefficient_in_watt_per_m2_per_kelvin,
                heat_exchanger_is_present=self.sh_storage_heat_exchanger_is_present,
                position_hot_water_storage_in_system=self.sh_storage_position,
                ambient_temperature_in_celsius=17,
                device_co2_footprint_in_kg=self.sh_storage_co2_footprint,
                investment_costs_in_euro=self.sh_storage_cost,
                lifetime_in_years=self.sh_storage_lifetime,
                maintenance_costs_in_euro_per_year=self.sh_storage_maintenance_costs_in_euro_per_year,
                subsidy_as_percentage_of_investment_costs=None,
            )

            my_hot_water_storage = simple_water_storage.SimpleHotWaterStorage(
                config=my_sh_storage_config,
                my_simulation_parameters=self.my_simulation_parameters,
            )

            my_hot_water_storage.mean_water_temperature_in_water_storage_in_celsius = 35

        # Build DHW Storage
        if self.dhw_storage_existing == True:
            from hisim.components.configuration import HouseholdWarmWaterDemandConfig
            HouseholdWarmWaterDemandConfig.freshwater_temperature = self.freshwater_temperature
            HouseholdWarmWaterDemandConfig.ww_temperature_demand = self.ww_temperature_demand  # DHW Speichertemperatur

            if self.ww_temperature_demand > self.dhw_storage_t_max_in_celsius:
                raise KeyError("ERROR: Temperatur TWW-Austritt soll höher als DHW Temperatur WP-Austritt sein! Eiganbewerte prüfen ")

            my_dhw_storage_config = simple_water_storage.SimpleDHWStorageConfig(
                building_name=self.building_name,
                name="DHWStorage",
                ambient_temperature_in_celsius=17,
                volume_heating_water_storage_in_liter=self.dhw_storage_volume_in_liter,
                heat_transfer_coefficient_in_watt_per_m2_per_kelvin=self.dhw_storage_heat_transfer_coefficient_in_watt_per_m2_per_kelvin,
                device_co2_footprint_in_kg=self.dhw_storage_co2_footprint,
                investment_costs_in_euro=self.dhw_storage_cost,
                lifetime_in_years=self.dhw_storage_lifetime,
                maintenance_costs_in_euro_per_year=self.dhw_storage_maintenance_costs_in_euro_per_year,
                subsidy_as_percentage_of_investment_costs=None,
            )

            my_dhw_storage = simple_water_storage.SimpleDHWStorage(
                config=my_dhw_storage_config,
                my_simulation_parameters=self.my_simulation_parameters,
            )
            my_dhw_storage.mean_water_temperature_in_water_storage_in_celsius = 60

        # Build PV
        if self.pv_existing == True:
            my_photovoltaic_system_config = generic_pv_system.PVSystemConfig(
                building_name=self.building_name,
                time=self.my_simulation_parameters.year,
                power_in_watt=self.pv_power,
                load_module_data=self.pv_load_module_data,
                module_name=self.pv_module_name,
                module_database=generic_pv_system.PVLibModuleAndInverterEnum(self.pv_module_database),
                integrate_inverter=self.pv_integrate_inverter,
                inverter_database=generic_pv_system.PVLibModuleAndInverterEnum(self.pv_inverter_database),
                inverter_name=self.pv_inverter_name,
                name="PVSystemRooftop",
                azimuth=self.pv_azimuth,
                tilt=self.pv_tilt,
                share_of_maximum_pv_potential=self.pv_share_of_maximum_pv_potential,
                source_weight=999,
                location=self.location,
                device_co2_footprint_in_kg=self.pv_co2_footprint,
                investment_costs_in_euro=self.pv_cost,
                lifetime_in_years=self.pv_lifetime,
                maintenance_costs_in_euro_per_year=self.pv_maintenance_costs_in_euro_per_year,
                prediction_horizon=self.pv_prediction_horizon,
                predictive=self.pv_predictive,
                predictive_control=self.pv_predictive_control,
                subsidy_as_percentage_of_investment_costs=None,
            )

            my_photovoltaic_system = generic_pv_system.PVSystem(
                config=my_photovoltaic_system_config,
                my_simulation_parameters=self.my_simulation_parameters,
            )

        # Build Battery
        if self.battery_existing == True:

            my_advanced_battery_config = advanced_battery_bslib.BatteryConfig(
                building_name=self.building_name,
                name="Battery",
                custom_battery_capacity_generic_in_kilowatt_hour=self.battery_capacity_generic_in_kilowatt_hour,
                custom_pv_inverter_power_generic_in_watt=self.battery_inverter_power_generic_in_watt,
                source_weight=self.ems_source_weight_battery,
                system_id=self.battery_system_id,   #: name of battery to search in database (bslib)
                charge_in_kwh=0,#self.battery_charge_in_kwh,
                discharge_in_kwh=0,#self.battery_discharge_in_kwh,
                device_co2_footprint_in_kg=self.battery_co2_footprint,
                investment_costs_in_euro=self.battery_cost,
                lifetime_in_years=self.battery_lifetime,
                lifetime_in_cycles=self.battery_lifetime_in_cycles,
                maintenance_costs_in_euro_per_year=self.battery_maintenance_costs_in_euro_per_year,
                subsidy_as_percentage_of_investment_costs=None,
            )

            my_advanced_battery = advanced_battery_bslib.Battery(
                my_simulation_parameters=self.my_simulation_parameters,
                config=my_advanced_battery_config,
            )

        # Build EMS Controller Gebäudeebene
        if self.ems_existing == True:
            if isinstance(self.ems_strategy, (int, float)):
                ems_building_strategie = controller_l2_district_energy_management_system.EMSControlStrategy(
                    int(self.ems_strategy))
            elif isinstance(self.ems_strategy, controller_l2_district_energy_management_system.EMSControlStrategy):
                ems_building_strategie = self.ems_strategy
            else:
                raise TypeError(
                    f"ems_strategy muss entweder ein int, float oder eine Instanz von EMSControlStrategy sein. Type aktuell: {type(self.ems_strategy)}")

            my_ems_building_config = controller_l2_district_energy_management_system.EMSDistrictConfig(
                building_name=self.building_name,
                name="EMS",
                strategy=ems_building_strategie,
                limit_to_shave=self.ems_limit_to_shave,
                building_indoor_temperature_offset_value=self.ems_building_temperature_offset_value,
                domestic_hot_water_storage_temperature_offset_value=self.ems_dhw_storage_temperature_offset_value,         #dhw
                space_heating_water_storage_temperature_offset_value=self.sh_simple_ems_sh_storage_temperature_offset_value  # heizung
            )

            my_ems_building =controller_l2_district_energy_management_system.L2GenericDistrictEnergyManagementSystem(
                    my_simulation_parameters=self.my_simulation_parameters,
                    config=my_ems_building_config,
                )

        # Build Electricity Meter
        my_electricity_meter_config=electricity_meter.ElectricityMeterConfig(
            building_name=self.building_name,
            name="ElectricityMeter",
            device_co2_footprint_in_kg=None,
            investment_costs_in_euro=None,
            lifetime_in_years=None,
            maintenance_costs_in_euro_per_year=None,
            subsidy_as_percentage_of_investment_costs=None,
        )

        my_electricity_meter = electricity_meter.ElectricityMeter(
            my_simulation_parameters=self.my_simulation_parameters,
            config=my_electricity_meter_config
        )

        # Build Electric Vehicle(s)
        if self.car_existing == True:
            if self.car_number_of_electric > 1:
                raise KeyError("Error: Derzeit kann nur ein E-Auto simuliert werden. Anzahl der Fahrzeuge in Eingabeexcel prüfen")

            charging_power = float((charging_station_set.Name or "").split("with ")[1].split(" kW")[0])

            my_car_config = generic_car.CarConfig(
                building_name=self.building_name,
                name="Car",
                source_weight=self.ems_source_weight_car,
                fuel=lt.LoadTypes.ELECTRICITY,
                consumption_per_km=self.car_consumption_per_km_electric,
                device_co2_footprint_in_kg=self.car_co2_footprint,
                investment_costs_in_euro=self.car_cost,
                lifetime_in_years=self.car_lifetime,
                maintenance_costs_in_euro_per_year=self.car_maintenance_costs_in_euro_per_year,
            )

            my_car_battery_config = advanced_ev_battery_bslib.CarBatteryConfig(
                building_name=self.building_name,
                name=f"CarBattery",
                system_id=self.car_battery_system_id_electric,
                p_inv_custom=charging_power*1000,
                e_bat_custom=self.car_battery_capacity_in_kwh,
                source_weight=self.ems_source_weight_car,
                charge=0,
                discharge=0,
            )

            my_car_battery_controller_config = controller_l1_generic_ev_charge.ChargingStationConfig(
                building_name=self.building_name,
                name=f"CarChargeController",
                source_weight=self.ems_source_weight_car,
                charging_station_set=my_occupancy_config.charging_station_set,
                battery_set=self.car_battery_setpoint_state_of_charge,
                lower_threshold_charging_power=charging_power * 1e3 * 0.1,
                device_co2_footprint_in_kg=self.car_battery_co2_footprint,
                investment_costs_in_euro=self.car_battery_cost,
                lifetime_in_years=self.car_battery_lifetime,
                maintenance_costs_in_euro_per_year=self.car_battery_maintenance_costs_in_euro_per_year,
            )

            my_car_information = generic_car.GenericCarInformation(my_occupancy_instance=my_occupancy)

            my_cars: List[generic_car.Car] = []
            my_car_batteries: List[advanced_ev_battery_bslib.CarBattery] = []
            my_car_battery_controllers: List[controller_l1_generic_ev_charge.L1Controller] = []
            car_number = 1

            for car_information_dict in my_car_information.data_dict_for_car_component.values():
                # Build Electric Vehicles
                my_car_config.name = f"Car_{car_number}"
                my_car = generic_car.Car(
                    my_simulation_parameters=self.my_simulation_parameters,
                    config=my_car_config,
                    data_dict_with_car_information=car_information_dict,
                )
                my_cars.append(my_car)
                # Build Electric Vehicle Batteries
                my_car_battery_config.source_weight = my_car.config.source_weight
                my_car_battery_config.name = f"CarBattery_{car_number}"
                my_car_battery = advanced_ev_battery_bslib.CarBattery(
                    my_simulation_parameters=self.my_simulation_parameters, config=my_car_battery_config,
                )
                my_car_batteries.append(my_car_battery)
                # Build Electric Vehicle Battery Controller
                my_car_battery_controller_config.source_weight = my_car.config.source_weight
                my_car_battery_controller_config.name = f"CarChargeControl_{car_number}"

                my_car_battery_controller = controller_l1_generic_ev_charge.L1Controller(
                    my_simulation_parameters=self.my_simulation_parameters, config=my_car_battery_controller_config,
                )
                my_car_battery_controllers.append(my_car_battery_controller)
                car_number += 1

            # Connect Electric Vehicles and Car Batteries
            zip_car_battery_controller_lists = list(zip(my_cars, my_car_batteries, my_car_battery_controllers))
            for car, car_battery, car_battery_controller in zip_car_battery_controller_lists:
                car_battery_controller.connect_only_predefined_connections(car)
                car_battery_controller.connect_only_predefined_connections(car_battery)
                car_battery.connect_only_predefined_connections(car_battery_controller)

        # =================================================================================================================================
        # Connect Component Inputs with Outputs
        if self.conventional_heater_existing:

            my_conventional_heater_controller.connect_only_predefined_connections(self.my_weather,)
            my_conventional_heater.connect_only_predefined_connections(my_conventional_heater_controller)

            #### connecting sh parts
            if self.heatpump_existing == True:
                my_conventional_heater_controller.connect_input(
                    my_conventional_heater_controller.WaterTemperatureInputFromWaterStorage,
                    my_hot_water_storage.component_name,
                    my_hot_water_storage.WaterTemperatureToSecondaryHeatGenerator,
                )
                my_conventional_heater.connect_input(
                    my_conventional_heater.WaterInputTemperatureSh,
                    my_hot_water_storage.component_name,
                    my_hot_water_storage.WaterTemperatureToSecondaryHeatGenerator,
                )
            else:
                my_conventional_heater_controller.connect_input(
                    my_conventional_heater_controller.WaterTemperatureInputFromWaterStorage,
                    my_hot_water_storage.component_name,
                    my_hot_water_storage.WaterTemperatureToHeatGenerator,
                )
                my_conventional_heater.connect_input(
                    my_conventional_heater.WaterInputTemperatureSh,
                    my_hot_water_storage.component_name,
                    my_hot_water_storage.WaterTemperatureToHeatGenerator,
                )
            my_conventional_heater_controller.connect_input(
                my_conventional_heater_controller.HeatingFlowTemperatureFromHeatDistributionSystem,
                my_heat_distribution_controller.component_name,
                my_heat_distribution_controller.HeatingFlowTemperature,
            )

            #### connecting dhw parts
            if self.conventional_heater_with_domestic_hot_water_preparation == True:
                my_conventional_heater_controller.connect_input(
                    my_conventional_heater_controller.WaterTemperatureInputFromDHWStorage,
                    my_dhw_storage.component_name,
                    my_dhw_storage.WaterTemperatureToHeatGenerator,
                )
                my_conventional_heater.connect_input(
                    my_conventional_heater.WaterInputTemperatureDhw,
                    my_dhw_storage.component_name,
                    my_dhw_storage.WaterTemperatureToHeatGenerator,
                )

                if self.heatpump_existing==True and self.heatpump_with_domestic_hot_water_preparation==True:
                    if self.solar_thermal_collector_for_dhw_existing == False:
                        # paralleler betrieb von Wärmeerzeuger
                        my_dhw_storage.connect_input(
                            my_dhw_storage.WaterTemperatureFromSecondaryHeatGenerator,
                            my_conventional_heater.component_name,
                            my_conventional_heater.WaterOutputTemperatureDhw,
                        )
                        my_dhw_storage.connect_input(
                            my_dhw_storage.WaterMassFlowRateFromSecondaryHeatGenerator,
                            my_conventional_heater.component_name,
                            my_conventional_heater.WaterOutputMassFlowDhw,
                        )
                    else:
                        raise KeyError("dhw storage soll mit hp, conventional heater und solar thermie verbudnen werden.. allerdings nur zwei möglich")
                else:
                    my_dhw_storage.connect_input(
                        my_dhw_storage.WaterTemperatureFromHeatGenerator,
                        my_conventional_heater.component_name,
                        my_conventional_heater.WaterOutputTemperatureDhw,
                    )
                    my_dhw_storage.connect_input(
                        my_dhw_storage.WaterMassFlowRateFromHeatGenerator,
                        my_conventional_heater.component_name,
                        my_conventional_heater.WaterOutputMassFlowDhw,
                    )

            if self.conventional_heater_fuel is Conventional_Fuel.GAS.name:
                my_gas_meter.add_component_input_and_connect(
                    source_object_name=my_conventional_heater.component_name,
                    source_component_output=my_conventional_heater.EnergyDemandSh,
                    source_load_type=loadtypes.LoadTypes.GAS,
                    source_unit=loadtypes.Units.WATT_HOUR,
                    source_tags=[loadtypes.InandOutputType.GAS_CONSUMPTION_UNCONTROLLED],
                    source_weight=999,
                )
                if self.conventional_heater_with_domestic_hot_water_preparation == True:
                    my_gas_meter.add_component_input_and_connect(
                        source_object_name=my_conventional_heater.component_name,
                        source_component_output=my_conventional_heater.EnergyDemandDhw,
                        source_load_type=loadtypes.LoadTypes.GAS,
                        source_unit=loadtypes.Units.WATT_HOUR,
                        source_tags=[loadtypes.InandOutputType.GAS_CONSUMPTION_UNCONTROLLED],
                        source_weight=999,
                    )

        # =================================================================================================================================
        # Connect Component Inputs with Outputs

        my_building.connect_only_predefined_connections(self.my_weather)
        my_building.connect_only_predefined_connections(my_occupancy)

        my_building.connect_input(
            my_building.ThermalPowerDelivered,
            my_heat_distribution.component_name,
            my_heat_distribution.ThermalPowerDelivered,
        )

        #################################################################################################################
        my_heat_distribution_controller.connect_only_predefined_connections(
            self.my_weather, my_building)

        my_heat_distribution.connect_only_predefined_connections(
            my_building, my_heat_distribution_controller)

        if self.sh_storage_existing == True and self.sh_storage_position == 1:
            my_heat_distribution.connect_input(
                my_heat_distribution.WaterTemperatureInput,
                my_hot_water_storage.component_name,
                my_hot_water_storage.WaterTemperatureToHeatDistribution,
            )

        else:
            my_heat_distribution.connect_input(
                my_heat_distribution.WaterTemperatureInput,
                my_heatpump.component_name,
                my_heatpump.TemperatureOutputSH,
            )

            my_heat_distribution.connect_input(
                my_heat_distribution.WaterMassFlowInput,
                my_heatpump.component_name,
                my_heatpump.MassFlowOutputSH,
            )
        ################################################################################################################
        if self.solar_thermal_collector_for_dhw_existing:
            my_solar_thermal_collector_controller.connect_only_predefined_connections(my_dhw_storage,my_solar_thermal_collector )
            my_solar_thermal_collector.connect_only_predefined_connections(my_dhw_storage,
                                                                           my_solar_thermal_collector_controller,
                                                                           self.my_weather)

            my_dhw_storage.connect_input(
                my_dhw_storage.WaterTemperatureFromHeatGenerator,
                my_solar_thermal_collector.component_name,
                my_solar_thermal_collector.WaterTemperatureOutput,
            )
            my_dhw_storage.connect_input(
                my_dhw_storage.WaterMassFlowRateFromHeatGenerator,
                my_solar_thermal_collector.component_name,
                my_solar_thermal_collector.WaterMassFlowOutput,
            )

            # Connect gas as secondary heat generator
            if self.heatpump_existing == True and self.heatpump_with_domestic_hot_water_preparation == True:
                if self.conventional_heater_existing and self.conventional_heater_with_domestic_hot_water_preparation:
                    raise ValueError("Either Heatpump or Conventional Heater with DHW Preparation must be existing to connect Solar Thermal Collector for DHW")
                my_dhw_storage.connect_input(
                    my_dhw_storage.WaterTemperatureFromSecondaryHeatGenerator,
                    my_heatpump.component_name,
                    my_heatpump.TemperatureOutputDHW,
                )
                my_dhw_storage.connect_input(
                    my_dhw_storage.WaterMassFlowRateFromSecondaryHeatGenerator,
                    my_heatpump.component_name,
                    my_heatpump.MassFlowOutputDHW,
                )
            elif self.conventional_heater_existing == True and self.conventional_heater_with_domestic_hot_water_preparation == True:
                if self.heatpump_existing and self.heatpump_with_domestic_hot_water_preparation:
                    raise ValueError(
                        "Either Heatpump or Conventional Heater with DHW Preparation must be existing to connect Solar Thermal Collector for DHW")
                my_dhw_storage.connect_input(
                    my_dhw_storage.WaterTemperatureFromSecondaryHeatGenerator,
                    my_conventional_heater.component_name,
                    my_conventional_heater.WaterOutputTemperatureDhw,
                )
                my_dhw_storage.connect_input(
                    my_dhw_storage.WaterMassFlowRateFromSecondaryHeatGenerator,
                    my_conventional_heater.component_name,
                    my_conventional_heater.WaterOutputMassFlowDhw,
                )
            else:
                raise KeyError("Either Heatpump or Conventional Heater with DHW Preparation must be existing to connect Solar Thermal Collector for DHW")
        #################################################################################################################
        my_dhw_storage.connect_only_predefined_connections(my_occupancy, )
        #################################################################################################################
        if self.heatpump_existing == True:
            if self.heatpump_fluid_primary_side.lower() in ["water", "brine"]:
                if type(self.heatpump_heat_source_if_not_air) is str:
                    self.heatpump_heat_source_if_not_air = Heat_Source_For_Brine_Heat_Pumps(
                        self.heatpump_heat_source_if_not_air)
                elif type(self.heatpump_heat_source_if_not_air) is Heat_Source_For_Brine_Heat_Pumps:
                    self.heatpump_heat_source_if_not_air = self.heatpump_heat_source_if_not_air
                else:
                    raise ValueError("Unknown heat source type")
            else:
                self.heatpump_heat_source_if_not_air = None


            my_heatpump.connect_only_predefined_connections(self.my_weather)

            if my_heatpump.parameters['Group'].iloc[0] == 1.0 or my_heatpump.parameters['Group'].iloc[
                0] == 4.0:
                print("INFO: Connection von HeatPump mit Außenlufttemperatur")
                my_heatpump.connect_input(
                    my_heatpump.TemperatureInputPrimary,
                    self.my_weather.component_name,
                    self.my_weather.DailyAverageOutsideTemperatures,
                )

            if my_heatpump.parameters['Group'].iloc[0] == 2.0 or my_heatpump.parameters['Group'].iloc[0] == 5.0:
                # Verknüpfung mit Sole als Umgebungswärmeqzuelle über entweder über Quarttiermodell oder wenn eigene Sole im Gebäude dann hier mit sole kreis aufnehmen und direkt verknüpfen
                print("INFO: Connection von HeatPump mit Soletemperatur")

            if my_heatpump.parameters['Group'].iloc[0] == 3.0 or my_heatpump.parameters['Group'].iloc[0] == 6.0:
                # Verknüpfung mit Wasser als Umgebungswärmeqzuelle über Quartiermodell da quartier Nahwärmenetz
                print("INFO: Connection von HeatPump mit Wassertemperatur")

            if self.heatpump_fluid_primary_side.lower() in ["water", "brine"]:

                if self.heatpump_heat_source_if_not_air in [Heat_Source_For_Brine_Heat_Pumps.NEAR_SURFACE_BRINE_TEMPERATURE,
                                                   Heat_Source_For_Brine_Heat_Pumps.CONSTANT_TEMPERATURE,
                                                   Heat_Source_For_Brine_Heat_Pumps.CONSTANT_THERMAL_POWER]:
                    heatpump_heat_source_fluid_type_primary_side = simple_heat_source.FluidMediaType[self.heatpump_heat_source_fluid_type_primary_side]
                    const_source=simple_heat_source.SimpleHeatSourceType[self.heatpump_heat_source_if_not_air.name]

                    my_hp_heat_source_config = simple_heat_source.SimpleHeatSourceConfig(
                        building_name=self.building_name,
                        name="SimpleHeatSource",
                        const_source=const_source,
                        power_th_in_watt=self.simple_heatsource_const_value_of_const_heat_source,
                        temperature_out_in_celsius=self.simple_heatsource_const_value_of_const_heat_source,
                        fluid_type=heatpump_heat_source_fluid_type_primary_side,
                        mass_fraction_of_fluid_mixed_in_water=self.heatpump_heat_source_mass_fraction_of_fluid_mixed_in_water,
                        massflow_nominal_in_kg_per_s=None,
                        use_external_massflow_as_signal_input_for_nominal_massflow=False,
                        device_co2_footprint_in_kg=self.simple_heatsource_co2_footprint,
                        investment_costs_in_euro=self.simple_heatsource_cost,
                        lifetime_in_years=self.simple_heatsource_lifetime,
                        maintenance_costs_in_euro_per_year=self.simple_heatsource_maintenance_costs_in_euro_per_year,
                    )

                    my_hp_heat_source = simple_heat_source.SimpleHeatSource(
                        my_simulation_parameters=self.my_simulation_parameters,
                        config=my_hp_heat_source_config,
                    )

                    my_hp_heat_source.connect_only_predefined_connections(self.my_weather, )

                    my_heatpump.connect_input(
                        my_heatpump.TemperatureInputPrimary,
                        my_hp_heat_source.component_name,
                        my_hp_heat_source.TemperatureOutput,
                    )

                    my_hp_heat_source.connect_input(
                        my_hp_heat_source.MassFlow,
                        my_heatpump.component_name,
                        my_heatpump.MassflowPrimarySide,
                    )

                    my_hp_heat_source.connect_input(
                        my_hp_heat_source.TemperatureInput,
                        my_heatpump.component_name,
                        my_heatpump.BrineTemperaturePrimaryOut,
                    )
                elif self.heatpump_heat_source_if_not_air in [Heat_Source_For_Brine_Heat_Pumps.GROUND_PROBE]:

                    ground_probe_sort_of_pipe = borehole_heat_exchanger.SortOfPipe[self.ground_probe_sort_of_pipe]
                    heatpump_heat_source_fluid_type_primary_side = borehole_heat_exchanger.FluidMediaType[self.heatpump_heat_source_fluid_type_primary_side]
                    ground_probe_bore_field_geometry = borehole_heat_exchanger.BoreFieldGeometry[self.ground_probe_bore_field_geometry]

                    my_hp_heat_source_config = borehole_heat_exchanger.GroundProbeConfig(
                        building_name=self.building_name,
                        name="GroundProbe",
                        sort_of_pipe=ground_probe_sort_of_pipe,
                        fluid_type=heatpump_heat_source_fluid_type_primary_side,
                        mass_fraction_of_fluid_mixed_in_water=self.heatpump_heat_source_mass_fraction_of_fluid_mixed_in_water,
                        bore_field_geometry=ground_probe_bore_field_geometry,
                        buried_depth_of_pipe=self.ground_probe_buried_depth_of_pipe,
                        length_of_borehole=self.ground_probe_length_of_borehole,
                        radius_of_borehole=self.ground_probe_radius_of_borehole,
                        number_of_boreholes_in_x_direction=self.ground_probe_number_of_boreholes_in_x_direction,
                        number_of_boreholes_in_y_direction=self.ground_probe_number_of_boreholes_in_y_direction,
                        borehole_spacing_both_directions=self.ground_probe_borehole_spacing_both_directions,
                        outer_pipe_radius=self.ground_probe_outer_pipe_radius,
                        inner_pipe_radius=self.ground_probe_inner_pipe_radius,
                        shank_spacing=self.ground_probe_shank_spacing,
                        pipe_roughness=self.ground_probe_pipe_roughness,
                        thermal_diffusivity_ground_in_sqm_per_s=self.ground_probe_thermal_diffusivity_ground_in_sqm_per_s,
                        thermal_conductivity_ground=self.ground_probe_thermal_conductivity_ground,
                        thermal_conductivity_grout=self.ground_probe_thermal_conductivity_grout,
                        thermal_conductivity_pipe=self.ground_probe_thermal_conductivity_pipe,
                        massflow_nominal_in_kg_per_s=self.heatpump_massflow_nominal_primary_side_in_kg_per_s,
                        device_co2_footprint_in_kg=self.ground_probe_co2_footprint,
                        investment_costs_in_euro=self.ground_probe_cost,
                        lifetime_in_years=self.ground_probe_lifetime,
                        maintenance_costs_in_euro_per_year=self.ground_probe_maintenance_costs_in_euro_per_year
                    )

                    my_hp_heat_source = borehole_heat_exchanger.GroundProbe(
                        my_simulation_parameters=self.my_simulation_parameters,
                        config=my_hp_heat_source_config,
                    )

                    my_heatpump.connect_input(
                        my_heatpump.TemperatureInputPrimary,
                        my_hp_heat_source.component_name,
                        my_hp_heat_source.TemperatureBrineOutlet,
                    )

                    my_hp_heat_source.connect_input(
                        my_hp_heat_source.TemperatureBrineIn,
                        my_heatpump.component_name,
                        my_heatpump.BrineTemperaturePrimaryOut,
                    )

                    my_hp_heat_source.connect_input(
                        my_hp_heat_source.Massflow,
                        my_heatpump.component_name,
                        my_heatpump.MassflowPrimarySide,
                    )

                    my_hp_heat_source.connect_input(
                        my_hp_heat_source.ThermalPowerHeatExtraction,
                        my_heatpump.component_name,
                        my_heatpump.ThermalPowerFromEnvironment,
                    )
                # =================================================================================================================================
                # Build Heating Meter für Anhwär´mnertzabnahme von W GebWP
                # =================================================================================================================================
            if self.heatpump_fluid_primary_side.lower() in ["water", "brine"] and self.heatpump_heat_source_if_not_air == Heat_Source_For_Brine_Heat_Pumps.DISTRICT_HEATING:

                my_heating_meter_dhnet_config = heating_meter.HeatingMeterConfig(
                building_name=self.building_name,
                name="HeatingMeterDHNetToHP",
                )

                my_heating_meter_dhnet = heating_meter.HeatingMeter(
                    my_simulation_parameters=self.my_simulation_parameters,
                    config=my_heating_meter_dhnet_config,
                )

                my_heating_meter_dhnet.add_component_input_and_connect(
                    source_object_name=my_heatpump.component_name,
                    source_component_output=my_heatpump.ThermalPowerFromEnvironment,
                    source_load_type=loadtypes.LoadTypes.HEATING,
                    source_unit=loadtypes.Units.WATT,
                    source_tags=[loadtypes.InandOutputType.HEAT_DELIVERED],
                    source_weight=999,
                )



            if self.heatpump_with_space_heating == True:

                self.heatpump_for_dhw_is_indoor = False

                my_heatpump.connect_only_predefined_connections(my_heatpump_controller_space_heating)

                if self.sh_storage_existing == True and self.sh_storage_position == 1:
                    my_heatpump.connect_input(
                        my_heatpump.TemperatureInputSecondarySH,
                        my_hot_water_storage.component_name,
                        my_hot_water_storage.WaterTemperatureToHeatGenerator,
                    )
                elif self.sh_storage_existing == True and self.sh_storage_position == 2:
                    my_heatpump.connect_input(
                        my_heatpump.TemperatureInputSecondarySH,
                        my_hot_water_storage.component_name,
                        my_hot_water_storage.WaterTemperatureToHeatGenerator,
                    )
                    my_heatpump.connect_input(
                        my_heatpump.SetHeatingTemperatureSH,
                        my_heat_distribution_controller.component_name,
                        my_heat_distribution_controller.HeatingFlowTemperature,
                    )
                else:
                    my_heatpump.connect_input(
                        my_heatpump.TemperatureInputSecondarySH,
                        my_heat_distribution.component_name,
                        my_heat_distribution.WaterTemperatureOutput,
                    )
                    my_heatpump.connect_input(
                        my_heatpump.SetHeatingTemperatureSH,
                        my_heat_distribution_controller.component_name,
                        my_heat_distribution_controller.HeatingFlowTemperature,
                    )

                if self.heatpump_passive_cooling_with_brine:
                    my_heatpump.connect_input(
                        my_heatpump.SetHeatingTemperatureSH,
                        my_heat_distribution_controller.component_name,
                        my_heat_distribution_controller.HeatingFlowTemperature,
                    )


                my_heatpump_controller_space_heating.connect_only_predefined_connections(self.my_weather, )

                my_heatpump_controller_space_heating.connect_input(
                    my_heatpump_controller_space_heating.HeatingFlowTemperatureFromHeatDistributionSystem,
                    my_heat_distribution_controller.component_name,
                    my_heat_distribution_controller.HeatingFlowTemperature,
                )

                if self.sh_storage_existing == True and self.sh_storage_position == 1:  # 1=speicher parallel zu wp, 2=speihcer in reihe bzw nicht vorhanden:
                    my_heatpump_controller_space_heating.connect_input(
                        my_heatpump_controller_space_heating.WaterTemperatureInput,
                        my_hot_water_storage.component_name,
                        my_hot_water_storage.WaterTemperatureToHeatGenerator,
                    )

                else:
                    my_heatpump_controller_space_heating.connect_input(
                        my_heatpump_controller_space_heating.WaterTemperatureInput,
                        my_heat_distribution.component_name,
                        my_heat_distribution.WaterTemperatureOutput,
                    )

            if self.heatpump_with_domestic_hot_water_preparation:

                if self.heatpump_for_dhw_is_indoor == True:
                    my_heatpump.connect_input(
                        my_heatpump.TemperatureInputPrimary,
                        my_building.component_name,
                        my_building.TemperatureIndoorAir,
                    )
                    my_heatpump.connect_input(
                        my_heatpump.TemperatureAmbient,
                        my_building.component_name,
                        my_building.TemperatureIndoorAir,
                    )

                my_heatpump.connect_only_predefined_connections(my_heatpump_controller_dhw)  # ,my_dhw_storage)

                my_heatpump.connect_input(
                    my_heatpump.TemperatureInputSecondaryDHW,
                    my_dhw_storage.component_name,
                    my_dhw_storage.WaterTemperatureToHeatGenerator,
                )

                my_heatpump_controller_dhw.connect_input(
                    my_heatpump_controller_dhw.WaterTemperatureInputFromDHWStorage,
                    my_dhw_storage.component_name,
                    my_dhw_storage.WaterTemperatureToHeatGenerator,
                )

                if self.solar_thermal_collector_for_dhw_existing == False:
                    my_dhw_storage.connect_only_predefined_connections(my_heatpump, )

                    my_dhw_storage.connect_input(
                        my_dhw_storage.WaterTemperatureFromHeatGenerator,
                        my_heatpump.component_name,
                        my_heatpump.TemperatureOutputDHW,
                    )
                    my_dhw_storage.connect_input(
                        my_dhw_storage.WaterMassFlowRateFromHeatGenerator,
                        my_heatpump.component_name,
                        my_heatpump.MassFlowOutputDHW,
                    )


        #################################################################################################################
        if self.sh_storage_existing == True :
            if self.conventional_heater_existing == True and self.sh_storage_position != 1:
                raise KeyError("Hot Water Storage has to be parallel to conventional heater")
            if self.sh_storage_position == 1:    # 1=speicher parallel zu wp, 2=speihcer in reihe bzw nicht vorhanden
                my_hot_water_storage.connect_input(
                    my_hot_water_storage.WaterTemperatureFromHeatDistribution,
                    my_heat_distribution.component_name,
                    my_heat_distribution.WaterTemperatureOutput,
                )
                my_hot_water_storage.connect_input(
                    my_hot_water_storage.WaterMassFlowRateFromHeatDistributionSystem,
                    my_heat_distribution.component_name,
                    my_heat_distribution.WaterMassFlowHDS,
                )
                if self.heatpump_existing == True and self.conventional_heater_existing == False:
                    my_hot_water_storage.connect_input(
                        my_hot_water_storage.WaterTemperatureFromHeatGenerator,
                        my_heatpump.component_name,
                        my_heatpump.TemperatureOutputSH,
                    )
                    my_hot_water_storage.connect_input(
                        my_hot_water_storage.WaterMassFlowRateFromHeatGenerator,
                        my_heatpump.component_name,
                        my_heatpump.MassFlowOutputSH,
                    )
                elif self.conventional_heater_existing == True and self.heatpump_existing == False:
                    my_hot_water_storage.connect_input(
                        my_hot_water_storage.WaterTemperatureFromHeatGenerator,
                        my_conventional_heater.component_name,
                        my_conventional_heater.WaterOutputTemperatureSh,
                    )
                    my_hot_water_storage.connect_input(
                        my_hot_water_storage.WaterMassFlowRateFromHeatGenerator,
                        my_conventional_heater.component_name,
                        my_conventional_heater.WaterOutputMassFlowSh,
                    )
                elif self.conventional_heater_existing == True and self.heatpump_existing == True:
                    my_hot_water_storage.connect_input(
                        my_hot_water_storage.WaterTemperatureFromHeatGenerator,
                        my_heatpump.component_name,
                        my_heatpump.TemperatureOutputSH,
                    )
                    my_hot_water_storage.connect_input(
                        my_hot_water_storage.WaterMassFlowRateFromHeatGenerator,
                        my_heatpump.component_name,
                        my_heatpump.MassFlowOutputSH,
                    )
                    my_hot_water_storage.connect_input(
                        my_hot_water_storage.WaterTemperatureFromSecondaryHeatGenerator,
                        my_conventional_heater.component_name,
                        my_conventional_heater.WaterOutputTemperatureSh,
                    )
                    my_hot_water_storage.connect_input(
                        my_hot_water_storage.WaterMassFlowRateFromSecondaryHeatGenerator,
                        my_conventional_heater.component_name,
                        my_conventional_heater.WaterOutputMassFlowSh,
                    )
                else:
                    raise ValueError("Unknown verbuindung vom hot water storage mit wp oder gas heater")

            if self.sh_storage_position == 2:    # 1=speicher parallel zu wp, 2=speihcer in reihe bzw nicht vorhanden
                my_hot_water_storage.connect_input(
                    my_hot_water_storage.WaterTemperatureFromHeatDistribution,
                    my_heat_distribution.component_name,
                    my_heat_distribution.WaterTemperatureOutput,
                )

                my_hot_water_storage.connect_input(
                    my_hot_water_storage.WaterMassFlowRateFromHeatDistributionSystem,
                    my_heat_distribution.component_name,
                    my_heat_distribution.WaterMassFlowHDS,
                )

        #################################################################################################################
        my_heating_meter_config = heating_meter.HeatingMeterConfig(
            building_name=self.building_name,
            name="HeatingMeter",
        )

        my_heating_meter = heating_meter.HeatingMeter(
            my_simulation_parameters=self.my_simulation_parameters,
            config=my_heating_meter_config,
        )

        if self.sh_storage_existing and self.sh_storage_position == 1:
            my_heating_meter.add_component_input_and_connect(
                source_object_name=my_hot_water_storage.component_name,
                source_component_output=my_hot_water_storage.ThermalPowerConsumptionHeatDistribution,
                source_load_type=lt.LoadTypes.HEATING,
                source_unit=lt.Units.WATT,
                source_tags=[lt.InandOutputType.HEAT_CONSUMPTION],
                source_weight=999,
            )
            my_heating_meter.add_component_input_and_connect(
                source_object_name=my_hot_water_storage.component_name,
                source_component_output=my_hot_water_storage.StandbyHeatLoss,
                source_load_type=lt.LoadTypes.HEATING,
                source_unit=lt.Units.WATT,
                source_tags=[lt.InandOutputType.HEAT_CONSUMPTION],
                source_weight=999,
            )
        elif self.sh_storage_existing and self.sh_storage_position == 2:
            my_heating_meter.add_component_input_and_connect(
                source_object_name=my_heat_distribution.component_name,
                source_component_output=my_heat_distribution.ThermalPowerDelivered,
                source_load_type=lt.LoadTypes.HEATING,
                source_unit=lt.Units.WATT,
                source_tags=[lt.InandOutputType.HEAT_CONSUMPTION],
                source_weight=999,
            )
            my_heating_meter.add_component_input_and_connect(
                source_object_name=my_hot_water_storage.component_name,
                source_component_output=my_hot_water_storage.StandbyHeatLoss,
                source_load_type=lt.LoadTypes.HEATING,
                source_unit=lt.Units.WATT,
                source_tags=[lt.InandOutputType.HEAT_CONSUMPTION],
                source_weight=999,
            )

        else:
            my_heating_meter.add_component_input_and_connect(  # Anteil Heatpump für Heizung erzeugung
                source_object_name=my_heat_distribution.component_name,
                source_component_output=my_heat_distribution.ThermalPowerDelivered,
                source_load_type=lt.LoadTypes.HEATING,
                source_unit=lt.Units.WATT,
                source_tags=[lt.InandOutputType.HEAT_CONSUMPTION],
                source_weight=999,
            )

        my_heating_meter.add_component_input_and_connect(  # Anteil Heatpump für Heizung erzeugung
            source_object_name=my_dhw_storage.component_name,
            source_component_output=my_dhw_storage.ThermalPowerConsumptionDHW,
            source_load_type=lt.LoadTypes.HEATING,
            source_unit=lt.Units.WATT,
            source_tags=[lt.InandOutputType.HEAT_CONSUMPTION],
            source_weight=999,
        )
        my_heating_meter.add_component_input_and_connect(  # Anteil Heatpump für Heizung erzeugung
            source_object_name=my_dhw_storage.component_name,
            source_component_output=my_dhw_storage.StandbyHeatLoss,
            source_load_type=lt.LoadTypes.HEATING,
            source_unit=lt.Units.WATT,
            source_tags=[lt.InandOutputType.HEAT_CONSUMPTION],
            source_weight=999,
        )


        if self.heatpump_existing:
            my_heating_meter.add_component_input_and_connect(  # Anteil Heatpump für Heizung erzeugung
                source_object_name=my_heatpump.component_name,
                source_component_output=my_heatpump.ThermalOutputPowerTotal,
                source_load_type=lt.LoadTypes.HEATING,
                source_unit=lt.Units.WATT,
                source_tags=[lt.InandOutputType.HEAT_DELIVERED],
                source_weight=999,
            )

        if self.solar_thermal_collector_for_dhw_existing:
            my_heating_meter.add_component_input_and_connect(  # Anteil Heatpump für Heizung erzeugung
                source_object_name=my_solar_thermal_collector.component_name,
                source_component_output=my_solar_thermal_collector.ThermalPowerOutput,
                source_load_type=lt.LoadTypes.HEATING,
                source_unit=lt.Units.WATT,
                source_tags=[lt.InandOutputType.HEAT_DELIVERED],
                source_weight=999,
            )

        if self.conventional_heater_existing:
            my_heating_meter.add_component_input_and_connect(  # Anteil Heatpump für Heizung erzeugung
                source_object_name=my_conventional_heater.component_name,
                source_component_output=my_conventional_heater.ThermalPowerGenerationSh,
                source_load_type=lt.LoadTypes.HEATING,
                source_unit=lt.Units.WATT,
                source_tags=[lt.InandOutputType.HEAT_DELIVERED],
                source_weight=999,
            )

            if self.conventional_heater_with_domestic_hot_water_preparation == True:
                my_heating_meter.add_component_input_and_connect(  # Anteil Heatpump für Heizung erzeugung
                    source_object_name=my_conventional_heater.component_name,
                    source_component_output=my_conventional_heater.ThermalOutputPowerDhw,
                    source_load_type=lt.LoadTypes.HEATING,
                    source_unit=lt.Units.WATT,
                    source_tags=[lt.InandOutputType.HEAT_DELIVERED],
                    source_weight=999,
                )


        #################################################################################################################
        if self.pv_existing == True:
            my_photovoltaic_system.connect_only_predefined_connections(self.my_weather)

        #################################################################################################################
        if self.ems_existing == True:

            #todo: abfragen einbauen, welches ems (geb oder building_setup) hier priorisiert regeln soll und entsprechend verbindungen anpassen

            if self.ems_source_weight_occupancy != 999:  # keine regelung über ems, nur verbrauch berücksichtigen
                my_ems_building.add_component_input_and_connect(
                    source_object_name=my_occupancy.component_name,
                    source_component_output=my_occupancy.ElectricalPowerConsumption,
                    source_load_type=lt.LoadTypes.ELECTRICITY,
                    source_unit=lt.Units.WATT,
                    source_tags=[lt.ComponentType.RESIDENTS, lt.InandOutputType.ELECTRICITY_CONSUMPTION_EMS_CONTROLLED],
                    source_weight=self.ems_source_weight_occupancy,
                )

                my_ems_building.add_component_output(
                    source_output_name=f"ElectricityToOrFromGridOf{my_occupancy.get_classname()}_",#"ElectricityToOrFromGridOfDHWMoreAdvancedHeatPumpHPLib_",
                    source_tags=[
                        lt.ComponentType.RESIDENTS,
                        lt.InandOutputType.ELECTRICITY_TARGET,
                    ],
                    source_weight=self.ems_source_weight_occupancy,
                    source_load_type=lt.LoadTypes.ELECTRICITY,
                    source_unit=lt.Units.WATT,
                    output_description="Target electricity for Occupancy. ",
                )

            if self.ems_source_weight_occupancy == 999:  # keine regelung über ems, nur verbrauch berücksichtigen
                my_ems_building.add_component_input_and_connect(
                    source_object_name=my_occupancy.component_name,
                    source_component_output=my_occupancy.ElectricalPowerConsumption,
                    source_load_type=lt.LoadTypes.ELECTRICITY,
                    source_unit=lt.Units.WATT,
                    source_tags=[lt.ComponentType.RESIDENTS, lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED],
                    source_weight=999,
                )

            if self.pv_existing==True:
                my_ems_building.add_component_input_and_connect(
                    source_object_name=my_photovoltaic_system.component_name,
                    source_component_output=my_photovoltaic_system.ElectricityOutput,
                    source_load_type=lt.LoadTypes.ELECTRICITY,
                    source_unit=lt.Units.WATT,
                    source_tags=[lt.ComponentType.PV, lt.InandOutputType.ELECTRICITY_PRODUCTION],
                    source_weight=999,
                )

            if self.heatpump_existing==True:
                if self.dhw_storage_existing == False:
                    self.ems_source_weight_heatpump_DHW = 999

                if self.heatpump_with_domestic_hot_water_preparation == True:
                    if self.ems_source_weight_heatpump_DHW != 999:      #regelung über ems
                        my_heatpump_controller_dhw.connect_input(
                            my_heatpump_controller_dhw.DHWStorageTemperatureModifier,
                            my_ems_building.component_name,
                            my_ems_building.DomesticHotWaterStorageTemperatureModifier,
                        )

                        my_ems_building.add_component_input_and_connect(          #Anteil Heatpump für DHW erzeugung
                            source_object_name=my_heatpump.component_name,
                            source_component_output=my_heatpump.ElectricalInputPowerDHW,
                            source_load_type=lt.LoadTypes.ELECTRICITY,
                            source_unit=lt.Units.WATT,
                            source_tags=[lt.ComponentType.HEAT_PUMP_DHW, lt.InandOutputType.ELECTRICITY_CONSUMPTION_EMS_CONTROLLED],
                            source_weight=self.ems_source_weight_heatpump_DHW,
                        )

                        my_ems_building.add_component_output(
                            source_output_name=f"ElectricityToOrFromGridOfDHW{my_heatpump.get_classname()}_",#"ElectricityToOrFromGridOfDHWMoreAdvancedHeatPumpHPLib_",#"ElectricityTarget_HP_DHW"+ "_w" + str(self.ems_source_weight_heatpump_DHW),
                            source_tags=[
                                lt.ComponentType.HEAT_PUMP_DHW,
                                lt.InandOutputType.ELECTRICITY_TARGET,
                            ],
                            source_weight=self.ems_source_weight_heatpump_DHW,
                            source_load_type=lt.LoadTypes.ELECTRICITY,
                            source_unit=lt.Units.WATT,
                            output_description="ElectricityToOrFromGrid for dhw Heat Pump. ",
                        )

                    if self.ems_source_weight_heatpump_DHW == 999:                  # keine regelung über ems, nur verbrauch berücksichtigen
                        my_ems_building.add_component_input_and_connect(
                            source_object_name=my_heatpump.component_name,
                            source_component_output=my_heatpump.ElectricalInputPowerDHW,
                            source_load_type=lt.LoadTypes.ELECTRICITY,
                            source_unit=lt.Units.WATT,
                            source_tags=[lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED],
                            source_weight=999,
                        )
                if self.heatpump_with_space_heating == True:
                    if self.sh_storage_existing == False:
                        self.ems_source_weight_heatpump_hotwater = 999

                    if self.ems_source_weight_heatpump_hotwater != 999:                 # regelung über ems

                        if my_ems_building.building_indoor_temperature_offset_value != 0:
                            my_heat_distribution_controller.connect_input(
                                my_heat_distribution_controller.BuildingTemperatureModifier,
                                my_ems_building.component_name,
                                my_ems_building.BuildingIndoorTemperatureModifier,
                            )

                            my_building.connect_input(
                                my_building.BuildingTemperatureModifier,
                                my_ems_building.component_name,
                                my_ems_building.BuildingIndoorTemperatureModifier,
                            )

                        my_heatpump_controller_space_heating.connect_input(
                            my_heatpump_controller_space_heating.SimpleHotWaterStorageTemperatureModifier,
                            my_ems_building.component_name,
                            my_ems_building.SpaceHeatingWaterStorageTemperatureModifier,
                        )

                        my_ems_building.add_component_input_and_connect(
                            source_object_name=my_heatpump.component_name,
                            source_component_output=my_heatpump.ElectricalInputPowerSH,
                            source_load_type=lt.LoadTypes.ELECTRICITY,
                            source_unit=lt.Units.WATT,
                            source_tags=[lt.ComponentType.HEAT_PUMP_BUILDING, lt.InandOutputType.ELECTRICITY_CONSUMPTION_EMS_CONTROLLED],
                            source_weight=self.ems_source_weight_heatpump_hotwater,
                        )

                        my_ems_building.add_component_output(
                            source_output_name=f"ElectricityToOrFromGridOfSH{my_heatpump.get_classname()}_",
                            source_tags=[
                                lt.ComponentType.HEAT_PUMP_BUILDING,
                                lt.InandOutputType.ELECTRICITY_TARGET,
                            ],
                            source_weight=self.ems_source_weight_heatpump_hotwater,
                            source_load_type=lt.LoadTypes.ELECTRICITY,
                            source_unit=lt.Units.WATT,
                            output_description="ElectricityToOrFromGrid for Space Heating Heat Pump. ",
                        )

                    if self.ems_source_weight_heatpump_hotwater == 999:
                        if my_ems_building.building_indoor_temperature_offset_value != 0:
                            raise KeyError(
                                "EMS Raumtemperatur modifier != 0, aber sh wp sourcew weight == 999 --> sourceweight muss kleiner 999 sein!")

                        my_ems_building.add_component_input_and_connect(
                            source_object_name=my_heatpump.component_name,
                            source_component_output=my_heatpump.ElectricalInputPowerSH,
                            source_load_type=lt.LoadTypes.ELECTRICITY,
                            source_unit=lt.Units.WATT,
                            source_tags=[lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED],
                            source_weight=999,
                        )

            if self.battery_existing == True:
                if self.ems_source_weight_battery == 999:
                    raise KeyError("Batteriespeicher emsSourceweight muss != 999 sein, da sonst nur Verbraucher --> unlogisch")

                my_ems_building.add_component_input_and_connect(
                    source_object_name=my_advanced_battery.component_name,
                    source_component_output=my_advanced_battery.AcBatteryPowerUsed,
                    source_load_type=lt.LoadTypes.ELECTRICITY,
                    source_unit=lt.Units.WATT,
                    source_tags=[lt.ComponentType.BATTERY, lt.InandOutputType.ELECTRICITY_CONSUMPTION_EMS_CONTROLLED],
                    source_weight=self.ems_source_weight_battery,
                )

                electricity_to_or_from_battery_target = (
                    my_ems_building.add_component_output(
                        source_output_name=f"ElectricityToOrFrom{my_advanced_battery.get_classname()}_",
                        source_tags=[
                            lt.ComponentType.BATTERY,
                            lt.InandOutputType.ELECTRICITY_TARGET,
                        ],
                        source_weight=self.ems_source_weight_battery,
                        source_load_type=lt.LoadTypes.ELECTRICITY,
                        source_unit=lt.Units.WATT,
                        output_description="Target electricity for Battery Control. ",
                    )
                )

                ################################
                # Connect Battery
                my_advanced_battery.connect_dynamic_input(
                    input_fieldname=advanced_battery_bslib.Battery.LoadingPowerInput,
                    src_object=electricity_to_or_from_battery_target,
                )

            if self.car_existing==True:
                if self.ems_source_weight_car == 999:
                    raise KeyError(
                        "Electric car emsSourceweight muss != 999 sein, da sonst nur Verbraucher --> unlogisch")

                for car, car_battery, car_battery_controller in list(zip_car_battery_controller_lists):
                    if self.ems_source_weight_car != 999:  # ems geregelt
                        my_ems_building.add_component_input_and_connect(
                            source_object_name=car_battery_controller.component_name,
                            source_component_output=car_battery_controller.BatteryChargingPowerToEMS,
                            source_load_type=lt.LoadTypes.ELECTRICITY,
                            source_unit=lt.Units.WATT,
                            source_tags=[lt.ComponentType.CAR_BATTERY,
                                         lt.InandOutputType.ELECTRICITY_CONSUMPTION_EMS_CONTROLLED],
                            source_weight=self.ems_source_weight_car,
                        )

                        electricity_target_car = my_ems_building.add_component_output(
                            source_output_name=f"ElectricityToOrFrom{car_battery_controller.get_classname()}_",
                            source_tags=[
                                lt.ComponentType.CAR_BATTERY,
                                lt.InandOutputType.ELECTRICITY_TARGET,
                            ],
                            source_weight=self.ems_source_weight_car,
                            source_load_type=lt.LoadTypes.ELECTRICITY,
                            source_unit=lt.Units.WATT,
                            output_description="Target Electricity for EV Battery Controller. ",
                        )

                        car_battery_controller.connect_dynamic_input(
                            input_fieldname=controller_l1_generic_ev_charge.L1Controller.ElectricityTarget,
                            src_object=electricity_target_car,
                        )
                    if self.ems_source_weight_car == 999:                  # nicht ems geregelt aber verbrauch in ems berücksichtigt
                        my_ems_building.add_component_input_and_connect(
                            source_object_name=car_battery_controller.component_name,
                            source_component_output=car_battery_controller.BatteryChargingPowerToEMS,
                            source_load_type=lt.LoadTypes.ELECTRICITY,
                            source_unit=lt.Units.WATT,
                            source_tags=[lt.ComponentType.CAR_BATTERY,
                                lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED,
                            ],
                            source_weight=999,
                        )

            my_electricity_meter.add_component_input_and_connect(
                source_object_name=my_ems_building.component_name,
                source_component_output=my_ems_building.TotalElectricityToGrid,
                source_load_type=loadtypes.LoadTypes.ELECTRICITY,
                source_unit=loadtypes.Units.WATT,
                source_tags=[loadtypes.InandOutputType.ELECTRICITY_PRODUCTION],
                source_weight=999,
            )
            my_electricity_meter.add_component_input_and_connect(
                source_object_name=my_ems_building.component_name,
                source_component_output=my_ems_building.TotalElectricityFromGrid,
                source_load_type=loadtypes.LoadTypes.ELECTRICITY,
                source_unit=loadtypes.Units.WATT,
                source_tags=[loadtypes.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED],
                source_weight=999,
            )

        ##################################
        # Electricity Meter falls kein EMS
        if self.ems_existing == False:

            if self.pv_existing == True:
                my_electricity_meter.add_component_input_and_connect(
                    source_object_name=my_photovoltaic_system.component_name,
                    source_component_output=my_photovoltaic_system.ElectricityOutput,
                    source_load_type=lt.LoadTypes.ELECTRICITY,
                    source_unit=lt.Units.WATT,
                    source_tags=[
                        lt.ComponentType.PV,
                        lt.InandOutputType.ELECTRICITY_PRODUCTION,
                    ],
                    source_weight=999,
                )

            my_electricity_meter.add_component_input_and_connect(
                source_object_name=my_occupancy.component_name,
                source_component_output=my_occupancy.ElectricalPowerConsumption,
                source_load_type=lt.LoadTypes.ELECTRICITY,
                source_unit=lt.Units.WATT,
                source_tags=[lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED],
                source_weight=999,
            )
            if self.heatpump_existing==True:
                my_electricity_meter.add_component_input_and_connect(
                    source_object_name=my_heatpump.component_name,
                    source_component_output=my_heatpump.ElectricalInputPowerTotal,
                    source_load_type=lt.LoadTypes.ELECTRICITY,
                    source_unit=lt.Units.WATT,
                    source_tags=[
                        lt.InandOutputType.ELECTRICITY_CONSUMPTION_UNCONTROLLED,
                    ],
                    source_weight=999,
                )

            if self.battery_existing == True:
                if self.ems_source_weight_battery == 999:
                    raise KeyError(
                        "Batteriespeicher emsSourceweight muss != 999 sein, da sonst nur Verbraucher --> unlogisch")
                if self.ems_existing == False:
                    raise KeyError("If Battery existing is true for building, ems is necessary!")

        # =================================================================================================================================
        # Add Components to Simulation Parameters

        self.my_sim.add_component(my_occupancy)

        if  self.building_existing == True:
            self.my_sim.add_component(my_building)

        if self.dhw_storage_existing == True:
            self.my_sim.add_component(my_dhw_storage)
        if self.heatpump_existing == True:
            self.my_sim.add_component(my_heatpump)
            if self.heatpump_with_space_heating:
                self.my_sim.add_component(my_heatpump_controller_space_heating)
            if self.heatpump_with_domestic_hot_water_preparation:
                self.my_sim.add_component(my_heatpump_controller_dhw)
            self.heatpump_geb = my_heatpump
            if self.heatpump_fluid_primary_side.lower() == "water" or self.heatpump_fluid_primary_side.lower() == "brine":
                self.my_heatpump = my_heatpump
                if self.heatpump_heat_source_if_not_air in [Heat_Source_For_Brine_Heat_Pumps.NEAR_SURFACE_BRINE_TEMPERATURE,
                                                   Heat_Source_For_Brine_Heat_Pumps.CONSTANT_TEMPERATURE,
                                                   Heat_Source_For_Brine_Heat_Pumps.CONSTANT_THERMAL_POWER,
                                                   Heat_Source_For_Brine_Heat_Pumps.GROUND_PROBE]:
                    self.my_sim.add_component(my_hp_heat_source)
                if self.heatpump_heat_source_if_not_air in [Heat_Source_For_Brine_Heat_Pumps.DISTRICT_HEATING]:
                    self.my_sim.add_component(my_heating_meter_dhnet)

        if self.conventional_heater_existing == True:
            self.my_sim.add_component(my_conventional_heater)
            self.my_sim.add_component(my_conventional_heater_controller)
            if  self.conventional_heater_fuel is Conventional_Fuel.GAS.name:
                self.my_sim.add_component(my_gas_meter)
                self.my_gas_meter_geb = my_gas_meter
        if self.solar_thermal_collector_for_dhw_existing == True:
            self.my_sim.add_component(my_solar_thermal_collector)
            self.my_sim.add_component(my_solar_thermal_collector_controller)
        if self.heat_distribution_system_existing == True:
            self.my_sim.add_component(my_heat_distribution)
            self.my_sim.add_component(my_heat_distribution_controller)
        if self.sh_storage_existing == True:
            self.my_sim.add_component(my_hot_water_storage)
        if self.pv_existing == True:
            self.my_sim.add_component(my_photovoltaic_system)
        if self.ems_existing == True:
            self.my_sim.add_component(my_ems_building)
        if self.battery_existing == True:
            self.my_sim.add_component(my_advanced_battery)
        if self.car_existing == True:
            for car, car_battery, car_battery_controller in list(zip_car_battery_controller_lists):
                self.my_sim.add_component(car)
                self.my_sim.add_component(car_battery)
                self.my_sim.add_component(car_battery_controller)


        self.my_sim.add_component(my_electricity_meter)
        self.my_sim.add_component(my_heating_meter)

        ######## Übergabe Parameter an Externe Modelle  #########

        self.electricity_meter_geb = my_electricity_meter
        if self.heatpump_existing== True:
            if self.heatpump_with_space_heating:
                self.heatpump_controller_space_heating=my_heatpump_controller_space_heating
            if self.heatpump_with_domestic_hot_water_preparation:
                self.heatpump_controller_dhw = my_heatpump_controller_dhw
