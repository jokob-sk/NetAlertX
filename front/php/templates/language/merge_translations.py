import json
import os

def merge_translations(main_file, other_files):
    # Load main file
    with open(main_file, 'r') as f:
        main_data = json.load(f)

    # Get keys and sort them alphabetically
    keys = sorted(main_data['en_us'].keys())

    # Sort the keys alphabetically in the main file
    main_data['en_us'] = {k: main_data['en_us'][k] for k in sorted(main_data['en_us'].keys())}

    # Rewrite sorted main file
    with open(main_file, 'w') as f:
        json.dump(main_data, f, indent=4)

    # Merge keys into other files
    for file_name in other_files:
        with open(file_name, 'r+') as f:
            data = json.load(f)
            for key in keys:
                if key not in data[file_name.split('.')[0]]:
                    data[file_name.split('.')[0]][key] = ""
            # Sort the keys alphabetically for each language
            data[file_name.split('.')[0]] = {k: data[file_name.split('.')[0]][k] for k in sorted(data[file_name.split('.')[0]].keys())}
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

if __name__ == "__main__":
    main_file = "en_us.json"
    other_files = ["de_de.json", "es_es.json", "fr_fr.json"]
    merge_translations(main_file, other_files)
