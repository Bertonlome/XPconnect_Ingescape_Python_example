#!/usr/bin/env python3
# coding: utf-8
# =========================================================================
# main.py
#
# Copyright (c) the Contributors as noted in the AUTHORS file.
# This file is part of Ingescape, see https://github.com/zeromq/ingescape.
# 
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =========================================================================
#

import signal
import getopt
import time
import xpc
from pathlib import Path

from echo import *

port = 5670
agent_name = "Aircraft agent"
device = "wlo1"
verbose = False
is_interrupted = False

short_flag = "hvip:d:n:"
long_flag = ["help", "verbose", "interactive_loop", "port=", "device=", "name="]

ingescape_path = Path("~/Documents/IngeScape").expanduser()

def print_usage():
    print("Usage example: ", agent_name, " --verbose --port 5670 --device device_name")
    print("\nthese parameters have default value (indicated here above):")
    print("--verbose : enable verbose mode in the application (default is disabled)")
    print("--port port_number : port used for autodiscovery between agents (default: 31520)")
    print("--device device_name : name of the network device to be used (useful if several devices available)")
    print("--name agent_name : published name for this agent (default: ", agent_name, ")")
    print("--interactive_loop : enables interactive loop to pass commands in CLI (default: false)")

def print_usage_help():
    print("Available commands in the terminal:")
    print("	/quit : quits the agent")
    print("	/help : displays this message")

def return_io_value_type_as_str(value_type):
    if value_type == igs.INTEGER_T:
        return "Airspeed"
    elif value_type == igs.DOUBLE_T:
        return "Double"
    elif value_type == igs.BOOL_T:
        return "Bool"
    elif value_type == igs.STRING_T:
        return "String"
    elif value_type == igs.IMPULSION_T:
        return "Impulsion"
    elif value_type == igs.DATA_T:
        return "Data"
    else:
        return "Unknown"

def return_event_type_as_str(event_type):
    if event_type == igs.PEER_ENTERED:
        return "PEER_ENTERED"
    elif event_type == igs.PEER_EXITED:
        return "PEER_EXITED"
    elif event_type == igs.AGENT_ENTERED:
        return "AGENT_ENTERED"
    elif event_type == igs.AGENT_UPDATED_DEFINITION:
        return "AGENT_UPDATED_DEFINITION"
    elif event_type == igs.AGENT_KNOWS_US:
        return "AGENT_KNOWS_US"
    elif event_type == igs.AGENT_EXITED:
        return "AGENT_EXITED"
    elif event_type == igs.AGENT_UPDATED_MAPPING:
        return "AGENT_UPDATED_MAPPING"
    elif event_type == igs.AGENT_WON_ELECTION:
        return "AGENT_WON_ELECTION"
    elif event_type == igs.AGENT_LOST_ELECTION:
        return "AGENT_LOST_ELECTION"
    else:
        return "UNKNOWN"

def signal_handler(signal_received, frame):
    global is_interrupted
    print("\n", signal.strsignal(signal_received), sep="")
    is_interrupted = True


def on_agent_event_callback(event, uuid, name, event_data, my_data):
    agent_object = my_data
    assert isinstance(agent_object, Echo)
    # add code here if needed


def on_freeze_callback(is_frozen, my_data):
    agent_object = my_data
    assert isinstance(agent_object, Echo)
    # add code here if needed


# inputs
def impulsion_input_callback(io_type, name, value_type, value, my_data):
    igs.info(f"Input {name} written")
    stow_gear()

def bool_input_callback(io_type, name, value_type, value, my_data):
    igs.info(f"Input {name} written to {value}")
    agent_object = my_data
    assert isinstance(agent_object, Echo)
    agent_object.boolI = value
    agent_object.boolO = value

def integer_input_callback(io_type, name, value_type, value, my_data):
    igs.info(f"Input {name} written to {value}")
    agent_object = my_data
    assert isinstance(agent_object, Echo)
    agent_object.integerI = value
    agent_object.integerO = value

