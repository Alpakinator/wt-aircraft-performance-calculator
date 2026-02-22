import os
import json
from blkx_parsers import blkx_parser
from pathlib import Path
# def gun_ammocount_assembler_old(central_dict, datamine_dir):
#     plane_gunammo_dict ={}
#     preset_has_gun = False
#     if "commonWeapons" in central_dict.keys() and isinstance(central_dict["commonWeapons"], dict):
#         # weapon_dict = central_dict["commonWeapons"]
#         for weaponkey, weapondict in central_dict["commonWeapons"].items():
#             # Get all keys that start with "blk" or "bullets"
#             if not "Weapon" in weaponkey:
#                 continue
#             for key in weapondict.keys():
#                 base_key = key.rstrip('0123456789')  # Remove any trailing numbers
                
#                 if base_key == "blk":
#                     blk_path = weapondict[key]
#                     blk_basename = os.path.basename(blk_path)
#                     bullets_key = "bullets" + key[3:]  # Match numbered suffix from blk key
                    
#                     if bullets_key in weapondict:
#                         bullet_count = weapondict[bullets_key]
                        
#                         if blk_basename in plane_gunammo_dict:
#                             plane_gunammo_dict[blk_basename]["ammo_count"] += bullet_count
#                             plane_gunammo_dict[blk_basename]["gun_count"] += 1
#                         else:
#                             plane_gunammo_dict[blk_basename] = {
#                                 "ammo_count": bullet_count,
#                                 "gun_count": 1
#                             }
                        
#     if "WeaponSlots" in central_dict.keys() and "WeaponSlot" in central_dict["WeaponSlots"].keys():
#         for slotkey, slot_dict in central_dict["WeaponSlots"].items():
#             if not "WeaponSlot" in slotkey:
#                 continue
#             if type(slot_dict) != dict:
#                 continue
            
#             for presetkey, presetdict in slot_dict.items(): 
#                 if not "WeaponPreset" in presetkey:
#                     continue
#                 if "Weapon" in presetdict.keys() and all(x in presetdict["Weapon"].keys() for x in ["blk", "bullets"]):
#                     if any(x in presetdict["Weapon"]["blk"] for x in ["cannon", "gun"]):
#                         preset_has_gun = True
#                         if os.path.basename(presetdict["Weapon"]['blk']) in plane_gunammo_dict:
#                             plane_gunammo_dict[os.path.basename(presetdict["Weapon"]['blk'])]["ammo_count"] += presetdict["Weapon"]["bullets"]
#                             plane_gunammo_dict[os.path.basename(presetdict["Weapon"]['blk'])]["gun_count"] += 1
#                         else:
#                             plane_gunammo_dict[os.path.basename(presetdict["Weapon"]['blk'])] = {"ammo_count": presetdict["Weapon"]["bullets"], "gun_count": 1}
#                 if preset_has_gun == True:
#                     return plane_gunammo_dict
#     else:
#         if "weapon_presets" in central_dict.keys() and "preset" in central_dict["weapon_presets"].keys():
#             for presetkey, preset_dict in central_dict["weapon_presets"].items():
#                 if "default" in preset_dict['name']:
#                     preset_file_path = os.path.join( datamine_dir, (preset_dict['blk'].lower() + 'x'))
#                     if not os.path.isfile(preset_file_path):
#                         return plane_gunammo_dict
#                     else:
#                         preset_file = blkx_parser(preset_file_path)
#                         if not preset_file:
#                             return plane_gunammo_dict
#                         for weaponkey, weapondict in preset_file.items():
#                             # Get all keys that start with "blk" or "bullets"
#                             if not "Weapon" in weaponkey:
#                                 continue
#                             for key in weapondict.keys():
#                                 base_key = key.rstrip('0123456789')  # Remove any trailing numbers
                                
#                                 if base_key == "blk":
#                                     blk_path = weapondict[key]
#                                     blk_basename = os.path.basename(blk_path)
#                                     bullets_key = "bullets" + key[3:]  # Match numbered suffix from blk key
                                    
#                                     if bullets_key in weapondict:
#                                         bullet_count = weapondict[bullets_key]
                                        
#                                         if blk_basename in plane_gunammo_dict:
#                                             plane_gunammo_dict[preset_dict['name']][blk_basename]["ammo_count"] += bullet_count
#                                             plane_gunammo_dict[preset_dict['name']][blk_basename]["gun_count"] += 1
#                                         else:
#                                             plane_gunammo_dict[preset_dict['name']][blk_basename] = {
#                                                 "ammo_count": bullet_count,
#                                                 "gun_count": 1
#                                 }
                    
#     return plane_gunammo_dict
    
