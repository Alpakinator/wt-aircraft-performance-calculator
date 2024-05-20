import os
import math
import json
import subprocess 
from ram_pressure_density_calculator import rameffect_er
from plane_power_calculator import engine_shortcuter, torque_from_hp, rpm_er
from blkx_parsers import fm_parser, central_parser

"""Doesn't work!.
In this project thrust will always be in [kgf], torque in [kgf/m] power in [hp] speed in [km/h] and AoA in °
therefore there will be many (speed/3.6) or (power*0.745699872) in those functions. 
polars.exe or .cpp should be made based on 'polares.cpp' from Gaijin open source DagorEngine, 
not present in this repo so this doesn't work."""

fm_dir = "input_files/fm_files/"
central_dir = "input_files/central_files/"
power_read_dir = "output_files/plane_power_files/"
central_fm_read_dir = "output_files/plane_name_files/central-fm_plane_names_piston.json"
TEST_file_dir = "ingame_prop_efficiency_log_files/"

lift_n_drag_calculator = "polars.exe" #put a name of a script / exe that can calulate lift and drag of a propeller section.
# Get the full path to the executable
executable_path = os.path.join(os.path.dirname(__file__),'..', 'lift_drag_WT_source', 'prop_eff_calc', lift_n_drag_calculator)
fm_files = [
     "p-47d_22_re", #8.7 oswald efficiency, wut?
    #  "la-7"
    #  "bf-109g-14"
    #  "spitfire_mk1",
    # "spitfiremkiia",
    #  "g_55_serie1",
    # "mc-205_serie1",

]
modes = [
    # "100%", 
    'WEP'
    ]
plot_all_planes = False
air_temp = 15
speed_type = 'TAS'
# no point in using IAS speed, it causes confusion

#############################################################################################################

# def total_velocity_calculator(section_prop_radius, reduct_RPM, speed):
#     total_velocity = math.sqrt(((2 * 3.14159265359 * section_prop_radius * (reduct_RPM/60))**2) + (speed**2))
#     return total_velocity

