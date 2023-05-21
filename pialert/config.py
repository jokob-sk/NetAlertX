

global  mySettings, mySettingsSQLsafe
#-------------------------------------------------------------------------------
# Import user values
# Check config dictionary
def ccd(key, default, config, name, inputtype, options, group, events=[], desc = "", regex = ""):
    result = default

    # use existing value if already supplied, otherwise default value is used
    if key in config:
        result =  config[key]

    global mySettings

    if inputtype == 'text':
        result = result.replace('\'', "{s-quote}")

    mySettingsSQLsafe.append((key, name, desc, inputtype, options, regex, str(result), group, str(events)))
    mySettings.append((key, name, desc, inputtype, options, regex, result, group, str(events)))

    return result