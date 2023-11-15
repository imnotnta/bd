import pickle, os, shutil

def read_dict(path):
    with open(path, 'rb') as handle:
        dct = pickle.load(handle)
    return dct

hashtags = ['Bitcoin', 'blockchain', 'btc', 'crypto']

for hashtag in hashtags:
    usernames = read_dict(os.path.join('all_users', f"{hashtag}.pkl"))
    other_hashtags = [_ for _ in hashtags if _ != hashtag]
    for username in usernames:
        path_to_info = os.path.join('user_info', hashtag, f"{username}.pkl")
        if not os.path.exists(path_to_info):
            for another_hashtag in other_hashtags:
                path_to_user = os.path.join('user_info', another_hashtag, f"{username}.pkl")
                if os.path.exists(path_to_user):
                    shutil.copyfile(path_to_user, path_to_info)
                    break
