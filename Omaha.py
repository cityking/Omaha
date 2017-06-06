#coding=utf-8
import random
from collections import Counter
from Omaha_utility import *

class PokerCard:
    '''
    1.一张牌包括点数和花色
    2.点数和花色一旦生成就不能改变
    '''
    __slots__ = ('rank', 'suit')
    def __init__(self, rank, suit):
        super().__setattr__( 'rank', rank )
        super().__setattr__( 'suit', suit )
    # print这个类的时候执行
    def __str__( self ):
        return "{0.rank}{0.suit}".format( self )
    # 不允许对牌重新赋值
    def __setattr__( self, name, value ):
        print ( "'{__class__.__name__}' 不能改变'{name}'的值".format( __class__= self.__class__, name= name ) )
    def __repr__( self ):
        #return "{__class__.__name__}(suit={suit!r}, rank={rank!r})".format(__class__=self.__class__, **self.__dict__)
        return "{0}{1}".format(self.suit, self.rank)
    def __str__( self ):
        return "{rank}{suit}".format(**self.__dict__)
    def __lt__( self, other ):
        if not isinstance( other, PokerCard):
            return NotImplemented
        return self.rank < other.rank
    def __le__( self, other ):
        try:
            return self.rank <= other.rank
        except AttributeError:
            return NotImplemented
    def __gt__( self, other ):
        if not isinstance( other, PokerCard):
            return NotImplemented
        return self.rank > other.rank
    def __ge__( self, other ):
        if not isinstance( other, PokerCard):
            return NotImplemented
        return self.rank >= other.rank
    def __eq__( self, other ):
        if not isinstance( other, PokerCard):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit
    def __ne__( self, other ):
        if not isinstance( other, PokerCard):
            return NotImplemented
        return self.rank != other.rank and self.suit == other.suit
    def trans_dict(self):
        suit = self.suit.name
        card_rank = self.rank
        return {'suit':suit, 'rank':card_rank}
        

class NumberCard( PokerCard ):
    def _points( self ):
        return int(self.rank), int(self.rank)

class AceCard( PokerCard ):
    insure= True
    def _points( self ):
        return 1, 11

class FaceCard( PokerCard ):
    def _points( self ):
        return 10, 10

class Suit:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
    def __repr__( self ):
        return self.symbol

class CardFactory:
    @classmethod
    def rank( self, rank ):
        '''
        这是类方法，直接用类本身调用；
        静态方法的区别是不接收参数
        '''
        self.class_, self.rank_str= {
            1:(AceCard,'14'),
            11:(FaceCard,'11'),
            12:(FaceCard,'12'),
            13:(FaceCard,'13'),
            }.get(rank, (NumberCard, str(rank)))
        return self
    @classmethod
    def suit( self, suit ):
        return self.class_( self.rank_str, suit )

class Deck(list):
    '''
    1.一副牌类，初始化就完成拿牌和洗牌。
    2.发牌主要包括每个人的两张底牌和7张公共牌
    3.发牌和公共牌要主动修改, 用setter
    '''
    def __init__( self ):
        Club, Diamond, Heart, Spade = Suit('Club','♣'), Suit('Diamond','♦'), Suit('Heart','♥'), Suit('Spade','♠')
        card_maker = CardFactory()
        self._cards = [ CardFactory.rank(r+1).suit(s) for r in range(13) for s in (Club, Diamond, Heart, Spade) ]
        random.shuffle( self._cards )
    # 发牌
    def pop(self):
        return self._cards.pop()

