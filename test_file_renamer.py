import os

cwd = os.getcwd()
test_files_folder = os.path.join(cwd, "test_files")

for file_name in os.listdir(test_files_folder):
    if "pdf" not in file_name[-4:].lower():
        continue
        os.remove(os.path.join(test_files_folder , file_name))
    else:
        while True:
            new_name = os.path.join(
                test_files_folder, f"{round(abs(hash(file_name))/(10**10))}.pdf")
            curr_name = os.path.join(test_files_folder, file_name)
            try:
                os.rename(curr_name, new_name)
                break
            except:
                pass
