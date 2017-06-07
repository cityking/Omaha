import socket
import time
import datetime
import Omaha
import threading
import Omaha_compare 
import json

CLIENT_NUM = 3
BASE_BET = 50
TIMER = 15 
grades ={'high':1, 'one_pair':2, 'two_pairs':3, 'three':4, 'straight':5, 'flush':6, 'full_house':7, 'four':8, 'straight_flush':9, 'royal_flush':10}


mylock = threading.RLock()

def trans_cards(cards):
    cards_list = []
    for card in cards:
        card = card.trans_dict()
        cards_list.append(card)
    return cards_list


class Player(object):
    def __init__(self, money):
        self.address = None
        self.player_no = None
        self.bluff = []    #底牌
        self.public_cards = []    #公牌
        self.card_type = None
        self.bet = False    #下注
        self.bet_money = 0
        self.current_bet = 0
        self.money = money
        self.discard = False    #弃牌
        self.all_in = False
        self.win = False

    def reset(self):
        self.bluff = []    #底牌
        self.public_cards = []    #公牌
        self.card_type = None
        self.bet = False    #下注
        self.bet_money = 0
        self.current_bet = 0
        self.discard = False    #弃牌
        self.all_in = False
        self.win = False

    

class TableInfo(object):
    def __init__(self):
        self.init = False
        self.current_bet = 0
        self.total_bet = 0
        self.start = False
        self.end = False
        self.cards_init = False
        self.players_count = 0
        self.end_count = 0
        self.players = []
        self.win = None
        self.circles = 0
        self.times = 0
        self.last_card_sent = False #是否开始发底牌
        self.last_card_sented = False   #是否发完底牌
        self.last_cards = 0
        self.first_bet = False
        self.sencond_bet = False
        self.small_bet = 0    #小盲注
        self.big_bet = 0    #大盲注
        self.send_public = False
        self.endplayer = None
        self.end_done = False
        self.bet_before = 0
        self.first_player = 0
        self.end_player = CLIENT_NUM - 1
        self.player_reset = 0
    def reset(self):
        self.current_bet = 0
        self.total_bet = 0
        self.start = False
        self.end = False
        self.cards_init = False
        self.players_count = 0
        self.win = None
        self.circles = 0
        self.last_card_sent = False #是否开始发底牌
        self.last_card_sented = False   #是否发完底牌
        self.last_cards = 0
        self.first_bet = False
        self.sencond_bet = False
        self.small_bet = 0    #小盲注
        self.big_bet = 0    #大盲注
        self.send_public = False
        self.endplayer = None
        self.end_done = False
        self.bet_before = 0
        self.end_count = 0
        self.player_reset = 0
     



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
        while True:
            conn, addr = self.socket.accept()
            print('CLient %s connected!' % str(addr))
            t = threading.Thread(target = self.handle, args = [conn, addr]) 
            t.setDaemon(1)
            t.start()
    
        return s

    def stop(self):
        if self.socket:
            self.socket.close()
        else:
            return '服务未启动'

    def handle(self, conn, addr):

        try: 
            send_data = {'status':0}
            send_data = json.dumps(send_data) 
            send_data += '\n'
            conn.send(send_data.encode('utf-8'))


            while True:
                data = conn.recv(1024) 
                if data:
                    data = data.decode('utf-8')
                    data = json.loads(data)
                    print(data)

                #开始游戏
                if 'client_status' in data.keys() and data['client_status'] == 1:
                    
                    player_no = self.start_game(conn, addr)

               
                    table = self.tables[0]
                    player = table.players[player_no]
                    next_player = table.players[(player_no+1) % CLIENT_NUM]
                    time.sleep(6)
                    self.bet_first(conn, player, next_player, table)

                #发前三张公牌
                while True:
                    if table.send_public or table.end:
                        cards_info = player.public_cards[0:3]
                        send_data = {'status':7, 'public_cards':cards_info}
                        send_data = json.dumps(send_data) + '\n'
                        conn.send(send_data.encode('utf-8'))
                        if player.player_no == table.end_player:
                            table.second_bet = True
                        break

                #第二圈下注

                self.bet_second(conn, player, next_player, table)

                
                #发第四张公牌
                while True:
                    if table.send_public or table.end:
                        cards_info = player.public_cards[3:4]
                        send_data = {'status':11, 'public_four':cards_info}
                        send_data = json.dumps(send_data) + '\n'
                        conn.send(send_data.encode('utf-8'))
                        if player.player_no == table.first_player:
                            table.second_bet = True
                        break

                #第三圈下注
                self.bet_second(conn, player, next_player, table)
               
                #发第五张公牌
                while True:
                    if table.send_public or table.end:
                        cards_info = player.public_cards[4:]
                        send_data = {'status':12, 'public_five':cards_info}
                        send_data = json.dumps(send_data) + '\n'
                        conn.send(send_data.encode('utf-8'))
                        if player.player_no == table.first_player:
                            table.end_bet = True
                        break


                #最后一圈下注
                self.bet_end(conn, player, next_player, table)
               
                #结束本次游戏，并返回赢家信息
                self.end_game(conn, table, player)
                
                time.sleep(30)
                #牌桌和玩家重置
                while True:
                    if table.end_count == CLIENT_NUM:
                        player.reset()
                        table.player_reset += 1
                        if table.player_reset == CLIENT_NUM:
                            table.reset()
                        break
        finally:
            conn.close()
                    
    def start_game(self, conn, addr):
        if self.tables==[]:
            #创建牌桌
            table = TableInfo()
            self.tables.append(table)
        else:
            table = self.tables[0]
        
        table.start = True
        #table.reset()
        
        #玩家初始化
        player = self.init_player(addr, conn)
       
        

        #下底注
        self.bet_before(player, conn)

        #发底牌 
        if player.player_no == CLIENT_NUM - 1:
            if table.bet_before == CLIENT_NUM:
                self.init_cards()
                
                send_data = {'status':3, 'bluff':player.bluff}
                send_data = json.dumps(send_data) + '\n'
                conn.send(send_data.encode('utf-8'))
                table.last_cards += 1
                if table.last_cards == CLIENT_NUM:
                    table.last_card_sented = True
        else:
            while True:
                if table.cards_init:
                    send_data = {'status':3, 'bluff':player.bluff}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))
                    table.last_cards += 1
                    if table.last_cards == CLIENT_NUM:
                        table.last_card_sented = True
                    break
        return player.player_no

    def bet_before(self, player, conn):
        table = self.tables[0]
        player.current_bet = BASE_BET 
        player.bet_money = BASE_BET
        table.current_bet = BASE_BET
        table.total_bet += BASE_BET
        player.money -= BASE_BET
        times = table.times
        first = times % CLIENT_NUM
        end = first-1
        if end == -1:
            end = CLIENT_NUM - 1
        table.first_player = first
        table.end_player = end
        table.players[first].bet = True
        table.first_bet = True
        table.last_card_sented = False
        table.bet_before += 1
        while True:
            if table.bet_before == CLIENT_NUM:
                current_players = []
                for current_player in table.players:
                    current_bet = current_player.current_bet
                    bet_money = current_player.bet_money
                    money = current_player.money
                    player_no = current_player.player_no
                    current_players.append({'player_no':player_no,'current_bet':current_bet, 'bet_money':bet_money, 'money':money})
                send_data = {'status': 2, 'players': current_players, 'total_bet': table.total_bet}
                send_data = json.dumps(send_data) + '\n'
                conn.send(send_data.encode('utf-8'))
                break
            

    def bet_first(self, conn, player, next_player, table):
        while True:
            if player.bet and not table.end:
                if table.players_count == 1:
                    table.end = True
                    break
                send_data = {'status':4, 'message':'bet first','base_bet':table.current_bet, 'time_del':TIMER}
                send_data = json.dumps(send_data) + '\n'
                conn.send(send_data.encode('utf-8'))

                #计时器
                start_time = datetime.datetime.now() 
                conn.setblocking(0)
                while True:
                    try:
                        data = conn.recv(1024) 
                        if data:
                            data = data.decode('utf-8')
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
                    print(data)
                    data = json.loads(data)
                    bet_type = str(data['type'])
                    

                if bet_type == '1':
                    player.discard = True
                    player.bet = False
                    player.current_bet = 0
                    table.circles += 1
                    next_player.bet = True
                    table.players_count -= 1
                    send_data = {'player_no':player.player_no,'status':6, 'bet_money':player.current_bet, 'money':player.money, 'total_bet':table.total_bet}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))
                    break

                elif bet_type == '2': 
                    player.bet_money += table.current_bet
                    player.current_bet = table.current_bet
                    player.money -= player.current_bet
                    table.current_bet = table.current_bet 
                    table.total_bet += player.current_bet
                    table.circles += 1
                    next_player.bet = True
                    player.bet = False
                    send_data = {'player_no':player.player_no,'status':6, 'bet_money':player.current_bet, 'money':player.money, 'total_bet':table.total_bet}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))

                elif bet_type == '3':
                    bet_money = data['addnum']
                    player.bet_money += bet_money 
                    player.current_bet = bet_money 
                    player.money -= player.current_bet
                    table.circles += 1
                    table.current_bet = player.current_bet 
                    table.total_bet += player.current_bet
                    next_player.bet = True
                    player.bet = False
                    send_data = {'player_no':player.player_no,'status':6, 'bet_money':player.current_bet, 'money':player.money, 'total_bet':table.total_bet}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))
               

                if player.player_no == table.end_player:
                    table.first_bet = False
                    table.send_public = True
                    break
            else:
                for current_player in table.players:
                    if current_player.bet:
                        if current_player == player:
                            break
                        send_data = {'status':5, 'player_no':current_player.player_no,'time_del':TIMER}
                        send_data = json.dumps(send_data) + '\n'
                        conn.send(send_data.encode('utf-8'))
                        while True:
                            if not current_player.bet:
                                send_data = {'player_no':current_player.player_no,'status':6, 'bet_money':current_player.current_bet, 'money':current_player.money, 'total_bet':table.total_bet}
                                send_data = json.dumps(send_data) + '\n'
                                conn.send(send_data.encode('utf-8'))
                                if current_player.player_no == table.end_player:
                                    table.first_bet = False
                                break
            if not table.first_bet:
                break


                    
               
    def bet_second(self, conn, player, next_player, table):
        while True:
            if table.end:
                break
            if player.bet and not table.end:
                if table.players_count == 1:
                    table.end = True
                if player.discard or player.all_in:
                    next_player.bet = True
                    player.bet = False
                    continue
                send_data = {'status':8, 'message':'bet second', 'base_bet':table.current_bet, 'time_del':TIMER}
                send_data = json.dumps(send_data) + '\n'
                conn.send(send_data.encode('utf-8'))
                #计时器
                start_time = datetime.datetime.now() 
                conn.setblocking(0)
                while True:
                    try:
                        data = conn.recv(1024) 
                        if data:
                            data = data.decode('utf-8')
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
                    data = json.loads(data)
                    bet_type = str(data['type'])


                if bet_type == '1':
                    player.current_bet = 0
                    player.discard = True
                    player.bet = False
                    table.send_public = True
                    next_player.bet = True
                    table.players_count -= 1
                    send_data = {'player_no':player.player_no,'status':10, 'bet_money':player.current_bet, 'money':player.money, 'total_bet':table.total_bet}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))
                    break

                elif bet_type == '2': 
                    player.bet_money += table.current_bet
                    player.current_bet = table.current_bet
                    player.money -= player.current_bet
                    table.current_bet = table.current_bet 
                    table.total_bet += player.current_bet
                    player.bet = False
                    next_player.bet = True
                    send_data = {'player_no':player.player_no,'status':10, 'bet_money':player.current_bet, 'money':player.money, 'total_bet':table.total_bet}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))

                elif bet_type == '3':
                    bet_money = data['addnum']
                    player.bet_money += bet_money
                    player.current_bet = bet_money 
                    player.money -= player.current_bet
                    table.current_bet = player.current_bet 
                    table.total_bet += player.current_bet
                    next_player.bet = True
                    player.bet = False
                    send_data = {'player_no':player.player_no,'status':10, 'bet_money':player.current_bet, 'money':player.money, 'total_bet':table.total_bet}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))

                elif bet_type == '4':
                    player.current_bet = player.money
                    player.bet_money += player.money
                    player.money = 0
                    table.total_bet += player.current_bet
                    next_player.bet = True
                    player.all_in = True
                    player.bet = False
                    table.players_count -= 1
                    send_data = {'player_no':player.player_no,'status':10, 'bet_money':player.current_bet, 'money':player.money, 'total_bet':table.total_bet}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))
                    break

                if player.player_no == table.end_player:
                    table.second_bet = False
                    table.send_public = True
                    break
            else:
                for current_player in table.players:
                    if current_player.bet:
                        if current_player == player:
                            break
                        send_data = {'status':9, 'player_no':current_player.player_no, 'time_del':TIMER}
                        send_data = json.dumps(send_data) + '\n'
                        conn.send(send_data.encode('utf-8'))
                        while True:
                            if not current_player.bet:
                                send_data = {'player_no':current_player.player_no,'status':10, 'bet_money':current_player.current_bet, 'money':current_player.money, 'total_bet':table.total_bet}
                                send_data = json.dumps(send_data) + '\n'
                                conn.send(send_data.encode('utf-8'))
                                if current_player.player_no == table.end_player:
                                    table.second_bet = False
                                break
            if not table.second_bet:
                break


    def bet_end(self, conn, player, next_player, table):
        while True:
            if table.end:
                break
            if player.bet and not table.end:
                if table.players_count == 1:
                    table.end = True
                    break

                if player.discard or player.all_in:
                    next_player.bet = True
                    player.bet = False
                    continue
               
                send_data = {'status':8, 'message':'bet end','base_bet':table.current_bet, 'time_del':TIMER}
                send_data = json.dumps(send_data) + '\n'
                conn.send(send_data.encode('utf-8'))
                #计时器
                start_time = datetime.datetime.now() 
                conn.setblocking(0)
                while True:
                    try:
                        data = conn.recv(1024) 
                        if data:
                            data = data.decode('utf-8')
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
                    data = json.loads(data)
                    bet_type = str(data['type'])


                if bet_type == '1':
                    player.current_bet = 0
                    player.discard = True
                    player.bet = False
                    table.send_public = True
                    next_player.bet = True
                    table.players_count -= 1
                    send_data = {'player_no':player.player_no,'status':10, 'bet_money':player.current_bet, 'money':player.money, 'total_bet':table.total_bet}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))
                    break

                elif bet_type == '2': 
                    player.bet_money += table.current_bet
                    player.current_bet = table.current_bet
                    player.money -= player.current_bet
                    table.current_bet = table.current_bet 
                    table.total_bet += player.current_bet
                    player.bet = False
                    next_player.bet = True
                    send_data = {'player_no':player.player_no,'status':10, 'bet_money':player.current_bet, 'money':player.money, 'total_bet':table.total_bet}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))

                elif bet_type == '3':
                    bet_money = data['addnum']
                    player.bet_money += bet_money 
                    player.current_bet = bet_money 
                    player.money -= player.current_bet
                    table.current_bet = player.current_bet 
                    table.total_bet += player.current_bet
                    next_player.bet = True
                    player.bet = False
                    send_data = {'player_no':player.player_no,'status':10, 'bet_money':player.current_bet, 'money':player.money, 'total_bet':table.total_bet}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))

                elif bet_type == '4':
                    player.current_bet = player.money
                    player.bet_money += player.money
                    player.money = 0
                    table.total_bet += player.current_bet
                    next_player.bet = True
                    player.all_in = True
                    player.bet = False
                    table.players_count -= 1
                    send_data = {'player_no':player.player_no,'status':10, 'bet_money':player.current_bet, 'money':player.money, 'total_bet':table.total_bet}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))


                if player.player_no == table.end_player:
                    table.end_bet = False
                    table.end = True
                    break
            else:
                for current_player in table.players:
                    if current_player.bet:
                        if current_player == player:
                            break
                        send_data = {'status':9, 'player_no':current_player.player_no, 'time_del':TIMER}
                        send_data = json.dumps(send_data) + '\n'
                        conn.send(send_data.encode('utf-8'))
                        while True:
                            if not current_player.bet:
                                send_data = {'player_no':current_player.player_no,'status':10, 'bet_money':current_player.current_bet, 'money':current_player.money, 'total_bet':table.total_bet}
                                send_data = json.dumps(send_data) + '\n'
                                conn.send(send_data.encode('utf-8'))
                                if current_player.player_no == table.end_player:
                                    table.end_bet = False
                                    
                                break
            if not table.end_bet:
                break




    
    #玩家初始化
    def init_player(self, addr, conn):
        table = self.tables[0]
        if table.players_count < CLIENT_NUM:
            for current in table.players:
                if current.address == addr:
                    player = current
                    break
            else:
                player = Player(5000)
                player.player_no = table.players_count
                player.address = addr
                table.players.append(player)
            table.players_count += 1
            while True:
                if table.players_count == CLIENT_NUM:
                    other_players = []
                    for other_player in table.players:
                        if other_player != player:
                            player_info = {'player_no':other_player.player_no}
                            other_players.append(player_info)

                    send_data = {'status':1, 'other_players':other_players, 'player_no':player.player_no}
                    send_data = json.dumps(send_data) + '\n'
                    conn.send(send_data.encode('utf-8'))
                    break
                            
            return player
        
    #初始化牌型    
    def init_cards(self):
       desk = self.tables[0]
       if not desk.cards_init:
           players=[ i for i in range(1, CLIENT_NUM+1)]
           table = Omaha.Table(players)
           for i in range(5):
               table.pop()
           players = self.tables[0].players
           for hand in table.hands:
               mylock.acquire()
             
               
               players[hand.player-1].bluff = trans_cards(hand.bluff)
               players[hand.player-1].public_cards = trans_cards(table.public_cards)
               players[hand.player-1].card_type = hand.card_type 
               desk.cards_init = True

               mylock.release()

               #for card in table.public_cards:
               #    print(card.suit.name)
               #    print(card.rank)
               print('公牌:%s' % table.public_cards)
               print('玩家%s的底牌:%s' % (hand.player, hand.bluff))
               print(hand.player,hand.card_type)
              
    def end_game(self, conn, table, player):
        while True:
            if table.end:
                if table.end_player==player.player_no:

                    current_players = []
                    for current in table.players:
                        if not current.discard:
                            current_players.append(current)
                    win_players = compare_result(current_players)
                    win_money_per_player = table.total_bet//len(win_players)    
                    table.win = win_players

                    results = []
                    for player in table.players:
                        if player in table.win:
                            money = win_money_per_player - player.bet_money
                            is_win = True 

                            max_type = 'high'
                            for card_type in player.card_type.keys():
                                if grades[card_type] > grades[max_type]:
                                    max_type = card_type
                            cards = trans_cards(player.card_type[max_type])        

                            result = {'player_no':player.player_no, 'card_type':max_type,'cards':cards, 'money':money, 'is_win':is_win}
                            results.append(result)
                    send_data = {'status':13, 'data':results}
                    send_data = json.dumps(send_data)+'\n'
                    conn.send(send_data.encode('utf-8'))
                    table.end_count += 1 

                    table.end_done = True
                    break
                else:
                    if table.end_done:
                        win_money_per_player = table.total_bet//len(table.win)    
                        results = []
                        for player in table.players:
                            if player in table.win:
                                money = win_money_per_player - player.bet_money
                                is_win = True 
    
                                max_type = 'high'
                                for card_type in player.card_type.keys():
                                    if grades[card_type] > grades[max_type]:
                                        max_type = card_type
                                cards = trans_cards(player.card_type[max_type])        
    
                                result = {'player_no':player.player_no, 'card_type':max_type,'cards':cards, 'money':money, 'is_win':is_win}
     

                                results.append(result)
                        send_data = {'status':13, 'data':results}
                        send_data = json.dumps(send_data)+'\n'
                        conn.send(send_data.encode('utf-8'))
                        table.end_count += 1
                        break



HOST = '0.0.0.0'
PORT = 3435
server = Server(HOST, PORT)
try:
    socket = server.start()
finally:
    server.stop()
