import socket
import time
import datetime
import Omaha
import threading
import Omaha_compare 
import json
import queue
from info import Player, TableInfo, CLIENT_NUM
from mythread import stop_thread
from log import logger
BASE_BET = 50
TIMER = 30 
grades = {'high':1, 'one_pair':2, 'two_pairs':3, 'three':4, 'straight':5, 'flush':6, 'full_house':7, 'four':8, 'straight_flush':9, 'royal_flush':10}

mylock = threading.RLock()

def trans_cards(cards):
    cards_list = []
    for card in cards:
        card = card.trans_dict()
        cards_list.append(card)
    return cards_list

def send_json(data, conn):
    data = json.dumps(data) + '\n'
    try:
        conn.sendall(data.encode('utf-8'))
        return 0
    except BrokenPipeError:
        return -1

def do_next_player(table, player):
    index = table.players.index(player)
    next_player = table.players[(index-1) % table.current_players_count]

    return next_player
    
def send_off_line_players(table, conn):
    send_players = []
    while True:
        if len(table.offline_players) > 0:
            players = []
            for player in table.offline_players:
                player_no_list = [player.player_no for player in table.players]
                if player.player_no not in player_no_list and player not in send_players:
                    player_no = player.player_no
                    identity = player.identity
                    players.append({'player_no':player_no, 'identity':identity})
                    send_players.append(player)
            if players != []:
                send_data = {'status':14, 'players':players}
                logger.info(send_data)
                send_json(send_data, conn)




def do_off_line(data, table, player, thread_status):
    if 'client_status' in data.keys() and data['client_status'] == 3:
        print('current_players_count', table.current_players_count)
        table.players_num -= 1
        if thread_status['status'] in ['init','start']:
            if player in table.players:
                table.players.remove(player)
                table.offline_players.append(player)
            if thread_status['status'] == 'start':
                table.current_players_count -= 1
            if table.current_players_count <= 1:
                table.start = False
                table.in_first = True
        if thread_status['status'] in ['to_players_temp', 'init_player', 'send_players']:
            table.players_temp.remove(player)
            if player in table.players:
                table.players.remove(player)
            table.current_players_count -= 1
            table.players_count -= 1
            if thread_status['status'] == 'send_players':
                table.offline_players.apend(player)
        if thread_status['status'] in ['init_cards', 'bet_first', 'bet_second', 'bet_end', 'end_game']:
            index = table.players.index(player)
            table.players.remove(player)
            table.offline_players.append(player)
            if thread_status['status'] != 'end_game':
                table.current_players_count -= 1
                table.players_count -= 1
            if player.bet:
                player.bet = False
                next_player = table.players[(index-1) % table.current_players_count]
                
                #如果next_player不存在，继续向前找
                i = 1
                while not next_player:
                    i += 1
                    next_player = table.players[(index-i) % table.current_players_count]
                    if i >= len(table.players):
                        break
                
                if next_player:
                    next_player.bet = True

                if table.current_players_count == 1:
                    table.end = True
                    table.end_num = 1
        if table.current_players_count <= 0:
            table.current_players_count = 0
            table.reset()
        print('do_off current_players_count', table.current_players_count)

        return -1 
    return 0

def recv_data(thread_parent,conn, qu, table, player, thread_status):

    thread_name = threading.current_thread().getName()
    conn.setblocking(0) 
    while True:
        try:
            data = conn.recv(1024) 
            if data:
                data = data.decode('utf-8')
                data = json.loads(data)
                if do_off_line(data, table, player, thread_status)==-1:
                    stop_thread(thread_parent)                
                    print('thread stop')
                    return -1
                else:
                    qu.put(data)
                    logger.info({thread_name:data})
        except Exception:
           pass 
        conn.setblocking(1) 

def judge_end_bet(table, bet_time):
    end_num = 0
    for player in table.players:
        if player.bet_money == table.current_bet and player not in table.allin_players and player not in table.discard_players:
            end_num += 1 
    if end_num == table.players_count:
        if end_num == 1:
            table.end = True
        if bet_time == 1:
            table.end_first = True
            table.send_public = True
        elif bet_time == 2:
            table.end_second = True
            table.send_public = True
        elif bet_time == 3:
            table.end = True
#        for player in table.players:
#            if player.player_no == table.first_player:
#                player.bet = True
#            else:
#                player.bet = False
        return True
    else:
        return False
