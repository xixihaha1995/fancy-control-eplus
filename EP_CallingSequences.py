import datetime, sys, os, threading
import time, random
from multiprocessing import Barrier

sys.path.insert(0, '/usr/local/EnergyPlus-22-1-0/')
sys.path.insert(0, 'C:/EnergyPlusV22-1-0')
from pyenergyplus.api import EnergyPlusAPI

def timeStepHandler(state):
    global eplastcalltime,wasteHeat, shared_dict
    threadName = threading.current_thread().name
    if not call_thread[threadName]:
        return
    curr_sim_time_in_hours = ep_api.exchange.current_sim_time(state)
    curr_sim_time_in_seconds = curr_sim_time_in_hours * 3600
    _round = round(curr_sim_time_in_seconds)
    accumulated_time = curr_sim_time_in_seconds - eplastcalltime[threadName]
    _converge = 2 > abs(accumulated_time - 30 * 60)
    print(f'HVAC detecting convergence,{_converge},'
          f'curr_sim_time_in_seconds: {curr_sim_time_in_seconds},'
          f'eplastcalltime[threadName]: {eplastcalltime[threadName]}')
    if not _converge:
        return
    eplastcalltime[threadName] = curr_sim_time_in_seconds
def overwrite_ep_weather(state):
    global call_thread, eplastcalltime_over, shared_dict
    warm_up = ep_api.exchange.warmup_flag(state)
    if not warm_up:
        threadName = threading.current_thread().name
        call_thread[threadName] = True

        curr_sim_time_in_hours = ep_api.exchange.current_sim_time(state)
        curr_sim_time_in_seconds = curr_sim_time_in_hours * 3600

        accumulated_time = curr_sim_time_in_seconds - eplastcalltime_over[threadName]
        _converge = round(abs(accumulated_time)) %(30 * 60) ==0 or abs(accumulated_time) > 1E4
        print(f'detecting convergence,{_converge},'
              f'curr_sim_time_in_seconds: {curr_sim_time_in_seconds},'
              f'eplastcalltime_over[threadName]: {eplastcalltime_over[threadName]}')
        if not _converge:
            return
        eplastcalltime_over[threadName] = curr_sim_time_in_seconds


def one_idf_run(name):
    state = ep_api.state_manager.new_state()
    ep_api.runtime.callback_begin_zone_timestep_before_set_current_weather(state, overwrite_ep_weather)
    ep_api.runtime.callback_end_system_timestep_after_hvac_reporting(state, timeStepHandler)
    ep_api.exchange.request_variable(state, "Site Outdoor Air Drybulb Temperature", "ENVIRONMENT")
    ep_api.exchange.request_variable(state, "Site Outdoor Air Humidity Ratio", "ENVIRONMENT")

    idfFilePath = 'RefBldgLargeOfficeNew2004_v1.4_7.2_5A_USA_IL_CHICAGO-OHARE_V2210.idf'
    weather_file_path = 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'
    output_path = f'./ep_trivial_output/{name}'
    sys_args = ['-d', output_path,'-w', weather_file_path, idfFilePath]
    ep_api.runtime.run_energyplus(state, sys_args)

def Call_EP():
    global eplastcalltime, eplastcalltime_over,call_thread,weatherInfo,\
        cond_pub, cond_sub, wasteHeat,ep_api,cond_mid, lock_pub,barrier,cond_waste,\
        sem0,sem1,sem2,nb_idf,barrierEng, shared_dict,cond_0,cond_1,cond_2,cond_3

    nb_idf = 2
    shared_dict = {}
    call_thread = {}
    vcwg_needed_time_idx_in_seconds = 0
    eplastcalltime = {}
    eplastcalltime_over = {}
    cond_mid = threading.Condition()
    cond_0 = threading.Condition()
    cond_1 = threading.Condition()
    cond_2 = threading.Condition()
    cond_3 = threading.Condition()
    weatherInfo = {}
    wasteHeat = {}
    barrier = Barrier(nb_idf)
    barrierEng = Barrier(nb_idf + 1)
    ep_api = EnergyPlusAPI()
    for i in range(nb_idf):
        _tmpEPName = f'EP-{i}'
        eplastcalltime[_tmpEPName] = 0
        eplastcalltime_over[_tmpEPName] = 0
        call_thread[_tmpEPName] = False
        wasteHeat[_tmpEPName] = -1
        _tmpDict = {}
        _tmpDict['time'] = 300
        _tmpDict['wasteHeat'] = -1
        _tmpDict['status'] = 'to_generate_weather'
        shared_dict[_tmpEPName] = _tmpDict
        thread_idf = threading.Thread(target=one_idf_run, name = _tmpEPName, args=(_tmpEPName,))
        thread_idf.start()

def run_vcwg():
    Call_EP()
    global shared_dict
    shared_dict['vcwg_time'] = 0
    shared_dict['weatherInfo'] = 25 + random.randint(1, 10)

if __name__ == '__main__':
    run_vcwg()
