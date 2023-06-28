import session_level
import sectors
from simp_aes import *
import sessions
import rsa
import aes
import os
import message as msglib
import time
import loading

def gen_chathash(passwd):
    return hashlib.sha256(passwd*3+b'salt').hexdigest().encode()
    
class User:
    def __init__(self,ip,username,password):
        if not ip:
            ip = '185.117.155.43'
            
        if not os.path.exists(username):
            os.mkdir(username)

        if not os.path.exists(username+'/'+username):
            print('[!] Session generation is started! It can take >10 mins!')
            data = sessions.gen_session(password)
            open(username+'/'+username,'wb').write(data)
        data = open(username+'/'+username,'rb').read()    
        try:
            self.keys = sessions.get_session(data,password)
        except:
            print('[-] You entered wrong passcode!!!')
            time.sleep(3)
        self.keys = sessions.get_session(data,password)
        self.conn = session_level.session(proxy=session_level.getproxy())
        self.conn.connect(ip,2025)
        self.session_key = b''
        self.username = username.encode()
        try:
            self.load(password)
        except:
            filenames = ['initinf','messages','keybase','rejected','invites','rn']
            for i in filenames:
                try:
                    os.remove(f'{self.username.decode()}/{i}.txt')
                except Exception as e:
                    print('[-]',e)
                self.load(password)
                
    def load(self,password):
        username = self.username.decode()
        self.initinf = sectors.sectorstype(username+'/initinf.txt',password)
        self.messages = sectors.sectorstype(username+'/messages.txt',password)
        self.keybase = sectors.sectorstype(username+'/keybase.txt',password)
        self.rejected = sectors.sectorstype(username+'/rejected.txt')
        self.invites = sectors.sectorstype(username+'/invites.txt',password)
        self.initinf.load()
        self.messages.load()
        self.keybase.load()
        self.rejected.load()
        self.invites.load()
        
    def recv(self):
        data = self.conn.recv()
        while not data:
            data = self.conn.recv()
        if self.session_key:
            data = aes_full_decrypt(self.session_key,data)
        return data

    def send(self,data,l=False):
        if l:
            data = sectors.write_sectors(data)
        if self.session_key:
            data = aes_full_encrypt(self.session_key,data)
        self.conn.send(data)
        
    def auth(self):
        self.send([self.keys[0].save_pkcs1(),self.username],True)
        encrypted_session_key = self.recv()
        self.session_key = rsa.decrypt(encrypted_session_key,self.keys[1])
        self.session_key = sectors.bytes_to_int(self.session_key)
        self.session_key = aes.aes(self.session_key)
        try:
            code = self.recv()
            if code == b'\x01':
                return code
        except:
            return b'\x01'#print('[-] This username is taken. Try to change it')

    def mkchat(self,username,password):
        self.send([b'\x00',username,gen_chathash(password)],True)
        code = self.recv()
        if code == b'\x01':
            return code#print('[-] Chat exists')
        else:
            self.join_chat(username,password)

    def join_chat(self,username,password):
        self.send([b'\x01',username,gen_chathash(password)],True)
        code = self.recv()
        if code == b'\x00':
            self.initinf.add([username,password])
            self.initinf.save()
            self.send_invite(self.username,username)
        elif code == b'\x03':
            #print('[-] You are already in chat')
            if self.initinf.find(0,username) == -1:
                self.initinf.add([username,password])
                self.initinf.save()
        #elif code == b'\x01':
        #    print('[-] Bad chat hash')
        #elif code == b'\x02':
        #    print('[-] Chat doesn\'t exist')
        return code
        

    def getpubkey(self,username):
        secnum = self.keybase.find(0,username)
        if secnum == -1:
            self.send([b'\x02',username],True)
            key = self.recv()
            if key != b'\x01':
                self.keybase.add([username,key])
                self.keybase.save()
                return key
            else:
                return b'\x01'
        else:
            return self.keybase.getdat(secnum,1)

    def send_invite(self,username,chat_username):
        chat_password = self.initinf.getdat(self.initinf.find(0,chat_username),1)
        chathash = gen_chathash(chat_password)
        user_pubkey = rsa.PublicKey.load_pkcs1(self.getpubkey(username))
        self.send([b'\x03',username,chathash,chat_username,rsa.encrypt(chat_password,user_pubkey)],True)
        code = self.recv()
        #if code == b'\x01':
        #    print('[-] Invalid chathash/chat')
        #elif code == b'\x02':
        #    print('[-] Invalid user')
        #elif code == b'\x03':
        #    print('[-] Already sent')
        return code

    def send_message(self,username,message):
        message = msglib.message(message,self.username,self.keys[1],1).compile()
        secnum = self.initinf.find(0,username)
        if secnum != -1:
            self.send([b'\x04',username,aes_full_encrypt(aes.aes(get_chat_key(self.initinf.getdat(secnum,1))),message)],True)
            code = self.recv()
            #if code == b'\x01':
            #    print('[-] You r not in chat')
            #elif code == b'\x02':
            #    print('[-] Invalid chat')
            return code
        else:
            return b'\x02'#print('[-] Chat not found')

    def mybuflength(self):
        self.send([b'\x05'],True)
        return sectors.bytes_to_int(self.recv())

    def getbuf(self,index):
        self.send([b'\x06',sectors.int_to_bytes(index)],True)
        out = self.recv()
        if out == b'\x01':
            return b'\x01'#print('[-] Invalid package index')
        else:
            return out

    def read_buffer(self):
        my_username = self.username.decode()
        if os.path.exists(my_username+'/rn.txt'):
            rn = int(open(my_username+'/rn.txt','r').read())
        else:
            rn = 0
            open(my_username+'/rn.txt','w').write('0')
            
        bl = self.mybuflength()
        if bl-1 >= rn:
            
            for i in range(bl-rn):
                try:
                    if bl-rn-1 > 5:
                        loading_ = loading.load(bl-rn-1,' packages loaded')
                        loading_.num=i
                        loading_.write()
                    buff = sectors.read_sectors(self.getbuf(rn+i))
                    if buff[0] == b'\x00':
                        chat_username,enc_pass = buff[1],buff[2]
                        enc_pass = rsa.decrypt(enc_pass,self.keys[1])
                        if self.invites.find(0,chat_username) == -1 and not self.check_my_chat(chat_username):
                            if self.rejected.find(0,chat_username) == -1:
                                self.invites.add([chat_username,enc_pass])
                                self.invites.save()
                        else:
                            self.join_chat(chat_username,enc_pass)
                        
                    elif buff[0] == b'\x01':
                        chat_username,message = buff[1],buff[2]
                        
                        secnum = self.initinf.find(0,chat_username)
                        messages_secnum = self.messages.find(0,chat_username)
                        
                        message = aes_full_decrypt(aes.aes(get_chat_key(self.initinf.getdat(secnum,1))),message)
                        user_username = sectors.read_sectors(message)[3]
                        author_key = self.getpubkey(user_username)

                        message_check = msglib.message(message,author_key=rsa.PublicKey.load_pkcs1(author_key)).check()
                        if message_check:
                            if messages_secnum == -1:
                                self.messages.add([chat_username,sectors.write_sector(sectors.write_sectors(message_check))])
                            else:
                                old_messages = self.messages.intel_field_get(messages_secnum,1)
                                if old_messages.find(2,message_check[2]) == -1:
                                    old_messages.add(message_check)
                                    self.messages.intel_field_set(messages_secnum,1,old_messages)
                            self.messages.save()
                            
                
                except Exception as e:
                    print('[-]',e)
            print('\n')
            self.messages.save()
            
        open(my_username+'/rn.txt','w').write(str(bl-1))

    def get_messages(self,username):
        messages_secnum = self.messages.find(0,username)
        if messages_secnum == -1:
            return [(b'Server',b'Empty chat. You can\'t read it history')] 
        old_messages = self.messages.intel_field_get(messages_secnum,1)
        return [(sectors.read_sectors(i)[0],sectors.read_sectors(i)[1]) for i in sectors.read_sectors(old_messages.data)]

    def check_my_chat(self,username):
        self.send([b'\x07',username],True)
        if self.recv() == b'\x00':
            return True
        else:
            return False
        
                        
                        
