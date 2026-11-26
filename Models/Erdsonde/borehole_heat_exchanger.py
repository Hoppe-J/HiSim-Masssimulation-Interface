""" Borehole Heat Exchanger. """

import hashlib

# clean

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import List
from enum import Enum
import pandas as pd
from datetime import datetime
from calendar import monthrange
import numpy as np

import pygfunction as gt
import matplotlib.pyplot as plt

# Import modules from HiSim
from hisim import log
from hisim import component as cp
from hisim import loadtypes as lt
from hisim.loadtypes import Units
from hisim.simulationparameters import SimulationParameters
from hisim.sim_repository_singleton import SingletonSimRepository, SingletonDictKeyEnum
from hisim.components import more_advanced_heat_pump_hplib

from hisim.component import ComponentInput, ComponentConnection, OpexCostDataClass, CapexCostDataClass
from hisim.postprocessing.kpi_computation.kpi_structure import KpiEntry, KpiHelperClass, KpiTagEnumClass



class SortOfPipe(Enum):
    """ Sort of Pipe   """

    DOUBLE_U_TUBE = "Double U-tube"
    SINGLE_U_TUBE = "Single U-tube"
    COAXIAL = "Coaxial"

class FluidMediaType(Enum):
    """ Sort of Media"""

    WATER = "Water"
    ETHYLEN_GLYCOL = "EthyleneGlycol"
    PROPYLEN_GLYCOL = "PropyleneGlycol"
    ETHANOL = "EthylAlcohol"
    METHANOL = "MethylAlcohol"

class BoreFieldGeometry(Enum):
    """ Predefined geometry of field  """

    L_SHAPED_FIELD = "L_shaped_field"
    RECTANGLE_FIELD = "Rectangle_field"
    STAGGERED_RECTANGLE_FIELD = "Staggered_rectangle_field"
    DENSE_RECTANGLE_FIELD = "Dense_rectangle_field"
    U_SHAPED_FIELD = "U_shaped_field"
    BOX_SHAPED_FIELD = "Box_shaped_field"
    CIRCLE_FIELD = "Circle_field"


@dataclass
class GroundProbeConfig(cp.ConfigBase):
    """Configuration of a generic HeatSource."""

    building_name: str
    name: str
    sort_of_pipe: SortOfPipe
    fluid_type: FluidMediaType
    mass_fraction_of_fluid_mixed_in_water: float
    bore_field_geometry: BoreFieldGeometry
    buried_depth_of_pipe: float
    length_of_borehole: float
    radius_of_borehole: float
    number_of_boreholes_in_x_direction: int
    number_of_boreholes_in_y_direction: int
    borehole_spacing_both_directions: float
    outer_pipe_radius: float
    inner_pipe_radius: float
    shank_spacing: float
    pipe_roughness: float
    thermal_diffusivity_ground_in_sqm_per_s: float
    thermal_conductivity_ground: float
    thermal_conductivity_grout: float
    thermal_conductivity_pipe: float
    massflow_nominal_in_kg_per_s: float
    device_co2_footprint_in_kg: float
    #: cost for investment in Euro
    investment_costs_in_euro: float
    #: lifetime in years
    lifetime_in_years: float
    # maintenance cost as share of investment [0..1]
    maintenance_costs_in_euro_per_year: float

    @classmethod
    def get_main_classname(cls):
        """Returns the full class name of the base class."""
        return GroundProbe.get_full_classname()

    @classmethod
    def get_default(
        cls,
        building_name: str = "BUI1",
    ) -> "GroundProbeConfig":
        """Returns default configuration of a Heat Source used for heating."""
        config = GroundProbeConfig(
            building_name=building_name,
            name="BoreHoleNetwork",
            sort_of_pipe=SortOfPipe.SINGLE_U_TUBE,
            fluid_type=FluidMediaType.PROPYLEN_GLYCOL,
            mass_fraction_of_fluid_mixed_in_water=0.20,
            bore_field_geometry=BoreFieldGeometry.L_SHAPED_FIELD,
            buried_depth_of_pipe=4,
            length_of_borehole=190,
            radius_of_borehole=0.075,
            number_of_boreholes_in_x_direction=1,
            number_of_boreholes_in_y_direction=1,
            borehole_spacing_both_directions=7.5,
            outer_pipe_radius=0.0211,
            inner_pipe_radius=0.0147,
            shank_spacing=0.052,
            pipe_roughness=1.0e-6,
            thermal_diffusivity_ground_in_sqm_per_s=1.0e-6,
            thermal_conductivity_ground=2,
            thermal_conductivity_grout=1,
            thermal_conductivity_pipe=0.4,
            massflow_nominal_in_kg_per_s=0.3,
            device_co2_footprint_in_kg=100,  # Todo: check value
            investment_costs_in_euro=2000,# Todo: check value
            lifetime_in_years=25,# Todo: check value
            maintenance_costs_in_euro_per_year=10,# Todo: check value
        )
        return config

@dataclass
class GroundProbeState:
    """Heat source state class saves the state of the heat source."""

    simulated_time_in_seconds: float
    soil_is_frozen:bool
    temperature_borehole_outlet: float
    temperature_borehole_inlet: float
    average_temperature_borehole_wall: float
    thermal_heat_extraction: float
    heat_extraction_rate_per_borehole_in_watt_per_meter: float
    deltaT_b: float

    def self_copy(self,):
        """Copy the Heat source state."""
        return GroundProbeState(
            self.simulated_time_in_seconds,
            self.soil_is_frozen,
            self.temperature_borehole_outlet,
            self.temperature_borehole_inlet,
            self.average_temperature_borehole_wall,
            self.thermal_heat_extraction,
            self.deltaT_b,
            self.heat_extraction_rate_per_borehole_in_watt_per_meter
        )


