 
from time import sleep, time, strftime
import sys
import pathlib

# -------------------------------------------------------------------
class Plugin_Object:
    def __init__(
        self,
        primaryId="",
        secondaryId="",
        watched1="",
        watched2="",
        watched3="",
        watched4="",
        extra="",
        foreignKey=""
    ):
        self.pluginPref = ""
        self.primaryId = primaryId
        self.secondaryId = secondaryId
        self.created = strftime("%Y-%m-%d %H:%M:%S")
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
        line = ("{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(
                                                self.primaryId,
                                                self.secondaryId,
                                                self.created,                                                
                                                self.watched1,
                                                self.watched2,
                                                self.watched3,
                                                self.watched4,
                                                self.extra,
                                                self.foreignKey
                                                )
        )
        return line
    


class Plugin_Objects:
    def __init__(self, result_file):
        self.result_file = result_file 
        self.objects = []

    def add_object ( self, primaryId="",
        secondaryId="",
        watched1="",
        watched2="",
        watched3="",
        watched4="",
        extra="",
        foreignKey="" ):

        self.objects.append(Plugin_Object(primaryId,
        secondaryId,
        watched1,
        watched2,
        watched3,
        watched4,
        extra,
        foreignKey)
        )


    def write_result_file(self):

        with open(self.result_file, mode='w') as fp:
            for obj in self.objects:
                fp.write ( obj.write() )
        fp.close()
        
