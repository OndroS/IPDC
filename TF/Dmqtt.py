import subprocess
from subprocess import Popen
import paho.mqtt.client as mqtt
import os
import json
import time
import threading

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata,flags_dict, rc):
	client.subscribe("test")
	client.subscribe("Download")
	client.subscribe("RunCluster")
	client.subscribe("CloseCluster")
	client.subscribe("CleanUp")
	client.subscribe("PortalConnect")

def Publish(target,channel,message):
	client = mqtt.Client()
	client.max_inflight_messages_set(200000)
	client.connect(target, 1883)
	(rc, mid) = client.publish(channel, message, qos=1)
	#time.sleep(0.01)
	print "DMQTT RESULT : "+str(rc)

def Download(message):
	# format : Fhash###Fname
	print "CallDownload : "+message
	tmp = message.split("###")
	Fhash = tmp[0]
	Fname = tmp[1]
	os.system("timeout 10 ipfs get "+Fhash+" -o /tmp/"+Fname)

def RunCluster(message,client):
        print "RunCluster : "+message
        cmd = "python /tmp/create_worker.py "+message
        try:
            p = Popen(cmd.split())
            client.WorkerPID = str(p.pid)
        except Exception as e:
            print "CREATE WORKER ERROR"

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	if msg.topic=='test':
		print str(msg.payload)
	elif msg.topic=="Download":
		Download(str(msg.payload))
	elif msg.topic=="RunCluster":
		RCthread = threading.Thread(target=RunCluster, name="RunCluster", args=(str(msg.payload),client))
		RCthread.setDaemon = True
		RCthread.start()
	elif msg.topic=="CloseCluster":
		os.system("kill -9 "+client.WorkerPID)
		print "KEVIN KILLED "+client.WorkerPID
		client.WorkerPID = ""
	elif msg.topic=="PortalConnect":
		ConnectIpList = str(msg.payload).split("###")
		for x in ConnectIpList:
			if x == "":continue
			cmd = "ipfs swarm connect "+x
			try:
				cmd = "ipfs id -f='<id>'"
				peerID = subprocess.check_output(cmd, shell=True)
				if peerID in x: # Can't connect to himself
					print "\n\nWelcome to be a Domain Portal.\nPlease press Enter!"
					continue
				cmd = "ipfs swarm connect "+x
				output = subprocess.check_output(cmd, shell=True)
				if "success" in output:
					RemoteIP = x.split("/")[2]
					Publish(RemoteIP,"test","\n\nSuccess to connect with Portal.\nPlease press Enter!")
					break
			except:
				pass
	elif msg.topic=="CleanUp":
		os.system("rm Map.py* Reduce.py* output.txt data.dat")
	#time.sleep(0.01)

client = mqtt.Client()
client.WorkerPID = ""
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 0)
client.loop_forever()
