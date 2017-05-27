# -*- coding: utf-8 -*-
import os,subprocess,time,threading,sys,pyspeedtest,urllib,sys,sendnoti
#import RPi.GPIO as GPIO
import mission
import time
missons=[False,False]
#GPIO.setwarnings(False)
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(14, GPIO.OUT)

from yowsup.layers.interface                           import YowInterfaceLayer                 #Reply to the message
from yowsup.layers.interface                           import ProtocolEntityCallback            #Reply to the message
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity         #Body message
from yowsup.layers.protocol_presence.protocolentities  import AvailablePresenceProtocolEntity   #Online
from yowsup.layers.protocol_presence.protocolentities  import UnavailablePresenceProtocolEntity #Offline
from yowsup.layers.protocol_presence.protocolentities  import PresenceProtocolEntity            #Name presence
from yowsup.layers.protocol_chatstate.protocolentities import OutgoingChatstateProtocolEntity   #is writing, writing pause
from yowsup.common.tools                               import Jid                               #is writing, writing pause
from yowsup.layers.protocol_media.protocolentities     import *
from yowsup.layers.protocol_media.mediauploader        import MediaUploader
from yowsup.layers.network import YowNetworkLayer
#from yowsup.layers.protocol_media.picture import YowMediaPictureLayer                             
from yowsup.layers.protocol_media.mediadownloader      import MediaDownloader
from yowsup.layers.auth import YowAuthenticationProtocolLayer
import sys, shutil, logging, mimetypes
#Log, but only creates the file and writes only if you kill by hand from the console (CTRL + C)
#import sys
#class Logger(object):
#    def __init__(self, filename="Default.log"):
#        self.terminal = sys.stdout
#        self.log = open(filename, "a")
#
#    def write(self, message):
#        self.terminal.write(message)
#        self.log.write(message)
#sys.stdout = Logger("/1.txt")
#print "Hello world !" # this is should be saved in yourlogfilename.txt
#------------#------------#------------#------------#------------#------------

allowedPersons=['xxxxxxxxxxx','xxxxxxxxxxx'] #Filter the senders numbers
ap = set(allowedPersons)
#global textmsg
#textmsg    = TextMessageProtocolEntity
name = "NAMEPRESENCE"
filelog = "/root/.yowsup/Not allowed.log"

