#!/usr/local/bin/python

import sys
import nest
import time

from configobj import ConfigObj
from influxdb import InfluxDBClient
from nest import utils as nu

config = ConfigObj(sys.path[0] + '/config.ini')
USER = config['nest']['user']
PASS = config['nest']['pass']
IFLX_HOST = config['influx']['host']
IFLX_USER = config['influx']['user']
IFLX_PASS = config['influx']['pass']
IFLX_DB = config['influx']['database']

# Metrics to loop
thermo_metrics = ['mode',
                  'battery_level',
               'fan',
               'humidity',
               'hvac_ac_state',
               'hvac_cool_x2_state',
               'hvac_heater_state',
               'hvac_aux_heater_state',
               'hvac_heat_x2_state',
               'hvac_heat_x3_state',
               'hvac_alt_heat_state',
               'hvac_alt_heat_x2_state',
               'hvac_emer_heat_state',
               'last_connection',
               'local_ip']

protect_metrics = ['smoke_status',
                   'battery_health_state',
            'battery_health_state',
            'co_status',
            'software_version']
			
structure_metrics = ['away',
                     'num_thermostats']

metrics_convert = ['temperature',
                   'target']

def send_to_influx(metrics, host=IFLX_HOST, port=8086, user=IFLX_USER,
                   pwd=IFLX_PASS, db=IFLX_DB):
    client = InfluxDBClient(host, port, user, pwd, db)
    client.write_points(metrics)


def gather_nest(u=USER, p=PASS):
    napi = nest.Nest(u, p, local_time=True)
    data = []
    # Jason loves mad precision, yo. Lets turn that shiz down a notch.
    nu.decimal.getcontext().prec = 4
    for structure in napi.structures:
        struct_name = structure.name
        
        t = nu.c_to_f(structure.weather.current.temperature)
        
        for s in structure_metrics:
            data.append({'measurement': s,
                         'tags': {'structure': struct_name},
                         'fields': {'value': getattr(structure, s)}})
		
        for device in structure.devices:
            for m in thermo_metrics:
                data.append({'measurement': m,
                             'tags': {'structure': struct_name,
                                      'device': device.name},
                             'fields': {'value': getattr(device, m)}})
							 
            for m in metrics_convert:
                data.append({'measurement': m,
                             'tags': {'structure': struct_name,
                                      'device': device.name},
                             'fields': {'value':
                                        nu.c_to_f(getattr(device, m))}})

        for protect in structure.protectdevices:
            for m in protect_metrics:
                data.append({'measurement': m,
                            'tags': {'structure': struct_name,
                                    'device': protect.name},
                            'fields': {'value': getattr(protect, m)}})

        t = nu.c_to_f(structure.weather.current.temperature)
        data.append({'measurement': 'temperature',
                     'tags': {'structure': struct_name,
                              'device': 'Outside'},
                     'fields': {'value':  t}})

        data.append({'measurement': 'humidity',
                     'tags': {'structure': struct_name,
                              'device': 'Outside'},
                     'fields': {'value': structure.weather.current.humidity}})

    return data
    
def pullFromNestPushToInfluxdb():
    data = gather_nest()
    send_to_influx(data)

if __name__ == '__main__':
    while True:
        pullFromNestPushToInfluxdb()
        time.sleep(300)