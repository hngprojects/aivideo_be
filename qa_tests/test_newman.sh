#!/bin/bash

# Define the output directory and file name
# OUTPUT_DIR="newman-reports"
# OUTPUT_FILE="$OUTPUT_DIR/report-$(date +%Y%m%d%H%M%S).html"

# Create the directory if it doesn't exist
# mkdir -p $OUTPUT_DIR

# Run Newman with HTML reporter
newman run aivideo_be/qa_tests/regression/Payments-Flow_one-off-subscription.postman_collection.json -r htmlextra

# newman run your-collection.json -r htmlextra --reporter-htmlextra-export newman-reports/report.html

# Run Newman with HTML reporter
newman run aivideo_be/qa_tests/regression/Stage_7_Anastasia.postman_collection2.json -r htmlextra
