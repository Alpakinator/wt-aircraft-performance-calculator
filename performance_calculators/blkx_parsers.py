import json
import os
def blkx_parser(blkx_dir):
    if os.path.getsize(blkx_dir) == 0:
        print(blkx_dir, 'is EMPTY')
        return None
    with open(blkx_dir) as blkx_unpars:
        blkx_dict = json.load(blkx_unpars)
        return listdict_to_dict_converter(blkx_dict)
    
def plane_file_accepter(files_to_plot, read_dir):
    planes_to_plot_dict = {}
    with open(read_dir, "r") as central_to_fm_json:
        central_to_fm_dict = json.load(central_to_fm_json)
        for file in files_to_plot: #likely unneccessary safety check
            if file in central_to_fm_dict.keys():
                planes_to_plot_dict[file] = central_to_fm_dict[file]
            else:
                print(file + " FM Doesn't exist")
                continue
    return planes_to_plot_dict

def fm_parser(fm_dir, fm_name, file_extension):
    # planes_to_plot_dict = plane_file_accepter(files_to_plot, read_dir)
    fm_path = os.path.join(fm_dir, fm_name+file_extension)
    if os.stat(fm_path).st_size == 0:
        return
    fm_dict = blkx_parser(fm_path)
    if fm_dict:
        return fm_dict
    return 

def central_parser(central_dir, central_name, file_extension):
    # planes_to_plot_dict = plane_file_accepter(files_to_plot, read_dir)
    central_dict = blkx_parser(os.path.join(central_dir, central_name+file_extension))
    if central_dict:
        return central_dict
    return 
    
def _strip_numeric_suffix(key):
    """Helper function to identify if key has numeric suffix and get base part"""
    # Find where the numeric suffix starts (if any)
    for i, char in enumerate(key[::-1]):
        if not char.isdigit():
            if i == 0:  # No numeric suffix
                return key, None
            # Return both base and suffix
            return key[:-i], key[-i:]
    return key, None  # All digits (shouldn't happen in practice)

def listdict_to_dict_converter(data):
    """
    Recursively converts all lists of dictionaries to dictionaries, 
    maintaining position-based indexing for all keys except for single key-value dictionaries
    """
    # Handle lists
    if isinstance(data, list):
        # If it's a list of dicts, convert to dictionary
        if data and all(isinstance(item, dict) for item in data):
            result = {}
            key_count = {}  # Track count of each base key
            original_keys = {}  # Track original keys with their suffixes
            
            # Check if all dictionaries have single key-value pairs
            is_single_key = all(len(item) == 1 for item in data)
            
            # Build result dictionary
            for idx, item in enumerate(data):
                for key, value in item.items():
                    base_key, suffix = _strip_numeric_suffix(key)
                    
                    if base_key not in key_count:
                        key_count[base_key] = 0
                        if suffix is not None:  # If key had original numeric suffix
                            original_keys[base_key] = key  # Store original key
                    
                    if is_single_key:
                        if key_count[base_key] == 0:
                            new_key = original_keys.get(base_key, base_key)  # Use original key if it had suffix
                        else:
                            new_key = f"{base_key}{key_count[base_key]}"
                    else:
                        if idx == 0:
                            new_key = original_keys.get(base_key, base_key)  # Use original key if it had suffix
                        else:
                            new_key = f"{base_key}{idx}"
                    
                    key_count[base_key] += 1
                    result[new_key] = listdict_to_dict_converter(value)
            
            return result
            
        # Process list elements recursively
        return [listdict_to_dict_converter(item) for item in data]
        
    # Handle dictionaries
    elif isinstance(data, dict):
        return {
            key: listdict_to_dict_converter(value) 
            for key, value in data.items()
        }
        
    # Return unchanged if not a container type
    return data

def main():
    """To test if the parsers make a correct dictionaty out of .blkx file"""
    central_dir = "input_files/central_files/"

    fm_filepath = ("output_files/plane_name_files/central-fm_plane_names.json")
    with open(fm_filepath, "r") as fm_json:
        # FM_dict = json.load(fm_json) #every sinhle aircraft cenral fm file parsed and printed
        FM_dict = ['re_2000_int']
        for file in FM_dict:
            print("this plane" ,file)
            fm_dir = (central_dir + file + '.blkx')
            # print(fm_dir)
            parsed = blkx_parser(fm_dir)
            print(parsed)



if __name__ == "__main__":
        main()