class Hand():
    '''
    1.初始化时有两张底牌,确定用哪副牌,确定是哪个玩家
    2.有个牌型属性，每次发了公共牌之后就自动计算
    '''
    def __init__(self, deck, player):
        # 手牌主要就是四张底牌, 然后玩家选择两张
        self.deck = deck
        self.player = player
        self.bluff = [deck.pop(), deck.pop(), deck.pop(), deck.pop()]
        self.card_type = {}

    # 检查组成牌型的牌是否符合要求
    def check_common(self, public_cards, card_type):
        bluff_common = []
        public_common = []
        for i in range(0, len(self.bluff)):
            if self.bluff[i] in card_type:
                bluff_common.append(self.bluff[i])
        for i in range(0, len(public_cards)):
            if public_cards[i] in card_type:
                public_common.append(public_cards[i])
        if len(bluff_common) >= 2 and len(public_common) >= 3:
            #print('同花牌：{0}\n底牌:{1}\n公共牌：{2}\n底牌部分：{3}\n公牌部分:{4}'.format(
            #        card_type,
            #        self.bluff,
            #        public_cards,
            #        bluff_common,
            #        public_common
            #    )
            #)
            #print('--------------------')
            return True
        else:
            return False

    # 将传入的5张牌组排序,默认都不相同
    def sort_cards(self, cards):
        card_rank = sorted([int(card.rank) for card in cards])
        card_dict = {card.rank: card for card in cards}
        sorted_cards = [card_dict[str(rank)] for rank in card_rank]
        #print('排列后的牌组：', sorted_cards)
        return card_rank, sorted_cards


    # 根据公共牌和底牌判断牌型并设置
    def set_card_type(self,public_cards):
        '''
        皇家同花顺(royal flush)：由AKQJ10五张组成，并且这5张牌花色相同 　　  
        同花顺(straight flush)：由五张连张同花色的牌组成 　　
        4条(four of a kind)：4张同点值的牌加上一张其他任何牌 　　
        满堂红(full house)（又称“葫芦”）：3张同点值加上另外一对 　　
        同花(flush)：5张牌花色相同，但是不成顺子 　　
        顺子(straight)：五张牌连张，至少一张花色不同 　　
        3条(three of a kind)：三张牌点值相同，其他两张各异 　　
        两对(two pairs)：两对加上一个杂牌 　　
        一对(one pair)：一对加上3张杂牌 　　
        高牌(high
        card):不符合上面任何一种牌型的牌型，由单牌且不连续不同花的组成

        '''
        total_cards = self.bluff + public_cards
        suit_dict = {
            'Club':[],
            'Diamond':[],
            'Heart':[],
            'Spade':[]
        }
        # 将所有牌按照花色分类
        for card in total_cards:
            suit_dict[card.suit.name].append(card)
        #print('同花分类：', suit_dict)
        # 判断同花
        for k in suit_dict:
            flush = None
            if len(suit_dict[k]) >= 5:
                # 先排序
                card_rank, flush = self.sort_cards(suit_dict[k])
                # 只要找到连续5个并且通过就好, 多组的话就覆盖
                i = 0
                while i+5 < len(flush):
                    if self.check_common(public_cards, flush[i:i+5]):
                        # 用all判断连续
                        if all(int(flush[i].rank)+1 == int(flush[i+1].rank)
                            for i in range(i, i+5)):
                            # 如果连续再判断是否满足两张底牌+三张公牌
                            if card_rank == [10,11,12,13,14]:
                                #print('皇家同花顺', k, flush[i:i+5])
                                self.card_type['royal_flush'] = flush[i:i+5]
                            else:
                                #print('同花顺：',k, flush[i:i+5])
                                self.card_type['straight_flush'] = flush[i:i+5]
                        else:
                            #print('同花:', k, flush[i:i+5])
                            self.card_type['flush'] = flush[i:i+5]
                    i += 1
                break
        # 先判断对子，再判断顺子
        rank_list, sorted_cards = self.sort_cards(total_cards)
        rank_counter = Counter(rank_list)
        #print('重复检查：', rank_counter.most_common())
        multi_list = rank_counter.most_common()
        multi_dict = {
            '4':[],
            '3':[],
            '2':[],
            '1':[]
        }
        for item in multi_list:
            multi_cards = []
            for card in total_cards:
                if int(card.rank) == item[0]:
                    multi_cards.append(card)
            multi_dict[str(item[1])].append(multi_cards)
        #print('重置后：', multi_dict)
        # 判断四条
        for item in multi_dict['4']:
            for card in total_cards:
                if card not in item:
                    temp = item.copy()
                    temp.append(card)
                    if self.check_common(public_cards, temp):
                        #print ('四条：', temp)
                        self.card_type['four'] = temp 
        # 判断葫芦或三条
        for item in multi_dict['3']:
            for t in multi_dict['2']:
                temp = item.copy()
                temp.extend(t)
                if self.check_common(public_cards, temp):
                    self.card_type['full_house'] = temp
            # 再判断三条
            not_three = []
            for card in total_cards:
                if card not in item:
                    not_three.append(card)
            pair_list = search(not_three,2)
            for i in pair_list:
                temp = item.copy()
                temp.extend(i)
                if self.check_common(public_cards, temp):
                    #print(temp)
                    self.card_type['three'] = temp
        # 判断两对或一对
        if len(multi_dict['2']) > 1:
            #print('multi_dict["2"]:',multi_dict['2'])
            for item in multi_dict['2']:
                temp = multi_dict['2'].copy()
                first = temp.pop()
                for second in temp:
                    temp_first = first.copy()
                    temp_first.extend(second)
                    two_pairs = temp_first
                    for card in total_cards:
                        if card not in two_pairs:
                            temp_two_pairs = two_pairs.copy()
                            temp_two_pairs.append(card)
                            if self.check_common(public_cards, temp_two_pairs):
                                #print('two pairs:', temp_two_pairs)
                                self.card_type['two_pairs'] = temp_two_pairs
        if len(multi_dict['2']) == 1:
            not_pair = []
            for card in total_cards:
                if card not in multi_dict['2'][0]:
                    not_pair.append(card)
            pair_list = search(not_pair, 3)
            for i in pair_list:
                temp = multi_dict['2'][0].copy()
                temp.extend(i)
                if self.check_common(public_cards, temp):
                    #print('one_pair:',temp)
                    self.card_type['one_pair'] = temp
        # 判断杂牌还是顺子
        card_rank, flush = self.sort_cards(total_cards)
        i = 0
        while i+5 < len(flush):
            if self.check_common(public_cards, flush[i:i+5]):
                # 用all判断连续
                if all(int(flush[i].rank)+1 == int(flush[i+1].rank)
                    for i in range(i, i+5)):
                    #print('顺子：', flush[i:i+5])
                    self.card_type['straight'] = flush[i:i+5]
            i+=1
        high_list = search(flush, 5)
        for high in high_list:
            if self.check_common(public_cards, high):
                #print ('高牌：', high)
                self.card_type['high'] = high
        pass

    def __repr__(self):
        #return "{__class__.__name__}(suit={suit!r}, rank={rank!r})".format(__class__=self.__class__, **self.__dict__)
        bluff_list = []
        for card in self.bluff:
            bluff_list.append('{0}{1}'.format(
                card.suit,card.rank
            )
            )
        return bluff_list


