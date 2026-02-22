import os
import json
import shutil
from pathlib import Path
from blkx_parsers import fm_parser, central_parser
from datamine_fetcher import  newest_repo_getter
from plane_names_inator import central_fm_jsoner, ingame_central_names_lister, planeinfoarray_maker, vehicle_image_name_jsoner, central_to_fm_giver, valid_plane_checker
from plane_mass_calculator import gun_ammocount_assembler, ammo_mass_calculator, plane_total_mass_calculator, plane_masses_to_json
from plane_power_calculator import enginecounter, power_curve_culator, engine_power_to_json, fileprepper
"""
Script for dowloading up-to-date datamine files and generating 
'engine power', 'plane names' and 'plane mass' .json files.
Comment in and out sections you want or dont want to run. 
Downloading datamine takes an hours so be careful with the lines for removing files.
"""
def version_key(path):
            """Extract and convert version numbers from path for sorting"""
            # Get folder name and remove 'aces_' prefix and '_latest' suffix
            version_str = path.name.split('_')[1]  # Gets the middle part with version
            if '.' not in version_str:  # Skip if no version number found
                return (0, 0, 0, 0)
                
            # Split version into components
            parts = version_str.split('.')
            
            # Convert to integers, pad with zeros if component missing
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            build = int(parts[3]) if len(parts) > 3 else 0
            
            # Special handling for 1.101 vs 1.99
            if major == 1:
                minor = int(str(minor).zfill(3))
                
            return (major, minor, patch, build)


def clean_fm_for_comparison(fm_dict):
    """Recursively clean FM dict by removing irrelevant sections at any nesting level"""
    #maybe 'Autopilot' will be useful
    irrelevant_keys = {
    "CockpitDoorSpeedClose", "CockpitDoorSpeedOpen", 
    "Gear", "SelfSealingTanks", "PartsWithSurface",
    "Parts", "Test", "Passport", "MouseAim", 
    "GearActuatorSpeed", "CockpitDoorBlockSpeed", "AirBrakeSpeed",
    "BayDoorSpeed", "BombLauncherSpeed", "InterceptorType", 
    "MaxSpeedNearGround", "MaxSpeedAtAltitude", "UseAutoPropInertia",   
    "isAirBrakeAvailableOnGround", "hasIndependentAirbrakesAndFlaps", 
    "maxChuteSpeed", "minChuteSpeed", "chuteRipSpeed",
    "GovernorFast", "GearShift", "FireExtinguisher", "Autopilot"
}
    if not isinstance(fm_dict, dict):
        return fm_dict
        
    return {
        k: clean_fm_for_comparison(v)
        for k, v in fm_dict.items()
        if k not in irrelevant_keys
    }

def has_files_recursive(path):
    """Check if directory contains any files (recursively)"""
    return any(item.is_file() for item in Path(path).rglob('*'))   

def find_latest_datamine():
    datamine_path = Path("input_files/datamines")
    latest_folders = []
    
    # Collect all '_latest' folders
    for folder in datamine_path.iterdir():
        if folder.is_dir() and folder.name.endswith('_latest'):
            latest_folders.append(folder)
    
    if not latest_folders:
        return None
        
    # Sort folders using version_key function and return highest version
    latest_folder = sorted(latest_folders, key=version_key)[-1]
    return str(latest_folder.name)

