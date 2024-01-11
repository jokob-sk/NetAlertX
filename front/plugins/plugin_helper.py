from time import strftime
import pytz
import sys
import re
import base64
from datetime import datetime

sys.path.append("/home/pi/pialert/front/plugins")
sys.path.append('/home/pi/pialert/pialert') 

from logger import mylog

#-------------------------------------------------------------------------------
def read_config_file():
    """
    retuns dict on the config file key:value pairs
    config_dir[key]
    """

    filename = '/home/pi/pialert/config/pialert.conf'


    print('[plugin_helper] reading config file')
    # load the variables from  pialert.conf
    with open(filename, "r") as file:
        code = compile(file.read(), filename, "exec")

    confDict = {} # config dictionary
    exec(code, {"__builtins__": {}}, confDict)
    return confDict 


pialertConfigFile = read_config_file()
timeZoneSetting = pialertConfigFile['TIMEZONE']
timeZone = pytz.timezone(timeZoneSetting)

# -------------------------------------------------------------------
def handleEmpty(input):
    if input == '' or None:
        return 'null'
    else:
        # Validate and sanitize message content
        # Remove potentially problematic characters if string
        if isinstance(input, str):  
            input = re.sub(r'[^\x00-\x7F]+', ' ', input)
        return  input

# -------------------------------------------------------------------
# Check if a valid MAC address
def is_mac(input):
    return re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", input.lower())

# -------------------------------------------------------------------
def decodeBase64(inputParamBase64):

    # Printing the input list to check its content.
    mylog('debug', ['[Plugins] Helper base64 input: ', input]) 
    print('[Plugins] Helper base64 input: ') 
    print(input) 
    

    # Extract the base64-encoded subnet information from the first element 
    # The format of the element is assumed to be like 'param=b<base64-encoded-data>'.      

    # Printing the extracted base64-encoded information.
    mylog('debug', ['[Plugins] Helper base64 inputParamBase64: ', inputParamBase64]) 
    

    # Decode the base64-encoded subnet information to get the actual subnet information in ASCII format.
    result = base64.b64decode(inputParamBase64).decode('ascii')

    # Print the decoded subnet information.
    mylog('debug', ['[Plugins] Helper base64 result: ', result]) 

    return result


# -------------------------------------------------------------------
class Plugin_Object:
    """ 
    Plugin_Object class to manage one object introduced by the plugin
    An object typically is a device but could also be a website or something 
    else that is monitored by the plugin.
    """

    def __init__(
        self,
        primaryId="",
        secondaryId="",
        watched1="",
        watched2="",
        watched3="",
        watched4="",
        extra="",
        foreignKey="",
    ):
        self.pluginPref = ""
        self.primaryId = primaryId
        self.secondaryId = secondaryId
        self.created = datetime.now(timeZone).strftime("%Y-%m-%d %H:%M:%S")
        self.changed = ""
        self.watched1 = watched1
        self.watched2 = watched2
        self.watched3 = watched3
        self.watched4 = watched4
        self.status = ""
        self.extra = extra
        self.userData = ""
        self.foreignKey = foreignKey

    def write(self):
        """ 
        write the object details as a string in the 
        format required to write the result file
        """
        line = "{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(
            self.primaryId,
            self.secondaryId,
            self.created,
            self.watched1,
            self.watched2,
            self.watched3,
            self.watched4,
            self.extra,
            self.foreignKey,
        )
        return line
    


class Plugin_Objects:
    """
    Plugin_Objects is the class that manages and holds all the objects created by the plugin.
    It contains a list of Plugin_Object instances.
    And can write the required result file.
    """
    
    def __init__(self, result_file):
        self.result_file = result_file
        self.objects = []

    def add_object(
        self,
        primaryId="",
        secondaryId="",
        watched1="",
        watched2="",
        watched3="",
        watched4="",
        extra="",
        foreignKey="",
    ):
        self.objects.append(
            Plugin_Object(
                primaryId,
                secondaryId,
                watched1,
                watched2,
                watched3,
                watched4,
                extra,
                foreignKey,
            )
        )

    def write_result_file(self):
        # print ("writing file: "+self.result_file)
        with open(self.result_file, mode="w") as fp:
            for obj in self.objects:
                fp.write(obj.write())
        fp.close()


    def __add__(self, other):
        if isinstance(other, Plugin_Objects):
            new_objects = self.objects + other.objects
            new_result_file = self.result_file  # You might want to adjust this
            new_instance = Plugin_Objects(new_result_file)
            new_instance.objects = new_objects
            return new_instance
        else:
            raise TypeError("Unsupported operand type for +")

    def __len__(self):
        return len(self.objects)




