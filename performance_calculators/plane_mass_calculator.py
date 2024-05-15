import os
import json
from blkx_parsers import central_parser, fm_parser
from pathlib import Path

def gun_ammocount_assembler(named_central_dict):
    planes_gun_ammo_dict = {}
    for plane_name, central_dict in named_central_dict.items():
        plane_armament_dict ={}
        if "commonWeapons" in central_dict.keys() and "Weapon" in central_dict["commonWeapons"].keys():
            if type(central_dict["commonWeapons"]["Weapon"]) == list:
                for weapon_num, weapon_dict in enumerate(central_dict["commonWeapons"]["Weapon"]):
                    if type(weapon_dict) == dict:
                        if os.path.basename(weapon_dict['blk']) in plane_armament_dict:
                            plane_armament_dict[os.path.basename(weapon_dict['blk'])]["ammo_count"] += weapon_dict["bullets"]
                            plane_armament_dict[os.path.basename(weapon_dict['blk'])]["gun_count"] += 1
                        else:
                            plane_armament_dict[os.path.basename(weapon_dict['blk'])] = {"ammo_count": weapon_dict["bullets"], "gun_count": 1}
                    elif type(weapon_dict) == str:
                        print("uh oh, ", plane_name, "is confusing")
            elif type(central_dict["commonWeapons"]["Weapon"]) == dict:
                if "preset" in central_dict["commonWeapons"]["Weapon"].keys():
                    planes_gun_ammo_dict[plane_name] = central_dict["commonWeapons"]["Weapon"]["preset"]
                elif all(x in central_dict["commonWeapons"]["Weapon"].keys() for x in ["blk", "bullets"]):
                    if os.path.basename(weapon_dict['blk']) in plane_armament_dict:
                        plane_armament_dict[os.path.basename(central_dict["commonWeapons"]["Weapon"]['blk'])]["ammo_count"] += central_dict["commonWeapons"]["Weapon"]["bullets"]
                        plane_armament_dict[os.path.basename(central_dict["commonWeapons"]["Weapon"]['blk'])]["gun_count"] += 1
                    else:
                        plane_armament_dict[os.path.basename(central_dict["commonWeapons"]["Weapon"]['blk'])] = {"ammo_count": central_dict["commonWeapons"]["Weapon"]["bullets"], "gun_count": 1}

        if "WeaponSlots" in central_dict.keys() and "WeaponSlot" in central_dict["WeaponSlots"].keys():
            for slot_num, slot_dict in enumerate(central_dict["WeaponSlots"]["WeaponSlot"]):
                if type(slot_dict["WeaponPreset"]) == dict:
                    if slot_dict["WeaponPreset"]["name"] == planes_gun_ammo_dict[plane_name]:
                        print(plane_name)
                        if type(slot_dict["WeaponPreset"]["Weapon"]) == list:
                            for weapon_num, weapon_dict in enumerate(slot_dict["WeaponPreset"]["Weapon"]):
                                if type(weapon_dict) == dict:
                                    if all(x in weapon_dict.keys() for x in ["blk", "bullets"]):
                                        if os.path.basename(weapon_dict['blk']) in plane_armament_dict:
                                            plane_armament_dict[os.path.basename(weapon_dict['blk'])]["ammo_count"] += weapon_dict["bullets"]
                                            plane_armament_dict[os.path.basename(weapon_dict['blk'])]["gun_count"] += 1
                                        else:
                                            plane_armament_dict[os.path.basename(weapon_dict['blk'])] = {"ammo_count": weapon_dict["bullets"], "gun_count": 1}
                                elif type(weapon_dict) == str:
                                    print("uh oh, ", plane_name, "is confusing")
                        elif type(slot_dict["WeaponPreset"]["Weapon"]) == dict:
                            if all(x in slot_dict["WeaponPreset"]["Weapon"].keys() for x in ["blk", "bullets"]):
                                if os.path.basename(weapon_dict['blk']) in plane_armament_dict:
                                    plane_armament_dict[os.path.basename(slot_dict["WeaponPreset"]["Weapon"]['blk'])]["ammo_count"] += slot_dict["WeaponPreset"]["Weapon"]["bullets"]
                                    plane_armament_dict[os.path.basename(slot_dict["WeaponPreset"]["Weapon"]['blk'])]["gun_count"] += 1
                                else:
                                    plane_armament_dict[os.path.basename(slot_dict["WeaponPreset"]["Weapon"]['blk'])] = {"ammo_count": slot_dict["WeaponPreset"]["Weapon"]["bullets"], "gun_count": 1}
                                print('hmm')

        planes_gun_ammo_dict[plane_name] = plane_armament_dict
    return planes_gun_ammo_dict