def double_input_callback(io_type, name, value_type, value, my_data):
    igs.info(f"Input {name} written to {value}")
    agent_object = my_data
    assert isinstance(agent_object, Echo)
    agent_object.doubleI = value
    agent_object.doubleO = value

def string_input_callback(io_type, name, value_type, value, my_data):
    igs.info(f"Input {name} written to {value}")
    agent_object = my_data
    assert isinstance(agent_object, Echo)
    agent_object.stringI = value
    set_flaps(value)

def data_input_callback(io_type, name, value_type, value, my_data):
    igs.info(f"Input {name} written to {value}")
    agent_object = my_data
    assert isinstance(agent_object, Echo)
    agent_object.dataI = value
    agent_object.dataO = value

# services
def receive_values_callback(sender_agent_name, sender_agent_uuid, service_name, tuple_args, token, my_data):
    agent_object = my_data
    assert isinstance(agent_object, Echo)
    boolV = tuple_args[0]
    integer = tuple_args[1]
    double = tuple_args[2]
    string = tuple_args[3]
    data = tuple_args[4]
    agent_object.receive_values(sender_agent_name, sender_agent_uuid, boolV, integer, double, string, data, token, my_data)


def send_values_callback(sender_agent_name, sender_agent_uuid, service_name, tuple_args, token, my_data):
    agent_object = my_data
    assert isinstance(agent_object, Echo)
    agent_object.send_values(sender_agent_name, sender_agent_uuid, token, my_data)

def get_dref(arg):
    with xpc.XPlaneConnect() as client:
        #get a dref
        dref = arg
        myValue = client.getDREF(dref)
        rounded_value = round(myValue[0], 1)
        myValueText = f"{rounded_value:.1f}"  # Format with 1 decimal place
        return myValueText
    
def stow_gear():
    with xpc.XPlaneConnect() as client:
        # Stow landing gear using a dataref
        print("Landing Gear Toggle")
        gear_dref = "sim/cockpit/switches/gear_handle_status"
        current_value = get_dref(gear_dref)
        if int(float(current_value)) == 0:
            client.sendDREF(gear_dref, 1)
        else:
            client.sendDREF(gear_dref, 0)

def set_flaps(setting):
    with xpc.XPlaneConnect() as client:
        # Stow landing gear using a dataref
        print("Setting flaps : " + setting)
        flap_dref = "sim/cockpit2/controls/flap_ratio"
        if setting == "UP":
            value = 0
        elif setting == "T/O":
            value = 0.5
        else:
            value = 1
            
        client.sendDREF(flap_dref, value)



