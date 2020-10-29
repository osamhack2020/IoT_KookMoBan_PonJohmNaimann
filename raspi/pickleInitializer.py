import pickle

data = {'phone_isFull' : True, 'weight' : 120, 'adminId' : 1}

with open('save.pickle', 'wb') as fw:
    pickle.dump(data, fw)
