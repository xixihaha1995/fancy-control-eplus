import datetime, sys, os, threading
import time
from multiprocessing import Barrier

sys.path.insert(0, '/usr/local/EnergyPlus-22-1-0/')
sys.path.insert(0, 'C:/EnergyPlusV22-1-0')
from pyenergyplus.api import EnergyPlusAPI


def get_zone_handles(state):
    global zone_names
    zone_names = ['Basement',
                  'Core_bottom',
                  'Core_mid',
                  'Core_top',
                  'Perimeter_bot_ZN_1',
                  'Perimeter_bot_ZN_2',
                  'Perimeter_bot_ZN_3',
                  'Perimeter_bot_ZN_4',
                  'Perimeter_mid_ZN_1',
                  'Perimeter_mid_ZN_2',
                  'Perimeter_mid_ZN_3',
                  'Perimeter_mid_ZN_4',
                  'Perimeter_top_ZN_1',
                  'Perimeter_top_ZN_2',
                  'Perimeter_top_ZN_3',
                  'Perimeter_top_ZN_4']
    '''
    OutputVariable	Zone Air Terminal VAV Damper Position	BASEMENT VAV BOX COMPONENT
    OutputVariable	Zone Air System Sensible Heating Energy	BASEMENT	
    #Actuator	System Node Setpoint	Mass Flow Rate Setpoint	BASEMENT VAV BOX DAMPER NODE;
    Actuator	System Node Setpoint	Mass Flow Rate Setpoint	BASEMENT VAV BOX OUTLET NODE NAME;
    '''
    zone_temp_c = []
    zone_target_temp_c = []
    zone_damper_pos_sensor = []
    zone_damper_pos_actuator = []
    for zone in zone_names:
        _tmpRtemp = ep_api.exchange.get_variable_handle(state,
                                                   "Zone Air Temperature",
                                                   zone)
        _tmpTtemp = ep_api.exchange.get_variable_handle(state,
                                                   "Zone Thermostat Air Temperature",
                                                   zone)
        _tmpDPosSensor = ep_api.exchange.get_variable_handle(state,
                                                    "Zone Air Terminal VAV Damper Position",
                                                    zone+" VAV BOX COMPONENT")
        _tmpDPosActuator = ep_api.exchange.get_actuator_handle(state,
                                                    "System Node Setpoint",
                                                    "Mass Flow Rate Setpoint",
                                                    zone+" VAV BOX OUTLET NODE NAME")

        if _tmpRtemp * _tmpTtemp * _tmpDPosSensor * _tmpDPosActuator < 0:
            raise Exception("Error: Invalid handle for zone: "+zone)
        zone_temp_c.append(_tmpRtemp)
        zone_target_temp_c.append(_tmpTtemp)
        zone_damper_pos_sensor.append(_tmpDPosSensor)
        zone_damper_pos_actuator.append(_tmpDPosActuator)

    return zone_temp_c, zone_target_temp_c, zone_damper_pos_sensor, zone_damper_pos_actuator

