#!/bin/sh

# Check if an input file was provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

# Extract the input file name
input_file="$1"

# Construct the output file name by adding '_output' before the file extension
input_file_renamed="${input_file%.*}_tracked_bak.${input_file##*.}"

mv "$input_file" "$input_file_renamed"

# Run the Python script, assuming the Python script takes an input and output file

python ./acceptchanges3.py -c -n --infile="$input_file_renamed" --outfile="$input_file"

echo "Original file renamed to: $input_file_renamed"
echo
echo "If LaTeX compile fails for the output file, copy all the parts before 'begin{document}' to the new file."