class EchoLayer(YowInterfaceLayer):
    ackQueue = []
    lock = threading.Condition()
    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        #print messageProtocolEntity
        if messageProtocolEntity.getType() == 'text':
            time.sleep(0.5)
        elif messageProtocolEntity.getType() == 'media':
            time.sleep(0.5)
        time.sleep(0.5)
        self.toLower(messageProtocolEntity.ack()) #Set received (double v)
        time.sleep(0.5)
        self.toLower(PresenceProtocolEntity(name = name)) #Set name Presence
        time.sleep(0.5)
        self.toLower(AvailablePresenceProtocolEntity()) #Set online
        time.sleep(0.5)
        self.toLower(messageProtocolEntity.ack(True)) #Set read (double v blue)
        time.sleep(0.5)
        self.toLower(OutgoingChatstateProtocolEntity(OutgoingChatstateProtocolEntity.STATE_TYPING, Jid.normalize(messageProtocolEntity.getFrom(False)) )) #Set is writing
        time.sleep(2)
        self.toLower(OutgoingChatstateProtocolEntity(OutgoingChatstateProtocolEntity.STATE_PAUSED, Jid.normalize(messageProtocolEntity.getFrom(False)) )) #Set no is writing
        time.sleep(1)
        self.onTextMessage(messageProtocolEntity) #Send the answer
        time.sleep(3)
        self.toLower(UnavailablePresenceProtocolEntity()) #Set offline

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        print entity.ack()
        self.toLower(entity.ack())
    def onMediaMessage(self, messageProtocolEntity):
        if messageProtocolEntity.getMediaType() == "image":
            url = messageProtocolEntity.url
            self.extension = self.getExtension(messageProtocolEntity.getMimeType())
            return self.downloadMedia(url)

    def downloadMedia(self, url):
        print("Downloading %s" % url)
        downloader = MediaDownloader(self.onSuccess, self.onError, self.onProgress)
        downloader.download(url)

    def onError(self):
        logger.error("Error download file")

    def onSuccess(self, path):
        outPath = "/root/%s%s" % (os.path.basename(path), self.extension)
        shutil.copyfile(path, outPath)
        print("\nPicture downloaded to %s" % outPath)

    def onProgress(self, progress):
        sys.stdout.write("Download progress => %d%% \r" % progress)
        sys.stdout.flush()

    def getExtension(self, mimetype):
        type = mimetypes.guess_extension(mimetype.split(';')[0])
        if type is None:
            raise Exception("Unsupported/unrecognized mimetype: "+mimetype);
        return type

    def image_send(self, number, path, caption = None):
        jid = number
        mediaType = "image"
        entity = RequestUploadIqProtocolEntity(mediaType, filePath = path)
        successFn = lambda successEntity, originalEntity: self.onRequestUploadResult(jid, mediaType, path, successEntity, originalEntity, caption)
        errorFn = lambda errorEntity, originalEntity: self.onRequestUploadError(jid, path, errorEntity, originalEntity)
        self._sendIq(entity, successFn, errorFn)

    def doSendMedia(self, mediaType, filePath, url, to, ip = None, caption = None):
        entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(filePath, url, ip, to, caption = caption)
        self.toLower(entity)

    def onRequestUploadResult(self, jid, mediaType, filePath, resultRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity, caption = None):
        if resultRequestUploadIqProtocolEntity.isDuplicate():
            self.doSendMedia(mediaType, filePath, resultRequestUploadIqProtocolEntity.getUrl(), jid,
                             resultRequestUploadIqProtocolEntity.getIp(), caption)
        else:
            successFn = lambda filePath, jid, url: self.doSendMedia(mediaType, filePath, url, jid, resultRequestUploadIqProtocolEntity.getIp(), caption)
            mediaUploader = MediaUploader(jid, self.getOwnJid(), filePath,
            resultRequestUploadIqProtocolEntity.getUrl(),
            resultRequestUploadIqProtocolEntity.getResumeOffset(),
            successFn, self.onUploadError, self.onUploadProgress, async=False)
            mediaUploader.start()

    def onRequestUploadError(self, jid, path, errorRequestUploadIqProtocolEntity, requestUploadIqProtocolEntity):
        logger.error("Request upload for file %s for %s failed" % (path, jid))

    def onUploadError(self, filePath, jid, url):
        logger.error("Upload file %s to %s for %s failed!" % (filePath, url, jid))

    def onUploadProgress(self, filePath, jid, url, progress):
        sys.stdout.write("%s => %s, %d%% \r" % (os.path.basename(filePath), jid, progress))
        sys.stdout.flush()
    def normalizeJid(self, number):
        if '@' in number:
            return number
        return "%s@s.whatsapp.net" % number
    def onTextMessage(self,messageProtocolEntity):        
        if messageProtocolEntity.getType() == 'text':
            message    = messageProtocolEntity.getBody().lower()
            print(message)            
        elif messageProtocolEntity.getType() == 'media':
            message    = messageProtocolEntity.getMediaType()        
        namemitt   = messageProtocolEntity.getNotify()
        recipient  = messageProtocolEntity.getFrom()        
        textmsg    = TextMessageProtocolEntity
        out_file = open(filelog,"a")
        out_file.write("------------------------"+"\n"+"Sender:"+"\n"+namemitt+"\n"+"Number sender:"+"\n"+recipient+"\n"+"Message text:"+"\n"+message+"\n"+"------------------------"+"\n"+"\n")
        out_file.close()
        #For a break to use the character \n
        #The sleep you write so