def gun_ammocount_assembler(central_dict, datamine_dir):
    plane_gunammo_dict ={}
    preset_has_gun = False
    if ("commonWeapons" in central_dict.keys() and 
        isinstance(central_dict["commonWeapons"], dict) and 
        "Weapon" in central_dict["commonWeapons"] and
        isinstance(central_dict["commonWeapons"]["Weapon"], dict) and not 'slot' in central_dict["commonWeapons"]["Weapon"].keys()):
        # weapon_dict = central_dict["commonWeapons"]
        for weaponkey, weapondict in central_dict["commonWeapons"].items():
            # Get all keys that start with "blk" or "bullets"
            if not "Weapon" in weaponkey:
                continue
            for key in weapondict.keys():
                base_key = key.rstrip('0123456789')  # Remove any trailing numbers
                
                if base_key == "blk":
                    blk_path = weapondict[key]
                    blk_basename = os.path.basename(blk_path)
                    bullets_key = "bullets" + key[3:]  # Match numbered suffix from blk key
                    
                    if bullets_key in weapondict:
                        bullet_count = weapondict[bullets_key]
                        
                        if blk_basename in plane_gunammo_dict:
                            plane_gunammo_dict[blk_basename]["ammo_count"] += bullet_count
                            plane_gunammo_dict[blk_basename]["gun_count"] += 1
                            preset_has_gun = True
                        else:
                            plane_gunammo_dict[blk_basename] = {
                                "ammo_count": bullet_count,
                                "gun_count": 1
                            }
                            preset_has_gun = True
            # if preset_has_gun == True:
            #     return plane_gunammo_dict
    elif("commonWeapons" in central_dict.keys() and 
            isinstance(central_dict["commonWeapons"], dict) and 
            "Weapon" in central_dict["commonWeapons"] and
            isinstance(central_dict["commonWeapons"]["Weapon"], dict) and 'slot' in central_dict["commonWeapons"]["Weapon"].keys() and central_dict["commonWeapons"]["Weapon"]['slot']==0):   
        default_preset = central_dict["commonWeapons"]["Weapon"]["preset"]
        if "WeaponSlots" in central_dict.keys() and "WeaponSlot" in central_dict["WeaponSlots"].keys() and "WeaponPreset" in central_dict["WeaponSlots"]["WeaponSlot"].keys() and 'name' in central_dict["WeaponSlots"]["WeaponSlot"]["WeaponPreset"].keys() and central_dict["WeaponSlots"]["WeaponSlot"]["WeaponPreset"]['name'] == default_preset:
            for weaponkey, weapondict in central_dict["WeaponSlots"]['WeaponSlot']["WeaponPreset"]['Weapon'].items():
                base_key = weaponkey.rstrip('0123456789')  # Remove any trailing numbers
                if base_key == "blk":
                    
                    blk_path = weapondict
                    blk_basename = os.path.basename(blk_path)
                    if blk_basename ==  "dummy_weapon.blk":
                        continue
                    bullets_key = "bullets" + weaponkey[3:]  # Match numbered suffix from blk key
                    # print(central_dict["WeaponSlots"]['WeaponSlot']["WeaponPreset"]['Weapon'][bullets_key])
                    
                    if bullets_key in central_dict["WeaponSlots"]['WeaponSlot']["WeaponPreset"]['Weapon'].keys():
                        # print(weaponkey, weapondict, bullets_key)
                        bullet_count = central_dict["WeaponSlots"]['WeaponSlot']["WeaponPreset"]['Weapon'][bullets_key]
                        if blk_basename in plane_gunammo_dict:
                            plane_gunammo_dict[blk_basename]["ammo_count"] += bullet_count
                            plane_gunammo_dict[blk_basename]["gun_count"] += 1
                            preset_has_gun = True
                        else:
                            plane_gunammo_dict[blk_basename] = {
                                "ammo_count": bullet_count,
                                "gun_count": 1
                            }
                            preset_has_gun = True
            # print(plane_gunammo_dict)
            # if preset_has_gun == True:
            #     return plane_gunammo_dict
    if "weapon_presets" in central_dict.keys() and "preset" in central_dict["weapon_presets"].keys():
        for presetkey, preset_dict in central_dict["weapon_presets"].items():
            if "default" in preset_dict['name']:
                preset_file_path = os.path.join( datamine_dir, (preset_dict['blk'].lower() + 'x'))
                if not os.path.isfile(preset_file_path):
                    return plane_gunammo_dict
                else:
                    preset_file = blkx_parser(preset_file_path)
                    if not preset_file:
                        return plane_gunammo_dict
                    for weaponkey, weapondict in preset_file.items():
                        # Get all keys that start with "blk" or "bullets"
                        if not "Weapon" in weaponkey:
                            continue
                        for key in weapondict.keys():
                            base_key = key.rstrip('0123456789')  # Remove any trailing numbers
                            
                            if base_key == "blk":
                                blk_path = weapondict[key]
                                blk_basename = os.path.basename(blk_path)
                                bullets_key = "bullets" + key[3:]  # Match numbered suffix from blk key
                                
                                if bullets_key in weapondict:
                                    bullet_count = weapondict[bullets_key]
                                    
                                    if blk_basename in plane_gunammo_dict:
                                        plane_gunammo_dict[blk_basename]["ammo_count"] += bullet_count
                                        plane_gunammo_dict[blk_basename]["gun_count"] += 1
                                    else:
                                        plane_gunammo_dict[blk_basename] = {
                                            "ammo_count": bullet_count,
                                            "gun_count": 1
                            }             
    return plane_gunammo_dict


