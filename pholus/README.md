# INFO
For anyone reading, `pholus.py` is not actively developed as this project only uses `pholus3.py`. 

# Pholus
A multicast DNS and DNS Service Discovery Security Assessment Tool
It can perform recconnaisance, Denial of Service, Man in the Middle attacks

## Scan passively
Scan passively (for amount of timeout)
python pholus3.py eth0 -stimeout 60

## Discovery of available services
Sends a DNS query for PTR records with the name "_services._dns-sd._udp.<Domain>"; 
this  yields a set of PTR records where the rdata of each PTR record is the two-label
<Service> name plus the same domain, e.g., "_http._tcp.<Domain>". 
By sending such a query, we can automatically discover all the services advertised in the network. 

python pholus3.py eth0 -sscan

#If you want to perform the scan both for IPv4 and IPv6:
python pholus3.py eth0 -sscan -4 -6

#You can also spoof the souce address to perform this reconnaissance in a stealthy way.
python pholus3.py eth0 -sscan -s4 192.168.2.30

## Send mdns request 
python pholus3.py eth0 --request

## Perform a scan using reverse mDNS by providing a subnet
python pholus3.py eth0 -rdns_scanning 192.168.2.0/24

## Send automatically fake responses
python pholus3.py eth0 -afre -stimeout 100

## further MiTM (and other) capabilities  
use --help to identify specific spoofing capabilities for MiTM purposes, eg -printer)  
  
## Read a pcap file and pring mDNS info (no sudo/root required)
python pholus3.py ../mdns_traffic.pcap --readpcap
