import os
import string



def list_and_compare_files(source,start_v,end_V):

    for entry in os.scandir(source):

        if entry.is_dir(follow_symlinks=False):

            list_and_compare_files(entry.path,start_v,end_V)

        elif entry.is_file(follow_symlinks=False):

            new_path = entry.path
            new_path.replace(start_v,end_V,1)

            if not os.path.exists(new_path):    
                print(f"ERROR\n\
                      FILE {entry.name} DOES NOT EXIST IN {new_path}\n")






valid = False

start_path: str = ""

while not valid:

    print("Inserisci absolute source path\n")

    start_path = input()

    if os.path.exists(start_path):
        valid = True


valid = False
dest_path: str = ""


while not valid:

    print("Inserisci absolute destination path\n")

    dest_path = input()

    if os.path.exists(dest_path):
        valid = True


start_v = start_path.split('\\',1)

end_v = dest_path.split('\\',1)



list_and_compare_files(start_path,start_v[0],end_v[0])