def ammo_mass_calculator(gun_dir, plane_gunammo_dict):
    
    all_ammo_mass = 0  # initialize the mass of ammo of planes 
    for weapon, ammo_count in plane_gunammo_dict.items():
        gun_path = os.path.join(gun_dir, (weapon.lower().removesuffix('.blk') + ".blkx"))
        if not os.path.isfile(gun_path):
            gun_path = os.path.join(gun_dir, 'rocketguns', (weapon.lower().removesuffix('.blk') + ".blkx"))
        try:
            weapon_dict = blkx_parser(gun_path)
            bullet_dict = weapon_dict["bullet"]
            
            if type(bullet_dict) == dict:
                shell_mass = bullet_dict["mass"]
                ammo_mass = shell_mass * plane_gunammo_dict[weapon]["ammo_count"]
                # break
            elif type(bullet_dict) == str:
                if "mass" in bullet_dict:
                    shell_mass = weapon_dict["bullet"][bullet_dict]
                    ammo_mass = shell_mass * plane_gunammo_dict[weapon]["ammo_count"]
                    print('WHAT?? \n\n\n\n\n\n')
                # break
        except:
            
            continue # that ignores all weapons that aren't guns, cause only guns are at gun_dir
        all_ammo_mass += ammo_mass
        plane_gunammo_dict[weapon].update({"shell_mass":shell_mass})
    plane_gunammo_dict.update({"all_ammo_mass" : int(all_ammo_mass)})
    plane_gun_ammo_mass_dict = plane_gunammo_dict
    return plane_gun_ammo_mass_dict

def plane_total_mass_calculator(fm_dict, plane_gun_ammo_mass_dict):
    'empty mass + oil mass + 90 kg per crewman + fuel mass + ammo mass + external stores'
    plane_all_mass_dict = {}
    empty_mass = int(fm_dict["Mass"]["EmptyMass"])
    try:
        max_fuel_mass = int(fm_dict["Mass"]["MaxFuelMass0"])
    except:
        max_fuel_mass = int(fm_dict["Mass"]["MaxFuelMass"])
    oil_mass = int(fm_dict["Mass"][ "OilMass"])
    crew = int(fm_dict["Crew"])
    pilot_mass = 90 * crew
    all_ammo_mass = int(plane_gun_ammo_mass_dict['all_ammo_mass'])
    nitro_mass = int(fm_dict["Mass"]["MaxNitro"])
    total_fuelless_mass = int(empty_mass + oil_mass + pilot_mass + all_ammo_mass + nitro_mass)
    plane_mass_list = {"EmptyMass":empty_mass, "max_fuel_mass":max_fuel_mass, "nitro_mass": nitro_mass, "oil_mass":oil_mass, "pilot_mass": pilot_mass, "all_ammo_mass":all_ammo_mass}
    plane_all_mass_dict=plane_mass_list
    return plane_all_mass_dict

def plane_masses_to_json(plane_all_mass_dict, write_dir):
    mass_write_dir = os.path.join(write_dir, "planes_masses.json")
    destination = Path.cwd() / write_dir
    destination.mkdir(exist_ok=True, parents=True)
    with open(mass_write_dir, 'w') as planes_masses_json:
        json.dump(plane_all_mass_dict, planes_masses_json, indent=2)

def main():
    write_dir = "output_files/plane_mass_files/"
    central_dir = "input_files/central_files/"
    fm_dir = "input_files/fm_files/"
    gun_dir = "input_files/weapon_files/"
    read_dir = "output_files/plane_name_files/central-fm_plane_names.json"
    # with open(read_dir, "r") as central_to_FM_json:
    #     central_to_FM_dict = json.load(central_to_FM_json)
    #     plane_gun_tuple = central_parser(central_dir, central_to_FM_dict, read_dir, ".blkx")
    #     planes_gun_ammo_dict = gun_ammocount_assembler(plane_gun_tuple)
    #     plane_gun_ammo_mass_dict = ammo_mass_calculator(gun_dir, planes_gun_ammo_dict)
    #     named_fm_dict = fm_parser(fm_dir, central_to_FM_dict, read_dir)
    #     plane_all_mass_dict = plane_total_mass_calculator(named_fm_dict, plane_gun_ammo_mass_dict)
    #     plane_masses_to_json(plane_all_mass_dict, write_dir)
    return

if __name__ == "__main__":
    main()  




