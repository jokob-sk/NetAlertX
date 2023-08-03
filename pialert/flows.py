import json

def update_value(json_data, object_path, key, value, target_property, desired_value):
    # Helper function to traverse the JSON structure and get the target object
    def traverse(obj, path):
        keys = path.split(".")
        for key in keys:
            if isinstance(obj, list):
                key = int(key)
            obj = obj[key]
        return obj

    # Helper function to update the target property with the desired value
    def update(obj, path, key, value, target_property, desired_value):
        keys = path.split(".")
        for i, key in enumerate(keys):
            if isinstance(obj, list):
                key = int(key)
            # Check if we have reached the desired object
            if i == len(keys) - 1 and obj[key][key] == value:
                # Update the target property with the desired value
                obj[key][target_property] = desired_value
            else:
                obj = obj[key]
        return obj

    # Get the target object based on the object path
    target_obj = traverse(json_data, object_path)
    # Update the value in the target object
    updated_obj = update(json_data, object_path, key, value, target_property, desired_value)
    return updated_obj