def compare_result(players):
    if len(players) == 1:
        return [players[0]]
    max_players = [players[0]] 
    for player in players:
        if Omaha_compare.compare(player.card_type, max_players[0].card_type) > 0:
            max_players = [player]
        elif Omaha_compare.compare(player.card_type, max_players[0].card_type) == 0:
            if player not in max_players:
                max_players.append(player)
             

    return max_players

def get_max_type(card_types):
     max_type = None 
     for card_type in card_types.keys():
         if max_type == None or grades[card_type] > grades[max_type]:
             max_type = card_type
     if max_type == None:
         return None, None
     cards = trans_cards(card_types[max_type])        
     return max_type,cards




def bet_method(player, table, next_player, bet_type, current_bet):
    
    if bet_type == '1':
        player.bet_type = 1
        player.discard = True
        table.discard_players.append(player)
        player.bet = False
        player.current_bet = 0
        next_player.bet = True
        table.players_count -= 1
        if table.players_count <= 1:
            discard_count = len(table.discard_players)
            if discard_count == len(table.players)-1:
                table.end_num = 1
                table.end = True

            elif table.players_count == 0:
                table.end = True

    elif bet_type == '2': 
        if current_bet == 0:
            player.bet_type = 5
        else:
            player.bet_type = 2
        player.bet_money += current_bet 
        player.current_bet = current_bet
        player.money -= player.current_bet
        table.total_bet += current_bet
        player.total_bet += current_bet
        next_player.bet = True
        player.bet = False
        if table.players_count == 1:
            table.end = True
        

    elif bet_type == '3':
        player.bet_type = 3
        player.add_bet = False
        current_bet = current_bet - player.current_bet
        player.bet_money += current_bet 
        player.current_bet = current_bet
        player.total_bet += current_bet
        player.money -= current_bet
        table.current_bet = player.bet_money 
        table.total_bet += player.current_bet
        next_player.bet = True
        player.bet = False

 
    elif bet_type == '4':
        player.bet_type = 4
        player.current_bet = player.money
        player.bet_money += player.money
        if player.bet_money > table.current_bet:
            table.current_bet = player.bet_money
        player.total_bet += player.money
        player.money = 0
        table.total_bet += player.current_bet
        next_player.bet = True
        player.all_in = True
        table.allin_players.append(player)
        player.bet = False
        table.players_count -= 1
        print('all_in players_count', table.players_count)
        if table.players_count == 0:
            table.end = True