def main():
    latest_folder = find_latest_datamine()
    if not latest_folder:
        raise Exception("No latest datamine folder found!")
    print(latest_folder)
    latest_datamine_dir = f"input_files/datamines/{latest_folder}/"
    latest_fm_dir = f"input_files/datamines/{latest_folder}/gamedata/flightmodels/fm/"
    latest_central_dir = f"input_files/datamines/{latest_folder}/gamedata/flightmodels/"
    latest_gun_dir = f"input_files/datamines/{latest_folder}/gamedata/weapons/"
    name_read_dir = "input_files/vehicle_names/"
    image_write_dir = "input_files/vehicle_images/"
    central_fm_read_dir = "output_files/plane_name_files/central-fm_plane_names.json"
    central_ingame_read_dir = "output_files/plane_name_files/central-ingame_plane_names.json"
    name_write_dir = "output_files/plane_name_files/"
    mass_write_dir = "output_files/plane_mass_files/"
    power_write_dir = "output_files/plane_power_files/"
    out_fm_path = "output_files/out_fm/"


    # Section for downloading datamine Starts!
    ###########################################
    answer0 = input("Welcome at the batch runner. First of, make sure your working directory ends with '/wtapc-data'(click anything).")

        
    answer1 = input("Do you want to download latest datamine files into 'input files/' directory. \nIt might take 30 min? \n(yes/no) ")
    if answer1 == 'yes':
        print('Started fetching datamine files! Might take an hour!')
        newest_repo_getter()
        print('Finished fetching datamine files! Have fun now.')


    # Section for downloading datamine ends
    ###########################################
    # Section for calcualting everything starts


    answer2 = input("Do you want to make files with plane names? Necessary for the next step \n(yes/no) ")
    if answer2 == 'yes':
        if os.path.isdir("output_files/plane_name_files/"):
            shutil.rmtree("output_files/plane_name_files/")
        
        central_fm_jsoner(latest_central_dir, latest_fm_dir, name_write_dir, '.blkx')
        ingame_central_names_lister(name_read_dir, name_write_dir, latest_fm_dir)
        vehicle_image_name_jsoner(image_write_dir, name_write_dir, central_fm_read_dir)

    answer3 = input("Do you want to create aircraft engine power and weight files? Might take 20 min. \n(yes/no) ")
    if answer3 == 'yes':
        if os.path.isdir(power_write_dir):
            shutil.rmtree(power_write_dir)
        if os.path.isdir(power_write_dir):
            shutil.rmtree(power_write_dir)
        print('Started the calculations! Raaahhh!')
        with open(central_fm_read_dir, "r") as central_to_FM_json:
            central_fm_dict = json.load(central_to_FM_json)
        with open(central_ingame_read_dir, "r") as central_to_ingame_json:
            central_ingame_dict = json.load(central_to_ingame_json)
        planes_all_mass_dict = {}
        named_power_curves_merged = {}
        plane_speed_multipliers = {}
        enginecounts = {}
        for central_name in central_ingame_dict['jet'].keys():
        # for central_name in ['yak-38']:
            print('Calculating power of ', central_name)
            central_dict = central_parser(latest_central_dir, central_name, ".blkx")
            fm_dict = fm_parser(latest_fm_dir, central_fm_dict[central_name], ".blkx")
            plane_gunammo_dict = gun_ammocount_assembler(central_dict, latest_datamine_dir)
            plane_gun_ammo_mass_dict = ammo_mass_calculator(latest_gun_dir, plane_gunammo_dict)
            plane_all_mass_dict = plane_total_mass_calculator(fm_dict, plane_gun_ammo_mass_dict)
            planes_all_mass_dict[central_name] = plane_all_mass_dict
            enginecount, engine_keys = enginecounter(fm_dict) #move to js
            power_curves_merged, speed_multiplier = power_curve_culator(central_name, fm_dict, central_dict, speed=0, speed_type='TAS', air_temp=15, octane=True, engine_modes=["military", "WEP"], min_alt=-4000, max_alt=20000, alt_tick=10)
            plane_speed_multipliers[central_name] = speed_multiplier
            named_power_curves_merged[central_name] = power_curves_merged 
            enginecounts[central_name] = enginecount
        plane_masses_to_json(planes_all_mass_dict, mass_write_dir) 
        engine_power_to_json(power_write_dir, named_power_curves_merged, plane_speed_multipliers, enginecounts)

        print('Finished the calculations! Raaahhh!')
    answer4 = input("Do you want to update custom .blk fm files, by remaking them for for all game versions? \nThe website needs them. It should take 5-10 minutes. \n(yes/no) ")
    if answer4 == 'yes':
        print('Started making .blk files for all game versions!')
        if os.path.isdir(out_fm_path):
            shutil.rmtree(out_fm_path)
        oldest_same_fm_counter = {}
        dir_list = sorted(Path("input_files/datamines").iterdir(), key=version_key)

        for datamine_folder in dir_list:   #comment out for testing
            if not datamine_folder.is_dir() or not has_files_recursive(datamine_folder):
                print('Empty datamine skipped', datamine_folder)
                continue      #comment out for testing
            # datamine_folder = Path("input_files/datamines/aces_2.1.0.18") #uncomment for testing
            # if datamine_folder.is_dir(): #uncomment for testing
             
            version_str = datamine_folder.name.split('_')[1]
            print("Processing " + version_str + "...")
            datamine_dir = f"{datamine_folder}"
            fm_dir = f"{datamine_folder}/gamedata/flightmodels/fm/"
            central_dir = f"{datamine_folder}/gamedata/flightmodels/"
            gun_dir = f"{datamine_folder}/gamedata/weapons/"
            out_fm_dir = f"{out_fm_path}fm_{version_str}/" 
            sorted_paths = sorted(Path(central_dir).iterdir())
            for central_path in sorted_paths:
                
                if not os.path.isfile(central_path):
                        continue
                central_name = central_path.name[0:-5]
                # print(central_name, version_str, 'is prepped')
                fm_file = central_to_fm_giver(central_name, central_dir, '.blkx')
                if not fm_file:
                    continue
                if not os.path.isfile(os.path.join(fm_dir, fm_file)):
                    continue
                fm_name = fm_file[0:-5]
    
                central_dict = central_parser(central_dir, central_name, ".blkx")
                fm_dict = fm_parser(fm_dir, fm_name, ".blkx")
                if not valid_plane_checker(central_name, central_dict, fm_dict):
                    continue
                plane_gunammo_dict = gun_ammocount_assembler(central_dict, datamine_dir)
                plane_gun_ammo_mass_dict = ammo_mass_calculator(gun_dir, plane_gunammo_dict)

                fm_dict = fileprepper(central_dict, fm_dict, plane_gun_ammo_mass_dict)

                if not central_name in oldest_same_fm_counter.keys():
                    oldest_same_fm_counter[central_name] = [clean_fm_for_comparison(fm_dict.copy()), [version_str]]

                elif oldest_same_fm_counter[central_name][0] == clean_fm_for_comparison(fm_dict.copy()):
                    continue
                else:
                    oldest_same_fm_counter[central_name][0] = clean_fm_for_comparison(fm_dict.copy())
                    oldest_same_fm_counter[central_name][1].append(version_str)

                write_path = Path.cwd() / out_fm_dir
                write_path.mkdir(exist_ok=True, parents=True)  
                with open(out_fm_dir + central_name + '.json', 'w') as plane_fm_file:
                    json.dump(fm_dict, plane_fm_file, indent=1)

        for key, value in oldest_same_fm_counter.items():
            oldest_same_fm_counter[key] = value[1][::-1]  # Added [::-1] to reverse the list
        oldest_same_fm_path = os.path.join(name_write_dir, "oldest_same_fm_dict.json")
        with open(oldest_same_fm_path, 'w') as oldest_same_fm_file:
            json.dump(oldest_same_fm_counter, oldest_same_fm_file, indent=1)

        print('Finished making custom .blkx files for all game versions!')
    answer5 = input("Do you want to do all these?: \n 1) create .json array of plane names and unique versions. \n 2) copy it to the website repo. \n 3)Copy all image names of planes to the website repo. \n(yes/no) ")
    if answer5 == 'yes':

        lib_destination = Path.cwd().parents[0] /"wt-aircraft-performance-calculator.org/src/lib/"
        dir_list = sorted(Path("input_files/datamines").iterdir(), key=version_key)
        version_names = [dir.name.split('_')[1] for dir in dir_list if dir.is_dir()][::-1]  # Added [::-1] to reverse the list
        all_verlist_path = os.path.join(name_write_dir, "all_versions_list.json")
        with open(all_verlist_path, 'w') as all_verlist_file:
            json.dump(version_names, all_verlist_file, indent=1)
        shutil.copy(all_verlist_path,  lib_destination)
        plane_image_names_path = Path.cwd() / name_write_dir / "vehicle_image_names.json"
        shutil.copy(plane_image_names_path,  lib_destination)
        oldest_same_fm_path = Path.cwd() / name_write_dir / "oldest_same_fm_dict.json"
        shutil.copy(oldest_same_fm_path,  lib_destination) 
        planeinfoarray_maker(name_write_dir) 
        array_source = Path.cwd() / name_write_dir / "central-ingame_plane_names_arr.json"
        shutil.copy(array_source,  lib_destination)
        
        img_destination = Path.cwd().parents[0] /"wtapc-org/static/images/plane_images"
        if os.path.isdir(img_destination):
            shutil.rmtree(img_destination)
        img_destination.mkdir(exist_ok=True, parents=True)
        for central_name in oldest_same_fm_counter.keys():
            img_source = Path.cwd() / image_write_dir / (central_name + '.png')
            if not img_source.exists():
                 continue
            shutil.copy(img_source, img_destination)
        
    print("This is the end of the script. UUuuuu")

    
if __name__ == "__main__":
    main()