import pandas as pd
import os
import json
from pathlib import Path
from blkx_parsers import blkx_parser, central_parser, fm_parser
from plane_power_calculator import enginecounter

def central_fm_jsoner(central_dir, fm_dir, name_write_dir, extension):
    central_fm_dict ={}

    central_fmwritepath = os.path.join(name_write_dir, "central-fm_plane_names.json")

    path_to_make = Path.cwd() / name_write_dir
    path_to_make.mkdir(exist_ok=True, parents=True)
    path_to_make = Path.cwd() / central_dir
    path_to_make.mkdir(exist_ok=True, parents=True)

    with open(central_fmwritepath, "w") as central_fm_json:
        sorted_paths = sorted(Path(central_dir).iterdir())
        for central_path in sorted_paths:
                    
            if not os.path.isfile(central_path):
                    continue
            central_name = central_path.name[0:-5]
            print(central_name)
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
            central_fm_dict[central_name] = fm_name
        json.dump(central_fm_dict, central_fm_json, indent=2)
    return

def central_to_fm_giver(central_name, central_dir, extension):
    centralfilepath = os.path.join(central_dir, central_name + extension)
    central_dict = blkx_parser(centralfilepath)
    if any(x in central_name for x in ("_killstreak", "event0")):
        print(central_name + " isn't interesting and is skipped")
        return
    with open (centralfilepath, "r") as central_file:
        for line in central_file:
            if "fmFile" in line:
                fm_name = (line
                        .strip()                    # Remove whitespace
                        .split('"')[-2]             # Get content between quotes
                        .split('/')[-1]             # Get filename after last /
                        .rstrip(',')                # Remove trailing comma
                        .strip('."\' '))             # Remove any remaining quotes/dots)
                fm_name = fm_name[:-4] + '.blkx'         # Remove whitespace
                return fm_name
        if central_dict:
            fm_name = central_name + extension
        else:
            print(central_name + "has no assigned flight model file and is skipped")
            return
        return fm_name

def ingame_central_names_lister(name_read_dir, name_write_dir, latest_fm_dir):
    '''
    Makes a dictionary of ingame plane names and file plane names
    '''
    units_filepath = os.path.join(name_read_dir, "units.csv")

    central_fmreadpath = os.path.join( name_write_dir, "central-fm_plane_names.json")
    central_ingamefilewritepath = os.path.join(name_write_dir, "central-ingame_plane_names.json")

    path_to_make = Path.cwd() /  name_write_dir
    path_to_make.mkdir(exist_ok=True, parents=True)
    path_to_make = Path.cwd() / name_read_dir
    path_to_make.mkdir(exist_ok=True, parents=True)

    dict_ingame_infiles = {}
    unit_names = pd.read_csv(units_filepath ,sep=";")
    dict_ingame_infiles = unit_names.set_index('<ID|readonly|noverify>')['<English>'].to_dict()

    with open (central_fmreadpath, "r") as central_fm_json:
        central_fm_dict = json.load(central_fm_json)
    # Initialize the third dictionary
    central_ingame_dict = {"piston":{}, "turboprop":{}, "jet":{}, "unknown":{}}
    # Iterate through the first dictionary
    for central_name in central_fm_dict:
        fm_dict = blkx_parser(os.path.join(latest_fm_dir, central_fm_dict[central_name] + ".blkx"))
        notneeded, engine_keys = enginecounter(fm_dict)
        if fm_dict[engine_keys[0]]["Main"]["Type"] == "Inline" or fm_dict[engine_keys[0]]["Main"]["Type"] == "Radial":
            category = "piston"
        elif fm_dict[engine_keys[0]]["Main"]["Type"] == "TurboProp":
            category = "turboprop"
        elif any (x == fm_dict[engine_keys[0]]["Main"]["Type"] for x in ("Jet", "Rocket", "PVRD")):
            category = "jet"
        else:
            category = "unknown"

        if (central_name + "_0") in dict_ingame_infiles.keys() and not dict_ingame_infiles[central_name + "_0"] == "":
            central_ingame_dict[category][central_name] = dict_ingame_infiles[central_name + "_0"].replace(u"\u00A0", " ")
        else:
            central_ingame_dict[category][central_name] = central_name

        # for infiles, ingame in dict_ingame_infiles.items():
        #     if central_name + '_0' == infiles:
        #         if not ingame == "":
        #             central_ingame_dict[category][central_name] = central_name
        #         else:
        #             central_ingame_dict[category][central_name] = ingame.replace(u"\u00A0", " ") #.replace(u"-", "‑")
        # if central_name not in central_ingame_dict:
        #     central_ingame_dict[category][central_name] = central_name

        if central_name == "j2m5_30mm":
            central_ingame_dict[category][central_name] = "J2M5 Raiden (30mm)"
    # here it ends
    with open (central_ingamefilewritepath, "w") as central_ingame_json:
        json.dump(central_ingame_dict, central_ingame_json, indent=2)
    return