if __name__ == "__main__":

    # catch SIGINT handler before starting agent
    signal.signal(signal.SIGINT, signal_handler)
    interactive_loop = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], short_flag, long_flag)
    except getopt.GetoptError as err:
        igs.error(err)
        sys.exit(2)
    for o, a in opts:
        if o == "-h" or o == "--help":
            print_usage()
            exit(0)
        elif o == "-v" or o == "--verbose":
            verbose = True
        elif o == "-i" or o == "--interactive_loop":
            interactive_loop = True
        elif o == "-p" or o == "--port":
            port = int(a)
        elif o == "-d" or o == "--device":
            device = a
        elif o == "-n" or o == "--name":
            agent_name = a
        else:
            assert False, "unhandled option"

    igs.agent_set_name(agent_name)
    igs.definition_set_version("1.0")
    igs.log_set_console(verbose)
    igs.log_set_file(True, None)
    igs.log_set_stream(verbose)
    igs.set_command_line(sys.executable + " " + " ".join(sys.argv))

    if device is None:
        # we have no device to start with: try to find one
        list_devices = igs.net_devices_list()
        list_addresses = igs.net_addresses_list()
        if len(list_devices) == 1:
            device = list_devices[0].decode('utf-8')
            igs.info("using %s as default network device (this is the only one available)" % str(device))
        elif len(list_devices) == 2 and (list_addresses[0] == "127.0.0.1" or list_addresses[1] == "127.0.0.1"):
            if list_addresses[0] == "127.0.0.1":
                device = list_devices[1].decode('utf-8')
            else:
                device = list_devices[0].decode('utf-8')
            print("using %s as de fault network device (this is the only one available that is not the loopback)" % str(device))
        else:
            if len(list_devices) == 0:
                igs.error("No network device found: aborting.")
            else:
                igs.error("No network device passed as command line parameter and several are available.")
                print("Please use one of these network devices:")
                for device in list_devices:
                    print("	", device)
                print_usage()
            exit(1)

    agent = Echo()

    igs.observe_agent_events(on_agent_event_callback, agent)
    igs.observe_freeze(on_freeze_callback, agent)

    igs.input_create("Landing_Gear_Toggle", igs.IMPULSION_T, None)
    igs.input_create("Flaps_setting", igs.STRING_T, None)

    igs.output_create("Airspeed", igs.INTEGER_T, None)
    igs.output_create("Altitude", igs.INTEGER_T, None)
    igs.output_create("Vertical_Speed", igs.INTEGER_T, None)
    igs.output_create("Heading", igs.INTEGER_T, None)
    igs.output_create("Left_Engine_N1%", igs.INTEGER_T, None)
    igs.output_create("Right_Engine_N1%", igs.INTEGER_T, None)
    igs.output_create("Flaps_setting", igs.STRING_T, None)
    igs.output_create("Landing_Gear_Extended", igs.BOOL_T, None)

    igs.observe_input("Landing_Gear_Toggle", impulsion_input_callback, agent)
    igs.observe_input("Flaps_setting", string_input_callback, agent)

    igs.service_init("receive_values", receive_values_callback, agent)
    igs.service_arg_add("receive_values", "bool", igs.BOOL_T)
    igs.service_arg_add("receive_values", "Airspeed", igs.INTEGER_T)
    igs.service_arg_add("receive_values", "double", igs.DOUBLE_T)
    igs.service_arg_add("receive_values", "string", igs.STRING_T)
    igs.service_arg_add("receive_values", "data", igs.DATA_T)
    igs.service_init("send_values", send_values_callback, agent)

    igs.log_set_console(True)
    igs.log_set_console_level(igs.LOG_INFO)

    igs.start_with_device(device, port)
    # catch SIGINT handler after starting agent
    signal.signal(signal.SIGINT, signal_handler)

    if interactive_loop:
        print_usage_help()
        while True:
            command = input()
            if command == "/quit":
                break
            elif command == "/help":
                print_usage_help()
    else:
        while (not is_interrupted) and igs.is_started():
            #My main loop
            newValue = get_dref("sim/cockpit2/gauges/indicators/airspeed_kts_pilot")
            igs.output_set_int("Airspeed", int(float(newValue)))
            newValue = get_dref("sim/cockpit2/gauges/indicators/altitude_ft_copilot")
            igs.output_set_int("Altitude", int(float(newValue)))
            newValue = get_dref("sim/cockpit2/gauges/indicators/vvi_fpm_pilot")
            igs.output_set_int("Vertical_Speed", int(float(newValue)))
            newValue = get_dref("sim/cockpit2/gauges/indicators/compass_heading_deg_mag")
            igs.output_set_int("Heading", int(float(newValue)))
            newValue = get_dref("sim/cockpit2/engine/indicators/engine_speed_rpm")
            igs.output_set_int("Left_Engine_N1%", int(float(newValue)))
            igs.output_set_int("Right_Engine_N1%", int(float(newValue)))
            newValue = get_dref("sim/flightmodel/controls/flaprqst")
            if float(newValue) == 0:
                igs.output_set_string("Flaps_setting", "UP")
            elif float(newValue) == 0.5:
                igs.output_set_string("Flaps_setting", "TO/APR")
            else:
                igs.output_set_string("Flaps_setting", "LAND")
            newValue = get_dref("Mustang/gear_lever")
            if float(newValue) == 1:
                igs.output_set_bool("Landing_Gear_Extended", True)
            else:
                igs.output_set_bool("Landing_Gear_Extended", False)

            time.sleep(0.1)

    if igs.is_started():
        igs.stop()