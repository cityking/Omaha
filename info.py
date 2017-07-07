
CLIENT_NUM = 7
class Player(object):
    def __init__(self, money):
        self.address = None
        self.player_no = None
        self.bluff = []    #底牌
        self.public_cards = []    #公牌
        self.card_type = {} 
        self.card_type_1 = {} 
        self.card_type_2 = {} 
        self.bet = False    #下注
        self.bet_added = False
        self.add_bet = True
        self.total_bet = 0
        self.bet_money = 0
        self.current_bet = 0
        self.money = money
        self.win_money = 0
        self.discard = False    #弃牌
        self.all_in = False
        self.win = False
        self.online = True 
        self.identity = None
        self.bet_type = 0

    def reset(self):
        self.bluff = []    #底牌
        self.public_cards = []    #公牌
        self.card_type = {} 
        self.card_type_1 = {} 
        self.card_type_2 = {} 
 
        self.add_bet = True
        self.bet = False    #下注
        self.bet_added = False
        self.bet_money = 0
        self.current_bet = 0
        self.discard = False    #弃牌
        self.all_in = False
        self.win = False
        self.total_bet = 0
        self.win_money = 0

    

class TableInfo(object):
    def __init__(self):
        self.init = False
        self.current_bet = 0
        self.total_bet = 0
        self.start = False
        self.end = False
        self.end_num = 0
        self.end_first = False
        self.end_second = False
        self.cards_init = False
        self.players_count = 0
        self.end_count = 0
        self.players = []
        self.discard_players = []
        self.allin_players = []
        self.offline_players = []
        self.win = None
        self.times = 0
        self.last_card_sent = False #是否开始发底牌
        self.last_card_sented = False   #是否发完底牌
        self.last_cards = 0
        self.follow_bet = True
        self.first_bet = False
        self.second_bet = False
        self.end_bet = False
        self.small_bet = 0    #小盲注
        self.big_bet = 0    #大盲注
        self.send_public = False
        self.endplayer = None
        self.end_done = False
        self.bet_before = 0 
        self.init_count = 0
        self.first_player = 0
        self.end_player = CLIENT_NUM - 1
        self.player_reset = 0
        self.current_players_count = 0
        self.in_first = True
        self.send_first = 0
        self.send_second = 0
        self.send_third = 0
        self.players_temp = [] #临时存储玩家
        self.bet_end_num = 0
        self.players_num = 0 #进入桌子的玩家数量
    def reset(self):
        self.current_bet = 0
        self.total_bet = 0
        self.start = False
        self.end = False
        self.end_num = 0
        self.end_first = False
        self.end_second = False
        self.cards_init = False
        self.players_count = 0
        self.win = None
        self.circles = 0
        self.last_card_sent = False #是否开始发底牌
        self.last_card_sented = False   #是否发完底牌
        self.last_cards = 0
        self.first_bet = False
        self.sencond_bet = False
        self.end_bet = False
        self.small_bet = 0    #小盲注
        self.big_bet = 0    #大盲注
        self.send_public = False
        self.endplayer = None
        self.end_done = False
        self.end_count = 0
        self.player_reset = 0
        self.in_first = True
        self.send_first = 0
        self.send_second = 0
        self.send_third = 0
        self.bet_before = 0 
        self.init_count = 0
        self.players_temp = [] #临时存储玩家
        self.discard_players = []
        self.allin_players = []
  
