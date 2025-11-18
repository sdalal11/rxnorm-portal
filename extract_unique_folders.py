import pandas as pd
import csv

# Read the CSV file
df = pd.read_csv('/Users/sanjanadalal/Desktop/turmerik/RxNorm/emails-folder.csv')

# Get unique folder numbers from assigned_folder column
unique_folders = sorted(df['assigned_folder'].unique())

print("Unique Folder Numbers from assigned_folder column:")
print("=" * 50)

# Print the unique folders
for folder in unique_folders:
    print(folder)

print(f"\nTotal unique folders: {len(unique_folders)}")

# Save to a text file for easy reference
with open('/Users/sanjanadalal/Desktop/turmerik/RxNorm/unique_folder_numbers.txt', 'w') as f:
    f.write("Unique Folder Numbers from emails-folder.csv\n")
    f.write("=" * 50 + "\n")
    for folder in unique_folders:
        f.write(f"{folder}\n")
    f.write(f"\nTotal unique folders: {len(unique_folders)}\n")

print("\nUnique folder numbers have been saved to: unique_folder_numbers.txt")

# Also create a comma-separated version for easy copy-paste
folder_list = ','.join(map(str, unique_folders))
print(f"\nComma-separated list: {folder_list}")

# Save comma-separated version
with open('/Users/sanjanadalal/Desktop/turmerik/RxNorm/unique_folders_comma_separated.txt', 'w') as f:
    f.write(folder_list)

print("Comma-separated list saved to: unique_folders_comma_separated.txt")