class GroundProbe(cp.Component):
    """Heat Source implementation."""

    TemperatureBrineIn = "TemperatureBrineIn"
    Massflow = "Massflow"
    ThermalPowerHeatExtraction = "ThermalPowerHeatExtraction"

    # Outputs
    HeatExtractionOfBoreField = "HeatExtractionOfBoreField"
    HeatExtractionRatePerBorehole = "HeatExtractionRatePerBorehole"
    AverageTemperatureUndisturbedSoilOfPipeLength = "AverageTemperatureUndisturbedSoilOfPipeLength"
    TemperatureUndisturbedSoilAtPipeHead = "TemperatureUndisturbedSoilAtPipeHead"
    TemperatureUndisturbedSoilAtPipeEnd = "TemperatureUndisturbedSoilAtPipeEnd"
    TemperatureBrineOutlet = "TemperatureBrineOutlet"
    TemperatureBrineInlet = "TemperatureBrineInlet"
    TemperatureDifferenceBrine = "TemperatureDifferenceBrine"
    TemperatureBoreholeWall = "TemperatureBoreholeWall"
    G_Function = "g-Function"
    MassFlow = "MassFlow"
    SoilFrozenState = "SoilFrozenState"
    TemperatureChangeBoreholeWallDueToHeatExtraction = "TemperatureChangeBoreholeWallDueToHeatExtraction"

    def __init__(
        self,
        my_simulation_parameters: SimulationParameters,
        config: GroundProbeConfig,
        my_display_config: cp.DisplayConfig = cp.DisplayConfig(),
    ) -> None:
        """Initialize the class."""

        self.my_simulation_parameters = my_simulation_parameters
        self.config = config
        component_name = self.get_component_name()
        super().__init__(
            name=component_name,
            my_simulation_parameters=my_simulation_parameters,
            my_config=config,
            my_display_config=my_display_config,
        )

        self.sort_of_pipe = config.sort_of_pipe
        self.fluid_type = config.fluid_type
        self.mass_fraction_of_fluid_mixed_in_water = config.mass_fraction_of_fluid_mixed_in_water
        self.bore_field_geometry = config.bore_field_geometry
        self.buried_depth_of_pipe = config.buried_depth_of_pipe
        self.length_of_borehole = config.length_of_borehole
        self.radius_of_borehole = config.radius_of_borehole
        self.number_of_boreholes_in_x_direction = config.number_of_boreholes_in_x_direction
        self.number_of_boreholes_in_y_direction = config.number_of_boreholes_in_y_direction
        self.borehole_spacing_both_directions = config.borehole_spacing_both_directions
        self.outer_pipe_radius = config.outer_pipe_radius
        self.inner_pipe_radius = config.inner_pipe_radius
        self.shank_spacing = config.shank_spacing
        self.pipe_roughness = config.pipe_roughness
        self.thermal_diffusivity_ground_in_sqm_per_s = config.thermal_diffusivity_ground_in_sqm_per_s
        self.thermal_conductivity_ground = config.thermal_conductivity_ground
        self.thermal_conductivity_grout = config.thermal_conductivity_grout
        self.thermal_conductivity_pipe = config.thermal_conductivity_pipe
        self.m_flow_network = config.massflow_nominal_in_kg_per_s

        self.number_of_boreholes = self.number_of_boreholes_in_y_direction+self.number_of_boreholes_in_x_direction-1

        self.calculation_method_g_function = "equivalent" #'similarities'

        self.boundary_condition_g_function = "UHTR" # "UBWT"  #"MIFT"     # https://github.com/MassimoCimmino/pygfunction/files/12443491/Mitchell_et_al_2020_WGC_Cross_g_functions.pdf

        self.options_g_function = {'nSegments': 8,
                                   'disp': True,
                                   'profiles': True}

        days_per_month = []
        current_date = datetime(year=self.my_simulation_parameters.start_date.year,month=1,day=1)
        while current_date.year <= current_date.year + 1:
            days = monthrange(current_date.year, current_date.month)[1]
            days_per_month.append(days)
            if current_date.month == 12:  # Dezember
                if self.my_simulation_parameters.end_date.year > current_date.year + 1:
                    current_date = datetime(current_date.year + 1, 1, 1)  # Januar des nächsten Jahres
                else:
                    break
            else:
                current_date = datetime(current_date.year, current_date.month + 1, 1)  # Nächster Monat

        days_in_year = sum(days_per_month)
        self.simulated_years_in_seconds = days_in_year*24*60*60

        self.seconds_away_from_1_January_of_year = (self.my_simulation_parameters.start_date - datetime(
            year=self.my_simulation_parameters.start_date.year, month=1, day=1)).total_seconds()

        self.end_date_in_seconds_from_zero = (self.my_simulation_parameters.end_date - datetime(
            year=self.my_simulation_parameters.start_date.year, month=1, day=1)).total_seconds()

        self.state = GroundProbeState(
            simulated_time_in_seconds=self.seconds_away_from_1_January_of_year,
            soil_is_frozen=False,
            deltaT_b=0,
            temperature_borehole_outlet=10,
            temperature_borehole_inlet=10,
            average_temperature_borehole_wall=10,
            thermal_heat_extraction=0,
            heat_extraction_rate_per_borehole_in_watt_per_meter=0,
        )

        self.previous_state = self.state.self_copy()

        self.ground_source_information = GroundHeatSourceInformation(config= self.config)
        self.build()

        # Inputs

        self.temperature_brine_in_channel: ComponentInput = self.add_input(
            object_name=self.component_name,
            field_name=self.TemperatureBrineIn,
            load_type=lt.LoadTypes.TEMPERATURE,
            unit=Units.CELSIUS,
            mandatory=True,
        )

        self.mass_flow_brine_in_kg_per_s_channel: ComponentInput = self.add_input(
            object_name=self.component_name,
            field_name=self.Massflow,
            load_type=lt.LoadTypes.VOLUME,
            unit=Units.KG_PER_SEC,
            mandatory=True,
        )

        self.thermal_power_channel: ComponentInput = self.add_input(
            object_name=self.component_name,
            field_name=self.ThermalPowerHeatExtraction,
            load_type=lt.LoadTypes.HEATING,
            unit=lt.Units.WATT,
            mandatory=True,
        )

        # Outputs

        self.thermal_heat_extraction_of_borefield_chanel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.HeatExtractionOfBoreField,
            load_type=lt.LoadTypes.HEATING,
            unit=lt.Units.WATT,
            output_description="Thermal Power from Soil",
        )

        self.heat_extraction_rate_per_borehole_chanel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.HeatExtractionRatePerBorehole,
            load_type=lt.LoadTypes.HEATING,
            unit=lt.Units.WATT_PER_METER,
            output_description="Heat extraction rate per borehole",
        )

        self.average_temperature_of_undisturbed_soil_channel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.AverageTemperatureUndisturbedSoilOfPipeLength,
            load_type=lt.LoadTypes.TEMPERATURE,
            unit=lt.Units.CELSIUS,
            output_description="Average temperature of undisturbed Soil over pipe length",
        )

        self.temperature_of_undisturbed_soil_in_depth_of_pipe_length_channel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.TemperatureUndisturbedSoilAtPipeEnd,
            load_type=lt.LoadTypes.TEMPERATURE,
            unit=lt.Units.CELSIUS,
            output_description=f"Temperature of undisturbed Soil at pipe head in {self.length_of_borehole} m",
        )

        self.temperature_of_undisturbed_soil_in_depth_of_buried_depth_of_pipe_channel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.TemperatureUndisturbedSoilAtPipeHead,
            load_type=lt.LoadTypes.TEMPERATURE,
            unit=lt.Units.CELSIUS,
            output_description=f"Temperature of undisturbed Soil at pipe head in {self.buried_depth_of_pipe} m",
        )

        self.temperature_borehole_inlet_chanel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.TemperatureBrineInlet,
            load_type=lt.LoadTypes.TEMPERATURE,
            unit=lt.Units.CELSIUS,
            output_description="Temperature of brine input",
        )
        self.temperature_difference_chanel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.TemperatureDifferenceBrine,
            load_type=lt.LoadTypes.TEMPERATURE,
            unit=lt.Units.CELSIUS,
            output_description="Temperature difference",
        )

        self.temperature_borehole_outlet_chanel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.TemperatureBrineOutlet,
            load_type=lt.LoadTypes.TEMPERATURE,
            unit=lt.Units.CELSIUS,
            output_description="Temperature of brine output",
        )
        self.temperature_borehole_wall_chanel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.TemperatureBoreholeWall,
            load_type=lt.LoadTypes.TEMPERATURE,
            unit=lt.Units.CELSIUS,
            output_description="Temperature of borehole wall.",
        )

        self.gFunc_value_chanel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.G_Function,
            load_type=lt.LoadTypes.ANY,
            unit=lt.Units.ANY,
            output_description="Value of G-Function",
        )
        self.mass_flow_brine_chanel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.MassFlow,
            load_type=lt.LoadTypes.VOLUME,
            unit=lt.Units.KG_PER_SEC,
            output_description="Total Massflow",
        )
        self.deltaT_b_chanel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.TemperatureChangeBoreholeWallDueToHeatExtraction,
            load_type=lt.LoadTypes.TEMPERATURE,
            unit=lt.Units.CELSIUS,
            output_description="deltaT_b",
        )

        self.soil_is_frozen_chanel: cp.ComponentOutput = self.add_output(
            object_name=self.component_name,
            field_name=self.SoilFrozenState,
            load_type=lt.LoadTypes.ANY,
            unit=lt.Units.ANY,
            output_description="Soil frozen state",
        )

        self.add_default_connections(self.get_default_connections_from_heatpump())

    def build(self):

        depth_delta = 3     # soil layers steps for calculating undisturbed soil temperature --> temperature every 3 meter
        self.depth_list = np.arange(0,int(self.length_of_borehole + 1),depth_delta).tolist()
        time_delta = self.my_simulation_parameters.seconds_per_timestep
        self.timelist_undisturbed_soil_temperature = np.arange(self.seconds_away_from_1_January_of_year,self.end_date_in_seconds_from_zero,time_delta).tolist()

        # get fluid properties
        self.cp_f = self.ground_source_information.cp_f  # Fluid specific isobaric heat capacity (J/kg.K)
        self.rho_f = self.ground_source_information.rho_f  # Fluid density (kg/m3)
        self.mu_f = self.ground_source_information.mu_f  # Fluid dynamic viscosity (kg/m.s)
        self.k_f = self.ground_source_information.k_f  # Fluid thermal conductivity (W/m.K)

        # get bore field
        self.boreField = self.get_predefined_bore_field_geometrie(bore_field_geometry=self.bore_field_geometry)

        self.nBoreholes = len(self.boreField)

        boreholes_are_parallel = True
        # todo: implmentation of different configuration with parallel pipes and pipes in serie
        if boreholes_are_parallel:
            m_flow_borehole = self.m_flow_network / self.number_of_boreholes
        else:  # boreholes are in serie
            m_flow_borehole = self.m_flow_network

        if self.sort_of_pipe == SortOfPipe.DOUBLE_U_TUBE:
            m_flow_pipe = m_flow_borehole / 2
        else:
            m_flow_pipe = m_flow_borehole

        # get borehole properties

        #todo:_ mit in simulation funktion damit zu jeden neuen m,assenstrom entsprechend berechnet wird

        convective_heat_transfer_pipe = gt.pipes.convective_heat_transfer_coefficient_circular_pipe(
            m_flow_pipe, self.inner_pipe_radius, self.mu_f, self.rho_f, self.k_f, self.cp_f, self.pipe_roughness
        )

        self.thermal_resistance_of_fluid = 1.0 / (convective_heat_transfer_pipe * 2 * np.pi * self.inner_pipe_radius)

        self.thermal_resistance_of_pipe = gt.pipes.conduction_thermal_resistance_circular_pipe(
            self.inner_pipe_radius, self.outer_pipe_radius, self.thermal_conductivity_pipe)

        self.thermal_resistance_of_grout = gt.pipes.conduction_thermal_resistance_circular_pipe(
            self.outer_pipe_radius, self.radius_of_borehole, self.thermal_conductivity_grout)

        thermal_resistance_of_fluid_to_fluid_coaxial_inner_pipe = gt.pipes.conduction_thermal_resistance_circular_pipe(
            self.inner_pipe_radius, self.outer_pipe_radius, self.thermal_conductivity_pipe)

        # get pipes
        pipes = self.get_borehole_pipes(sort_of_pipe=self.sort_of_pipe)

        # get network
        self.network = gt.networks.Network(
            boreholes=self.boreField,
            pipes=pipes,
            m_flow_network=self.m_flow_network,
            cp_f=self.cp_f,
            bore_connectivity=None,
            nSegments=None,
            segment_ratios=None, )

        # get load aggregation
        dt = self.my_simulation_parameters.seconds_per_timestep  # Time step (s)
        tmax = (self.my_simulation_parameters.end_date-self.my_simulation_parameters.start_date).total_seconds() # Maximum time (s)
        Nt = 25  # Number of time steps for g function

        # Load aggregation scheme
        self.LoadAgg = gt.load_aggregation.ClaessonJaved(dt, tmax)

        # time_g_function = gt.utilities.time_ClaessonJaved(dt, tmax + dt)
        self.timearray_g_function = gt.utilities.time_geometric(dt, tmax + dt, Nt)
        self.timearray_g_function = np.insert(self.timearray_g_function, 0, 0)

        self.timearray_g_function += self.seconds_away_from_1_January_of_year

        log.information("Calculation of g-function for borehole heat exchanger")

        self.gFunc = gt.gfunction.gFunction(
            boreholes_or_network=self.network,
            alpha=self.thermal_diffusivity_ground_in_sqm_per_s,
            time=self.timearray_g_function,
            boundary_condition=self.boundary_condition_g_function,
            options=self.options_g_function)

        self.timelist_g_function = self.timearray_g_function.tolist()

        # Time constant for no massflow
        heat_resistance_coefficient_pipes_to_soil = (self.thermal_resistance_of_pipe + self.thermal_resistance_of_grout + 1 / (
                                                            self.thermal_conductivity_ground)) * self.length_of_borehole

        total_inner_volume_of_borefield = ((np.pi / 4) * (
                    (2 * self.inner_pipe_radius) ** 2) * self.length_of_borehole) * self.number_of_boreholes  # in m^3

        total_outer_surface_of_pipes = (
                                                   np.pi * 2 * self.outer_pipe_radius * self.length_of_borehole) * self.number_of_boreholes  # in m^2

        mass_of_brine_in_borefield = total_inner_volume_of_borefield * self.rho_f

        self.time_constant_for_no_massflow = ((mass_of_brine_in_borefield * self.cp_f) *
                                              (heat_resistance_coefficient_pipes_to_soil / total_outer_surface_of_pipes))

        if self.my_simulation_parameters.logging_level == 4: # Debug Modus
            #  -------------------------------------------------------------------------
            #   Draw bore fields
            # -------------------------------------------------------------------------
            gt.boreholes.visualize_field(self.boreField)
            pipes[0].visualize_pipes()
            self.gFunc.visualize_g_function()
            plt.tight_layout()
            plt.show()


    def get_default_connections_from_heatpump(
            self,
    ):
        """Get default connections."""
        connections = []
        hp_classname = more_advanced_heat_pump_hplib.MoreAdvancedHeatPumpHPLib.get_classname()
        connections.append(
            ComponentConnection(
                GroundProbe.TemperatureBrineIn,
                hp_classname,
                more_advanced_heat_pump_hplib.MoreAdvancedHeatPumpHPLib.BrineTemperaturePrimaryOut,
            )
        )

        connections.append(
            ComponentConnection(
                GroundProbe.Massflow,
                hp_classname,
                more_advanced_heat_pump_hplib.MoreAdvancedHeatPumpHPLib.MassflowPrimarySide,
            )
        )

        connections.append(
            ComponentConnection(
                GroundProbe.ThermalPowerHeatExtraction,
                hp_classname,
                more_advanced_heat_pump_hplib.MoreAdvancedHeatPumpHPLib.ThermalPowerFromEnvironment,
            )
        )

        return connections

    def i_prepare_simulation(self) -> None:
        """Prepares the simulation."""

        if SingletonSimRepository().exist_entry(key=SingletonDictKeyEnum.WEATHERTEMPERATUREOUTSIDEYEARLYFORECAST):
            temperature = SingletonSimRepository().get_entry(
                key=SingletonDictKeyEnum.WEATHERTEMPERATUREOUTSIDEYEARLYFORECAST)
        else:
            raise KeyError(
                "The key weather_temperature_forecast was not found in the singleton sim repository. "
                "Please check in your system setup if the weather config if predictive controle is true."
            )

        log.information(f"Preparing {self.component_name} monthly average outside temperature for simulation")
        monthly_average_temperature_outside_air = self.calculate_average_outside_temperature(temperaturelist=temperature,
                                                                               average_over="monthly")

        log.information(f"Preparing {self.component_name} yearly average outside temperature for simulation")
        self.yearly_average_temperature_outside_air = self.calculate_average_outside_temperature(temperaturelist=temperature,
                                                                               average_over="yearly")[0]

        self.maximum_monthly_average_temperature_outside_air = max(monthly_average_temperature_outside_air)

        self.month_number_with_highest_average_temperature_outside_air = monthly_average_temperature_outside_air.index(self.maximum_monthly_average_temperature_outside_air)+1

        self.minimum_monthly_average_temperature_outside_air = min(monthly_average_temperature_outside_air)

        self.month_number_with_lowest_average_temperature_outside_air = monthly_average_temperature_outside_air.index(self.minimum_monthly_average_temperature_outside_air) + 1

        self.number_of_days_from_beginning_of_year_till_month_with_lowest_average_temperature_outside_air = sum(self.days_per_month[:self.month_number_with_lowest_average_temperature_outside_air])

        self.number_of_days_from_beginning_of_year_till_month_with_highest_average_temperature_outside_air = sum(
            self.days_per_month[:self.month_number_with_highest_average_temperature_outside_air])

        self.amplitude_yearly_average_temperature_and_maximum_monthly_average_temperature_outside_air = self.maximum_monthly_average_temperature_outside_air-self.yearly_average_temperature_outside_air

        self.temperature_array_of_undisturbed_soil = []
        for time in self.timelist_undisturbed_soil_temperature:
            temperature_array = self.calculation_undisturbed_soil_temperature(
                simulated_time_in_seconds=time,
                depth_list=self.depth_list, )
            self.temperature_array_of_undisturbed_soil.append(temperature_array)

    def calculate_average_outside_temperature(
            self, temperaturelist: List[float], average_over: str
    ) -> List[float]:
        """Calculate the  average outside temperatures."""
        average_outside_temperature_list_in_celsius = []
        total_number_of_timesteps_temperature_list = len(temperaturelist)
        start_index = 0

        if average_over=="daily":
            timestep_24h = int(24 * 3600 / self.my_simulation_parameters.seconds_per_timestep)
            for index in range(0, total_number_of_timesteps_temperature_list):
                daily_average_temperature = float(np.mean(temperaturelist[start_index: start_index + timestep_24h]))
                if index == start_index + timestep_24h:
                    start_index = index
                average_outside_temperature_list_in_celsius.append(daily_average_temperature)

        if average_over=="monthly":
            self.days_per_month = []
            current_date = datetime(year=self.my_simulation_parameters.start_date.year, month=1, day=1)
            while current_date.year <= current_date.year + 1:
                days = monthrange(current_date.year, current_date.month)[1]
                self.days_per_month.append(days)
                if current_date.month == 12:  # Dezember
                    if self.my_simulation_parameters.end_date.year > current_date.year + 1:
                        current_date = datetime(current_date.year + 1, 1, 1)  # Januar des nächsten Jahres
                    else:
                        break
                else:
                    current_date = datetime(current_date.year, current_date.month + 1, 1)  # Nächster Monat

            for days_in_month in self.days_per_month:
                timestep_1month = int(days_in_month * 24 * 3600 / self.my_simulation_parameters.seconds_per_timestep)
                if start_index + timestep_1month > total_number_of_timesteps_temperature_list:
                    timestep_1month = total_number_of_timesteps_temperature_list - start_index
                monthly_average_temperature = float(
                    np.mean(temperaturelist[start_index: start_index + timestep_1month]))
                average_outside_temperature_list_in_celsius.append(monthly_average_temperature)
                start_index += timestep_1month

        if average_over == "yearly":
            days_in_year = sum(self.days_per_month)
            timestep_1year = int(days_in_year * 24 * 3600 / self.my_simulation_parameters.seconds_per_timestep)
            if start_index + timestep_1year > total_number_of_timesteps_temperature_list:
                timestep_1year = total_number_of_timesteps_temperature_list - start_index
            monthly_average_temperature = float(
                np.mean(temperaturelist[start_index: start_index + timestep_1year]))
            average_outside_temperature_list_in_celsius.append(monthly_average_temperature)
            start_index += timestep_1year

        return average_outside_temperature_list_in_celsius

    def i_save_state(self) -> None:
        """Saves the state."""
        self.previous_state = self.state.self_copy()

    def i_restore_state(self) -> None:
        """Restores the state."""
        self.state = self.previous_state.self_copy()

    def i_doublecheck(self, timestep: int, stsv: cp.SingleTimeStepValues) -> None:
        """Doublechecks."""
        pass

    def write_to_report(self):
        """Write configuration to the report."""
        return self.config.get_string_dict()

    def i_simulate(self, timestep: int, stsv: cp.SingleTimeStepValues, force_convergence: bool) -> None:
        """Performs the simulation of the heat source model."""


        #todo: mix aus serien und parallel verschaltung von rohren einbauen

        simulated_time_in_seconds = self.state.simulated_time_in_seconds

        temperature_brine_in = stsv.get_input_value(self.temperature_brine_in_channel)

        thermal_heat_extraction = stsv.get_input_value(self.thermal_power_channel)

        mass_flow_brine = stsv.get_input_value(self.mass_flow_brine_in_kg_per_s_channel)

        ################################################################################################################
        # calculation of undisturbed temperature of soil in differenz depth

        index_undisturbed_soil_temperature = self.timelist_undisturbed_soil_temperature.index(simulated_time_in_seconds)

        temperature_array_of_undisturbed_soil_at_actual_timestep = self.temperature_array_of_undisturbed_soil[index_undisturbed_soil_temperature]

        temperature_of_undisturbed_soil_in_depth_of_pipe_length_in_celsius = np.mean(
            np.interp(self.length_of_borehole, self.depth_list, temperature_array_of_undisturbed_soil_at_actual_timestep))

        temperature_of_undisturbed_soil_in_depth_of_buried_depth_of_pipe_in_celsius = np.mean(
            np.interp(self.buried_depth_of_pipe, self.depth_list, temperature_array_of_undisturbed_soil_at_actual_timestep))

        average_temperature_of_undisturbed_soil = np.mean(temperature_array_of_undisturbed_soil_at_actual_timestep)

        # calculation of g fuction with interpolation of timesteps
        index_g_func = np.searchsorted(self.timelist_g_function, simulated_time_in_seconds)
        if index_g_func == 0:
            t1, t2 = self.timelist_g_function[0], self.timelist_g_function[0]
            g1, g2 = self.gFunc.gFunc[0], self.gFunc.gFunc[0]
        else:
            t1, t2 = self.timelist_g_function[index_g_func - 1], self.timelist_g_function[index_g_func]
            g1, g2 = self.gFunc.gFunc[index_g_func - 1], self.gFunc.gFunc[index_g_func]

        if t2 != t1:
            gFunc_value = g1 + (simulated_time_in_seconds - t1) / (t2 - t1) * (g2 - g1)
        else:
            gFunc_value = g1

        heat_extraction_rate_per_borehole_in_watt_per_meter = thermal_heat_extraction / self.number_of_boreholes / self.length_of_borehole
        self.LoadAgg.initialize(gFunc_value / (2 * np.pi * self.thermal_conductivity_ground))

        self.LoadAgg.set_current_load(heat_extraction_rate_per_borehole_in_watt_per_meter)

        deltaT_b_array = self.LoadAgg.temporal_superposition()

        deltaT_b = deltaT_b_array[0]

        # calculation of temperatures
        temperature_borehole_wall = average_temperature_of_undisturbed_soil - deltaT_b

        # temperature_borehole_inlet = self.network.get_network_inlet_temperature(
        #     Q_t=thermal_heat_extraction,
        #     T_b=temperature_borehole_wall,
        #     m_flow_network=np.array([self.m_flow_network]),
        #     cp_f=self.cp_f,
        #     nSegments=1)

        temperature_borehole_inlet = temperature_brine_in

        temperature_borehole_outlet = self.network.get_network_outlet_temperature(
            T_f_in=temperature_borehole_inlet,
            T_b=temperature_borehole_wall,
            m_flow_network=np.array([self.m_flow_network]),
            cp_f=self.cp_f,
            nSegments=1)