def get_building_handles(state):
    '''
    Time, OAT, RH, Damper_Position, Demand_Watts, Chiler_SET_C, Boiler_SET_C
    HVAC,Average,Chiller Electricity Rate [W]
    HVAC,Average,Boiler Heating Rate [W]
    HVAC,Average,Chiller Evaporator Outlet Temperature [C]
    HVAC,Average,Boiler Outlet Temperature [C]

    Damper_Position, Chiler_SET_C, Boiler_SET_C
    Actuator	System Node Setpoint	Temperature Setpoint	HEATSYS1 SUPPLY EQUIPMENT OUTLET NODE;
    Actuator	System Node Setpoint	Temperature Setpoint	COOLSYS1 SUPPLY EQUIPMENT OUTLET NODE 1;
    OutputVariable	Zone Air Temperature	BASEMENT
    '''
    global allHandles
    allHandles = {}
    allHandles['sensor'] = {}
    allHandles['actuator'] = {}

    allHandles['sensor']['OAT_C'] = 0
    allHandles['sensor']['RH_percent'] = 0
    allHandles['sensor']['hvac_electricity_watts'] = 0
    allHandles['sensor']['Chiler_SET_C'] = 0
    allHandles['sensor']['Boiler_SET_C'] = 0
    allHandles['sensor']['room_temp_c'] = []
    allHandles['sensor']['Damper_Position'] = []
    allHandles['sensor']['room_target_temp_c'] = []

    allHandles['actuator']['Damper_Position'] = []
    allHandles['actuator']['Chiler_SET_C'] = 0
    allHandles['actuator']['Boiler_SET_C'] = 0
    allHandles['actuator']['OAT_C'] = 0
    allHandles['actuator']['RH_percent'] = 0

    oat_c = ep_api.exchange.get_variable_handle(state,"Site Outdoor Air Drybulb Temperature",
                                                                             "Environment")
    rh_percent = ep_api.exchange.get_variable_handle(state,"Site Outdoor Air Humidity Ratio",
                                                                             "Environment")
    hvac_electricity = ep_api.exchange.get_variable_handle(state,"Facility Total HVAC Electricity Demand Rate",
                                                                                "WHOLE BUILDING")
    chiler_set_c_sensor = ep_api.exchange.get_variable_handle(state,
                                                       "Chiller Evaporator Outlet Temperature",
                                                       "COOLSYS1 CHILLER 1")
    boiler_set_c_sensor = ep_api.exchange.get_variable_handle(state,
                                                         "Boiler Outlet Temperature",
                                                         "HEATSYS1 BOILER")
    chiler_set_c_actuator = ep_api.exchange.get_actuator_handle(state,
                                                        "System Node Setpoint",
                                                        "Temperature Setpoint",
                                                        "COOLSYS1 SUPPLY EQUIPMENT OUTLET NODE 1")
    boiler_set_c_actuator = ep_api.exchange.get_actuator_handle(state,
                                                        "System Node Setpoint",
                                                        "Temperature Setpoint",
                                                        "HEATSYS1 SUPPLY EQUIPMENT OUTLET NODE")
    odb_actuator_handle = ep_api.exchange.get_actuator_handle(state,
                                                              "Weather Data", "Outdoor Dry Bulb", "Environment")
    orh_actuator_handle = ep_api.exchange.get_actuator_handle(state,
                                                              "Weather Data", "Outdoor Relative Humidity", "Environment")
    if oat_c * rh_percent * hvac_electricity* \
            chiler_set_c_sensor * boiler_set_c_sensor * \
            chiler_set_c_actuator * boiler_set_c_actuator * \
            odb_actuator_handle * orh_actuator_handle < 0:
        raise Exception("Error: Invalid handle")

    zone_temp_c, zone_target_temp_c, zone_damper_pos_sensor, zone_damper_pos_actuator = get_zone_handles(state)

    allHandles['sensor']['hvac_electricity_watts'] = hvac_electricity
    allHandles['sensor']['room_temp_c'] = zone_temp_c
    allHandles['sensor']['Chiler_SET_C'] = chiler_set_c_sensor
    allHandles['sensor']['Boiler_SET_C'] = boiler_set_c_sensor
    allHandles['sensor']['Damper_Position'] = zone_damper_pos_sensor
    allHandles['sensor']['OAT_C'] = oat_c
    allHandles['sensor']['RH_percent'] = rh_percent
    allHandles['sensor']['room_target_temp_c'] = zone_target_temp_c

    allHandles['actuator']['Chiler_SET_C'] = chiler_set_c_actuator
    allHandles['actuator']['Boiler_SET_C'] = boiler_set_c_actuator
    allHandles['actuator']['Damper_Position'] = zone_damper_pos_actuator
    allHandles['actuator']['OAT_C'] = odb_actuator_handle
    allHandles['actuator']['RH_percent'] = orh_actuator_handle
