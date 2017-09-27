#!/usr/bin/env python
import smtplib, sys, getopt, fileinput

def getemail(): #Gets email info stored in file
	with open('/mnt/data/XPLANE/XSDK/creds.txt', 'r') as f:
		srvr=f.readline().strip()
		addr=f.readline().strip()
		passw=f.readline().strip()
		addrto=f.readline().strip()
		return srvr,addrto,addr,passw

def sendemail(subj,msg): #Sends email
	srvr,addrto,addr,passw=getemail()
	message="""\From: %s\nTo: %s\nSubject: %s\n\n%s""" % (addr, addr, subj, msg)
	try:
		#print("Sending mail from "+addr+" to "+addrto)
		server=smtplib.SMTP_SSL(srvr, 465)
		server.ehlo()
		server.login(addr,passw)
		server.sendmail(addr,addrto,message)
		server.close()
		#print("Successfully sent the mail:")
	except:
		#e = sys.exc_info()[0]
		print("Failed to send the mail with error:")
		#print(e)

def main(argv): #This is where the magic happens
	syntaxstring=("sysemail.py <subject> <body>")
	try:
		subject=sys.argv[1]
		body=fileinput.input(sys.argv[2:])
	except getopt.GetoptError:
		print(syntaxstring)
		sys.exit(2)

	#for opt, arg in opts:
	#	if opt in ("-s", "--subject"): #Plots average prices for type
	#		subject=arg
	#	elif opt in ("-b", "--body"): #Plots the cheapest aircraft of this type
	#		body=arg

	print("Running...")

	print(subject)

	msg=""
	for line in body:
		msg=msg+line
	print(msg)
	sendemail(subject,msg)

	print("Finished!")

if __name__ == "__main__":
   main(sys.argv[1:])

# Scrub the second Sunday of every month.
#24 0 15-21 * * root [ $(date +\%w) -eq 0 ] && [ -x /bin/btrfs ] && /bin/btrfs scrub start -B /