# todo>: speicherttermin einbauen, der bei regeneration die umgebungstemperatur erhöht --> immer weiter erwärmnen mit irgendeinen polynom abbilden, damit dann entzug mit höhrer temperatur wieder ist

        # fluid temperature over borehole lenght
        #T_f = pipes[0].get_temperature(z, T_f_in[it], T_b[it], m_flow_borehole, cp_f)

        # # calculation of temperature if no massflow
        # if mass_flow_brine == 0:
        #     temperature_borehole_outlet = average_temperature_of_undisturbed_soil + (self.state.temperature_borehole_outlet-average_temperature_of_undisturbed_soil) * np.exp(
        #         -(self.my_simulation_parameters.seconds_per_timestep) / self.time_constant_for_no_massflow)
        #     temperature_borehole_inlet = average_temperature_of_undisturbed_soil + (self.state.temperature_borehole_inlet-average_temperature_of_undisturbed_soil) * np.exp(
        #         -(self.my_simulation_parameters.seconds_per_timestep) / self.time_constant_for_no_massflow)
        #     temperature_borehole_wall = average_temperature_of_undisturbed_soil + (self.state.average_temperature_borehole_wall-average_temperature_of_undisturbed_soil) * np.exp(
        #         -(self.my_simulation_parameters.seconds_per_timestep) / self.time_constant_for_no_massflow)

        #todo: prüfen warum so oft forced wenn die beiden berechnungen aktiv?

        # heat_extraction_network = self.network.get_network_heat_extraction_rate(
        #     T_f_in=temperature_borehole_inlet,
        #     T_b=temperature_borehole_wall,
        #     m_flow_network=np.array([self.m_flow_network]),
        #     cp_f=self.cp_f,
        #     nSegments=1)
        #
        # average_heat_extraction_per_borehole = np.mean(self.network.get_fluid_heat_extraction_rate(
        #     T_f_in=temperature_borehole_inlet,
        #     T_b=temperature_borehole_wall,
        #     m_flow_network=np.array([self.m_flow_network]),
        #     cp_f=self.cp_f,
        #     nSegments=1))

        # ################################################################################################################
        # # get frozen state

        soil_is_frozen = self.get_frozen_state_of_soil(temperature_pipe_surface=temperature_borehole_wall,
                                                       actual_frozen_state=self.state.soil_is_frozen)



        #############################################################################################################
        #set outputs
        stsv.set_output_value(self.average_temperature_of_undisturbed_soil_channel, average_temperature_of_undisturbed_soil)
        stsv.set_output_value(self.temperature_of_undisturbed_soil_in_depth_of_pipe_length_channel,temperature_of_undisturbed_soil_in_depth_of_pipe_length_in_celsius)
        stsv.set_output_value(self.temperature_of_undisturbed_soil_in_depth_of_buried_depth_of_pipe_channel,temperature_of_undisturbed_soil_in_depth_of_buried_depth_of_pipe_in_celsius)
        stsv.set_output_value(self.thermal_heat_extraction_of_borefield_chanel, self.state.thermal_heat_extraction)
        stsv.set_output_value(self.heat_extraction_rate_per_borehole_chanel, self.state.heat_extraction_rate_per_borehole_in_watt_per_meter)
        stsv.set_output_value(self.temperature_borehole_outlet_chanel,  self.state.temperature_borehole_outlet)
        stsv.set_output_value(self.temperature_borehole_inlet_chanel,  self.state.temperature_borehole_inlet)
        stsv.set_output_value(self.temperature_difference_chanel,  self.state.temperature_borehole_outlet- self.state.temperature_borehole_inlet)
        stsv.set_output_value(self.temperature_borehole_wall_chanel, self.state.average_temperature_borehole_wall)# temperature_borehole_wall)
        stsv.set_output_value(self.gFunc_value_chanel, gFunc_value)
        stsv.set_output_value(self.mass_flow_brine_chanel, mass_flow_brine)
        stsv.set_output_value(self.deltaT_b_chanel,  self.state.deltaT_b)

        # #############################################################################################################
         #set state
        self.state.simulated_time_in_seconds = simulated_time_in_seconds + self.my_simulation_parameters.seconds_per_timestep
        self.state.deltaT_b = deltaT_b
        self.state.temperature_borehole_outlet = temperature_borehole_outlet
        self.state.temperature_borehole_inlet = temperature_borehole_inlet
        self.state.average_temperature_borehole_wall = temperature_borehole_wall
        self.state.soil_is_frozen = soil_is_frozen
        self.state.thermal_heat_extraction = thermal_heat_extraction
        self.state.heat_extraction_rate_per_borehole_in_watt_per_meter = heat_extraction_rate_per_borehole_in_watt_per_meter

    def calculation_undisturbed_soil_temperature(self,depth_list, simulated_time_in_seconds,):

        soil_temperarature_array = []

        for depth in depth_list:

            term1 = depth*np.sqrt(np.pi/(self.thermal_diffusivity_ground_in_sqm_per_s*self.simulated_years_in_seconds))

            phi0 = 1.06*np.pi

            term2 = ((2*np.pi*simulated_time_in_seconds)/self.simulated_years_in_seconds)-phi0-term1

            soil_temperature = self.yearly_average_temperature_outside_air+self.amplitude_yearly_average_temperature_and_maximum_monthly_average_temperature_outside_air*np.exp(-term1)*np.cos(term2)

            soil_temperarature_array.append(soil_temperature)

        return soil_temperarature_array

    def get_frozen_state_of_soil(self, temperature_pipe_surface, actual_frozen_state):

        Tcritical_hi = 0#-0.1736
        Tcritical_lo = 0#-0.2264

        if temperature_pipe_surface <= Tcritical_lo:
            # soil changes to frozen state
            soil_is_frozen = True
        elif temperature_pipe_surface > Tcritical_hi:
            # soil changes to unfrozen state
            soil_is_frozen = False
        else:
            # soil keeps its current state
            soil_is_frozen = actual_frozen_state

        return soil_is_frozen

    def get_predefined_bore_field_geometrie(self,bore_field_geometry):
        if bore_field_geometry == BoreFieldGeometry.RECTANGLE_FIELD:
            boreField = gt.borefield.Borefield.rectangle_field(N_1=self.number_of_boreholes_in_x_direction,
                                                          N_2=self.number_of_boreholes_in_y_direction,
                                                          B_1=self.borehole_spacing_both_directions,
                                                          B_2=self.borehole_spacing_both_directions,
                                                          H=self.length_of_borehole,
                                                          D=self.buried_depth_of_pipe,
                                                          r_b=self.radius_of_borehole,
                                                          tilt=0,)
        elif bore_field_geometry == BoreFieldGeometry.L_SHAPED_FIELD:
            boreField = gt.borefield.Borefield.L_shaped_field(N_1=self.number_of_boreholes_in_x_direction,
                                                          N_2=self.number_of_boreholes_in_y_direction,
                                                          B_1=self.borehole_spacing_both_directions,
                                                          B_2=self.borehole_spacing_both_directions,
                                                          H=self.length_of_borehole,
                                                          D=self.buried_depth_of_pipe,
                                                          r_b=self.radius_of_borehole,
                                                          tilt=0,)
        elif bore_field_geometry == BoreFieldGeometry.STAGGERED_RECTANGLE_FIELD:
            boreField = gt.borefield.Borefield.staggered_rectangle_field(N_1=self.number_of_boreholes_in_x_direction,
                                                          N_2=self.number_of_boreholes_in_y_direction,
                                                          B_1=self.borehole_spacing_both_directions,
                                                          B_2=self.borehole_spacing_both_directions,
                                                          H=self.length_of_borehole,
                                                          D=self.buried_depth_of_pipe,
                                                          r_b=self.radius_of_borehole,
                                                               include_last_borehole=True,
                                                          tilt=0,)
        elif bore_field_geometry == BoreFieldGeometry.DENSE_RECTANGLE_FIELD:
            boreField = gt.borefield.Borefield.dense_rectangle_field(N_1=self.number_of_boreholes_in_x_direction,
                                                          N_2=self.number_of_boreholes_in_y_direction,
                                                          B=self.borehole_spacing_both_directions,
                                                          H=self.length_of_borehole,
                                                          D=self.buried_depth_of_pipe,
                                                          r_b=self.radius_of_borehole,
                                                           include_last_borehole=True,
                                                          tilt=0,)
        elif bore_field_geometry == BoreFieldGeometry.U_SHAPED_FIELD:
            boreField = gt.borefield.Borefield.U_shaped_field(N_1=self.number_of_boreholes_in_x_direction,
                                                          N_2=self.number_of_boreholes_in_y_direction,
                                                          B_1=self.borehole_spacing_both_directions,
                                                          B_2=self.borehole_spacing_both_directions,
                                                          H=self.length_of_borehole,
                                                          D=self.buried_depth_of_pipe,
                                                          r_b=self.radius_of_borehole,
                                                          tilt=0,)
        elif bore_field_geometry == BoreFieldGeometry.BOX_SHAPED_FIELD:
            boreField = gt.borefield.Borefield.box_shaped_field(N_1=self.number_of_boreholes_in_x_direction,
                                                          N_2=self.number_of_boreholes_in_y_direction,
                                                          B_1=self.borehole_spacing_both_directions,
                                                          B_2=self.borehole_spacing_both_directions,
                                                          H=self.length_of_borehole,
                                                          D=self.buried_depth_of_pipe,
                                                          r_b=self.radius_of_borehole,
                                                          tilt=0,)
        elif bore_field_geometry == BoreFieldGeometry.CIRCLE_FIELD:
            raise ValueError("BoreFieldGeometry.CIRCLE_FIELD not implemented")
            # boreField = gt.borefield.Borefield.circle_field(N_1=self.number_of_boreholes_in_x_direction,
            #                                               N_2=self.number_of_boreholes_in_y_direction,
            #                                               B_1=self.borehole_spacing_both_directions,
            #                                               B_2=self.borehole_spacing_both_directions,
            #                                               H=self.length_of_borehole,
            #                                               D=self.buried_depth_of_pipe,
            #                                               r_b=self.radius_of_borehole,
            #                                               tilt=0,)
        else:
            raise ValueError("Unknown Predefined Bore Field Geometry")

        return boreField

    def get_borehole_pipes(self,sort_of_pipe):

        pipes = []

        if sort_of_pipe == SortOfPipe.DOUBLE_U_TUBE:
            self.pipe_pos = [(-self.shank_spacing, 0.), (0., -self.shank_spacing), (self.shank_spacing, 0.),
                             (0., self.shank_spacing)]
            for borehole in self.boreField:
                DOUBLE_U_TUBE = gt.pipes.MultipleUTube(
                    pos=self.pipe_pos,
                    r_in=self.inner_pipe_radius,
                    r_out=self.outer_pipe_radius,
                    borehole=borehole,
                    k_s=self.thermal_conductivity_ground,
                    k_g=self.thermal_conductivity_grout,
                    R_fp=self.thermal_resistance_of_fluid + self.thermal_resistance_of_pipe,
                    nPipes=2,
                    config='parallel')
                pipes.append(DOUBLE_U_TUBE)

        elif sort_of_pipe == SortOfPipe.SINGLE_U_TUBE:
            self.pipe_pos = [(-self.shank_spacing, 0.), (self.shank_spacing, 0.)]
            for borehole in self.boreField:
                SingleUTube = gt.pipes.SingleUTube(
                    pos=self.pipe_pos,
                    r_in=self.inner_pipe_radius,
                    r_out=self.outer_pipe_radius,
                    borehole=borehole,
                    k_s=self.thermal_conductivity_ground,
                    k_g=self.thermal_conductivity_grout,
                    R_fp=self.thermal_resistance_of_fluid + self.thermal_resistance_of_pipe, )

                pipes.append(SingleUTube)

        elif sort_of_pipe == SortOfPipe.COAXIAL:
            raise ValueError("not fully implemented --> R_ff fehlt")
            self.pipe_pos = [(-self.shank_spacing, 0.), (self.shank_spacing, 0.)]
            for borehole in self.boreField:
                CoaxialPipe = gt.pipes.Coaxial(
                    pos=self.pipe_pos,
                    r_in=self.inner_pipe_radius,
                    r_out=self.outer_pipe_radius,
                    borehole=borehole,
                    k_s=self.thermal_conductivity_ground,
                    k_g=self.thermal_conductivity_grout,
                    R_ff=thermal_resistance_of_fluid_to_fluid_coaxial_inner_pipe,
                    R_fp=thermal_resistance_of_fluid + self.thermal_resistance_of_pipe, )

                pipes.append(CoaxialPipe)

        else:
            raise ValueError("Unknown Sort of Pipe")

        return pipes

    @staticmethod
    def get_cost_capex(
        config: GroundProbeConfig,
        simulation_parameters: SimulationParameters
    ) -> CapexCostDataClass:
        """Returns investment cost, CO2 emissions and lifetime."""
        seconds_per_year = 365 * 24 * 60 * 60
        capex_per_simulated_period = (config.investment_costs_in_euro / config.lifetime_in_years) * (
            simulation_parameters.duration.total_seconds() / seconds_per_year
        )
        device_co2_footprint_per_simulated_period = (config.device_co2_footprint_in_kg / config.lifetime_in_years) * (
            simulation_parameters.duration.total_seconds() / seconds_per_year
        )
        capex_cost_data_class = CapexCostDataClass(
            capex_investment_cost_in_euro=config.investment_costs_in_euro,
            device_co2_footprint_in_kg=config.device_co2_footprint_in_kg,
            lifetime_in_years=config.lifetime_in_years,
            capex_investment_cost_for_simulated_period_in_euro=capex_per_simulated_period,
            device_co2_footprint_for_simulated_period_in_kg=device_co2_footprint_per_simulated_period,
            kpi_tag=KpiTagEnumClass.GROUND_PROBE
        )
        return capex_cost_data_class

    def get_cost_opex(
        self,
        all_outputs: List,
        postprocessing_results: pd.DataFrame,
    ) -> OpexCostDataClass:
        # pylint: disable=unused-argument
        """Calculate OPEX costs, consisting of maintenance costs for Heat Distribution System."""
        opex_cost_data_class = OpexCostDataClass(
            opex_energy_cost_in_euro=0,
            opex_maintenance_cost_in_euro=self.calc_maintenance_cost(),
            co2_footprint_in_kg=0,
            consumption_in_kwh=0,
            loadtype=lt.LoadTypes.ANY,
            kpi_tag=KpiTagEnumClass.GROUND_PROBE
        )

        return opex_cost_data_class

    def get_component_kpi_entries(
        self,
        all_outputs: List,
        postprocessing_results: pd.DataFrame,
    ) -> List[KpiEntry]:
        """Calculates KPIs for the respective component and return all KPI entries as list."""

        list_of_kpi_entries: List[KpiEntry] = []
        for index, output in enumerate(all_outputs):
            if output.component_name == self.component_name:
                if output.field_name == self.HeatExtractionOfBoreField and output.load_type == lt.LoadTypes.HEATING and output.unit == lt.Units.WATT:
                    thermal_output_power_values_in_watt = postprocessing_results.iloc[:, index].loc[
                        postprocessing_results.iloc[:, index] > 0.0
                        ]
                    thermal_output_energy_in_kilowatt_hour = KpiHelperClass.compute_total_energy_from_power_timeseries(
                        power_timeseries_in_watt=thermal_output_power_values_in_watt,
                        timeresolution=self.my_simulation_parameters.seconds_per_timestep,
                    )
                    thermal_output_energy_entry = KpiEntry(
                        name="Thermal heat extraction energy of bore field",
                        unit="kWh",
                        value=thermal_output_energy_in_kilowatt_hour,
                        tag=KpiTagEnumClass.GROUND_PROBE,
                        description=self.component_name,
                    )
                    list_of_kpi_entries.append(thermal_output_energy_entry)

                elif output.field_name == self.HeatExtractionRatePerBorehole and output.load_type == lt.LoadTypes.HEATING and output.unit == lt.Units.WATT_PER_METER:
                    specific_thermal_output_power_values_in_watt_per_meter = postprocessing_results.iloc[:, index].loc[
                        postprocessing_results.iloc[:, index] > 0.0
                        ]

                    (
                        mean_specific_thermal_output_power_values_in_watt_per_meter,
                        max_specific_thermal_output_power_values_in_watt_per_meter,
                        min_specific_thermal_output_power_values_in_watt_per_meter,
                    ) = KpiHelperClass.calc_mean_max_min_value(
                        list_or_pandas_series=specific_thermal_output_power_values_in_watt_per_meter)

                    mean_specific_thermal_output_power_values_in_watt_per_meter_entry = KpiEntry(
                        name="Mean specific thermal heat extraction rate of bore field",
                        unit="W/m",
                        value=mean_specific_thermal_output_power_values_in_watt_per_meter,
                        tag=KpiTagEnumClass.GROUND_PROBE,
                        description=self.component_name,
                    )
                    list_of_kpi_entries.append(mean_specific_thermal_output_power_values_in_watt_per_meter_entry)

                    max_specific_thermal_output_power_values_in_watt_per_meter_entry = KpiEntry(
                        name="Max specific thermal heat extraction rate of bore field",
                        unit="W/m",
                        value=max_specific_thermal_output_power_values_in_watt_per_meter,
                        tag=KpiTagEnumClass.GROUND_PROBE,
                        description=self.component_name,
                    )
                    list_of_kpi_entries.append(max_specific_thermal_output_power_values_in_watt_per_meter_entry)

                    min_specific_thermal_output_power_values_in_watt_per_meter_entry = KpiEntry(
                        name="Min specific thermal heat extraction rate of bore field",
                        unit="W/m",
                        value=min_specific_thermal_output_power_values_in_watt_per_meter,
                        tag=KpiTagEnumClass.GROUND_PROBE,
                        description=self.component_name,
                    )
                    list_of_kpi_entries.append(min_specific_thermal_output_power_values_in_watt_per_meter_entry)

                elif output.field_name == self.TemperatureBrineInlet:
                    inlet_temperature_list_in_celsius = postprocessing_results.iloc[:, index]
                elif output.field_name == self.TemperatureBrineOutlet:
                    outlet_temperature_list_in_celsius = postprocessing_results.iloc[:, index]

        # get mean, max and min values of flow and return temperatures
        temperature_diff_in_and_out_in_celsius = (
                inlet_temperature_list_in_celsius - outlet_temperature_list_in_celsius
        )
        (
            mean_temperature_difference_between_in_and_out_in_celsius,
            max_temperature_difference_between_in_and_out_in_celsius,
            min_temperature_difference_between_in_and_out_in_celsius,
        ) = KpiHelperClass.calc_mean_max_min_value(list_or_pandas_series=temperature_diff_in_and_out_in_celsius)

        (
            mean_inlet_temperature_in_celsius,
            max_inlet_temperature_in_celsius,
            min_inlet_temperature_in_celsius,
        ) = KpiHelperClass.calc_mean_max_min_value(list_or_pandas_series=inlet_temperature_list_in_celsius)

        (
            mean_outlet_temperature_in_celsius,
            max_outlet_temperature_in_celsius,
            min_outlet_temperature_in_celsius,
        ) = KpiHelperClass.calc_mean_max_min_value(list_or_pandas_series=outlet_temperature_list_in_celsius)

        # make kpi entries and append to list
        mean_inlet_temperature_entry = KpiEntry(
            name="Mean inlet temperature of bore field",
            unit="°C",
            value=mean_inlet_temperature_in_celsius,
            tag=KpiTagEnumClass.GROUND_PROBE,
            description=self.component_name,
        )
        list_of_kpi_entries.append(mean_inlet_temperature_entry)

        mean_outlet_temperature_entry = KpiEntry(
            name="Mean outlet temperature of bore field",
            unit="°C",
            value=mean_outlet_temperature_in_celsius,
            tag=KpiTagEnumClass.GROUND_PROBE,
            description=self.component_name,
        )
        list_of_kpi_entries.append(mean_outlet_temperature_entry)

        mean_temperature_difference_entry = KpiEntry(
            name="Mean temperature difference of bore field",
            unit="°C",
            value=mean_temperature_difference_between_in_and_out_in_celsius,
            tag=KpiTagEnumClass.GROUND_PROBE,
            description=self.component_name,
        )
        list_of_kpi_entries.append(mean_temperature_difference_entry)

        max_inlet_temperature_entry = KpiEntry(
            name="Max inlet temperature of bore field",
            unit="°C",
            value=max_inlet_temperature_in_celsius,
            tag=KpiTagEnumClass.GROUND_PROBE,
            description=self.component_name,
        )
        list_of_kpi_entries.append(max_inlet_temperature_entry)

        max_outlet_temperature_entry = KpiEntry(
            name="Max return temperature of bore field",
            unit="°C",
            value=max_outlet_temperature_in_celsius,
            tag=KpiTagEnumClass.GROUND_PROBE,
            description=self.component_name,
        )
        list_of_kpi_entries.append(max_outlet_temperature_entry)

        max_temperature_difference_entry = KpiEntry(
            name="Max temperature difference of bore field",
            unit="°C",
            value=max_temperature_difference_between_in_and_out_in_celsius,
            tag=KpiTagEnumClass.GROUND_PROBE,
            description=self.component_name,
        )
        list_of_kpi_entries.append(max_temperature_difference_entry)

        min_inlet_temperature_entry = KpiEntry(
            name="Min inlet temperature of bore field",
            unit="°C",
            value=min_inlet_temperature_in_celsius,
            tag=KpiTagEnumClass.GROUND_PROBE,
            description=self.component_name,
        )
        list_of_kpi_entries.append(min_inlet_temperature_entry)

        min_outlet_temperature_entry = KpiEntry(
            name="Min outlet temperature of bore field",
            unit="°C",
            value=min_outlet_temperature_in_celsius,
            tag=KpiTagEnumClass.GROUND_PROBE,
            description=self.component_name,
        )
        list_of_kpi_entries.append(min_outlet_temperature_entry)

        min_temperature_difference_entry = KpiEntry(
            name="Min temperature difference of bore field",
            unit="°C",
            value=min_temperature_difference_between_in_and_out_in_celsius,
            tag=KpiTagEnumClass.GROUND_PROBE,
            description=self.component_name,
        )
        list_of_kpi_entries.append(min_temperature_difference_entry)

        return list_of_kpi_entries


@dataclass_json
@dataclass
class GroundHeatSourceInformation:
    """Class for collecting important heat distribution parameters to pass to other components."""

    def __init__(self, config: GroundProbeConfig,):
        """Initialize the class."""

        self.ground_source_config = config

        self.fluid_props()

    def fluid_props(self,):
        fluid = gt.media.Fluid(self.ground_source_config.fluid_type.value, self.ground_source_config.mass_fraction_of_fluid_mixed_in_water * 100)
        self.cp_f = fluid.cp  # Fluid specific isobaric heat capacity (J/kg.K)
        self.rho_f = fluid.rho  # Fluid density (kg/m3)
        self.mu_f = fluid.mu  # Fluid dynamic viscosity (kg/m.s)
        self.k_f = fluid.k  # Fluid thermal conductivity (W/m.K)

