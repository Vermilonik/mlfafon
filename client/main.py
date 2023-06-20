import colorama
import updater
import client
import os
import platform

colorama.init()
WHITE = colorama.Fore.WHITE
RED = colorama.Fore.LIGHTRED_EX
GREEN  = colorama.Fore.LIGHTGREEN_EX

def clear():
    if 'wind' in platform.system().lower():
        os.system('cls')
    else:
        os.system('clear')

def ascer(byte):
    try:
        return byte.decode()
    except:
        return str(byte)[2:-1]

def check_args(args,l):
    if len(args) < l:
        print(RED+'[-] Not enoght args. Should be'+WHITE,l)
        return 1
    return 0

usr = client.User(input('[+] Ip(default 185.117.155.43): '),input('[+] Username: '),input('[+] Password: ').encode())
code = usr.auth()

if code == b'\x01':
    print(RED+'[-] This username is taken. Try to change it')
    
while True:
    cmd = input('[+] Cmd: ').split()
    if len(cmd) > 0:
        cmd,args = cmd[0],cmd[1:]
        if cmd == 'help':
            print(GREEN+'''
[!] help   -   *shows help*                         - no arguments
[!] chats  -   *shows all your chats and indexes*   - no arguments
[!] join   -   *joins chat*                         - username password
[!] select -   *selects chat*                       - chat index
[!] mkchat -   *makes chat*                         - username password
[!] exit   -   *exits select mode*                  - no arguments
[!] invite -   *invites user*                       - user & chat usernames
[!] update -   *loads all info from server*         - no arguments 
[!] invites-   *shows your invites to reject|accept*- no arguments
[!] accept -   *accepts invite to some chat*        - index in invites
[!] reject -   *rejects invite to some chat*        - index in invites
    
    '''+WHITE)
        elif cmd == 'chats':
            print(GREEN+'\n'.join([f'[{e}] {ascer(i)}' for e,i in enumerate(usr.initinf.fields(0))])+WHITE)
            
        elif cmd == 'join':
            if check_args(args,2):
                continue
            username,password = args[0],args[1]
            code = usr.join_chat(username.encode(),password.encode())
            if code == b'\x01':
                print(RED+'[-] Bad chat hash'+WHITE)
            elif code == b'\x02':
                print(RED+'[-] Chat doesn\'t exist'+WHITE)
                
        elif cmd == 'mkchat':
            if check_args(args,2):
                continue
            username,password = args[0],args[1]
            code = usr.mkchat(username.encode(),password.encode())
            if code == b'\x01':
                print(RED+'[-] Chat exists'+WHITE)
                
        elif cmd == 'invite':
            if check_args(args,2):
                continue
            u0,u1 = args[0],args[1]
            code = usr.send_invite(u0.encode(),u1.encode())
            if code == b'\x01':
                print(RED+'[-] Invalid chathash/chat'+WHITE)
            elif code == b'\x02':
                print(RED+'[-] Invalid user'+WHITE)
            elif code == b'\x03':
                print(RED+'[-] Already sent'+WHITE)

        elif cmd == 'update':
            usr.read_buffer()
            print(GREEN+'[+] updated'+WHITE)
            
        elif cmd == 'select':
            if check_args(args,1):
                continue
            
            chat_username = usr.initinf.fields(0)[int(args[0])]
            while True:
                clear()
                usr.read_buffer()
                print(GREEN+'\n'.join([f'{ascer(a)}: {ascer(m)}' for a,m in usr.get_messages(chat_username)])+WHITE)
                cmd = input(GREEN+'[+] Message: ')
                if len(cmd) > 0:
                    if cmd == 'exit':
                        ___ = input('[?] Are you shure to exit?(y/n): ')
                        if ___ == 'y':
                            break
                        else:
                            code = usr.send_message(chat_username,b'exit')
                            if code == b'\x01':
                                print(RED+'[-] You r not in chat'+WHITE)
                            elif code == b'\x02':
                                print(RED+'[-] Invalid chat'+WHITE)
                    else:
                        code = usr.send_message(chat_username,cmd.encode())
                        if code == b'\x01':
                            print(RED+'[-] You r not in chat'+WHITE)
                        elif code == b'\x02':
                            print(RED+'[-] Invalid chat'+WHITE)

        elif cmd == 'invites':
            print(GREEN+'\n'.join([f'[{e}] {ascer(i)}' for e,i in enumerate(usr.invites.fields(0))])+WHITE)

        elif cmd == 'accept':
            if check_args(args,1):
                continue
            sector_num = int(args[0])
            usr.join_chat(usr.invites.getdat(sector_num,0),usr.invites.getdat(sector_num,1))
            usr.invites.rem(sector_num)
            usr.invites.save()
            

        elif cmd == 'reject':
            if check_args(args,1):
                continue
            sector_num = int(args[0])
            username = usr.invites.getdat(sector_num,0)
            usr.invites.rem(sector_num)
            usr.rejected.add([username])
            usr.rejected.save()
            usr.invites.save()
                    

                    
                        