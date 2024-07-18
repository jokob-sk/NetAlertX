import re

""""
how to rebuild and re-run...

savefolder=~/naxdev/NetAlertX.v7
cd ~/naxdev
mv NetAlertX $savefolder
gh repo clone FlyingToto/NetAlertX
cd NetAlertX
ln -s ../docker-compose.yml.ffsb42 .
ln -s ../.env.omada.ffsb42 .
cd front/plugins/omada_sdn_imp/
cp -p $savefoder/front/plugins/omada_sdn_imp/omada_sdn.py* .
cp -p $savefoder/front/plugins/omada_sdn_imp/README.md .
cp -p $savefoder/front/plugins/omada_sdn_imp/omada_account_sample.png .
cp -p $savefoder/front/plugins/omada_sdn_imp/testre.py .
#cp -p $savefoder/front/plugins/omada_sdn_imp/config.json config.json.v6
cd ~/naxdev/NetAlertX
sudo docker-compose --env-file .env.omada.ffsb42  -f ./docker-compose.yml.ffsb42  up

to gather data for Boris:
today=$(date +%Y_%m_%d__%H_%M)
mkdir /drives/c/temp/4boris/$today
cd  /drives/c/temp/4boris/$today
scp hal:~/naxdev/logs/app.log .
scp hal:~/naxdev/NetAlertX/front/plugins/omada_sdn_imp/* .
gzip -c app.log  > app_$today.log.gz


scp hal:~/naxdev/NetAlertX/front/plugins/omada_sdn_imp/omada_sdn.py /drives/c/temp/4boris/
"""




def extract_mac_addresses(text):
    mac_pattern = r"([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})"
    #mac_pattern = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
    #r"(([0-9A-F]{2}-){5}[0-9A-F]{2})"
    #r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"
    #r"([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})"
    mac_addresses = re.findall(mac_pattern, text)
    return ["".join(parts) for parts in mac_addresses]

# Example usage:
foo = """
Name: office
Address: 0C-80-63-69-C4-D1 (192.168.0.5)
Status: CONNECTED (CONNECTED)
Ports: 28
Supports PoE: False
Model: T1600G-28TS v3.0
LED Setting: SITE_SETTINGS
Uptime: 5day(s) 22h 39m 6s
Uplink switch: D8-07-B6-71-FF-7F office24
Downlink devices:
- 40-AE-30-A5-A7-50 ompapaoffice
- B0-95-75-46-0C-39 pantry12
"""

mac_list = extract_mac_addresses(foo)
print("mac list",mac_list)
# ['0C-80-63-69-C4-D1', 'D8-07-B6-71-FF-7F', '40-AE-30-A5-A7-50', 'B0-95-75-46-0C-39']
# ['C4-:D1', 'FF-:7F', 'A7-:50', '0C-:39']

linked_switches_and_ports_by_mac = {}


foo = """"
something
some BOB12
blah BOB23
--- BEGIN ---
something else BOB12
blah BOB23
--- END ---
"""
def extract_BOB_patterns(foo):
    pattern = r"BOB\d{2}(?=.*BEGIN)"
    matches = re.findall(pattern, foo, re.DOTALL)
    return matches

BOBresult = extract_BOB_patterns(foo)
print("BOB:",BOBresult)  # Output: ['BOB12', 'BOB23']


#0C-80-63-69-C4-D1 
clientmac_by_switchmac_by_switchportSSID = {}
switch_mac_and_ports_by_clientmac = {}

def extract_uplinks_mac_and_ports(tplink_device_dump):
    mac_switches = []
    mac_pattern = r"([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})(?=.*BEGIN)"
    mac_addresses = re.findall(mac_pattern, tplink_device_dump,re.DOTALL)
    mac_switches =  ["".join(parts) for parts in mac_addresses]
    print(" mac_switches1=",mac_switches)
    mymac = mac_switches[0]
    mylinks =  mac_switches[1:]
    for mylink in mylinks:
        port_pattern = r"(?=\{.*\"port\"\: )([0-9]+)(?=.*"+re.escape(mylink)+r")"
        port_pattern = r"(?:{/s\"port\"\: )([0-9]+)(?:[!\}].*"+re.escape(mylink)+r")"        
        #port_pattern = rf"{{.*?{found_mac}.*?port\s*:\s*(\d+).*?}}"
        #port_pattern = rf"{{.*?.*?port\s*:\s*(\d+)[!\\}]*{mylink}?}}"
        port_pattern = r"(?:\{[!\}]port/s:/s)([0-9]+\,)(?:[!\}]*"+re.escape(mylink)+r"[!\{]*\})"        
        #port_pattern = r"(?:\{.*\"port\"\: )([0-9]+)(?=.*"+re.escape(mylink)+r")"
        port_pattern = r"(?:{[^}]*\"port\"\: )([0-9]+)(?=[^}]*"+re.escape(mylink)+r")"
        
        myport = re.findall(port_pattern, tplink_device_dump,re.DOTALL)
        print("myswitch=",mymac, "- link_switch=", mylink, "myport=", myport) 
    return(0)


'''
with open('/tmp/switch.bigroom.dump.json', 'r') as file:
    foo3 = file_content = file.read()
print("bigroom", end="")
extract_uplinks_mac_and_ports(foo3)
with open('/tmp/switch.office.dump.json', 'r') as file:
    foo4 = file_content = file.read()
print("office", end="")
extract_uplinks_mac_and_ports(foo4)
'''

import netifaces
gw = netifaces.gateways()
print(gw['default'][netifaces.AF_INET][0])


d = {'a': ['0', 'Arthur'], 'b': ['foo', 'Belling']}

print(d.items())
print(d.keys())
print(d.values())


foo = 2
#while foo > 0:
#    foo = 'toto'
print("foo is ",foo)

if foo in ( 'bar', '', 'null'):
    print("foo is bar")
else:
    print("foo is not bar")

foo='192-168-0-150.local'
bar = foo.split('.')[0]
print("bar=",bar,"-")
bar2 = 'toto'
print("bar2=",bar2,"-")



import concurrent.futures
import time
import random

def phello(arg):
    print('running phell',arg)
    delay = random.uniform(0, 6)
    time.sleep(delay)
    return f"parallel hello : {arg}", delay

def testparalel():
    arguments = ["Alice", "Bob", "Charlie", "David"]
    results = {}
    results2 = {}
    para = 10

    # Using ThreadPoolExecutor for parallel execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=para) as executor:
        # Submit tasks to the executor
        future_to_arg = {executor.submit(phello, arg): arg for arg in arguments}
        
        # Wait for all futures to complete
        done, _ = concurrent.futures.wait(future_to_arg)

        # Retrieve results
        for future in done:
            arg = future_to_arg[future]
            try:
                result, result2 = future.result()
                results[arg] = result
                results2[arg] = result2
            except Exception as exc:
                print(f"{arg} generated an exception: {exc}")

    # Print results after all threads have completed
    print("All threads completed. Results:")
    for arg, result in results.items():
        print(f"arg:{arg}, result={results[arg]}, result2={results2[arg]}")


testparalel()