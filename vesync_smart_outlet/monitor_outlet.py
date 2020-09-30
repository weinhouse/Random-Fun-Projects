#!/usr/bin/env python3

from pyvesync_v2 import VeSync
import os
import mailer
import time
import datetime

power_threshold = 30 # in Watts
sleeptime_seconds = 600
vsync_email = 'larry@weinhouse.com'
vesync_password = os.environ['vesyncPassword'] # added as -e option on docker start.
sg_password = os.environ['sendgridKey'] # added as -e option on docker start.
logfile = 'rad_wagon_battery.log'

manager = VeSync(vsync_email, vesync_password, time_zone='US/Pacific')
manager.login()
manager.update()
manager.energy_update_interval = 60
my_switch = manager.outlets[0]

mail_from_larry = mailer.Sendgrid(sg_password, 'Larry Weinhouse', 'larry@weinhouse.com')


def poll_outlet(my_switch):
    try:
        manager.update_energy()
        my_switch.update()
        volts = my_switch.voltage
        power = my_switch.power
        name = my_switch.device_name
        t = datetime.datetime.now()
        logentry = '{}: {}, power-V:{} power-W:{}'.format(t, name, volts, power)
        with open(logfile, "a") as f:
            f.write('{}\n'.format(logentry))
            f.close()
        return power
    except Exception as e:
        mail_from_larry.a_message("error polling rad battery outlet", str(e),
            ["weinhouse@gmail.com"])
        exit(1)

with open(logfile, "w") as f:
    f.write('{}\n'.format(str(datetime.datetime.now())))
    f.close()
power = poll_outlet(my_switch)

if power > power_threshold:
        begin_time = time.time()
while power > power_threshold:
    time.sleep(sleeptime_seconds)
    power = poll_outlet(my_switch)
    if power <= power_threshold:
        try:
            my_switch.turn_off()
        except Exception as e:
            mail_from_larry.a_message("error turning off rad battery outlet",
                str(e), ["weinhouse@gmail.com"])
            exit(1)
        endtime = round((time.time() - begin_time)/60, 2)
        with open(logfile, "r") as f:
            log = f.read()
        subjectline = 'rad battery charged in {} minutes'.format(endtime)
        mail_from_larry.a_message(subjectline, log, ["weinhouse@gmail.com"])
        exit(0)
