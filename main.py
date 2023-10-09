#!python3.8
from bs4 import BeautifulSoup as BS

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import chromedriver_binary
import requests
import tempfile
import cv2
import os
import setting

class LifeFlyer:
    def __init__(self, store_url):
        self.images = self.getLifeFlyer(store_url)
        return

    def getLifeFlyer(self, url):
        images = []

        flyer_list = self.getFlyerLinkList(url)

        for link in flyer_list:
            image_link = self.convertTileURL2OriginalURL(self.getFlyerTileLink(link))
            images.append(self.getFlyer(image_link))

            if requests.get(image_link.replace("0.jpg", "1.jpg")).text != "":
                images.append(self.getFlyer(image_link.replace("0.jpg", "1.jpg")))

        return images

    def getFlyerLinkList(self, url):
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        # 読み込み待機
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located)
        except :
            print("タイムアウト")
            exit()
        
        html = driver.page_source
        driver.quit()

        data = BS(html, "html.parser")
        flyers = data.find_all("div", class_="shufoo-info-area")
        flyer_links = [tag.find("a").get("href") for tag in flyers]
        return flyer_links

    def getFlyerTileLink(self, url):
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        # 読み込み待機
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located)
        except :
            print("タイムアウト")
            exit()
        
        html = driver.page_source

        data = BS(html, "html.parser")

        # 基準になる部分が背景透過になるわけがないので画像が表示されるまでループさせる
        while(True):
            if data.find(id="0_0").find("img").get("src") == "http://asp.shufoo.net/site/chirashi_viewer_js/js/../images/transparent.png":
                driver.implicitly_wait(10)
                html = driver.page_source

                data = BS(html, "html.parser")
            else:
                break

        driver.quit()

        return data.find(id="0_0").find("img").get("src")

    def convertTileURL2OriginalURL(self, tile_image_url):
        return "https://asp.shufoo.net/oi.php?/c/" + "/".join([i for i in tile_image_url.split("/") if i.isdigit()]) + "/index/orig/0.jpg"

    def getFlyer(self, url):
        res = requests.get(url)

        fp = tempfile.NamedTemporaryFile(dir="./", delete=False)
        fp.write(res.content)
        fp.close()
        img = cv2.imread(fp.name)
        os.remove(fp.name)

        return img

def main():
    Flyer = LifeFlyer(setting.store_url)
    
    for i in range(len(Flyer.images)):
        cv2.imwrite(f"flyer_{i}.png", cv2.resize(Flyer.images[i], dsize=None, fx=0.25, fy=0.25))

    for i in range(len(Flyer.images)):
        with open(f"flyer_{i}.png", "rb") as f:
            file_bin = f.read()
        image = {f"flyer_{i}" : (f"flyer_{i}.png", file_bin)}
        res = requests.post(setting.webhook_url, files=image)
        print(res.status_code)

    for i in range(len(Flyer.images)): os.remove("flyer_{i}.png")

    return 0

if __name__ == "__main__":
    main()