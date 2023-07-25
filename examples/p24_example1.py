from sciencemode import sciencemode
import time


ack = sciencemode.ffi.new("Smpt_ack*")
device = sciencemode.ffi.new("Smpt_device*")
extended_version_ack = sciencemode.ffi.new("Smpt_get_extended_version_ack*")

com = sciencemode.ffi.new("char[]", b"COM3")

ret = sciencemode.smpt_check_serial_port(com)
print("Port check is {}", ret)

ret = sciencemode.smpt_open_serial_port(device,com)
print("smpt_open_serial_port: {}", ret)

packet_number = sciencemode.smpt_packet_number_generator_next(device)
print("next packet_number {}", packet_number)

ret = sciencemode.smpt_send_get_extended_version(device, packet_number)
print("smpt_send_get_extended_version: {}", ret)

ret = False

while ( not sciencemode.smpt_new_packet_received(device)):
    time.sleep(1)

sciencemode.smpt_last_ack(device, ack);
print("command number {}, packet_number {}", ack.command_number, ack.packet_number)

ret = sciencemode.smpt_get_get_extended_version_ack(device, extended_version_ack)
print("smpt_get_get_extended_version_ack: {}", ret)
print("fw_hash {} ",extended_version_ack.fw_hash)


ll_init = sciencemode.ffi.new("Smpt_ll_init*")
ll_init.high_voltage_level = sciencemode.Smpt_High_Voltage_Default
ll_init.packet_number = sciencemode.smpt_packet_number_generator_next(device)
ret = sciencemode.smpt_send_ll_init(device, ll_init)
print("smpt_send_ll_init: {}", ret)
time.sleep(1)

packet_number = sciencemode.smpt_packet_number_generator_next(device)
print("next packet_number {}", packet_number)


ll_config = sciencemode.ffi.new("Smpt_ll_channel_config*")

ll_config.enable_stimulation = True
ll_config.channel = sciencemode.Smpt_Channel_Red
ll_config.connector = sciencemode.Smpt_Connector_Yellow
ll_config.number_of_points = 3
ll_config.points[0].time = 100
ll_config.points[0].current = 20
ll_config.points[1].time = 100
ll_config.points[1].current = 20
ll_config.points[2].time = 100
ll_config.points[2].current = -20


for i in range(3):
    ll_config.packet_number = sciencemode.smpt_packet_number_generator_next(device)
    ret = sciencemode.smpt_send_ll_channel_config(device, ll_config)
    print("smpt_send_ll_channel_config: {}", ret)
    time.sleep(1)

packet_number = sciencemode.smpt_packet_number_generator_next(device)
ret = sciencemode.smpt_send_ll_stop(device, packet_number)
print("smpt_send_ll_stop: {}", ret)

ml_init = sciencemode.ffi.new("Smpt_ml_init*")
ml_init.packet_number = sciencemode.smpt_packet_number_generator_next(device)
ret = sciencemode.smpt_send_ml_init(device, ml_init)
print("smpt_send_ml_init: {}", ret)
time.sleep(1)

ml_update = sciencemode.ffi.new("Smpt_ml_update*")
ml_update.packet_number = sciencemode.smpt_packet_number_generator_next(device)
for i in range(8):
    ml_update.enable_channel[i] = True
    ml_update.channel_config[i].period = 20
    ml_update.channel_config[i].number_of_points = 3
    ml_update.channel_config[i].points[0].time = 100
    ml_update.channel_config[i].points[0].current = 20
    ml_update.channel_config[i].points[1].time = 100
    ml_update.channel_config[i].points[1].current = 20
    ml_update.channel_config[i].points[2].time = 100
    ml_update.channel_config[i].points[2].current = -20
    
ret = sciencemode.smpt_send_ml_update(device, ml_update)
print("smpt_send_ml_update: {}", ret)

ml_get_current_data = sciencemode.ffi.new("Smpt_ml_get_current_data*")


for i in range(10):
    ml_get_current_data.data_selection = sciencemode.Smpt_Ml_Data_Channels
    ml_get_current_data.packet_number = sciencemode.smpt_packet_number_generator_next(device)
    ret = sciencemode.smpt_send_ml_get_current_data(device, ml_get_current_data)
    print("smpt_send_ml_get_current_data: {}", ret)
    time.sleep(1)


packet_number = sciencemode.smpt_packet_number_generator_next(device)
ret = sciencemode.smpt_send_ml_stop(device, packet_number)
print("smpt_send_ml_stop: {}", ret)


ret = sciencemode.smpt_close_serial_port(device)
print("smpt_close_serial_port: {}", ret)