import pickle

data = {'phone_isFull' : False, 'weight' : True}

with open('save.pickle', 'wb') as fw:
    pickle.dump(data, fw)
