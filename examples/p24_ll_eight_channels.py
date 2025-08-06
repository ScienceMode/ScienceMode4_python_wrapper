from sciencemode import sciencemode
import time


ack = sciencemode.ffi.new("Smpt_ack*")
device = sciencemode.ffi.new("Smpt_device*")
extended_version_ack = sciencemode.ffi.new("Smpt_get_extended_version_ack*")

com = sciencemode.ffi.new("char[]", b"COM3")

ret = sciencemode.smpt_check_serial_port(com)
print(f"Port check is {ret}")

ret = sciencemode.smpt_open_serial_port(device,com)
print(f"smpt_open_serial_port: {ret}", )

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
print(f"fw_hash {extended_version_ack.fw_hash} ")


ll_init = sciencemode.ffi.new("Smpt_ll_init*")
ll_init.high_voltage_level = sciencemode.Smpt_High_Voltage_Default
ll_init.packet_number = sciencemode.smpt_packet_number_generator_next(device)
ret = sciencemode.smpt_send_ll_init(device, ll_init)
print(f"smpt_send_ll_init: {ret}")
time.sleep(1)

packet_number = sciencemode.smpt_packet_number_generator_next(device)
print(f"next packet_number {packet_number}")


ll_config = sciencemode.ffi.new("Smpt_ll_channel_config*")

ll_config.enable_stimulation = True
ll_config.number_of_points = 3
ll_config.points[0].time = 100
ll_config.points[0].current = 20
ll_config.points[1].time = 100
ll_config.points[1].current = 20
ll_config.points[2].time = 100
ll_config.points[2].current = -20


for i in range(30):
    ll_config.packet_number = sciencemode.smpt_packet_number_generator_next(device)
    ll_config.channel = sciencemode.Smpt_Channel_Red
    ll_config.connector = sciencemode.Smpt_Connector_Yellow
    ret = sciencemode.smpt_send_ll_channel_config(device, ll_config)
    print(f"1. channel smpt_send_ll_channel_config: {ret}")
    ll_config.packet_number = sciencemode.smpt_packet_number_generator_next(device)
    ll_config.channel = sciencemode.Smpt_Channel_Blue
    ll_config.connector = sciencemode.Smpt_Connector_Yellow
    ret = sciencemode.smpt_send_ll_channel_config(device, ll_config)
    print(f"2. channel smpt_send_ll_channel_config: {ret}")
    ll_config.packet_number = sciencemode.smpt_packet_number_generator_next(device)
    ll_config.channel = sciencemode.Smpt_Channel_Black
    ll_config.connector = sciencemode.Smpt_Connector_Yellow
    ret = sciencemode.smpt_send_ll_channel_config(device, ll_config)
    print(f"3. channel smpt_send_ll_channel_config: {ret}")
    ll_config.packet_number = sciencemode.smpt_packet_number_generator_next(device)
    ll_config.channel = sciencemode.Smpt_Channel_White
    ll_config.connector = sciencemode.Smpt_Connector_Yellow
    ret = sciencemode.smpt_send_ll_channel_config(device, ll_config)
    print(f"4. channel smpt_send_ll_channel_config: {ret}")
    ll_config.packet_number = sciencemode.smpt_packet_number_generator_next(device)
    ll_config.channel = sciencemode.Smpt_Channel_Red
    ll_config.connector = sciencemode.Smpt_Connector_Green
    ret = sciencemode.smpt_send_ll_channel_config(device, ll_config)
    print(f"5. channel smpt_send_ll_channel_config: {ret}")
    ll_config.packet_number = sciencemode.smpt_packet_number_generator_next(device)
    ll_config.channel = sciencemode.Smpt_Channel_Blue
    ll_config.connector = sciencemode.Smpt_Connector_Green
    ret = sciencemode.smpt_send_ll_channel_config(device, ll_config)
    print(f"6. channel smpt_send_ll_channel_config: {ret}")
    ll_config.packet_number = sciencemode.smpt_packet_number_generator_next(device)
    ll_config.channel = sciencemode.Smpt_Channel_Black
    ll_config.connector = sciencemode.Smpt_Connector_Green
    ret = sciencemode.smpt_send_ll_channel_config(device, ll_config)
    print(f"7. channel smpt_send_ll_channel_config: {ret}")
    ll_config.packet_number = sciencemode.smpt_packet_number_generator_next(device)
    ll_config.channel = sciencemode.Smpt_Channel_White
    ll_config.connector = sciencemode.Smpt_Connector_Green
    ret = sciencemode.smpt_send_ll_channel_config(device, ll_config)
    print(f"8. channel smpt_send_ll_channel_config: {ret}")
    time.sleep(0.1)

packet_number = sciencemode.smpt_packet_number_generator_next(device)
ret = sciencemode.smpt_send_ll_stop(device, packet_number)
print(f"smpt_send_ll_stop: {ret}")

ret = sciencemode.smpt_close_serial_port(device)
print(f"smpt_close_serial_port: {ret}")
