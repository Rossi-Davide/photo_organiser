#organizza le foto data una cartella di origine e una di destinazione
"""
La versione corrente implementa il multithreading per la copia
Per ogni file da copiare viene gestito un thread separato in modo che le operazioni di gestione della coda non 
rallentino la copia
Dovrebbe apportare un aumento delle prestazioni in quanto la larghezza di banda massima del bus 
è sempre utilizzata
"""
import os 
import shutil
import datetime
import queue
import math
import threading


def add_missing_folders(path_list,dest_path = '', starting_year = 2000):

    for year in range(starting_year,(datetime.datetime.now()).year+1):

        abs_path = os.path.join(dest_path,str(year))

        if not os.path.isdir(abs_path):

            #creating new directory with name
            try:
                os.mkdir(abs_path)
            except (FileExistsError,FileNotFoundError,OSError)as error:

                print(f"{error}\n")


            #adding them to the list
            path_list.append(str(year))



"""
Riceve le informazioni di un singolo file e si occupa di copiarlo  
"""
def copy_singlefile_threaded(source, destination,semaphore):
   
   with semaphore:   
        try:
            shutil.copyfile(source,destination, follow_symlinks=False)
            shutil.copystat(source,destination, follow_symlinks=False)

        except OSError as error:
            print(f"{error}\n")
        


def copy_files_empty_queue(queue,dest_path,dest_folders,starting_year=2000):

    maximum_filesthread = 100

    semaphore = threading.BoundedSemaphore(maximum_filesthread)


    while not queue.empty():

        file_object = queue.get()

        #calcolo l'anno di creazione del file per capire in quale cartella smistarlo

        stats = file_object.stat(follow_symlinks= False)

        creation_year = math.trunc(stats.st_birthtime/31536000)

        creation_year = 1970 + creation_year

        #indice nella lista della cartella dell'anno
        offset = creation_year - starting_year

        if offset < 0:

            print(f"file offset is less than 0, therefore not belonging to any folder\n\
                            file name: {file_object.name}\n\
                            file creation year: {creation_year}\n\
                            file location: {file_object.path}\n\
                            EXPLICIT ACTION REQUIRED\n")
            
        else:

            #indice valido, preparo il nome del file e costruisco percorso destinazione

            year = dest_folders[offset]
            folder_dest_path = os.path.join(dest_path,year)
            filename_offset = ""

            full_dest_path = ""

            filename_elems = file_object.name.split('.')

            #first check for existence of a file with the same name before copying files
            
            exists:bool = True
            iterator: int = 1

            while exists:

                filename = ""

                #string concat to include extension and name offset
                if len(filename_elems) <=1:
                    filename = ''.join((filename_elems[0],filename_offset))
                
                else:

                    filename = ''.join(filename_elems[0:len(filename_elems)-1])

                    filename = ''.join((filename,filename_offset,'.',filename_elems[len(filename_elems)-1]))
                


                possible_file_path = os.path.join(folder_dest_path,filename)

                

                exists = os.path.exists(possible_file_path)    
        
                
                if exists:

                    #file already exists, editing filename offset and trying again
                    filename_offset = ''.join(("_",str(iterator)))


                    

                full_dest_path = possible_file_path
                iterator+=1


            print(f"{file_object.path} going to : {full_dest_path}\n")


            try:
                #creo nuovo thread per il file da copiare
                new_thread = threading.Thread(target=copy_singlefile_threaded,args=(file_object.path,full_dest_path,semaphore),name=filename)

                #faccio partire il thread, termina automaticamente alla fine della copia
                new_thread.start()
            
            except ValueError as error:
                print(f"{error}\n")
 

            













def list_and_copy_files(queue,source_path,dest_path,dest_folders):

    for entry in os.scandir(source_path):

        #if queue is full start emptying 

        if queue.full():

            copy_files_empty_queue(queue,dest_path,dest_folders,int(dest_folders[0]))


        #at this point queue definetly has some space
        #processing entry 

        if entry.is_dir(follow_symlinks=False):

            list_and_copy_files(queue,entry.path,dest_path,dest_folders)

        elif entry.is_file(follow_symlinks=False):

            queue.put(entry)

            



def transfer_files(source_path,dest_path,dest_folders):

    dest_folders.sort()

    beginning = datetime.datetime.now()

    #creating file queue 

    file_queue = queue.Queue()
    list_and_copy_files(file_queue,source_path,dest_path,dest_folders)

    #copying remaining files in the queue 
    copy_files_empty_queue(file_queue,dest_path,dest_folders,int(dest_folders[0]))

    end = datetime.datetime.now()

    print(f"SECONDS ELAPSED: {end-beginning}\n")
 









#MAIN



print("Alcune informazioni prima di iniziare\n")

input_correct = False

source_abspath = NotImplemented
destination_abspath = NotImplemented


while not input_correct:

    input_path = input("Inserisci il path ASSOLUTO della cartella di partenza\n")
    

    if os.path.isabs(input_path) == False:
        print("È necessario inserire un percorso assoluto\n")
        continue


    if os.path.isdir(input_path) == False:
        print("È necessario inserire una cartella di partenza valida\n")
        continue


    source_abspath = input_path

    input_correct = True


input_correct = False

while not input_correct:

    input_path = input("Inserisci il path ASSOLUTO della cartella di destinazione\n")
    

    if os.path.isabs(input_path) == False:
        print("È necessario inserire un percorso assoluto\n")
        continue


    if os.path.isdir(input_path) == False:
        print("È necessario inserire una cartella di destinazione valida\n")
        continue


    destination_abspath = input_path
    input_correct = True


#ADDITIONAL CHECKS ON PATHS 

if destination_abspath is NotImplemented or source_abspath is NotImplemented:
    raise Exception("È sopraggiunto un errore e uno o più path non sono validi\n")

print("\nInformazioni di partenza valide,inizializzazione e controlli in corso:\n")



starting_size = os.path.getsize(source_abspath)
dest_disk_data = shutil.disk_usage(destination_abspath)

if starting_size >= dest_disk_data.free: 
    raise Exception("La destinazione selezionata non ha sufficiente spazio per contenere tutti gli elementi di partenza\n")







dest_folders = [] #sottocartelle di destinazione per la copia 


#listing years directory folders 

for entry in os.scandir(destination_abspath):

    if entry.is_dir() == True:

        #additional checks required to verify if it's a photos folder

        if len(entry.name) == 4 and entry.name.isnumeric() and entry.name.startswith('20'):

            #converting the name to int and checking if it's less or equal than current year
            folder_year = int(entry.name)

            current_datetime = datetime.datetime.now()

            if folder_year <= current_datetime.year:

                dest_folders.append(entry.name)



lowest_year = 2000

for i in range(0,len(dest_folders)):

    if i == 0:
        lowest_year = int(dest_folders[i])

    elif int(dest_folders[i])<lowest_year:
        lowest_year = int(dest_folders[i])




year_range = (datetime.datetime.now()).year-lowest_year+1

if len(dest_folders)< year_range:
    print("There are definetly some years folders missing. Adding folders...\n")
    add_missing_folders(dest_folders,destination_abspath,lowest_year)






print("Begginning transfer\n")

transfer_files(source_abspath,destination_abspath,dest_folders)

