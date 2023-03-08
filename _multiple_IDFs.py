import datetime, sys, os, threading
import time, random
from multiprocessing import Barrier

sys.path.insert(0, '/usr/local/EnergyPlus-22-1-0/')
sys.path.insert(0, 'C:/EnergyPlusV22-1-0')
from pyenergyplus.api import EnergyPlusAPI

def run_vcwg():
    global vcwg_needed_time_idx_in_seconds
    vcwg_needed_time_idx_in_seconds = 0
    while True:
        if not sem0.acquire():
            print("VCWG: Timeout waiting for energy")
            return
        vcwg_needed_time_idx_in_seconds += 300

        barrier_0.wait()
        print(f'VCWG: vcwg_needed_time_idx_in_seconds: {vcwg_needed_time_idx_in_seconds}'
              f' eplastcalltime: {eplastcalltime}')
        barrier_1.wait()
        sem0.release()
def timeStepHandler(state):
    global eplastcalltime

    for _otherEPWarmed_vcwgCalled in call_thread.values():
        if not _otherEPWarmed_vcwgCalled:
            return

    barrier_0.wait()

    curr_sim_time_in_hours = ep_api.exchange.current_sim_time(state)
    curr_sim_time_in_seconds = curr_sim_time_in_hours * 3600  # Should always accumulate, since system time always advances
    threadName = threading.current_thread().name
    accumulated_time = curr_sim_time_in_seconds - eplastcalltime[threadName]

    time_index_alignment_bool = 1 > abs(accumulated_time - 300)
    if not time_index_alignment_bool:
        print(f'Thread: {threading.current_thread().name},'
              f'accumulated_time: {accumulated_time}, '
              f'eplastcalltime: {eplastcalltime}, '
              f'vcwg_needed_time_idx_in_seconds: {vcwg_needed_time_idx_in_seconds}')
        return
    eplastcalltime[threadName] = curr_sim_time_in_seconds



    barrier_1.wait()
def overwrite_ep_weather(state):
    global call_thread
    warm_up = ep_api.exchange.warmup_flag(state)
    if not warm_up:
        _threadName = threading.current_thread().name
        call_thread[_threadName] = True
        if not call_thread['vcwg']:
            threading.Thread(target=run_vcwg).start()
            call_thread['vcwg'] = True
def one_idf_run(name):
    global eplastcalltime,ep_api, call_thread, weatherInfo
    threadName = threading.current_thread().name
    eplastcalltime[threadName] = 0
    call_thread[threadName] = False
    weatherInfo[threadName] = 0

    ep_api = EnergyPlusAPI()
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
    global barrier_0, barrier_1, sem0, \
        vcwg_needed_time_idx_in_seconds, eplastcalltime, call_thread,weatherInfo
    weatherInfo = {}
    nb_idf = 2
    call_thread = {}
    call_thread['vcwg'] = False
    vcwg_needed_time_idx_in_seconds = 0
    eplastcalltime = {}
    sem0 = threading.Semaphore(1)
    cond = threading.Condition()
    barrier_0 = Barrier(nb_idf + 1)
    barrier_1 = Barrier(nb_idf + 1)
    for i in range(nb_idf):
        thread_idf = threading.Thread(target=one_idf_run, args=(i,))
        thread_idf.start()

if __name__ == '__main__':
    Call_EP()