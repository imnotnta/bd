import os
import shutil

# folder = ['2', 'bd', 'crawled_data', 'user_info', 'blockchain']
folder = ['4', 'bd', 'crawled_data', 'user_info', 'blockchain']
folder_src = os.path.join(*folder)
lf_src = os.listdir(folder_src)

folder_dst = folder[-1]
print(f"Num file in source folder = {len(lf_src)}")
print(f"Num file in destination folder = {len(os.listdir(folder_dst))}")

count = 0
for name in lf_src:
    src_path = os.path.join(folder_src, name)
    dst_path = os.path.join(folder_dst, name)
    if not os.path.exists(dst_path) and os.stat(src_path).st_size > 1024 * 1.5: #file lớn hơn 1.5kB
        count += 1
        shutil.copyfile(src_path, dst_path)

print(f"Số file đã copy = {count}")
print(f"Num files in destination folder = {len(os.listdir(folder_dst))}")