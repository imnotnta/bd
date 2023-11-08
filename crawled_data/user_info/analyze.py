# import os

# with open('logs_huydsai02_1.txt', 'r') as f:
#     lines = f.readlines()

# list_log = []
# for line in lines:
#     time = line.split()[0][:-1]
#     username = line.split(":")[1].strip()
#     list_log.append((float(time), username))

# list_log.sort(key = lambda x : x[0])

# #Check the last one need time > 12s:
# index = 0
# count = 0
# for i in range(len(list_log) - 1):
#     t = list_log[i + 1][0] - list_log[i][0]
#     if t > 10 and t <= 175:
#         print(list_log[i], list_log[i + 1])
#         count += 1

# print(index)
# print(count)
# print(os.path.exists(os.path.join('blockchain', 'lishaolongl.pkl')))
# print([i[1] for i in list_log][:500])

print(isinstance("ABC", str))