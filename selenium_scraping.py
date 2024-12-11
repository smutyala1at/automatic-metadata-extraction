from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import json

driver = webdriver.Chrome()

ROWS = 48
page = 1
page_links = []

def get_software_page_links(page, ROWS, page_links):

    while True:
        driver.get(f"https://helmholtz.software/software?order=brand_name&page={page}&rows={ROWS}")
        driver.implicitly_wait(10)
        repo_list = driver.find_elements(By.CSS_SELECTOR, '[data-testid="software-masonry-card"]')
        href_links = [item.get_attribute('href') for item in repo_list]
        page_links.extend(href_links)
        page += 1
        if (len(href_links) < ROWS): 
            with open("./files/software_pages.json", "w", encoding="utf-8") as wf:
                json.dump({
                    "links": page_links
                }, wf)
            break
    driver.quit()


def get_repo_links(file_name_or_path):
    with open(file_name_or_path, "r", encoding="utf-8") as rf:
        file_content = json.load(rf)
        file_content["final_links"] = []
    
    for link in file_content["links"]:
        print("searching in ", link)
        driver.get(link)
        driver.implicitly_wait(10)
        try: 
            repo_link = driver.find_element(By.XPATH, '//a[@title="Github repository"]')
        except NoSuchElementException:
            try:
                repo_link = driver.find_element(By.XPATH, '//a[@title="Gitlab repository"]')
            except NoSuchElementException:
                repo_link = None
                print("Neither github nor gitlab link is found")

        if repo_link:
            file_content["final_links"].append(repo_link.get_attribute('href'))
            print("github_link: ", repo_link.get_attribute('href'))

    with open(file_name_or_path, "w", encoding="utf-8") as wf:
        json.dump(file_content, wf, ensure_ascii=False, indent=4)

#get_repo_links("./files/software_pages.json")
#get_software_page_links(page, ROWS, page_links)

