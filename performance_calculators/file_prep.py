from pathlib import Path
from plane_power_calculator import enginecounter, engine_shortcuter, old_type_fm_detector, exception_fixer, rpm_er, wep_rpm_ratioer, wep_mp_er, definition_alt_power_adjuster, deck_power_maker, same_engine_checker

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
    relevant_keys = {
          "Mass", "Engine0", "Engine1", "Engine2",  "Engine3",  "Engine4",  "Engine5",  "Engine6",  "Engine7",  "Engine8",  "Engine9", "EngineType0", "EngineType1", "EngineType2", "EngineType3", "Propeller0", "Modif", "Guns", "engines_are_same", "engine_count"
          }
    if not isinstance(fm_dict, dict):
        return fm_dict
       
    # return {
    #     k: clean_fm_for_comparison(v)
    #     for k, v in fm_dict.items()
    #     if k not in irrelevant_keys

    # }
    #or only include what is useful
    return {
        k: v for k, v in fm_dict.items() 
        if k in relevant_keys
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

def fileprepper(central_dict, fm_dict, plane_gun_ammo_mass_dict):
    """
    A bulk function running previous functions to make a list of engine power values from -4000m to 20000m for every superchrger gear.
    """
    compr_stages_count = 1
    fm_dict["engine_count"], engine_keys = enginecounter(fm_dict)
    for engine in engine_keys:
        Engine, Compressor, Main, Afterburner, Propeller = engine_shortcuter(fm_dict, engine)
        "Prepping parameters in fm_dict for calculation"
        if Main["Type"] == "Inline" or Main["Type"] == "Radial":
            old_type_fm_detector(Compressor, Main)
            exception_fixer(Compressor)
            rpm_er(Main, Propeller)
            wep_rpm_ratioer(Main, Compressor, Propeller)
            wep_mp_er(Engine, Compressor, Main, Afterburner)
            for compr_stage in range(0, 6):
                if "Power" + str(compr_stage) in Compressor:
                    compr_stages_count = compr_stage + 1
            for h in range(0, compr_stages_count):
                definition_alt_power_adjuster(Main, Compressor, Propeller, h)
                deck_power_maker(Main, Compressor, h)
    if 'modifications' in central_dict.keys():
        important_mods = {}
        for key, value in central_dict['modifications'].items():
            if value == []:
                central_dict['modifications'][key] = ['u']
            if key in ["new_radiator", "cd_98", "CdMin_Fuse", "new_cover", "structure_str",
                       "hp_105",  "new_compressor", "new_engine_injection", "150_octan_fuel", 
                        "100_octan_spitfire", "ussr_fuel_b-95", "ussr_fuel_b-100",
                       "hp_105_jet", "f_4c_CdMin_Fuse", "new_compressor_jet", "hydravlic_power"
                        ]:
                important_mods[key] = value
                
        fm_dict['Modif'] = important_mods
    else:
        fm_dict['Modif'] = {}

    if "MaxFuelMass0" in fm_dict["Mass"]:
        fm_dict["Mass"]["MaxFuelMass"] = fm_dict["Mass"].pop("MaxFuelMass0")
    fm_dict["Mass"]['pilots_mass']= 90 * fm_dict["Crew"]
    fm_dict["Guns"] = plane_gun_ammo_mass_dict
    fm_dict["engines_are_same"]  = same_engine_checker(fm_dict, engine_keys)
    return fm_dict
