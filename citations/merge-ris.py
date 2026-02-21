import os

def merge_ris_files(input_folder, output_file):
    ris_files = [f for f in os.listdir(input_folder) if f.endswith('.ris')]
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for file in ris_files:
            file_path = os.path.join(input_folder, file)
            with open(file_path, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read().strip())  # Read and write contents, trimming excess whitespace
                outfile.write("\n\n")  # Add spacing between entries for clarity

    print(f"Successfully merged {len(ris_files)} files into {output_file}.")

input_folder = "Citations Output" # Name accordingly or use make directory
output_file = os.path.join(input_folder, "merged_citations.ris")
merge_ris_files(input_folder, output_file)
