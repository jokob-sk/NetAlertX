import io
import sys


#-------------------------------------------------------------------------------
def write_file (pPath, pText):
    # Write the text depending using the correct python version
    if sys.version_info < (3, 0):
        file = io.open (pPath , mode='w', encoding='utf-8')
        file.write ( pText.decode('unicode_escape') ) 
        file.close() 
    else:
        file = open (pPath, 'w', encoding='utf-8') 
        if pText is None:
            pText = ""
        file.write (pText) 
        file.close() 

#-------------------------------------------------------------------------------
def get_file_content(path):

    f = open(path, 'r') 
    content = f.read() 
    f.close() 

    return content  