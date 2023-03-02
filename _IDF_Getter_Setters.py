import datetime, sys, os

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
    zone_temp_c = []
    zone_damper_pos_sensor = []
    zone_damper_pos_actuator = []
    for zone in zone_names:
        _tmp = ep_api.exchange.get_variable_handle(state,
                                                   "Zone Air Temperature",
                                                   zone)
        if _tmp < 0:
            raise Exception("Error: Invalid handle")
        zone_temp_c.append(_tmp)

    for i in [1,2,3,5]:
        _tmp = ep_api.exchange.get_variable_handle(state,
                                                   "Air System Outdoor Air Flow Fraction",
                                                   "VAV_"+str(i))
        if _tmp < 0:
            raise Exception("Error: Invalid handle")
        zone_damper_pos_sensor.append(_tmp)

        _tmp = ep_api.exchange.get_actuator_handle(state,
                                                   "System Node Setpoint",
                                                   "Mass Flow Rate Setpoint",
                                                   "VAV_"+str(i)+"_OAINLET NODE")
        if _tmp < 0:
            raise Exception("Error: Invalid handle")
        zone_damper_pos_actuator.append(_tmp)

    return zone_temp_c, zone_damper_pos_sensor, zone_damper_pos_actuator

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
    OutputVariable	Air System Outdoor Air Flow Fraction	VAV_1
    OutputVariable	Air System Outdoor Air Flow Fraction	VAV_2
    OutputVariable	Air System Outdoor Air Flow Fraction	VAV_3
    OutputVariable	Air System Outdoor Air Flow Fraction	VAV_5
    Actuator	System Node Setpoint	Mass Flow Rate Setpoint	VAV_1_OAINLET NODE;
    '''
    global allHandles
    allHandles = {}
    allHandles['sensor'] = {}
    allHandles['actuator'] = {}

    allHandles['sensor']['OAT_C'] = 0
    allHandles['sensor']['RH_percent'] = 0
    allHandles['sensor']['EnergyConsumption_Watts'] = {}
    allHandles['sensor']['EnergyConsumption_Watts']['Chiler'] = 0
    allHandles['sensor']['EnergyConsumption_Watts']['Boiler'] = 0
    allHandles['sensor']['Chiler_SET_C'] = 0
    allHandles['sensor']['Boiler_SET_C'] = 0
    allHandles['sensor']['room_temp_c'] = []
    allHandles['sensor']['Damper_Position'] = []

    allHandles['actuator']['Damper_Position'] = []
    allHandles['actuator']['Chiler_SET_C'] = 0
    allHandles['actuator']['Boiler_SET_C'] = 0

    oat_c = ep_api.exchange.get_variable_handle(state,"Site Outdoor Air Drybulb Temperature",
                                                                             "Environment")
    rh_percent = ep_api.exchange.get_variable_handle(state,"Site Outdoor Air Humidity Ratio",
                                                                             "Environment")
    chill_watts = ep_api.exchange.get_variable_handle(state,
                                                      "Chiller Electricity Rate",
                                                      "COOLSYS1 CHILLER 1")
    boiler_watts = ep_api.exchange.get_variable_handle(state,
                                                         "Boiler Heating Rate",
                                                         "HEATSYS1 BOILER")
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
    if oat_c * rh_percent * chill_watts * boiler_watts * \
            chiler_set_c_sensor * boiler_set_c_sensor * \
            chiler_set_c_actuator * boiler_set_c_actuator < 0:
        raise Exception("Error: Invalid handle")

    zone_temp_c, zone_damper_pos_sensor, zone_damper_pos_actuator = get_zone_handles(state)
    allHandles['sensor']['OAT_C'] = oat_c
    allHandles['sensor']['RH_percent'] = rh_percent
    allHandles['sensor']['EnergyConsumption_Watts']['Chiler'] = chill_watts
    allHandles['sensor']['EnergyConsumption_Watts']['Boiler'] = boiler_watts
    allHandles['sensor']['Chiler_SET_C'] = chiler_set_c_sensor
    allHandles['sensor']['Boiler_SET_C'] = boiler_set_c_sensor
    allHandles['sensor']['room_temp_c'] = zone_temp_c
    allHandles['sensor']['Damper_Position'] = zone_damper_pos_sensor
    allHandles['actuator']['Damper_Position'] = zone_damper_pos_actuator
    allHandles['actuator']['Chiler_SET_C'] = chiler_set_c_actuator
    allHandles['actuator']['Boiler_SET_C'] = boiler_set_c_actuator

def get_sensor_value(state):
    time_in_hours = ep_api.exchange.current_sim_time(state)
    _readable_time = datetime.timedelta(hours=time_in_hours)
    print('Time: ', _readable_time)
    sensor_values = {}
    sensor_values['OAT_C'] = ep_api.exchange.get_variable_value(state, allHandles['sensor']['OAT_C'])
    sensor_values['RH_percent'] = ep_api.exchange.get_variable_value(state, allHandles['sensor']['RH_percent'])
    sensor_values['EnergyConsumption_Watts'] = {}
    sensor_values['EnergyConsumption_Watts']['Chiler'] = \
        ep_api.exchange.get_variable_value(state, allHandles['sensor']['EnergyConsumption_Watts']['Chiler'])
    sensor_values['EnergyConsumption_Watts']['Boiler'] = \
        ep_api.exchange.get_variable_value(state, allHandles['sensor']['EnergyConsumption_Watts']['Boiler'])
    sensor_values['Chiler_SET_C'] = ep_api.exchange.get_variable_value(state, allHandles['sensor']['Chiler_SET_C'])
    sensor_values['Boiler_SET_C'] = ep_api.exchange.get_variable_value(state, allHandles['sensor']['Boiler_SET_C'])
    sensor_values['room_temp_c'] = []
    sensor_values['Damper_Position'] = []
    for i in range(len(allHandles['sensor']['room_temp_c'])):
        sensor_values['room_temp_c'].append(
            ep_api.exchange.get_variable_value(state, allHandles['sensor']['room_temp_c'][i]))
    for i in range(len(allHandles['sensor']['Damper_Position'])):
        sensor_values['Damper_Position'].append(
            ep_api.exchange.get_variable_value(state, allHandles['sensor']['Damper_Position'][i]))
    return sensor_values
def set_actuators(state, actuator_values):
    ep_api.exchange.set_actuator_value(state, allHandles['actuator']['Chiler_SET_C'], actuator_values['Chiler_SET_C'])
    ep_api.exchange.set_actuator_value(state, allHandles['actuator']['Boiler_SET_C'], actuator_values['Boiler_SET_C'])
    for i in range(len(allHandles['actuator']['Damper_Position'])):
        ep_api.exchange.set_actuator_value(state, allHandles['actuator']['Damper_Position'][i], actuator_values['Damper_Position'][i])
def api_to_csv(state):
    orig = ep_api.exchange.list_available_api_data_csv(state)
    newFileByteArray = bytearray(orig)
    api_path = os.path.join(os.path.dirname(__file__), 'api_data.csv')
    newFile = open(api_path, "wb")
    newFile.write(newFileByteArray)
    newFile.close()
def timeStepHandler(state):
    global get_handle_bool
    if not get_handle_bool:
        get_building_handles(state)
        get_handle_bool = True
        api_to_csv(state)
    warm_up = ep_api.exchange.warmup_flag(state)
    if not warm_up:
        sensor_values = get_sensor_value(state)
        print(sensor_values)
        set_actuators(state, sensor_values)
def init():
    sys.path.insert(0, '/usr/local/EnergyPlus-22-1-0/')
    sys.path.insert(0, 'C:/EnergyPlusV22-1-0')
    from pyenergyplus.api import EnergyPlusAPI
    global ep_api, get_handle_bool
    get_handle_bool = False
    ep_api = EnergyPlusAPI()
    state = ep_api.state_manager.new_state()
    ep_api.runtime.callback_after_predictor_before_hvac_managers(state, timeStepHandler)
    ep_api.exchange.request_variable(state, "Site Outdoor Air Drybulb Temperature", "ENVIRONMENT")
    ep_api.exchange.request_variable(state, "Site Outdoor Air Humidity Ratio", "ENVIRONMENT")
    return state

def main():
    state = init()
    idfFilePath = 'RefBldgLargeOfficeNew2004_v1.4_7.2_5A_USA_IL_CHICAGO-OHARE.idf'
    weather_file_path = 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
    output_path = './ep_trivial'
    sys_args = '-d', output_path, '-w', weather_file_path, idfFilePath
    ep_api.runtime.run_energyplus(state, sys_args)

if __name__ == '__main__':
    main()