class Server(object):
    def __init__(self, host, port, proxy='TCP'):
        self.host = host
        self.port = port
        self.proxy = proxy
        self.clients = []
        self.tables = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(7)
        
    def start(self):
        self.create_tables()
        while True:
            conn, addr = self.socket.accept()
            logger.info('CLient %s connected!' % str(addr))
            t = threading.Thread(target = self.handle, args = [conn, addr]) 
            t.setDaemon(1)
            t.start()
    
        return s

    def stop(self):
        if self.socket:
            self.socket.close()
        else:
            return '服务未启动'

    def create_tables(self):
        for i in range(20):
            table = TableInfo()
            self.tables.append(table)
        print('tables created')

    def handle(self, conn, addr):

        try: 
            logger.info('-'*100)
            thread = threading.current_thread()
            thread_name = thread.getName()
            thread_status = {'status':'init'}
            is_first = True
            table = None
            for mytable in self.tables:
                if mytable.players_num < 7 and not mytable.start:
                    mytable.players_num += 1
                    table = mytable
                    break
            
            if not table:
                send_data = {'status': 16}
                result = send_json(send_data, conn)
                return -1
            logger.info({'table.players_num':table.players_num})
            index = self.tables.index(table)
            logger.info({'table_no':index})
            send_data = {'status':0}
            result = send_json(send_data, conn)
            if result == -1:
                table.start == False
                if table.current_players_count == 0:
                    table.in_first = True
                return -1


            player = Player(5000)
 
            qu = queue.Queue()
            t = threading.Thread(target = recv_data, args = [thread,conn, qu, table, player, thread_status]) 
            t.setDaemon(1)
            t.start()

            t_send = threading.Thread(target = send_off_line_players, args=[table, conn])
            t_send.setDaemon(1)
            t_send.start()
           

            while True:
                logger.info('-'*100)
                if player.money < BASE_BET*2: 
                    start = 1 #钱不够, 不能开局
                else:
                    start = 2 #可以开局
                send_data = {'status':15, 'time':TIMER, 'start':start}
                send_json(send_data, conn)
                logger.info(send_data)
                start_time = datetime.datetime.now() 
                time.sleep(3)
                while True:
                    if is_first:
                        is_first = False
                        time.sleep(3)

   
                    now_time = datetime.datetime.now()
                    timedel = now_time-start_time
                    if timedel.total_seconds() >= TIMER:
                        if player in table.players:
                            table.players.remove(player)
                            table.offline_players.append(player)
                        table.players_num -= 1
                        return -1 
                    data = qu.get()
                    if data:
                        if 'client_status' in data.keys() and data['client_status'] == 1:
                            break
                while table.start:
                    pass

                
                thread_status['status'] = 'init'
                print(thread_name, 'start')
                logger.info({thread_name:'start', 'player':player})
 
              
                print(thread_name,'table.start')
                logger.info({thread_name:'tabe.start'})
                table.current_players_count += 1
                thread_status['status'] = 'start'
                print(thread_name, {'current_players_count':table.current_players_count})
                logger.info({thread_name:{'current_players_count':table.current_players_count}})
                if table.current_players_count > CLIENT_NUM:
                    break

                print(thread_name,{'table.in_first':table.in_first})
                if table.in_first:
                    table.in_first = False
                    time.sleep(5)
                    start_time = datetime.datetime.now()
                    print({'players_num':table.players_num, 'current_players_num':table.current_players_count})
                    while True:
                        if table.current_players_count == table.players_num and table.current_players_count > 1:
                            print({'players_num':table.players_num, 'current_players_num':table.current_players_count})
                            table.start = True
                            break
                        else:
                            now_time = datetime.datetime.now()
                            time_del = (now_time - start_time).total_seconds()
                            if table.current_players_count > 1 and time_del > 5:
                                table.start = True
                                break

                while True:
                    if table.start:
                        break
                print(thread_name,'start game')
                 
                #开始游戏
                if 'client_status' in data.keys() and data['client_status'] == 1:
                    identity = data['identity']

                    while True:
                        if table.start:
                            break
                    
                    self.start_game(conn, identity, table,player, thread_status)


                    if player == -1:
                        return -1

                     

                    print(thread_name, 'start bet_first')
                    logger.info({thread_name:'start bet_first'}) 
                    thread_status['status']='bet_first'
                    if self.bet_first(conn, player, table, qu)==-1:
                        return -1
                    print(thread_name, 'end bet_first')
                    logger.info({thread_name:'end bet_first'}) 

                #发前三张公牌
                

                while True:
                    if not table.end:
                        time.sleep(1)
                    if table.end and table.end_num == 1:
                        break
                    if table.send_public or table.end:
                        time.sleep(1)
                        player.add_bet = True
                        if table.players_count <= 1:
                            table.end = True
                        table.second_bet = False
                        cards_info = player.public_cards[0:3]
                        card_type, cards = get_max_type(player.card_type_1)
                        send_data = {'status':7, 'public_cards':cards_info, 'card_type':card_type, 'cards':cards}
                        result = send_json(send_data, conn)                        
                        logger.info({thread_name:send_data})
                        table.send_first += 1 
                        if table.send_first == table.current_players_count:
                            table.second_bet = True
                            table.send_public = False
                            table.current_bet = 0 

                            
                        break

                #第二圈下注

                thread_status['status']='bet_second'
                logger.info({thread_name:'start bet_second'}) 
                if self.bet_second(conn, player, table, qu) == -1:
                    return -1


                
                #发第四张公牌
                while True:
                    if not table.end:
                        time.sleep(1)
                    if table.end and table.end_num == 1:
                        break
                    if table.send_public or table.end:
                        time.sleep(1)
                        player.add_bet = True
                        if table.players_count == 1:
                            table.end = True

                        table.second_bet = False
                        cards_info = player.public_cards[3:4]
                        card_type, cards = get_max_type(player.card_type_2)
                        send_data = {'status':11, 'public_four':cards_info, 'card_type':card_type, 'cards':cards}
                        result = send_json(send_data, conn)
                        logger.info({thread_name:send_data})

                        table.send_second += 1
                        if table.send_second == table.current_players_count:

                            table.second_bet = True
                            table.end_second = False
                            table.send_public = False
                            table.current_bet = 0 

                        break

                #第三圈下注


                if self.bet_second(conn, player, table, qu) == -1:
                    return -1

                logger.info({thread_name:'end bet_second'}) 
                #发第五张公牌
                while True:
                    if not table.end:
                        time.sleep(1)
                    if table.end and table.end_num == 1:
                        break
                    if table.send_public or table.end:
                        time.sleep(1)
                        player.add_bet = True
                        if table.players_count == 1:
                            table.end = True

                        cards_info = player.public_cards[4:]
                        card_type, cards = get_max_type(player.card_type)
                        send_data = {'status':12, 'public_five':cards_info, 'card_type':card_type, 'cards':cards}
                        print(send_data)
                        result = send_json(send_data, conn)
                        logger.info({thread_name:send_data})

                        table.send_third += 1
                        if table.send_third == table.current_players_count:
                            table.end_bet = True
                            table.current_bet = 0 
                        break



                #最后一圈下注
                if table.current_players_count == 0:
                    return -1
                thread_status['status']='bet_end'
                if self.bet_end(conn, player, table, qu) == -1:
                    return -1
                time.sleep(1)
                #结束本次游戏，并返回赢家信息

                self.end_game(conn, table, player)
                time.sleep(2)
                print('end_game')
                print({'end_count':table.end_count})

                 
                #牌桌和玩家重置
                while True:
                    time.sleep(2)
                    if table.end_count >= table.current_players_count:
                        print({'table.end_count':table.end_count})
                        player.reset()
                        table.player_reset += 1
                        table.current_players_count -= 1
                        thread_status['status']='end_game'
                        if table.current_players_count<=0:
                            table.current_players_count = 0
                            table.reset()
                        if player.money <= 0:
                            table.players.remove(player)
                            table.offline_players.append(player)
                            

                        print('end')
                        table.times+=1
                        time.sleep(3)
                        break
        finally:
            conn.close()
                    
    def start_game(self, conn, identity, table, player, thread_status):
        
        #玩家初始化
        player = self.init_player(identity, conn, table, player, thread_status)
        if player == -1:
            return -1
        if table.current_players_count == 1:
            table.start = False

        while True:
            if table.start:
                break
        

        #下底注

        self.bet_before(table, player, conn)

        #发底牌 
        
        while True:
            if len(table.players) > 1:
                break

        print('start send_bluff')
        thread_status['status'] = 'init_cards'
        if player == table.players[0]:
            if table.bet_before == table.current_players_count:
                self.init_cards(table)
                while True:
                    if len(player.bluff) == 4:
                        send_data = {'status':3, 'bluff':player.bluff}
                        logger.info({'bluff':player.bluff})
                        print({'player_no':player.player_no, 'card_type':player.card_type})
                        break
                result = send_json(send_data, conn)

                table.last_cards += 1
                if table.last_cards == table.current_players_count:
                    table.last_card_sented = True
        else:
            while True:
                if table.cards_init:
                    while True:
                        if len(player.bluff) == 4:
                            send_data = {'status':3, 'bluff':player.bluff}
                            logger.info(send_data)
                            result = send_json(send_data, conn)
                            break

                    table.last_cards += 1
                    if table.last_cards == table.current_players_count:
                        table.last_card_sented = True
                    break

        print('end send_bluff')
        time.sleep(0.3)
        
        return player

    def bet_before(self, table, player, conn):
        player.current_bet = BASE_BET 
        player.bet_money = BASE_BET
        table.current_bet = BASE_BET
        table.total_bet += BASE_BET
        player.money -= BASE_BET
        times = table.times
        first = times %table.current_players_count 
        end = first-1
        if end == -1:
            end = table.current_players_count - 1
        table.first_player = first
        table.end_player = end
        table.players[first].bet = True
        table.first_bet = True
        table.last_card_sented = False
        table.bet_before += 1
        while True:
            if table.bet_before == table.current_players_count:
                current_players = []
                for current_player in table.players:
                    current_bet = current_player.current_bet
                    bet_money = current_player.bet_money
                    money = current_player.money
                    player_no = current_player.player_no
                    current_players.append({'player_no':player_no,'current_bet':current_bet, 'bet_money':bet_money, 'money':money})
                send_data = {'status': 2, 'players': current_players, 'total_bet': table.total_bet}
                result = send_json(send_data, conn)
                #if result == -1:
                #    return -1
                break
            

    def bet_first(self, conn, player, table, qu):
        
        print(table.end)
        bet_times = 0   #本轮下注次数
        player.bet_money = 0
        player.current_bet = 0

        while True:
            if table.end_first or table.end:
                break
            #当前下注情况
            current_bet = table.current_bet
            if current_bet == 0:
                current_bet = BASE_BET

            if player.bet and not table.end:

                if player.discard or player.all_in:
                    next_player = do_next_player(table, player)
                    next_player.bet = True
                    player.bet = False
                    continue 
                
                #是否为第二次下注
                if bet_times > 0:
                    if player.bet_money == table.current_bet:
                        if table.players_count == 1:
                            table.end = True
                            break
                        else:
                            if judge_end_bet(table, 1):
                                break
                            else:
                                next_player = do_next_player(table, player)
                                next_player.bet = True                                
                                continue
                    elif player.bet_money < table.current_bet+BASE_BET:
                        current_bet = table.current_bet - player.bet_money
                bet_times += 1


                if table.players_count == 1 and len(table.discard_players)==table.current_players_count-1:
                    table.end = True
                    break

                if player.add_bet:
                    flag = 1
                else:
                    flag = 2

                send_data = {'player_no':player.player_no, 'status':4, 'message':'bet first','base_bet':current_bet, 'time_del':TIMER, 'add_bet':flag, 'add_base':BASE_BET}
                logger.info(send_data)
                result = send_json(send_data, conn)
                time.sleep(0.3)
                #计时器
                start_time = datetime.datetime.now() 
                
                while True:
                    try:
                        if table.current_players_count == 1:
                            table.end = True
                            table.end_num = 1
                            return 0
                        data = qu.get(block=False) 
                        if data:
                            break
                    except Exception:
                        pass
                    now_time = datetime.datetime.now()
                    timedel = now_time-start_time
                    if timedel.total_seconds() >= TIMER:
                        data = '1'
                        break
                if data == '1':
                    bet_type = '1' 
                else:
                    bet_type = str(data['type'])
                    if bet_type == '3':
                        current_bet = data['addnum']
                        print('receive current_bet', current_bet)


                if table.current_players_count == 1:
                    table.end = True
                    table.end_num = 1
                    return 0
 
                next_player = do_next_player(table, player)
                bet_method(player, table,next_player, bet_type, current_bet) 

                send_data = {'player_no':player.player_no,'status':6, 'bet_money':player.bet_money, 'money':player.money, 'total_bet':table.total_bet, 'bet_type':player.bet_type}
                result = send_json(send_data, conn)

                #如果当前还没开始
                if table.current_bet == 0:
                    table.current_bet = player.current_bet 

                if bet_times >= 2:
                    if player.bet_money == table.current_bet:
                        if judge_end_bet(table, 1):
                            break
                
            else:
                while True:
                    for current_player in table.players:
                        if current_player.bet:
                            if current_player.all_in or current_player.discard:
                                continue
                            if current_player == player or table.end_first:
                                break
                            send_data = {'status':5, 'player_no':current_player.player_no,'time_del':TIMER}
                            result = send_json(send_data, conn)

                            while True:
                                if table.end or table.end_first:
                                    break
                                if not current_player.bet:
                                    send_data = {'player_no':current_player.player_no,'status':6, 'bet_money':current_player.bet_money, 'money':current_player.money, 'total_bet':table.total_bet, 'bet_type':current_player.bet_type}
                                    result = send_json(send_data, conn)
                                    logger.info(send_data)
                                    break
                    if player.bet or table.end_first or table.end:
                        break
    def bet_second(self, conn, player, table, qu):

        player.bet_money = 0
        player.current_bet = 0

        while True:
            if table.second_bet:
                break
            if table.end:
                return 0 

        bet_times = 0   #本轮下注次数

        while True:

            if table.end_second or table.end:
                break
            #当前下注情况
            current_bet = table.current_bet

            if player.bet and not table.end:

                if player.discard or player.all_in:
                    next_player = do_next_player(table, player)
                    next_player.bet = True
                    player.bet = False
                    continue 
 
                #是否为第二次下注
                if bet_times > 0:
                    print({'bet_money':player.bet_money, 'current_bet':player.current_bet})
                    if player.bet_money == table.current_bet:
                        if table.players_count == 1:
                            table.end = True
                            break
                        elif judge_end_bet(table, 2):
                            return 0                        
                        else:
                            next_player = do_next_player(table, player)
                            next_player.bet = True
                            continue

                    elif player.bet_money < table.current_bet+BASE_BET:
                        current_bet = table.current_bet - player.bet_money
                bet_times += 1


                if table.players_count == 1 and len(table.discard_players)==table.current_players_count-1:
                    table.end = True
                    break
                if player.add_bet:
                    if current_bet == 0:
                        flag = 3
                    else:
                        flag = 1
                else:
                    flag = 2
               
                send_data = {'status':8, 'message':'bet second','base_bet':current_bet, 'time_del':TIMER, 'add_bet':flag, 'add_base':BASE_BET}
                result = send_json(send_data, conn)
                time.sleep(0.3)

                #计时器
                start_time = datetime.datetime.now() 
                conn.setblocking(0)
                while True:
                    try:
                        if table.current_players_count == 1:
                            table.end = True
                            table.end_num = 1
                            return 0

                        data = qu.get(block=False) 
                        if data:
                            break
                    except Exception:
                        pass
                    now_time = datetime.datetime.now()
                    timedel = now_time-start_time
                    if timedel.total_seconds() >= TIMER:
                        data = '1'
                        break
                conn.setblocking(1)
                
                if data == '1':
                    bet_type = '1' 
                else:
                    bet_type = str(data['type'])
                    if bet_type == '3':
                        current_bet = data['addnum']

                if table.current_players_count == 1:
                    table.end = True
                    table.end_num = 1
                    return 0

                next_player = do_next_player(table, player)
                bet_method(player, table,next_player, bet_type, current_bet) 

                send_data = {'player_no':player.player_no,'status':10, 'bet_money':player.bet_money, 'money':player.money, 'total_bet':table.total_bet, 'bet_type':player.bet_type}
                result = send_json(send_data, conn)
                logger.info(send_data)

                #如果当前还没开始
                if table.current_bet == 0:
                    table.current_bet = player.current_bet 

                if bet_times >= 2:
                    if player.bet_money == table.current_bet:
                        if judge_end_bet(table, 2):
                            break
 
               
            else:
                while True:
                    for current_player in table.players:
                        if current_player.bet:
                            if current_player.all_in or current_player.discard:
                                continue


                            if current_player == player or table.end_second:
                                break
                            send_data = {'status':9, 'player_no':current_player.player_no,'time_del':TIMER}
                            result = send_json(send_data, conn)

                            while True:
                                if table.end or table.end_second:
                                    break
                                if not current_player.bet:
                                    send_data = {'player_no':current_player.player_no,'status':10, 'bet_money':current_player.bet_money, 'money':current_player.money, 'total_bet':table.total_bet, 'bet_type':current_player.bet_type}
                                    result = send_json(send_data, conn)
                                    logger.info(send_data)
                                    break
                    if player.bet or table.end_second or table.end:
                        break
    def bet_end(self, conn, player, table, qu):

        player.current_bet = 0
        player.bet_money = 0
        while True:
            if table.end_bet:
                break
            if table.end:
                return 0 

        bet_times = 0   #本轮下注次数

        while True:

            if table.end:
                break
            #当前下注情况
            current_bet = table.current_bet

            print('current_bet', current_bet, table.current_bet)
