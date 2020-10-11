import pickle

with open('phone_isFull.pickle', 'wb') as fw:
    pickle.dump('isEmpty', fw)