def main():
    if plot_all_planes == True:
        with open(central_fm_read_dir, "r") as central_to_FM_json:
            planes_to_plot = json.load(central_to_FM_json)
    else:
        planes_to_plot = fm_files
    
    named_central_dict = central_parser(central_dir, planes_to_plot, central_fm_read_dir, ".blkx")
    named_fm_dict = fm_parser(fm_dir, planes_to_plot, central_fm_read_dir)
    for plane_name, central_dict in named_central_dict.items():
        fm_dict = named_fm_dict[plane_name]
        Engine, Compressor, Main, Afterburner, Propeller = engine_shortcuter(fm_dict)
        rpm_er(Main, Propeller)
        if "Reductor" in Propeller:
            reduction_ratio = Propeller["Reductor"]
        elif 'Transmission0' in fm_dict:
            reduction_ratio = fm_dict['Transmission0']["PropellerReductor0"]
        if not Afterburner:
            final_engine_modes = ["100%"]
        else:
            final_engine_modes = modes
        speed_propspeed_dict = {}

        if "AdvancedPropRadius" in Propeller:
            min_pitch = Propeller["PhiMin"]
            max_pitch = Propeller["PhiMax"]
            prop_radius = Propeller["AdvancedPropRadius"]
            blade_number = Propeller["NumBlades"]
        elif "Geometry" in fm_dict["PropellerType0"]:
            min_pitch = fm_dict["PropellerType0"]["Governor"]["PitchMin"]
            max_pitch = fm_dict["PropellerType0"]["Governor"]["PitchMax"]
            prop_radius = fm_dict["PropellerType0"]["Geometry"]["Radius"]
            blade_number = fm_dict["PropellerType0"]["Geometry"]["NumBlades"]
        for mode in final_engine_modes:
            if (Main["WEP_RPM"] - Main["military_RPM"]) < 5:
                rpm = Main["military_RPM"]
            elif mode == 'WEP':
                rpm = Main["WEP_RPM"]
            with open (power_read_dir + plane_name +'_'+mode+'.json', 'r') as power_json:
                power_dict = json.load(power_json)
                speed_multiplier = power_dict['speed_mult']
                reduct_RPM = rpm * reduction_ratio
                for alt in range (10, 31, 30):
                    alt_st = str(alt)
                    for speed in range (10, 500, 10):
                        speed_str = '[{}]'.format(speed)
                        alt_RAM = (rameffect_er(alt, air_temp, speed, speed_type, speed_multiplier))
                        try:
                            power_RAM = power_dict['power_at_alt'][int(round(((alt_RAM + 4000)/10),0))] 
                        except KeyError:
                            continue #If engine power is 0, the dictionary ends, so you can't apply RAM effect.
                        thrust_100propeff = ((power_RAM*745.7) / (speed/3.6))/9.80665
                        eng_torque = torque_from_hp(power_RAM, reduct_RPM)
                        # print(rpm, power_RAM, reduction_ratio, torque)
                        sectiondraglift = {}
                        for p_pitch in range (int(10*min_pitch), int(10*max_pitch), 1):
                            p_pitch = p_pitch/10
                            total_drag = 0
                            total_lift = 0
                            for prop_section in range (0,4):
                                
                                sect_hub_dist = [0.35, 0.55, 0.75, 0.95][prop_section] # or an average distance of a section: [0.175, 0.45, 0.65, 0.85][prop_section], or 
                                if "AdvancedPropRadius" in Propeller:
                                    section_twist = Propeller["PropPhi" + str(prop_section)] ########################################################################
                                elif "Geometry" in fm_dict["PropellerType0"]:
                                    section_twist = fm_dict["PropellerType0"]["Geometry"]["BladePitch" + str(prop_section)]  ########################################################################
                                
                                section_prop_radius = prop_radius * sect_hub_dist
                                # advance_ratio = (speed/3.6)/((reduct_RPM/60)*2*section_prop_radius)
                                #it's in hm/h!
                                sect_horiz_vel = 3.6*(2 * 3.14159265359 * section_prop_radius * (reduct_RPM/60))
                                prop_section_vel = round((math.sqrt(((sect_horiz_vel)**2) + ((speed)**2))), 2)
                                prop_section_vel_str = '[{}]'.format(prop_section_vel)
                                airflow_aoa = math.degrees(math.atan(speed /  (sect_horiz_vel)))  # or math.asin(speed /  prop_section_vel)
                                section_pitch = str(((p_pitch) + section_twist) - airflow_aoa)
                                # print(speed, section_pitch, airflow_aoa)
                                # arg order: path, blk, altitude, blade section num, vertical angle, aoa, speed list
                                # print(plane_name, alt_st, str(prop_section), '0', section_pitch, prop_section_vel_str)
                                # print(speed, section_pitch, airflow_aoa)
                                output = subprocess.check_output([executable_path, plane_name, alt_st, str(prop_section), '0', section_pitch, prop_section_vel_str])
                                
                                sec_lift, sec_drag = [float(num_str)/9.80665 for num_str in output.strip().split(b',')]

                                total_lift += (sec_lift) 
                                total_drag += (sec_drag)
                            total_torque = (math.cos(math.radians(airflow_aoa)) * total_drag) * blade_number
                            total_thrust = (math.cos(math.radians(airflow_aoa)) * total_lift) * blade_number
                            prop_eff = (total_thrust/thrust_100propeff)*100
                            # print(total_drag, total_torque, eng_torque)
                            print(
                                'prop_section: ',prop_section, ' | ',
                                'prop_pitch: ',p_pitch,' | ',
                                'speed: ',speed,' | ',
                                'sect_horiz_vel: ',sect_horiz_vel,' | ',
                                'prop_section_vel: ',prop_section_vel,' | ',
                                'section_twist: ',section_twist,' | ',
                                'airflow_aoa: ',airflow_aoa,' | ',
                                'section_pitch: ',section_pitch,' | ',
                                'sec_lift: ',sec_lift,' | ',
                                'sec_drag: ',sec_drag,' | ',
                                'total_lift', total_lift,' | ',
                                'total_drag', total_drag,' | ',
                                'total_thrust', total_thrust,' | ',
                                'prop_eff', prop_eff,' | ',
                                'total_torque', total_torque,' | ',
                                'eng_torque', eng_torque,' | ',
                                'thrust_100propeff', thrust_100propeff,' | ', 
                                '------------------------------------------------------------------------------------------------',
                                )


                            if total_torque < eng_torque or total_thrust < 0:
                                continue
                                # print("Total Drag:", total_drag, p_pitch)
                                # print("Total Lift:", total_lift)

                            else:

                                min_pitch = p_pitch
                                break
                            


def prop_porperties_checker():
    if plot_all_planes == True:
        with open(central_fm_read_dir, "r") as central_to_FM_json:
            planes_to_ass_ess = json.load(central_to_FM_json)
    else:
        planes_to_ass_ess = fm_files
    named_central_dict = central_parser(central_dir, planes_to_ass_ess, central_fm_read_dir, ".blkx")
    named_fm_dict = fm_parser(fm_dir, planes_to_ass_ess, central_fm_read_dir)
    for plane_name, central_dict in named_central_dict.items():
        fm_dict = named_fm_dict[plane_name]
        Engine, Compressor, Main, Afterburner, Propeller = engine_shortcuter(fm_dict)


if __name__ == "__main__":
        main()  