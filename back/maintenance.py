import sys
import shutil
import subprocess


def main ():    

    argument = str(sys.argv[1])

    ## Main Commands
    if argument == 'backup_db':
        res = backup_db()
        print(res)

    if argument == 'restore_db':
        res = restore_db()

def backup_db ():
    # Header    
    shutil.copyfile("/home/pi/pialert/db/pialert.db", "/home/pi/pialert/config/pialert.db_bak")


def restore_db ():
    # Header
    shutil.copyfile("/home/pi/pialert/config/pialert.db_bak", "/home/pi/pialert/db/pialert.db")


#===============================================================================
# BEGIN
#===============================================================================
if __name__ == '__main__':
    sys.exit(main())   