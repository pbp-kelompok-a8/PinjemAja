import unittest
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class ProfileFunctionalTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            options = webdriver.EdgeOptions()
            options.add_argument('--headless=new')
            options.add_argument('--window-size=1280,1200')
            cls.browser = webdriver.Edge(options=options)
        except Exception as exc:
            super().tearDownClass()
            raise unittest.SkipTest(f'Browser driver tidak tersedia: {exc}')
        cls.wait = WebDriverWait(cls.browser, 10)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def fill(self, **fields):
        for name, value in fields.items():
            self.browser.find_element(By.NAME, name).send_keys(value)

    def click(self, element):
        self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        try:
            element.click()
        except ElementClickInterceptedException:
            self.browser.execute_script("arguments[0].click();", element)

    def submit(self):
        self.click(self.browser.find_element(By.CSS_SELECTOR, 'form button[type="submit"]'))

    def test_register_via_browser(self):
        self.browser.get(f'{self.live_server_url}/profile/register/')
        self.fill(username='seleniumuser', email='sel@test.com',
                  password1='ComplexPass123!', password2='ComplexPass123!')
        self.submit()
        self.wait.until(EC.url_contains('/profile/me/'))
        self.assertTrue(User.objects.filter(username='seleniumuser').exists())

    def test_login_then_edit_bio(self):
        User.objects.create_user('selenium2', 'sel2@test.com', 'ComplexPass123!')
        self.browser.get(f'{self.live_server_url}/profile/login/')
        self.fill(username='selenium2', password='ComplexPass123!')
        self.submit()
        self.wait.until(lambda d: '/profile/login' not in d.current_url)

        self.browser.get(f'{self.live_server_url}/profile/edit/')
        self.browser.find_element(By.ID, 'id_bio').send_keys('Halo dari Selenium')
        self.click(self.browser.find_element(
            By.CSS_SELECTOR, 'form#edit-profile-form-container button[type="submit"]'))
        self.wait.until(EC.url_contains('/profile/me/'))
        self.assertIn('Halo dari Selenium', self.browser.page_source)