def get_sensor_value(state):
    time_in_hours = ep_api.exchange.current_sim_time(state)
    # _readable_time = datetime.timedelta(hours=time_in_hours)
    print('Time: ', time_in_hours)
    sensor_values = {}
    sensor_values['hvac_electricity_watts'] = ep_api.exchange.get_variable_value(state,
                                                                           allHandles['sensor']['hvac_electricity_watts'])
    sensor_values['room_temp_c'] = []
    for i in range(len(allHandles['sensor']['room_temp_c'])):
        sensor_values['room_temp_c'].append(
            ep_api.exchange.get_variable_value(state, allHandles['sensor']['room_temp_c'][i]))
    sensor_values['Chiler_SET_C'] = ep_api.exchange.get_variable_value(state, allHandles['sensor']['Chiler_SET_C'])
    sensor_values['Boiler_SET_C'] = ep_api.exchange.get_variable_value(state, allHandles['sensor']['Boiler_SET_C'])
    sensor_values['Damper_Position'] = []
    for i in range(len(allHandles['sensor']['Damper_Position'])):
        sensor_values['Damper_Position'].append(
            ep_api.exchange.get_variable_value(state, allHandles['sensor']['Damper_Position'][i]))
    sensor_values['OAT_C'] = ep_api.exchange.get_variable_value(state, allHandles['sensor']['OAT_C'])
    sensor_values['RH_percent'] = ep_api.exchange.get_variable_value(state, allHandles['sensor']['RH_percent'])
    sensor_values['room_target_temp_c'] = []
    for i in range(len(allHandles['sensor']['room_target_temp_c'])):
        sensor_values['room_target_temp_c'].append(
            ep_api.exchange.get_variable_value(state, allHandles['sensor']['room_target_temp_c'][i]))

    return sensor_values
def set_actuators(state, to_set):
    ep_api.exchange.set_actuator_value(state, allHandles['actuator']['Chiler_SET_C'], to_set['Chiler_SET_C'])
    ep_api.exchange.set_actuator_value(state, allHandles['actuator']['Boiler_SET_C'], to_set['Boiler_SET_C'])
    ep_api.exchange.set_actuator_value(state, allHandles['actuator']['OAT_C'], to_set['OAT_C'])
    ep_api.exchange.set_actuator_value(state, allHandles['actuator']['RH_percent'], to_set['RH_percent'])
    for i in range(len(allHandles['actuator']['Damper_Position'])):
        ep_api.exchange.set_actuator_value(state, allHandles['actuator']['Damper_Position'][i], to_set['Damper_Position'][i])
def timeStepHandler(state):
    global get_handle_bool
    if not get_handle_bool:
        get_building_handles(state)
        get_handle_bool = True
    warm_up = ep_api.exchange.warmup_flag(state)
    if not warm_up:
        # barrier_0.wait()
        sensor_values = get_sensor_value(state)
        #print thread info
        print(f'Thread: {threading.current_thread().name}, state: {state}')
        # barrier_1.wait()
def init_idf():

    global ep_api, get_handle_bool
    get_handle_bool = False
    ep_api = EnergyPlusAPI()
    state = ep_api.state_manager.new_state()
    ep_api.runtime.callback_after_predictor_before_hvac_managers(state, timeStepHandler)
    ep_api.exchange.request_variable(state, "Site Outdoor Air Drybulb Temperature", "ENVIRONMENT")
    ep_api.exchange.request_variable(state, "Site Outdoor Air Humidity Ratio", "ENVIRONMENT")
    return state

def one_idf_run(name):
    state = init_idf()
    idfFilePath = 'RefBldgLargeOfficeNew2004_v1.4_7.2_5A_USA_IL_CHICAGO-OHARE_V2210.idf'
    weather_file_path = 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
    output_path = f'./ep_trivial_output/{name}'
    sys_args = ['-d', output_path, '-a','-w', weather_file_path, idfFilePath]
    ep_api.runtime.run_energyplus(state, sys_args)

def VCWG_EP_District():
    global barrier_0, barrier_1, sem0
    nb_idf = 1
    sem0 = threading.Semaphore(1)
    barrier_0 = Barrier(nb_idf + 1)
    barrier_1 = Barrier(nb_idf + 1)
    for i in range(nb_idf):
        thread_idf = threading.Thread(target=one_idf_run, args=(i,))
        thread_idf.start()

    # while True:
    #     #timed semaphore wait 60 seconds
    #     if not sem0.acquire(timeout=60):
    #         print("VCWG: Timeout waiting for energy")
    #         #end this function
    #         return
    #
    #     print(f"VCWG: Uploading weather for time step")
    #     # time.sleep(1)
    #     barrier_0.wait()
    #
    #     barrier_1.wait()
    #     print(f"VCWG: Downloading energy for time step")
    #     # time.sleep(1)
    #     sem0.release()

if __name__ == '__main__':
    VCWG_EP_District()