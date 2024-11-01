import datetime, asyncio
from VRFSystemCommunicator import VRFSystemCommunicator as vrc
from VentilationSystemCommunicator import VentilationSystemCommunicator as vsc

import pandas as pd


class Ctrl():
    def _init_(self, vrCom, vsCom):
        self.vrCom = vrCom
        self.vsCom = vsCom


async def main():
    vrCom = vrc(12)
    vsCom = vsc(16)

    # Enable current_date_time method
    print('Subscribe COV...')
    await vrCom.subscribe_date_time_cov()
    
    # Number of indoor units in each VRF system
    i_unit_num = [5,4,5,4]

    last_dt = vrCom.current_date_time()
    while True:
        # Output current date and time
        dt = vrCom.current_date_time()

        # Change mode, air flow direction, and set point temperature depends on season
        is_s = 5 <= dt.month and dt.month <= 10
        mode = vrc.Mode.Cooling if is_s else vrc.Mode.Heating
        dir = vrc.Direction.Horizontal if is_s else vrc.Direction.Vertical
        sp = 26 if is_s else 22
    
        print(dt.strftime('%Y/%m/%d %H:%M:%S'))

        # When the HVAC changed to operating hours
        if(not(is_hvac_time(last_dt)) and is_hvac_time(dt)):
            for o_idx in range(1, len(i_unit_num)+1):
                for i_idx in range(1, i_unit_num[o_idx-1]+1):
                    await sample_ctrl(vrCom, vsCom, o_idx, i_idx, mode, dir, sp)

        # When the HVAC changed to stop hours
        if(is_hvac_time(last_dt) and not(is_hvac_time(dt))):
            for o_idx in range(1, len(i_unit_num)+1):
                for i_idx in range(1, i_unit_num[o_idx-1]+1):
                    v_name = 'VRF' + str(o_idx) + '-' + str(i_idx)

                    print('Turning off ' + v_name + '...',end='')
                    rslt = await vrCom.turn_off(o_idx, i_idx)
                    print('success' if rslt else 'failed')

                    print('Turning off ' + v_name + ' (Ventilation)...',end='')
                    rslt = await vsCom.stop_ventilation(o_idx, i_idx)
                    print('success' if rslt else 'failed')


        last_dt = dt # Save last date and time
        await asyncio.sleep(0.5)


def is_hvac_time(dtime):
    start_time = datetime.time(7, 0)
    end_time = datetime.time(19, 0)   
    now = dtime.time()
    is_business_hour = start_time <= now <= end_time
    is_weekday = (dtime.weekday() != 5 and dtime.weekday() != 6)
    return is_weekday and is_business_hour

def write_log():
    df_log = pd.DataFrame()
    

async def sample_ctrl(vrCom, vsCom, o_idx, i_idx, mode, dir, sp):
    v_name = 'VRF' + str(o_idx) + '-' + str(i_idx)
    print('Turning on ' + v_name + '...',end='')
    rslt = await vrCom.turn_on(o_idx, i_idx)
    print('success' if rslt[0] else 'failed: ' + rslt[1])

    print('Turning on ' + v_name + ' (Ventilation)...',end='')
    rslt = await vsCom.start_ventilation(o_idx, i_idx)
    print('success' if rslt[0] else 'failed: ' + rslt[1])

    print('Changing mode of ' + v_name + ' to ' + str(mode) + '...',end='')
    rslt = await vrCom.change_mode(o_idx, i_idx, mode)
    print('success' if rslt[0] else 'failed: ' + rslt[1])

    print('Changing set point temperature of ' + v_name + ' to ' + str(sp) + 'C...',end='')
    rslt = await vrCom.change_setpoint_temperature(o_idx, i_idx, sp)
    print('success' if rslt[0] else 'failed: ' + rslt[1])

    print('Changing fanspeed of ' + v_name + ' to Middle...',end='')
    rslt = await vrCom.change_fan_speed(o_idx, i_idx, vrc.FanSpeed.Middle)
    print('success' if rslt[0] else 'failed: ' + rslt[1])

    print('Changing air flow direction of ' + v_name + ' to ' + str(dir) + '...',end='')
    rslt = await vrCom.change_direction(o_idx, i_idx, dir)
    print('success' if rslt[0] else 'failed: ' + rslt[1])


def random_ctrl():
    pass

if __name__ == "__main__":
    asyncio.run(main())