from sciencemode import sciencemode
import time


ack = sciencemode.ffi.new("Smpt_ack*")
device = sciencemode.ffi.new("Smpt_device*")
extended_version_ack = sciencemode.ffi.new("Smpt_get_extended_version_ack*")

com = sciencemode.ffi.new("char[]", b"COM3")

ret = sciencemode.smpt_check_serial_port(com)
print(f"Port check is {ret}")

ret = sciencemode.smpt_open_serial_port(device,com)
print(f"smpt_open_serial_port: {ret}")

packet_number = sciencemode.smpt_packet_number_generator_next(device)
print(f"next packet_number {packet_number}")

ret = sciencemode.smpt_send_get_extended_version(device, packet_number)
print(f"smpt_send_get_extended_version: {ret}")

ret = False

while ( not sciencemode.smpt_new_packet_received(device)):
    time.sleep(1)

sciencemode.smpt_last_ack(device, ack);
print(f"command number {ack.command_number}, packet_number {ack.packet_number}")

ret = sciencemode.smpt_get_get_extended_version_ack(device, extended_version_ack)
print(f"smpt_get_get_extended_version_ack: {ret}")
print(f"fw_hash {extended_version_ack.fw_hash}")


ml_init = sciencemode.ffi.new("Smpt_ml_init*")
ml_init.packet_number = sciencemode.smpt_packet_number_generator_next(device)
ret = sciencemode.smpt_send_ml_init(device, ml_init)
print(f"smpt_send_ml_init: {ret}")
time.sleep(1)

ml_update = sciencemode.ffi.new("Smpt_ml_update*")
ml_update.packet_number = sciencemode.smpt_packet_number_generator_next(device)
channel = 0
ml_update.enable_channel[channel] = True
ml_update.channel_config[channel].period = 20
ml_update.channel_config[channel].number_of_points = 3
ml_update.channel_config[channel].points[0].time = 100
ml_update.channel_config[channel].points[0].current = 20
ml_update.channel_config[channel].points[1].time = 100
ml_update.channel_config[channel].points[1].current = 20
ml_update.channel_config[channel].points[2].time = 100
ml_update.channel_config[channel].points[2].current = -20

ret = sciencemode.smpt_send_ml_update(device, ml_update)
print(f"smpt_send_ml_update: {ret}", )

ml_get_current_data = sciencemode.ffi.new("Smpt_ml_get_current_data*")


for i in range(10):
    ml_get_current_data.data_selection = sciencemode.Smpt_Ml_Data_Channels
    ml_get_current_data.packet_number = sciencemode.smpt_packet_number_generator_next(device)
    ret = sciencemode.smpt_send_ml_get_current_data(device, ml_get_current_data)
    print(f"smpt_send_ml_get_current_data: {ret}")
    time.sleep(1)


packet_number = sciencemode.smpt_packet_number_generator_next(device)
ret = sciencemode.smpt_send_ml_stop(device, packet_number)
print(f"smpt_send_ml_stop: {ret}")


ret = sciencemode.smpt_close_serial_port(device)
print(f"smpt_close_serial_port: {ret}")
