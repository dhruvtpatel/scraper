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

        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.CLASS_NAME, 'profile-header-section-item')))

        profile_sections = driver.find_elements(By.CLASS_NAME, 'profile-header-section-item')

        for section in profile_sections:
            try:
                labels = section.find_elements(By.CLASS_NAME, 'profile-section-label')
                values = section.find_elements(By.CLASS_NAME, 'profile-section-value')

                for label, value in zip(labels, values):
                    scraped_data[label.text] = value.text
            except NoSuchElementException as e:
                print(f"Warning (profile-header-section-item): {e}")

        education_sections = driver.find_elements(By.CLASS_NAME, 'profile-sub-section')

        for section in education_sections:
            try:
                labels = section.find_elements(By.CLASS_NAME, 'sub-title')
                values = section.find_elements(By.CLASS_NAME, 'list-item')

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
initial_columns = ["Licensee Name", "Degree", "License Type", "License Number", "License Status", "Primary Work Setting",
                   "License Issue Date", "License Renewal Date", "License Expiration Date", "Business Address",
                   "Business Telephone", "Accepting New Patients", "Accepts Medicaid", "Translations Services Available",
                   "Insurance Plans Accepted", "Hospital Affiliations", "NPI Number", "Education", "Training", "ABMS Board Certification"]

filtered_df = pd.DataFrame(columns=initial_columns)

csv_file_path = 'physician_raw.csv'
df = pd.read_csv(csv_file_path)

txt_file_path = 'names.txt'  # Replace with actual text file path
with open(txt_file_path, 'r') as file:
    names_to_filter = [line.strip() for line in file]

filtered_df = df[df['Physician Name'].isin(names_to_filter)].copy()

for index, row in filtered_df.iterrows():
    license_number_suffix = str(row['License Number'])
    url = f'https://findmydoctor.mass.gov/profiles/{license_number_suffix}'
    
    scraped_data = scrape_data(url)

    for label, value in scraped_data.items():
        if label not in filtered_df.columns:
            filtered_df.loc[:, label] = ''
        filtered_df.at[index, label] = value

filtered_csv_path = 'physician_scraped.csv'
filtered_df.to_csv(filtered_csv_path, index=False)

print(f"Filtered data saved to {filtered_csv_path}")