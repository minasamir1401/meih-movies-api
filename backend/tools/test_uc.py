import undetected_chromedriver as uc
import time

def test():
    print("Starting UC test...")
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        driver = uc.Chrome(options=options)
        print("Driver started successfully!")
        driver.get("https://www.google.com")
        print(f"Title: {driver.title}")
        driver.quit()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