#            if current_bet == 0:
#                current_bet = BASE_BET

            if player.bet and not table.end:

                if player.discard or player.all_in:
                    next_player = do_next_player(table, player)
                    next_player.bet = True
                    player.bet = False
                    continue 

                #是否为第二次下注
                if bet_times > 0:
                    if player.bet_money == table.current_bet:
                        if table.players_count == 1:
                            table.end = True
                            return 0 
                        elif judge_end_bet(table, 3):
                            return 0                        
                        else:
                            next_player = do_next_player(table, player)
                            next_player.bet = True
                            continue
                    elif player.bet_money < table.current_bet+BASE_BET:
                        current_bet = table.current_bet - player.bet_money
                bet_times += 1


                if table.players_count == 1 and len(table.discard_players)==table.current_players_count-1:
                    table.end = True
                    break
                if player.add_bet:
                    if current_bet == 0:
                        flag = 3
                    else:
                        flag = 1
                else:
                    flag = 2

                send_data = {'status':8, 'message':'bet end','base_bet':current_bet, 'time_del':TIMER, 'add_bet':flag, 'add_base':BASE_BET}
                logger.info(send_data)
                result = send_json(send_data, conn)
                time.sleep(0.3)

                #计时器
                start_time = datetime.datetime.now() 
                while True:
                    try:
                        if table.current_players_count == 1:
                            break
                        data = qu.get(block=False) 
                        if data:
                            break
                    except Exception:
                        pass
                    now_time = datetime.datetime.now()
                    timedel = now_time-start_time
                    if timedel.total_seconds() >= TIMER:
                        data = '1'
                        break
                
                if data == '1':
                    bet_type = '1' 
                else:
                    bet_type = str(data['type'])
                    if bet_type == '3':
                        current_bet = data['addnum']

                if table.current_players_count == 1:
                    table.end = True
                    table.end_num = 1
                    return 0


                next_player = do_next_player(table, player)
                bet_method(player, table,next_player, bet_type, current_bet) 

                send_data = {'player_no':player.player_no,'status':10, 'bet_money':player.bet_money, 'money':player.money, 'total_bet':table.total_bet, 'bet_type':player.bet_type}
                result = send_json(send_data, conn)
                logger.info(send_data)

                #如果当前还没开始
                if table.current_bet == 0:
                    table.current_bet = player.current_bet 
                if bet_times >= 2:
                    if player.bet_money == table.current_bet:
                        if judge_end_bet(table, 3):
                            break
                
            else:
                while True:
                    for current_player in table.players:
                        if current_player.bet:
                            if current_player.all_in or current_player.discard:
                                continue

                            if current_player == player or table.end:
                                break
                            send_data = {'status':9, 'player_no':current_player.player_no,'time_del':TIMER}
                            result = send_json(send_data, conn)

                            while True:
 
                                if table.end:
                                    break
                                if not current_player.bet:
                                    send_data = {'player_no':current_player.player_no,'status':10, 'bet_money':current_player.bet_money, 'money':current_player.money, 'total_bet':table.total_bet, 'bet_type':current_player.bet_type}
                                    result = send_json(send_data, conn)
                                    logger.info(send_data)
                                    break
                    if player.bet or table.end:
                        break
 



    
    #玩家初始化
    def init_player(self, identity, conn, table, player, thread_status):
        print( 'start init_player')
        if table.players_count < table.current_players_count:
            if player.identity:
                if player.money <= 0:
                    table.players.remove(player)
                    table.players_num -= 1
                    table.offline_players.append(player)
                    table.current_players_count -= 1
                    if table.current_players_count == 1:
                        table.start = False
                        table.in_first = True
                        return -1
            else:
                no_list_1 = [player.player_no for player in table.players_temp]
                no_list_2 = [player.player_no for player in table.players]
                for i in range(0, CLIENT_NUM):
                    if i not in no_list_1 and i not in no_list_2:
                        player.player_no = i                       
                        break
                player.identity =identity 
            
            table.players_temp.append(player)
            print('end init_player')

            table.players_count += 1
            thread_status['status'] = 'to_players_temp'
            print({'players_count':table.players_count})
            flag =1
            while True:

                if table.current_players_count <= 0:
                    return -1
                if table.current_players_count == 1 and table.players_count > 1 and flag == 1:
                    flag = 0
                    table.players_count = 1 
                    table.start = False
                    table.in_first = True 
                if table.players_count == table.current_players_count and len(table.players_temp) > 1:
                    print('send players')
                    table.players = sorted(table.players_temp, key=lambda my_player: my_player.player_no)
                    #table.players = table.players_temp 
                    thread_status['status'] = 'init_player'
                    other_players = []
                    for other_player in table.players:
                        if other_player != player:
                            player_info = {'player_no':other_player.player_no, 'identity':other_player.identity}
                            other_players.append(player_info)
                    if other_players == []:
                        continue
                    send_data = {'status':1, 'other_players':other_players, 'player_no':player.player_no,'identity':player.identity}
                    result = send_json(send_data, conn)

                    thread_status['status'] = 'send_players'

                    break

            return player
        
    #初始化牌型    
    def init_cards(self, table):
       print({'init_cards':table.players})
       while True:
           if len(table.players) == table.current_players_count:
               break
       if not table.cards_init:
           players=[ i for i in range(1, table.current_players_count+1)]
           desk = Omaha.Table(players)
           for i in range(5):
               desk.pop()

           #如果类型为空，重新洗牌
           for hand in desk.hands:
               if hand.card_type == {}:
                   desk = Omaha.Table(players)
                   for i in range(5):
                       desk.pop()
                   break

           players = table.players

           for hand in desk.hands:
               print('hand.player', hand.player)
               players[hand.player-1].bluff = trans_cards(hand.bluff)
               players[hand.player-1].public_cards = trans_cards(desk.public_cards)
               players[hand.player-1].card_type = hand.card_type 
               players[hand.player-1].card_type_1 = hand.card_type_1 
               players[hand.player-1].card_type_2 = hand.card_type_2 

               logger.info('公牌:%s' % desk.public_cards)
               logger.info('玩家%s的底牌:%s' % (hand.player, hand.bluff))
               logger.info(hand.card_type)
               
           table.cards_init = True 
              
    def end_game(self, conn, table, player):
        while True:
            if table.end:
                if table.end_num == 1:
                    results = [] 
                    results_fail = []
                    if player == table.players[0]:
                        for win_player in table.players:
                            if win_player not in table.discard_players and win_player not in table.offline_players:
                                win_money = table.total_bet
                                win_player.money += win_money
                                is_win = (win_player in table.discard_players)
                                is_win = True
                                win_player.win_money = win_money
                                result = {'player_no':win_player.player_no, 'card_type':'','cards':[], 'money':win_player.money, 'is_win':is_win, 'win_money':win_player.win_money}
                                results.append(result)
                                table.end_done = True 
                            else:
                                win_player.win_money -= (win_player.total_bet+BASE_BET)
                                result = {'player_no':win_player.player_no, 'money':win_player.money,'total_bet':win_player.total_bet, 'win_money':win_player.win_money }
                                results_fail.append(result)
                    else:
                        while True:
                            if table.end_done:
                                for win_player in table.players:
                                    if win_player not in table.discard_players:
                                        is_win = True
                                        result = {'player_no':win_player.player_no, 'card_type':'','cards':[], 'money':win_player.money, 'is_win':is_win, 'total_bet':table.total_bet-win_player.total_bet, 'win_money':win_player.win_money}
                                        results.append(result)
                                        table.end_done = True 
                                    else:
                                        result = {'player_no':win_player.player_no, 'money':win_player.money, 'total_bet':win_player.total_bet, 'win_money':win_player.win_money}
                                        results_fail.append(result)
                                    

                                break 
                    send_data = {'status':13, 'data0':results_fail, 'data':results}
                    result = send_json(send_data, conn)
                    logger.info(send_data)
                    table.end_count += 1 
                    break
                    
                     
                if table.players[0]==player:
                    current_players = []
                    for current in table.players:
                        if not current.discard:
                            current_players.append(current)

                    win_players = compare_result(current_players)
                    
                    win_money_per_player = table.total_bet//len(win_players)    


                    #ALL_IN
                    for win_player in win_players:
                        if win_player in table.allin_players:
                            re_turn = 0
                            for player in table.players:
                                if player.total_bet > win_player.total_bet:
                                    money = (player.total_bet - win_player.total_bet)//len(win_players)
                                    player.money += money
                                    player.win_money += money
                                    re_turn += money
                            win_player.money += (win_money_per_player-re_turn)
                            win_player.win_money = win_money_per_player - re_turn
                        else:
                            win_player.win_money = win_money_per_player
                            win_player.money += win_money_per_player
                                
                    table.win = win_players

                    results = []
                    results_fail = []
                    for win_player in table.players:
                        if win_player in table.win:
                            is_win = True 

                            max_type = 'high'
                            for card_type in win_player.card_type.keys():
                                if grades[card_type] > grades[max_type]:
                                    max_type = card_type
                            cards = trans_cards(win_player.card_type[max_type])        

                            result = {'player_no':win_player.player_no, 'card_type':max_type,'cards':cards, 'money':win_player.money, 'is_win':is_win, 'win_money':win_player.win_money}
                            results.append(result)
                        else:
                            win_player.win_money -= (win_player.total_bet+BASE_BET)
                            result = {'player_no':win_player.player_no, 'money':win_player.money, 'win_money':win_player.win_money}
                            results_fail.append(result)
                            
                    send_data = {'status':13,'data0':results_fail, 'data':results}
                    logger.info(send_data)
                    result = send_json(send_data, conn)
                    table.end_count += 1 

                    table.end_done = True
                    break
                else:
                    if table.end_done:
                        win_money_per_player = table.total_bet//len(table.win)    
                        results = []
                        results_fail = []
                        for win_player in table.players:
                            if win_player in table.win:
                                is_win = True 
    
                                max_type = 'high'
                                for card_type in win_player.card_type.keys():
                                    if grades[card_type] > grades[max_type]:
                                        max_type = card_type
                                cards = trans_cards(win_player.card_type[max_type])        
    
                                result = {'player_no':win_player.player_no, 'card_type':max_type,'cards':cards, 'money':win_player.money, 'is_win':is_win, 'win_money':win_player.win_money}
     

                                results.append(result)
                            else:
                                result = {'player_no':win_player.player_no, 'money':win_player.money, 'win_money':win_player.win_money}
                                results_fail.append(result)
 
                        send_data = {'status':13,'data0':results_fail, 'data':results}
                        logger.info(send_data)
                        result = send_json(send_data, conn)
                        table.end_count += 1
                        break



HOST = '0.0.0.0'
PORT = 3435
server = Server(HOST, PORT)
try:
    socket = server.start()
finally:
    server.stop()