def planeinfoarray_maker(write_dir):
    central_ingamefilereadpath = os.path.join(write_dir, "central-ingame_plane_names.json")
    central_ingamefilewritepath = os.path.join(write_dir, "central-ingame_plane_names_arr.json")

    path_to_make = Path.cwd() / write_dir
    path_to_make.mkdir(exist_ok=True, parents=True)

    central_ingame_array = {"piston":[], "turboprop":[], "jet":[]}
    with open(central_ingamefilereadpath, "r") as central_ingame_json:
        central_ingame_dict = json.load(central_ingame_json)
        for category in central_ingame_dict.keys():
            for central_name, ingame_name in central_ingame_dict[category].items():
                central_ingame_array[category].append({"id": central_name, "name":ingame_name, "nogap":ingame_name.replace(" ","").replace("-","").replace(".","")})
    with open (central_ingamefilewritepath, "w") as central_ingame_objectarray_json:
        json.dump(central_ingame_array, central_ingame_objectarray_json, indent=2)
    return

        
def vehicle_image_name_jsoner(source_file, destination_dir, central_fm_read_dir):
    with open(central_fm_read_dir, "r") as central_fm_json:
        central_fm_dict = json.load(central_fm_json)
    images_folder = Path(source_file)
    
    all_image_names = []
    for file in images_folder.iterdir():
        if file.is_file():
            if file.name.endswith('.png'):
                name_without_ext = file.name.removesuffix('.png')
                if name_without_ext in central_fm_dict.keys():
                    all_image_names.append(file.name)
    destination_file = os.path.join(destination_dir, "vehicle_image_names.json")
    path_to_make = Path.cwd() / destination_dir
    path_to_make.mkdir(exist_ok=True, parents=True)
    with open(destination_file, 'w') as png_names_destination:
        json.dump(all_image_names, png_names_destination, indent=2)

def valid_plane_checker(central_name, central_dict, fm_dict):
    if not fm_dict:
        print(central_name, " fm file is empty and is skipped")
        return False
    if any(x in central_dict.keys() for x in ("helicopter", "Engine0")):
        return False
    if "Engine0" not in fm_dict.keys() and "EngineType0" not in fm_dict.keys():
        print(central_name, " has no engine and is skipped")
        return False
    else:
        return True        


# for changing icons into antional abbreviations like [UK]
# rep = {u"\u00A0": " ",
#        u"\u25cb": "[Seal-Clubbing]",
#        u"\u2417":"[CN]",
#        u"\u2582": "[SU]",
#        u"\u2584": "[FR]",
#        u"\u2580": "[DE]",
#        u"\u2583": "[US]",
#        u"\u2585": "[JP]",
#        u"\u2584": "[FIN]",
#        u"\u25d0": "[HUN]",
#        u"\u2584Corsair F Mk II": "[UK]Corsair F Mk II",
#        u"\u2584AD-4NA Skyraider": "[FR]AD-4NA Skyraider",
#        u"\u2584AD-4 Skyraider": "[FR]AD-4 Skyraider",
#        u"": "[]",
#         u"": "[]",
#         u"": "[]",
#         u"": "[]",

#        }
# rep = dict((re.escape(k), v) for k, v in rep.iteritems())
# #Python 3 renamed dict.iteritems to dict.items so use rep.items() for latest versions
# pattern = re.compile("|".join(rep.keys()))
# text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)




def main():
    read_dir = "input_files/vehicle_names/"
    write_dir = "output_files/plane_name_files/"
    fm_dir = "input_files/fm_files/"
    central_dir = "input_files/central_files/"
    # fm_lister(central_dir,fm_dir, write_dir)
    # central_fm_jsoner(central_dir, write_dir, image_dir)
    ingame_central_names_lister(read_dir, write_dir)
    


if __name__ == "__main__":
    main()