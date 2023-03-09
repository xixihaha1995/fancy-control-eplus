import datetime, sys, os, threading
import time, random
from multiprocessing import Barrier

sys.path.insert(0, '/usr/local/EnergyPlus-22-1-0/')
sys.path.insert(0, 'C:/EnergyPlusV22-1-0')
from pyenergyplus.api import EnergyPlusAPI

def time_align_check(eplastdict, vcwg_needed_time_idx_in_seconds):
    for key, value in eplastdict.items():
        if abs(value - vcwg_needed_time_idx_in_seconds) > 2:
            return False
    return True

def timeStepHandler(state):
    global eplastcalltime,wasteHeat
    threadName = threading.current_thread().name
    if not call_thread[threadName]:
        return
    curr_sim_time_in_hours = ep_api.exchange.current_sim_time(state)
    curr_sim_time_in_seconds = curr_sim_time_in_hours * 3600
    _round = round(curr_sim_time_in_seconds)
    accumulated_time = curr_sim_time_in_seconds - eplastcalltime[threadName]
    _converge = 2 > abs(accumulated_time - 300)
    if not _converge:
        return
    eplastcalltime[threadName] = curr_sim_time_in_seconds
    wasteHeat[threadName] = 300 + random.randint(1, 10)
    semDict[(int(threadName) + 2) % len(semDict)].release()
def overwrite_ep_weather(state):
    global call_thread
    warm_up = ep_api.exchange.warmup_flag(state)
    if not warm_up:
        _threadName = threading.current_thread().name
        call_thread[_threadName] = True
        semDict[(int(_threadName) + 1) % len(semDict)].acquire()


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
    global vcwg_needed_time_idx_in_seconds, eplastcalltime, call_thread,weatherInfo,\
        cond_pub, cond_sub, wasteHeat,ep_api,cond_mid, lock_pub,barrier,cond_waste,\
        sem0,sem1,sem2,nb_idf,barrierEng, semDict

    weatherInfo = {}
    wasteHeat = {}
    nb_idf = 3
    semDict = [0 for i in range(nb_idf + 2)]
    for i in range(nb_idf +2):
        semDict[i] = threading.Semaphore(0)
    semDict[0] = threading.Semaphore(1)

    call_thread = {}
    call_thread['vcwg'] = False
    vcwg_needed_time_idx_in_seconds = 0
    eplastcalltime = {}
    cond_pub = threading.Condition()
    cond_waste = threading.Condition()
    lock_pub = threading.Lock()
    cond_sub = threading.Condition()
    cond_mid = threading.Condition()
    sem0 = threading.Semaphore(1)
    sem1 = threading.Semaphore(0)
    sem2 = threading.Semaphore(0)
    barrier = Barrier(nb_idf)
    barrierEng = Barrier(nb_idf + 1)
    ep_api = EnergyPlusAPI()
    for i in range(nb_idf):
        _tmpEPName = f'{i}'
        eplastcalltime[_tmpEPName] = 0
        call_thread[_tmpEPName] = False
        wasteHeat[_tmpEPName] = -1
        thread_idf = threading.Thread(target=one_idf_run, name = _tmpEPName, args=(_tmpEPName,))
        thread_idf.start()
def run_vcwg():
    Call_EP()
    global vcwg_needed_time_idx_in_seconds, weatherInfo,wasteHeat
    vcwg_needed_time_idx_in_seconds = 300
    while True:
        semDict[0].acquire()
        print(f'vcwg download wasteHeat: {wasteHeat}')
        wasteHeat = {k: -1 for k in wasteHeat}
        semDict[1].release()
        
        semDict[-1].acquire()
        vcwg_needed_time_idx_in_seconds += 300
        print(f'vcwg upload time: {vcwg_needed_time_idx_in_seconds}')
        semDict[0].release()

if __name__ == '__main__':
    run_vcwg()
