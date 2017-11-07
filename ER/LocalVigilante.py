import json
import os
import paho.mqtt.client as mqtt
import sqlite3
import subprocess
import time

# db initial
DbPath = "/tmp/.db"
conn = sqlite3.connect(DbPath+"/chain.db")
c = conn.cursor()
c.execute("create table if not exists keystore(peerID text, Kname text,Khash text, PRIMARY KEY(peerID,Kname))")
conn.commit()

# Load Node set of chain
def GetChainNodeSet():
    Jobject = ""
    ChainNodeSet = set()
    f = open("/tmp/Ohash","r")
    while True:
        line = f.readline()
        if not line:
            break
        cmd = "timeout 10 ipfs object get "+line
        Jobject = json.loads(subprocess.check_output(cmd, shell=True))
        for x in Jobject['Links']:
            if "node-" in x['Name']:
                ChainNodeSet.add(x['Name'].split("###")[1])
        return ChainNodeSet
    return "ERROR"

def Publish(target, channel, message):
	client = mqtt.Client()
	client.max_inflight_messages_set(200000)
        client.connect(target, 1883)
        client.loop_start()
        msg_info = client.publish(channel, message, qos=1)
        if msg_info.is_published() == False:
        	msg_info.wait_for_publish()
	client.disconnect()

def LoadDescription():
    Ddict = dict()
    f = open('/tmp/description.conf','r')
    while True:
        line = f.readline()
        if not line:
                break
        tmp = line.split("=")
        try:
                for i in range(len(tmp)):
                        if tmp[0] == "description":
                                tmp[i] = tmp[i].replace("\n","")
                                continue
                        tmp[i] = tmp[i].replace(" ","")
                        tmp[i] = tmp[i].replace("\n","")
                        tmp[i] = tmp[i].replace("\t","")
                tmp[0] = tmp[0].lower()
                Ddict[tmp[0]] = tmp[1]
        except:
                continue
    return Ddict

def GetKhash():
        Ddict = LoadDescription()
        cmd = "timeout 300 ipfs add -r createChain/"+Ddict['chainname']+"/keystore"
        Klist = subprocess.check_output(cmd, shell=True).split("\n")
	for x in Klist:
		try:
			tmp = x.split(" ")
			if tmp[2] == "keystore":
				return tmp[1]
		except:
			pass
	return "ERROR"

def GetPeerID():
	cmd = "timeout 10 ipfs id -f='<id>'"
	peerID = subprocess.check_output(cmd, shell=True)
	return peerID

def CheckKhash(peerID):
	global c
	Khash = c.execute("select Khash from keystore where peerID = '"+peerID+"' and Kname = 'keystore'")
	for x in Khash:
		return x[0]
	return "ERROR"

# Check createChain
while True:
    Flist = os.listdir("/tmp")
    if "createChain" in Flist:
        break
    else:
        print "waiting for createChain"
    time.sleep(1)

peerID = GetPeerID()
OldKhash = "TaiwanNumberOne"
'''
try:
    c.execute("delete from keystore")
    conn.commit()
    c.execute("insert into keystore values('"+peerID+"','"+OldKhash+"')")	
    conn.commit()
    CNset = GetChainNodeSet()
    for x in CNset:
        Publish(x,"KeyStore","insert###"+peerID+"###"+OldKhash)
except:
    pass
'''
while True:
	# Update Khash
	NewKhash = GetKhash()
	if OldKhash != NewKhash:
		c.execute("INSERT OR REPLACE INTO keystore values('"+peerID+"','keystore','"+NewKhash+"')")
		conn.commit()
                CNset = GetChainNodeSet()
                for x in CNset:
                    Publish(x,"KeyStore",peerID+"###keystore###"+NewKhash)
		OldKhash = NewKhash
	time.sleep(1)