def ammo_mass_calculator(gun_dir, planes_gun_ammo_dict):
    for plane_name, gun_dict in planes_gun_ammo_dict.items():
        all_ammo_mass = 0  # initialize the mass of ammo of planes 
        for weapon, ammo_count in gun_dict.items():
            try:
                with open (gun_dir + weapon.removesuffix('.blk') + ".blkx") as weapon_file:
                    weapon_dict = json.load(weapon_file)
                    for bullet_index, bullet_dict in enumerate(weapon_dict["bullet"]):
                        if type(bullet_dict) == dict:
                            shell_mass = bullet_dict["mass"]
                            ammo_mass = shell_mass * planes_gun_ammo_dict[plane_name][weapon]["ammo_count"]
                            # print(ammo_mass)
                            break
                        elif type(bullet_dict) == str:
                            if "mass" in bullet_dict:
                                shell_mass = weapon_dict["bullet"][bullet_dict]
                                ammo_mass = shell_mass * planes_gun_ammo_dict[plane_name][weapon]["ammo_count"]
                            break
            except:
                continue # that ignores all weapons that aren't guns, cause only guns are at gun_dir
            all_ammo_mass += ammo_mass
            planes_gun_ammo_dict[plane_name][weapon].update({"shell_mass":shell_mass})
        planes_gun_ammo_dict[plane_name].update({"all_ammo_mass" : int(all_ammo_mass)})
    planes_gun_ammo_mass_dict = planes_gun_ammo_dict
    return planes_gun_ammo_mass_dict

def plane_total_mass_calculator(named_fm_dict, planes_gun_ammo_mass_dict):
    'empty mass + oil mass + 90 kg per crewman + fuel mass + ammo mass + external stores'
    fm_plane_names_piston_dict = {}
    for plane_name, fm_dict in named_fm_dict.items():
        empty_mass = int(fm_dict["Mass"]["EmptyMass"])
        try:
            max_fuel_mass = int(fm_dict["Mass"]["MaxFuelMass0"])
        except:
            max_fuel_mass = int(fm_dict["Mass"]["MaxFuelMass"])
        oil_mass = int(fm_dict["Mass"][ "OilMass"])
        crew = int(fm_dict["Crew"])
        pilot_mass = 90 * crew
        all_ammo_mass = int(planes_gun_ammo_mass_dict[plane_name]['all_ammo_mass'])
        nitro_mass = int(fm_dict["Mass"]["MaxNitro"])
        total_fuelless_mass = int(empty_mass + oil_mass + pilot_mass + all_ammo_mass + nitro_mass)
        plane_mass_list = {"empty_mass":empty_mass, "max_fuel_mass":max_fuel_mass, "nitro_mass": nitro_mass, "oil_mass":oil_mass, "pilot_mass": pilot_mass, "all_ammo_mass":all_ammo_mass}
        fm_plane_names_piston_dict[plane_name]=plane_mass_list
    return fm_plane_names_piston_dict

def plane_masses_to_json(fm_plane_names_piston_dict, write_dir):
    masswritepath = os.path.join(write_dir, "plane_mass_piston.json")
    destination = Path.cwd() / write_dir
    destination.mkdir(exist_ok=True, parents=True)
    with open(masswritepath, 'w') as plane_mass_piston_json:
        json.dump(fm_plane_names_piston_dict, plane_mass_piston_json, indent=2)

def main():
    write_dir = "output_files/plane_mass_files/"
    central_dir = "input_files/central_files/"
    fm_dir = "input_files/fm_files/"
    gun_dir = "input_files/weapon_files/"
    read_dir = "output_files/plane_name_files/central-fm_plane_names_piston.json"
    # with open(read_dir, "r") as central_to_FM_json:
    #     central_to_FM_dict = json.load(central_to_FM_json)
    #     plane_gun_tuple = central_parser(central_dir, central_to_FM_dict, read_dir, ".blkx")
    #     planes_gun_ammo_dict = gun_ammocount_assembler(plane_gun_tuple)
    #     planes_gun_ammo_mass_dict = ammo_mass_calculator(gun_dir, planes_gun_ammo_dict)
    #     named_fm_dict = fm_parser(fm_dir, central_to_FM_dict, read_dir)
    #     fm_plane_names_piston_dict = plane_total_mass_calculator(named_fm_dict, planes_gun_ammo_mass_dict)
    #     plane_masses_to_json(fm_plane_names_piston_dict, write_dir)
    return

if __name__ == "__main__":
    main()  




