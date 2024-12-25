from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import asyncio
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains
import pyperclip
import json

from dotenv import load_dotenv
load_dotenv()

USERNAME = os.getenv("USERNAME_")
PASSWORD = os.getenv("PASSWORD")
API_KEY = os.getenv("API_KEY")

if not USERNAME or not PASSWORD:
    raise ValueError("USERNAME or PASSWORD environment variables not set")


def update_csv_with_api_responses(input_csv_path, output_csv_path):
    df = pd.read_csv(input_csv_path)
    
    for index, row in df.iterrows():
        # Initialize the Chrome WebDriver once before the loop
        driver = webdriver.Chrome()
        prompt = row['prompt']
        url = "https://helmholtz-blablador.fz-juelich.de/"
        bot_content = insert_text_and_click_button(url, driver, prompt)

        # Create the conversation data as a list of dictionaries
        conversation_data = [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": bot_content}
        ]

        # Store the conversation data in the dataframe as a JSON string
        df.loc[index, 'conversation'] = json.dumps(conversation_data)
        driver.quit() 

    # Save the updated dataframe to the output CSV file
    df.to_csv(output_csv_path, index=False)


def insert_text_and_click_button(url, driver, text):
    try:
        driver.get(url)
        # Wait for the search input to be present
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#input-vaadin-text-field-53"))
        )
        print("Search input found")
        
        # Click the search input and type 'carl von'
        search_input.click()
        search_input.send_keys("carl von")
        print("Typed 'carl von' in search input")

        # Wait for the vaadin button to be clickable and click it
        vaadin_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//vaadin-button[contains(@class, 'u-signin-button') and contains(@class, 'u-idpAuthentication-samlWeb._entryFromMetadata_5613fa6eb2a7fb113a8cb374e9212986+1.') and contains(@class, 'u-text-left')]"))
        )
        vaadin_button.click()
        print("Vaadin button clicked successfully")

        username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='username']"))
        )
        username.click()
        username.send_keys(USERNAME)

        password = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='password']"))
        )
        password.click()
        password.send_keys(PASSWORD)

        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/main/div/div[1]/div/div[2]/form/input[4]"))
        )
        login_button.click()

        dropdown_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='component-11']/div[2]/div/div[1]/div/input"))
        )
        dropdown_input.clear()
        dropdown_input.send_keys("2 - ")
        dropdown_input.send_keys(Keys.ENTER)
        print("typed-2")

        click_parameters_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='component-20']/button"))
        )
        click_parameters_button.click()

        set_parameters_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='component-23']/div[2]/div/input"))
        )
        set_parameters_input.clear()
        set_parameters_input.send_keys("32720")
        print("typed-32720")
        set_parameters_input.send_keys(Keys.RETURN)

        click_parameters_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='component-20']/button"))
        )
        click_parameters_button.click()

        
        textarea = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[@id='input_box']/label/textarea"))
        )

        driver.execute_script("""
            var textarea = document.querySelector("#input_box textarea");
            textarea.value = arguments[0];
            textarea.dispatchEvent(new Event('input', { bubbles: true }));  // Trigger input event
            textarea.dispatchEvent(new Event('change', { bubbles: true })); // Trigger change event
        """, text)

        submit_button = driver.find_element(By.CSS_SELECTOR, "#component-15")
        driver.execute_script("arguments[0].click();", submit_button)


        time.sleep(70)

        message_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='message bot svelte-1s78gfg message-bubble-border']//span[@class='md svelte-8tpqd2 chatbot prose']"))
        )

        # Extract the text inside the <p> tag (which is inside the second span for bot's message)
        message_content = message_element.find_element(By.TAG_NAME, "p").text
        return message_content
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Set up the WebDriver (make sure to specify the correct path to your chromedriver)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    
    # Call the function with the metadata_dataset.csv file
    input_file = 'processed_metadata.csv'
    output_file = 'new.csv'
    update_csv_with_api_responses(input_file, output_file)
    print(f"Results saved to {input_file}")