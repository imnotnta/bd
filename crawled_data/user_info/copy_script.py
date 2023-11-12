import os
import shutil

for typ in ['btc', 'blockchain', 'Bitcoin']:
# folder = ['2', 'bd', 'crawled_data', 'user_info', 'blockchain']
    folder = ['huymovie2002', typ]
    folder_src = os.path.join(*folder)
    if not os.path.exists(folder_src):
        continue
    lf_src = os.listdir(folder_src)

    folder_dst = folder[-1]

    old_num_dst = len(os.listdir(folder_dst))
    count = 0
    for name in lf_src:
        src_path = os.path.join(folder_src, name)
        dst_path = os.path.join(folder_dst, name)
        # if not os.path.exists(dst_path) and os.stat(src_path).st_size > 1024 * 1.5: #file lớn hơn 1.5kB
        if not os.path.exists(dst_path):
            count += 1
            shutil.copyfile(src_path, dst_path)

    if count != 0:
        print(typ)
        print(f"Num file in source folder = {len(lf_src)}")
        print(f"Num file in destination folder = {old_num_dst}")
        print(f"Số file đã copy = {count}")
        print(f"Num files in destination folder = {len(os.listdir(folder_dst))}")

print("DONE")