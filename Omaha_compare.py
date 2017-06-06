import Omaha

grades ={'high':1, 'one_pair':2, 'two_pairs':3, 'three':4, 'straight':5, 'flush':6, 'full_house':7, 'four':8, 'straight_flush':9, 'royal_flush':10}

def max_type(card_type):
    max_type = 'high'
    for ctype in card_type:
        if grades[ctype] > grades[max_type]:
            max_type = ctype
    return max_type

def compare_type(card_type1, card_type2):
    max_type1 = max_type(card_type1) 
    max_type2 = max_type(card_type2)
    return grades[max_type1] - grades[max_type2]

def sort_cards(cards):
    card_rank = sorted([int(card.rank) for card in cards])
    card_dict = {card.rank: card for card in cards}
    sorted_cards = [card_dict[str(rank)] for rank in card_rank]
    #print('排列后的牌组：', sorted_cards)
    return sorted_cards


def compare_high(cards1, cards2):
    cards1 = sort_cards(cards1)
    cards2 = sort_cards(cards2)
    for i in range(1,6):
        if cards1[-i].rank != cards2[-i].rank:
            return int(cards1[-i].rank) - int(cards2[-i].rank)
    return 0

def compare_one(cards1, cards2):
    cards1 = cards1[0:2] + sort_cards(cards1[2:])
    cards2 = cards2[0:2] + sort_cards(cards2[2:])
    if cards1[0].rank != cards2[0].rank:
        return int(cards1[0].rank) - int(cards2[0].rank)
    for i in range(1, 4):
        if cards1[-i].rank != cards2[-i].rank:
            return int(cards1[-i].rank)-int(cards2[-i].rank)
    return 0
    

def compare_two(cards1, cards2):
    cards1 = sort_cards(cards1[0:4])+cards1[4:]
    cards2 = sort_cards(cards2[0:4])+cards2[4:]
    if cards1[2].rank != cards2[2].rank:
        return int(cards1[2].rank)-int(cards2[2].rank)
    if cards1[0].rank != cards2[0].rank:
        return int(cards1[0].rank)-int(cards2[0].rank)
    if cards1[4].rank != cards2[4].rank:
        return int(cards1[4].rank)-int(cards2[4].rank)
    return 0
   

def compare_three(cards1, cards2):
    cards1 = cards1[0:3] + sort_cards(cards1[3:])
    cards2 = cards2[0:3] + sort_cards(cards2[3:])
    if cards1[0].rank != cards2[0].rank:
        return int(cards1[2].rank)-int(cards2[2].rank)
    if cards1[4].rank != cards2[4].rank:
        return int(cards1[4].rank)-int(cards2[4].rank)
    if cards1[3].rank != cards2[3].rank:
        return int(cards1[3].rank)-int(cards2[3].rank)
    return 0
 

def compare_straight(cards1, cards2):
    cards1 = sort_cards(cards1)
    cards2 = sort_cards(cards2)
    return int(cards1[0].rank)-int(cards2[0].rank)

def compare_full(cards1, cards2):
    if cards1[0].rank != cards2[0].rank:
        return int(cards1[0].rank)-int(cards2[0].rank)
    return int(cards1[3].rank)-int(cards2[3].rank)

def compare_four(cards1, cards2):
    if cards1[0].rank != cards2[0].rank:
        return int(cards1[0].rank)-int(cards2[0].rank)
    return int(cards1[4].rank)-int(cards2[4].rank)
   
def compare_flush(cards1, cards2):
    cards1 = sort_cards(cards1)
    cards2 = sort_cards(cards2)
    for i in range(1,6):
        if cards1[-i].rank != cards2[-i].rank:
            return int(cards1[-i].rank) - int(cards2[-i].rank)
    return 0

def compare_sflush(cards1, cards2):
    cards1 = sort_cards(cards1)
    cards2 = sort_cards(cards2)
    return int(cards1[0].rank)-int(cards2[0].rank)

def compare(card_type1, card_type2):
    type_result = compare_type(card_type1, card_type2)
    if type_result == 0:
        if max_type(card_type1) == 'high':
            return compare_high(card_type1['high'], card_type2['high'])
        if max_type(card_type1) == 'one_pair':
            return compare_one(card_type1['one_pair'], card_type2['one_pair'])
        if max_type(card_type1) == 'two_pairs':
            return compare_two(card_type1['two_pairs'], card_type2['two_pairs'])
        if max_type(card_type1) == 'three':
            return compare_three(card_type1['three'], card_type2['three'])
        if max_type(card_type1) == 'straight':
            return compare_straight(card_type1['straight'], card_type2['straight'])
        if max_type(card_type1) == 'flush':
            return compare_flush(card_type1['flush'], card_type2['flush'])
        if max_type(card_type1) == 'full_house':
            return compare_full(card_type1['full_house'], card_type2['full_house'])
        if max_type(card_type1) == 'straight_flush':
            return compare_sflush(card_type1['straight_flush'], card_type2['sflush'])
        if max_type(card_type1) == 'four':
            return compare_four(card_type1['four'], card_type2['four'])
        if max_type(card_type1) == 'high':
            return 0 
 

    else:
        return type_result



if __name__ == '__main__':

    #from Omaha import PokerCard, Suit
    #Club, Diamond, Heart, Spade = Suit('Club','♣'), Suit('Diamond','♦'), Suit('Heart','♥'), Suit('Spade','♠')
    #cards1 = []
    #cards1.append(PokerCard('8', Club))
    #cards1.append(PokerCard('4', Diamond))
    #cards1.append(PokerCard('5', Club))
    #cards1.append(PokerCard('6', Club))
    #cards1.append(PokerCard('7', Club))

    #cards2 = []
    #cards2.append(PokerCard('6', Club))
    #cards2.append(PokerCard('5', Diamond))
    #cards2.append(PokerCard('3', Club))
    #cards2.append(PokerCard('4', Club))
    #cards2.append(PokerCard('7', Club))
    #     
    #print(compare_straight(cards1, cards2))

    players = [1,2]
    for t in range(5):
        #print('----------')
        table = Omaha.Table(players)
        for i in range(5):
            table.pop()
        #print('公牌:%s' % table.public_cards)
        cardstype = []
        for hand in table.hands:
            #if hand.card_type == {}:
            #if 'straight_flush' in hand.card_type.keys():
            print('公牌:%s' % table.public_cards)
            print('玩家%s的底牌:%s' % (hand.player, hand.bluff))
            print(hand.player,hand.card_type)
            cardstype.append(hand.card_type)

        print(compare(cardstype[0], cardstype[1]))


