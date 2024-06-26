import requests
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import pandas as pd
import sys
import asyncio as aio
from aioconsole import ainput
import os
import re


search_field_selector = 'input[data-t="search-bar-search-term-input"]'
fetch_again_free_selector = '#details > div > div > div.row-flex-detailspanel > div.padding-actionpanel > div > div > div > div > div.container-block.padding-top-medium.row > div > div.detail-button-group > button'
download_preview_btn_selector = '#details > div > div > div.row-flex-detailspanel > div.flex-same-length > div.padding-left-large.padding-right-large > div > div.clear-fix.container--focus > div > div > span:nth-child(2) > div > button'


async def main():
    # wait for user to press enter
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(headless=False, user_data_dir='./playwrightData', accept_downloads=True)
        page = await browser.new_page()

        await page.goto('https://stock.adobe.com/se/')
        line = await ainput("Press enter when you have logged in to adobe stock photo. Then the script will begin.")

        files_data = pd.read_csv("files.csv")
        
        for index, row in files_data.iterrows():
            workingPage = await browser.new_page()
            asset_id = str(int(row['AdobeId']))
            completed = row['Completed']
            try:
                if(completed == True):
                    continue 
                print(f'Iterating on asset id: {asset_id}')

                await workingPage.goto('https://stock.adobe.com/se/')
                await workingPage.locator(search_field_selector).fill(asset_id)
                await workingPage.keyboard.press('Enter')

                async with workingPage.expect_download() as download_info:
                    try: 
                        download_free_btn = workingPage.locator(fetch_again_free_selector)
                        await download_free_btn.click()
                    except PlaywrightTimeoutError as timeoutEx:
                        raise timeoutEx
                    except Exception as ex:
                        print('Not licensed')
                        download_preview_btn = workingPage.locator(download_preview_btn_selector)
                        await download_preview_btn.click()
                
                    download = await download_info.value

                    file_extension = os.path.splitext(download.suggested_filename)[1]
                    filename = re.sub(r'[^\w_. -]', '_', f'{asset_id}{file_extension}')

                    await download.save_as(f'./Output/{filename}')
                    files_data.loc[index, ['Completed']] = True
                    files_data.to_csv('files.csv')
            except Exception as ex:
                print(f'Failed to download asset id: {asset_id}')
                print(ex)
            finally:
                await workingPage.close()
        print('Completed!') #190700247
        await browser.close()

aio.run(main())


#loop = aio.ProactorEventLoop()
#aio.set_event_loop(loop)

#loop = aio.get_event_loop()
#loop.run_until_complete(main())
#loop.close()
