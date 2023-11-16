import pickle, os

######################## Đổi thông tin ở đây ####################
dict_path = 'info.pkl'
folders = ['huydsai02', 'huymovie2002', 'nvhuy126', 'vatly2020']
# folders = ['aehuyhoang1', 'huynv2002', 'nvhuy127', 'nvhuy128']
# folders = ['nvhuy127']
#################################################################

def save_dict(dct, path):
    with open(path, 'wb') as handle:
        pickle.dump(dct, handle, protocol=pickle.HIGHEST_PROTOCOL)

def read_dict(path):
    with open(path, 'rb') as handle:
        dct = pickle.load(handle)
    return dct

dct = read_dict(dict_path)
print("Before update:")
print(f"Num finished = {len(dct['Finished'])}, Num Error = {len(dct['Error'])}")

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
print("After update:")
print(f"Num finished = {len(dct['Finished'])}, Num Error = {len(dct['Error'])}")

save_dict(dct, dict_path)