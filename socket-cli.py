import socket
import json
import time
import random

HOST = '127.0.0.1'
PORT = 3435
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect((HOST,PORT))
end = False

random_data = random.randint(0, 1000)
identity = 'identity' + str(random_data)
while True:
    if end:
        end = False
        select = input()
        if int(select) == 0:
            send_data = {'client_status':1, 'identity':identity}
            send_data = json.dumps(send_data)
            s.send(send_data.encode('utf-8'))
 
    data, addr = s.recvfrom(1024)
    if data:
        data = data.decode('utf-8')
        datas = data.split('\n')
        for data in datas:
            if data:
                try:
                    data = json.loads(data)
                except Exception:
                    print('error_data',data)
                    break
                
                if data['status']==0:
                    select = input()
                    if int(select) == 0:
                        send_data = {'client_status':1, 'identity':identity}
                        send_data = json.dumps(send_data)
                        s.send(send_data.encode('utf-8'))
                if data['status'] == 4:
                    print(data)
                    print('1)弃牌 2)跟注 3)加注')
                    select = input()
                    if int(select) == 3:
                        select = input()
                        send_data = {'client_status': 2,'type':3,'addnum':int(select)}
                    else:
                        send_data = {'client_status': 2,'type':select}
                    send_data = json.dumps(send_data)
                    s.send(send_data.encode('utf-8'))
                if data['status'] == 8:
                    print(data)
                    print('1)弃牌 2)过牌或跟注 3)加注 4)all in')
                    select = input()
                    if int(select) == 3:
                        select = input()
                        send_data = {'client_status': 2,'type':3,'addnum':int(select)}
                    else:
                        send_data = {'client_status': 2,'type':select}

                    send_data = json.dumps(send_data)
                    s.send(send_data.encode('utf-8'))
                if data['status'] == 13:
                    end = True
                    print(data)

 

                elif 'end' in data:
                    s.send('end'.encode('utf-8'))
                else:
                    print(data)
s.close()

