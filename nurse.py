import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def scrape_data(url):
    
    driver = webdriver.Chrome()
    
    scraped_data = {}

    try:
        driver.get(url)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'profile-section-item')))

        education_sections = driver.find_elements(By.CLASS_NAME, 'field-group-field')

        for section in education_sections:
            try:
                labels = section.find_elements(By.CLASS_NAME, 'field-group-field-label')
                values = section.find_elements(By.CLASS_NAME, 'field-group-field-data')

                for label, value in zip(labels, values):
                    scraped_data[label.text] = value.text
            except NoSuchElementException as e:
                print(f"Warning (profile-section): {e}")

    except TimeoutException:
        print("Timed out waiting for page to load")

    finally:
        driver.quit()

    return scraped_data

# List of columns in raw .csv and in sub-pages
initial_columns = ["License Number To Read", "Licensee Name", "License Type", "License Status", "First Name", "Middle Name", "Last Name",
                   "Address", "Issue Date", "Expiration Date", "Suspension Start Date",
                   "Suspension End Date", "Surrendered Date", "Revoked Date", "Void Date",
                   "Retirement Date", "School", "Degree"]

filtered_df = pd.DataFrame(columns=initial_columns)

csv_file_path = 'nurse_raw.csv'
df = pd.read_csv(csv_file_path)

# Accounts for license numbers being arbitrary among RNs
df["License Number To Read"] = df.index + 402925

df['Full Name'] = df.apply(lambda row: f"{row['First Name']} {row['Middle Name']} {row['Last Name']}" if not pd.isna(row['Middle Name']) and row['Middle Name'] != '' else f"{row['First Name']} {row['Last Name']}", axis=1)

txt_file_path = 'names.txt'  # Replace with actual text file path
with open(txt_file_path, 'r') as file:
    names_to_filter = [line.strip() for line in file]

filtered_df = df[df['Full Name'].isin(names_to_filter)].copy()

for index, row in filtered_df.iterrows():
    license_number_suffix = str(row['License Number To Read'])
    url = f'https://checkahealthlicense.mass.gov/profiles/{license_number_suffix}'
    
    scraped_data = scrape_data(url)

    for label, value in scraped_data.items():
        if label not in filtered_df.columns:
            filtered_df.loc[:, label] = ''
        filtered_df.at[index, label] = value

filtered_csv_path = 'nurse_scraped.csv'
filtered_df.to_csv(filtered_csv_path, index=False)

print(f"Filtered data saved to {filtered_csv_path}")