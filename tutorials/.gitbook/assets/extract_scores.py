import os
import csv

def process_pdbqt_files(folder_path):
    # Create a CSV file for storing filenames and numbers
    csv_file_path = 'scores.csv'
    with open(csv_file_path, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Filename', 'Affinity'])

        # Iterate through all files in the folder
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.pdbqt'):
                file_path = os.path.join(folder_path, file_name)

                # Read the content of the file
                with open(file_path, 'r') as file:
                    lines = file.readlines()

                    # Ensure the file has at least 3 lines
                    if len(lines) >= 3:
                        # Get the second line of the file
                        second_line = lines[1]

                        # Extract the first negative number from the second line
                        try:
                            affinity = next(float(word) for word in second_line.split() if '-' in word)
                        except StopIteration:
                            print(f"Invalid format in file: {file_name}")
                            print(f"Second line content: {second_line}")
                            print("---")
                            continue

                        # Write to CSV
                        csv_writer.writerow([file_name, affinity])

                        print(f"Processed: {file_name}")
                    else:
                        print(f"File too short: {file_name}")

    print(f"CSV file created: {csv_file_path}")

# Specify the path to your folder containing pdbqt files
folder_path = './results'

# Call the function
process_pdbqt_files(folder_path)

