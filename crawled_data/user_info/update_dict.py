import pickle, os

######################## Đổi thông tin ở đây ####################
dict_path = 'info.pkl'
folders = ['vatly2020', 'huydsai02', 'aehuyhoang1', 'huynv2002', 'choiiiiii307']
#################################################################

def save_dict(dct, path):
    with open(path, 'wb') as handle:
        pickle.dump(dct, handle, protocol=pickle.HIGHEST_PROTOCOL)

def read_dict(path):
    with open(path, 'rb') as handle:
        dct = pickle.load(handle)
    return dct

dct = read_dict(dict_path)

for folder in folders:
    with open(os.path.join(folder, 'logs.txt')) as f:
        lines = f.readlines()
    for line in lines:
        state, name = line.split(":")
        if line.startswith("Finish") or line.startswith("Already"):
            dct['Finished'].append(name.strip())
        elif line.startswith("Error"):
            dct["Error"].append(name.strip())

dct['Finished'] = list(set(dct['Finished']))
dct['Error'] = list(set(dct['Error']))

save_dict(dct, dict_path)