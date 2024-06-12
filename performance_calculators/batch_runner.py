import os
import json
import shutil
from blkx_parsers import fm_parser, central_parser
from datamine_fetcher import datamine_folder_fetcher, datamine_file_fetcher, airplane_img_downloader
from plane_names_inator import fm_lister, central_fm_jsoner, ingame_central_names_lister, dict_to_objectarray_converter, vehicle_image_name_jsoner
from plane_mass_calculator import gun_ammocount_assembler, ammo_mass_calculator, plane_total_mass_calculator, plane_masses_to_json
from plane_power_calculator import enginecounter, power_curve_culator, engine_power_to_json

"""
Script for dowloading up-to-date datamine files and generating 
'engine power', 'plane names' and 'plane mass' .json files.
Comment in and out sections you want or dont want to run. 
Downloading datamine takes an hours so be careful with the lines for removing files.
"""
def main():
    fm_dir = "input_files/fm_files/"
    central_dir = "input_files/central_files/"
    gun_dir = "input_files/weapon_files/"
    name_read_dir = "input_files/vehicle_name_files/"
    image_write_dir = "input_files/plane_images/"
    
    central_fm_read_dir = "output_files/plane_name_files/central-fm_plane_names_piston.json"
    name_write_dir = "output_files/plane_name_files/"
    mass_write_dir = "output_files/plane_mass_files/"
    power_write_dir = "output_files/plane_power_files/"
    image_names_dir = "output_files/plane_name_files/vehicle_image_names.json"

    # Section for downloading datamine Starts
    # answer0 = input("Welcome at the batch runner. First of, make sure your working directory ends with '..../wt-aircraft-performance-calculator'(click anything).")
    answer1 = input("Do you want to delete datamine files from 'input files/' directory? \nThey take ~30min to download in the next step. \n(yes/no) ")
    if answer1 == 'yes':
        if os.path.exists(central_dir):
            shutil.rmtree(central_dir)
        if os.path.exists(fm_dir):
            shutil.rmtree(fm_dir)
        if os.path.exists(gun_dir):
            shutil.rmtree(gun_dir)
        if os.path.exists(image_write_dir):
            shutil.rmtree(image_write_dir)

    # answer3 = input("Do you want to delete the current files in the 'output_files/' directory? \n(yes/no) ")
    # if answer3 == 'yes':
    #     shutil.rmtree("output_files/")  

        
    answer2 = input("Do you want to download newest datamine files into 'input files/' directory? \n(yes/no) ")
    if answer2 == 'yes':
        print('Started fetching datamine files! Might take an hour!')
        datamine_folder_fetcher("input_files/fm_files", "aces.vromfs.bin_u/gamedata/flightmodels/fm/", "")
        datamine_folder_fetcher("input_files/central_files", "aces.vromfs.bin_u/gamedata/flightmodels/", "")
        datamine_folder_fetcher("input_files/weapon_files", "aces.vromfs.bin_u/gamedata/weapons/", "")
        datamine_file_fetcher("input_files/vehicle_name_files", "lang.vromfs.bin_u/lang/units.csv", "")
        if os.path.isdir("output_files/"):
            shutil.rmtree("output_files/")
        fm_lister(central_dir, fm_dir, name_write_dir)
        central_fm_jsoner(central_dir, name_write_dir, image_names_dir)
        airplane_img_downloader(image_write_dir, 'atlases.vromfs.bin_u/units/', central_fm_read_dir, "")
        print('Finished fetching datamine files! Have fun now.')

    
    # Section for downloading datamine ends
    ###########################################
    # Section for calcualting everything starts
    answer4 = input("Do you want to make files with plane names? Necessary for the next step \n(yes/no) ")
    if answer4 == 'yes':
        vehicle_image_name_jsoner(image_write_dir, name_write_dir,)
        fm_lister(central_dir, fm_dir, name_write_dir)
        central_fm_jsoner(central_dir, name_write_dir, image_names_dir)
        ingame_central_names_lister(name_read_dir, name_write_dir)
        dict_to_objectarray_converter(name_write_dir)


    answer5 = input("Do you want to calculate aircraft engine power and weight? \n(yes/no) ")
    if answer5 == 'yes':
        print('Started the calculations! Raaahhh!')
        with open(central_fm_read_dir, "r") as central_to_FM_json:
            central_to_FM_dict = json.load(central_to_FM_json)
            named_central_dict = central_parser(central_dir, central_to_FM_dict, central_fm_read_dir, ".blkx")
            named_fm_dict = fm_parser(fm_dir, central_to_FM_dict, central_fm_read_dir)

        planes_gun_ammo_dict = gun_ammocount_assembler(named_central_dict)
        planes_gun_ammo_mass_dict = ammo_mass_calculator(gun_dir, planes_gun_ammo_dict)
        fm_plane_names_piston_dict = plane_total_mass_calculator(named_fm_dict, planes_gun_ammo_mass_dict)
        plane_masses_to_json(fm_plane_names_piston_dict, mass_write_dir)

        plane_engine_count = enginecounter(named_fm_dict)
        named_power_curves_merged, plane_speed_multipliers = power_curve_culator(named_fm_dict,
                                                                                        named_central_dict, speed=0,
                                                                                        speed_type='TAS', air_temp=15,
                                                                                        octane=True,
                                                                                        engine_modes=["military", "WEP"],
                                                                                        alt_tick=10)
        engine_power_to_json(power_write_dir, named_power_curves_merged, plane_speed_multipliers, plane_engine_count)

        print('Finished the calculations! Raaahhh!')

    print("This is the end of the script. UUuuuu")



    
if __name__ == "__main__":
    main()