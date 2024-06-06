import json
import os
import sys

def merge_translations(main_file, other_files):
    # Load main file
    with open(main_file, 'r') as f:
        main_data = json.load(f)

    # Get keys and sort them alphabetically
    keys = sorted(main_data.keys())

    # Sort the keys alphabetically in the main file
    main_data = {k: main_data[k] for k in keys}

    # Rewrite sorted main file
    with open(main_file, 'w') as f:
        json.dump(main_data, f, indent=4)

    # Merge keys into other files
    for file_name in other_files:
        with open(file_name, 'r+') as f:
            data = json.load(f)
            for key in keys:
                if key not in data:
                    data[key] = ""
            # Sort the keys alphabetically for each language
            data = {k: data[k] for k in sorted(data.keys())}
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

if __name__ == "__main__":
    current_path = os.path.dirname(os.path.abspath(__file__))
    # language codes can be found here: http://www.lingoes.net/en/translator/langcode.htm
    json_files = ["en_us.json", "de_de.json", "es_es.json", "fr_fr.json", "nb_no.json", "ru_ru.json", "it_it.json", "pt_br.json", "pl_pl.json", "zh_cn.json", "tr_tr.json"]
    file_paths = [os.path.join(current_path, file) for file in json_files]
    merge_translations(file_paths[0], file_paths[1:])