class BettingStrategy:
    pass

class Table:
    '''
    1. 初始化时就要确定玩家，牌
    '''
    def __init__(self,players):
        self.deck = Deck()
        self.public_cards = []
        # 给每个选手发底牌
        self.hands = [Hand(self.deck, player) for player in players]
    # 发公共牌,同时更新牌型
    def pop(self):
        card = self.deck.pop()
        self.public_cards.append(card)
        if len(self.public_cards) == 5:
            for hand in self.hands:
                hand.set_card_type(self.public_cards)
                #print(hand.card_type)

















        
if __name__ == '__main__':
    #Club, Diamond, Heart, Spade = Suit('Club','♣'), Suit('Diamond','♦'), Suit('Heart','♥'), Suit('Spade','♠')
    #print(Club, Diamond, Heart, Spade )
    #d2 = [ PokerCard('A', Spade), PokerCard('2', Spade), PokerCard('3', Spade), ]
    #print(d2)
    #deck = Deck()
    #hand = [d.pop(), d.pop()]
    players = [1,2,3,4,5,6,7]
    for t in range(5):
        #print('----------')
        table = Table(players)
        for i in range(5):
            table.pop()
        #print('公牌:%s' % table.public_cards)
        for hand in table.hands:
            #if hand.card_type == {}:
            #if 'straight_flush' in hand.card_type.keys():
            print('公牌:%s' % table.public_cards)
            print('玩家%s的底牌:%s' % (hand.player, hand.bluff))
            print(hand.player,hand.card_type)
            for card_type in hand.card_type:
                print(card_type, hand.card_type[card_type][0].suit)
                print(card_type, hand.card_type[card_type][0].rank)


            pass