##        time.sleep(1)

        if messageProtocolEntity.getFrom(False)<>"xxxxxx":
            if message == 'hi':
                answer = "Hi "+namemitt+". What can i do for you today?\n-cv\n-aboutme\n-skills\n-temperature\n-speedtest\n-projects"                
                self.toLower(textmsg(answer, to = recipient ))
                #self.toLower(textmsg(answer, to = recipient ))
                print answer              
            elif message == '-list':
                answer = "Hi "+namemitt+"\n\nYou can ask me these things:\n-cv\n-aboutme\n-skills\n-temperature\n-speedtest\n-projects"
                self.toLower(textmsg(answer, to = recipient ))
                print answer
            elif message == 'temperature' or message == '-temperature':
                t=float(subprocess.check_output(["/opt/vc/bin/vcgencmd measure_temp | cut -c6-9"], shell=True)[:-1])
                ts=str(t)
                answer = 'My Raspberry Pi CPU temperature is '+ts+' °C'
                self.toLower(textmsg(answer, to = recipient ))
                print answer
            elif message == 'speedtest' or message == '-speedtest':
                try:
                    st = pyspeedtest.SpeedTest()
                    ping=st.ping()
                    #print ping
                    #print "%.2f" % down
                    #print up
                    answer="My ping is %.1f " % ping
                    self.toLower(textmsg(answer, to = recipient ))
                    down=st.download()/1000000
                    answer="My download speed is %.2f mbps" % down
                    self.toLower(textmsg(answer, to = recipient ))
                    up=st.upload()/1000000
                    answer="My upload speed is %.2f mbps" % up
                    self.toLower(textmsg(answer, to = recipient ))
                    #print answer
                except:
                    answer="low speed can not connect server"
                    self.toLower(textmsg(answer, to = recipient ))
            elif message == 'restart' and messageProtocolEntity.getFrom(False)=="905073648830":
                answer = "Ok "+namemitt+", rebooting. Bye bye."
                self.toLower(textmsg(answer, to = recipient ))
                print answer
                time.sleep(3)
                self.toLower(UnavailablePresenceProtocolEntity())
                time.sleep(2)
                os.system('sudo reboot')
            elif message == 'ip' and messageProtocolEntity.getFrom(False)=="905073648830":
                try:
                    external_ip = urllib.urlopen('https://api.ipify.org/').read()
                    answer = "My ip address is %s " % (external_ip)
                    self.toLower(textmsg(answer, to = recipient ))
                except:
                    answer = "couldn't connect server"
                    self.toLower(textmsg(answer, to = recipient ))
            elif message == '-cv' or message == 'cv' :
                answer = "https://drive.google.com/file/d/0B7VfVk5mxGRrWHZ0SnItUTM2UGM/view" 
                self.toLower(textmsg(answer, to = recipient ))
                print answer
                #path = "/home/pi/Desktop/olcak/file/CV.jpg"
                #self.image_send(recipient, path)
                answer = "Here is my CV" 
                self.toLower(textmsg(answer, to = recipient ))
            elif message == 'position':
                answer = "Hi "+namemitt+", here is the position you asked me." 
                self.toLower(textmsg(answer, to = recipient ))
                print answer
                latitude="38.5167447" # from -90 to 90, positive means north and negative means south
                longitude="27.2405762" # from -180 to 180, positive means east and negative means west
                locationName="My Lovely house" # optional, the first line will become a clickable link, the second won't
                locationURL="https://www.google.com.tr/maps/@38.5167447,27.2405762,596m/data=!3m1!1e3?hl=sg" # optional, this is the link you'll be redirected when you click the locationName
                locationEncoding="raw"
                outLocation = (LocationMediaMessageProtocolEntity(latitude, longitude, locationName, locationURL, locationEncoding, to = recipient ))
                self.toLower(outLocation)
            elif message == '-aboutme' or message == 'aboutme':
                answer = "Hi! My name is Kutluhan Buyukburc and I am graduating from Ceylal Bayar University this June, with a Bachelor's degree in Electrical and Electronic Engineering. I enjoy playing chess (I won several chess competitions in my state when I was in high school!), going to the gym, and creating codes for Internet of things. I especially like creating codes that are useful to me and"
                answer=answer + "the people around me, such as a notification application for the online game Travian, and also an application which allows me to watch youtube videos while working on other programs on my computer. I am from Izmir, Turkey and I wish to seek employment in Singapore. Aside from my personal reasons for moving, I also find Singapore to be technologically advanced (way more than Turkey) and I am very intrigued by some technology that I observed while I was in Singapore. My favourite place in Singapore is the Night Safari and my favourite food would definitely be Chicken Rice =)"
                #answer=answer + ""
                self.toLower(textmsg(answer, to = recipient ))
            elif message == '-projects' or message == 'projects':
                answer="https://github.com/kbuyukburc\nYou can find my projects$"
                self.toLower(textmsg(answer, to = recipient ))
            elif message == '-skills' or message == 'skills':
                answer="PIC programing\nPLC programing\nLinux and Raspberry Pi knowledge\nC/C++ Python VB.net Asp.net PHP programing and SQL database knowledge\nAlso I have knowledge of finding vulnerabilities with Kali Linux tools"                
                self.toLower(textmsg(answer, to = recipient ))
                #GPIO.output(14, True) # Pin 2 in up
                #answer = "Ok, il GPIO14 è su true"
                #self.toLower(textmsg(answer, to = recipient ))
                #print answer
            #elif message == 'off gpio14':
                #GPIO.output(14, False) # Pin 2 in down
                #answer = "Ok, il GPIO14 è su false"
                #self.toLower(textmsg(answer, to = recipient ))
                #print answer
            #elif message == "image":
             #   print("Echoing image %s to %s" % (messageProtocolEntity.url, messageProtocolEntity.getFrom(False)))
              #  answer = "Hi "+namemitt+", thank you for sending me your picture."
              #  self.toLower(textmsg(answer, to = recipient ))
              #  self.onMediaMessage(messageProtocolEntity)
              #  print answer
            #elif message == "location":
             #   print("Echoing location (%s, %s) to %s" % (messageProtocolEntity.getLatitude(), messageProtocolEntity.getLongitude(), messageProtocolEntity.getFrom(False)))
              #  answer = "Hi "+namemitt+", thank you for sending me your geolocation."
              #  self.toLower(textmsg(answer, to = recipient ))
               # print answer
            #elif message == "vcard":
             #   print("Echoing vcard (%s, %s) to %s" % (messageProtocolEntity.getName(), messageProtocolEntity.getCardData(), messageProtocolEntity.getFrom(False)))
              #  answer = "Hi "+namemitt+", thank you for sending me your contact."
              #  self.toLower(textmsg(answer, to = recipient ))
              #  print answer
            else:
                answer = "Sorry "+namemitt+", I can not understand what you're asking me..\nCould you please write one of the following\n-cv\n-aboutme\n-skills\n-temperature\n-speedtest\n-projects " 
                self.toLower(textmsg(answer, to = recipient))
                print answer                
        elif messageProtocolEntity.getFrom(False)=="xxxxxxxx":
            answer = "nevar amk"
            self.toLower(textmsg(answer, to = recipient))
            print answer
        else:
            answer = "Hi "+namemitt+", I'm sorry, I do not want to be rude, but I can not chat with you..\n-cv\n-aboutme\n-skills\n-temperature\n-speedtest\n-projects"
            #time.sleep(2)
            self.toLower(textmsg(answer, to = recipient))
            print answer
            #out_file = open(filelog,"a")
            #out_file.write("------------------------"+"\n"+"Sender:"+"\n"+namemitt+"\n"+"Number sender:"+"\n"+recipient+"\n"+"Message text:"+"\n"+message+"\n"+"------------------------"+"\n"+"\n")
            #out_file.close()
reload(sys)
sys.setdefaultencoding('utf8')
#thread1 = myThread()
#thread1.start()
