from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import json
import asyncio

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
            with open("../files/links.json", "w", encoding="utf-8") as wf:
                json.dump({
                    "page_links": page_links
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
                file_content["final_links"].append({
                    "software_organization": link,
                    "repo_link": ""
                })
                print("Neither github nor gitlab link is found")

        if repo_link:
            file_content["final_links"].append({
                "software_organization": link,
                "repo_link": repo_link.get_attribute('href')
            })
            print("github_link: ", repo_link.get_attribute('href'))

    with open(file_name_or_path, "w", encoding="utf-8") as wf:
        json.dump(file_content, wf, ensure_ascii=False, indent=4)

async def get_gitlab_project_id(repo_link):

    try:
        driver.get(repo_link)
    except Exception as e:
        return ""
    
    driver.implicitly_wait(10)

    try: 
        span_element = driver.find_element(By.XPATH, "//span[@itemprop='identifier' and @data-testid='project-id-content']")
        project_id = span_element.text.strip().split(" ")[2]
        return project_id
    except NoSuchElementException:
        try:
            alert = driver.find_element(By.CLASS_NAME, "gl-alert-body")
            return ""
        except NoSuchElementException:
            return ""
        
#get_software_page_links(page, ROWS, page_links)
#get_repo_links("../files/links.json")
