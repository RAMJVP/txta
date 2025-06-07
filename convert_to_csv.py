import csv

# Input raw data
raw_data = [
    ["No.", "Column 1", "State Name", "Election Year", "Current Tenure", "Total AC", "Total PC", "Total Rajyasabha"],
    [1, "", "Andhra Pradesh", 2024, "12 June, 2019 - 11 June, 2024", 175, 25, 11],
    [2, "", "Arunachal Pradesh", 2024, "3 June, 2019 - 2 June, 2024", 60, 2, 1],
    [3, "", "Odisha", 2024, "25 June, 2019 - 24 June, 2024", 147, 21, 10],
    [4, "", "Sikkim", 2024, "3 June, 2019 - 2 June, 2024", 32, 1, 1],
    [5, "", "Haryana", 2024, "4 Nov, 2019 - 4 Nov, 2024", 90, 10, 5],
    [6, "", "Maharashtra", 2024, "27 Nov, 2019 - 26 Nov, 2024", 288, 48, 19],
    [7, "", "Jharkhand", 2025, "6 Jan, 2020 - 5 Jan, 2025", 81, 14, 6],
    [8, "", "Delhi", 2025, "24 Feb, 2020 - 23 Feb, 2025", 70, 7, 3],
    [9, "", "Bihar", 2025, "23 Nov, 2021 - 22 Nov, 2025", 243, 40, 16],
    [10, "", "Assam", 2026, "21 May, 2021 - 20 May, 2026", 126, 14, 7],
    [11, "", "Kerala", 2026, "24 May, 2021 - 23 May, 2026", 140, 20, 9],
    [12, "", "Tamil Nadu", 2026, "11 May, 2021 - 10 May, 2026", 234, 39, 18],
    [13, "", "West Bengal", 2026, "8 May, 2021 - 7 May, 2026", 294, 42, 16],
    [14, "", "Puducherry", 2026, "16 June, 2021 - 15 June, 2026", 30, 1, 1],
    [15, "", "Goa", 2027, "15 Mar, 2022 - 14 Mar, 2027", 40, 2, 1],
    [16, "", "Manipur", 2027, "14 Mar, 2022 - 13 Mar, 2027", 60, 2, 1],
    [17, "", "Punjab", 2027, "17 Mar, 2022 - 16 Mar, 2027", 117, 13, 7],
    [18, "", "Uttarakhand", 2027, "29 Mar, 2022 - 28 Mar, 2027", 70, 5, 3],
    [19, "", "Uttar Pradesh", 2027, "23 May, 2022 - 22 May, 2027", 403, 80, 31],
    [20, "", "Gujarat", 2027, "12 Dec, 2022 - 11 Dec, 2027", 182, 26, 11],
    [21, "", "Himachal Pradesh", 2027, "12 Dec, 2022 - 11 Dec, 2027", 68, 4, 3],
    [22, "", "Meghalaya", 2028, "23 Mar, 2023 - 22 Mar, 2028", 60, 2, 1],
    [23, "", "Nagaland", 2028, "23 Mar, 2023 - 22 Mar, 2028", 60, 1, 1],
    [24, "", "Tripura", 2028, "23 Mar, 2023 - 22 Mar, 2028", 60, 2, 1],
    [25, "", "Karnataka", 2028, "17 May, 2023 - 16 May, 2028", 224, 28, 12]
]

# Output file path
output_file = "elections_data.csv"

def clean_and_save_csv(data, file_path):
    # Remove unnecessary columns and empty rows
    cleaned_data = []
    for row in data:
        if row and any(row):  # Ensure row is not empty
            cleaned_row = [cell for cell in row if cell != ""]
            cleaned_data.append(cleaned_row)

    # Write to CSV
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(cleaned_data)

    print(f"CSV file saved to {file_path}")

# Execute the cleaning and saving
clean_and_save_csv(raw_data, output_file)
