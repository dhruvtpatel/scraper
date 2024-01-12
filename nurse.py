import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def scrape_data(url):
    
    # Set up the Chrome driver
    driver = webdriver.Chrome()
    
    scraped_data = {}

    try:
        # Navigate to the URL
        driver.get(url)

        # Wait for the profile-section elements to be present on the page
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'profile-section-item')))

        # Locate the profile-section elements
        education_sections = driver.find_elements(By.CLASS_NAME, 'field-group-field')

        for section in education_sections:
            try:
                # Extract label and value elements within each profile section
                labels = section.find_elements(By.CLASS_NAME, 'field-group-field-label')
                values = section.find_elements(By.CLASS_NAME, 'field-group-field-data')

                # Iterate through the label and value elements and add to the dictionary
                for label, value in zip(labels, values):
                    scraped_data[label.text] = value.text
            except NoSuchElementException as e:
                # Handle missing elements gracefully
                print(f"Warning (profile-section): {e}")

    except TimeoutException:
        print("Timed out waiting for page to load")

    finally:
        # Close the browser window in any case
        driver.quit()

    return scraped_data

# Initialize an empty DataFrame with possible columns from web scraping

initial_columns = ["License Number To Read", "Licensee Name", "License Type", "License Status", "First Name", "Middle Name", "Last Name",
                   "Address", "Issue Date", "Expiration Date", "Suspension Start Date",
                   "Suspension End Date", "Surrendered Date", "Revoked Date", "Void Date",
                   "Retirement Date", "School", "Degree"]

# Add more columns based on your specific needs

# Create the DataFrame
filtered_df = pd.DataFrame(columns=initial_columns)

# Read the CSV file into a DataFrame
csv_file_path = 'nurse_raw.csv'  # Replace with your actual CSV file path
df = pd.read_csv(csv_file_path)

df["License Number To Read"] = df.index + 402925

df['Full Name'] = df.apply(lambda row: f"{row['First Name']} {row['Middle Name']} {row['Last Name']}" if not pd.isna(row['Middle Name']) and row['Middle Name'] != '' else f"{row['First Name']} {row['Last Name']}", axis=1)

# Read the names from the .txt file into a list
txt_file_path = 'names.txt'  # Replace with your actual text file path
with open(txt_file_path, 'r') as file:
    names_to_filter = [line.strip() for line in file]

# Filter the DataFrame based on Physician Name
filtered_df = df[df['Full Name'].isin(names_to_filter)].copy()

for index, row in filtered_df.iterrows():
    license_number_suffix = str(row['License Number To Read'])
    url = f'https://checkahealthlicense.mass.gov/profiles/{license_number_suffix}'
    
    # Scrape data from the URL
    scraped_data = scrape_data(url)

    # Add the scraped data to the DataFrame
    for label, value in scraped_data.items():
        # Create a new column if it doesn't exist
        if label not in filtered_df.columns:
            filtered_df.loc[:, label] = ''
        # Set the value in the corresponding row and column
        filtered_df.at[index, label] = value

# Save the updated DataFrame to a new CSV file
filtered_csv_path = 'nurse_scraped.csv'
filtered_df.to_csv(filtered_csv_path, index=False)

print(f"Filtered data saved to {filtered_csv_path}")