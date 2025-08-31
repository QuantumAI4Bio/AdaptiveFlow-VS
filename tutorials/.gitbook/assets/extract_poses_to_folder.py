import os
import tarfile

def extract_and_rename(tar_file_path):
    # Create a folder named "results" if it doesn't exist
    output_folder = 'results'
    os.makedirs(output_folder, exist_ok=True)

    with tarfile.open(tar_file_path, 'r:gz') as tar:
        for member in tar.getmembers():
            # Check if the member is a file
            if member.isfile():
                # Extract the file content
                file_content = tar.extractfile(member).read().decode('utf-8')

                # Get the third line of the file
                third_line = file_content.split('\n')[2].strip()

                # Extract the name after ":"
                name_after_colon = third_line.split(":")[1].strip().replace(" ", "")

                # Add .pdbqt extension to the file
                new_file_name = f"{name_after_colon}.pdbqt"

                # Read the content of the file
                file_data = tar.extractfile(member).read()

                # Write the file to the "results" folder
                with open(os.path.join(output_folder, new_file_name), 'wb') as new_file:
                    new_file.write(file_data)

                print(f"Extracted and renamed: {os.path.join(output_folder, new_file_name)}")

# Specify the path to your tar.gz file
tar_file_path = '0.tar.gz'

# Call the function
extract_and_rename(tar_file_path)
