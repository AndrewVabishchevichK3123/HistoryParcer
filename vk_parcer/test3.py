import re
from playwright.sync_api import Playwright, sync_playwright, expect

def test_successful_login(playwright: Playwright) -> None:
    """
    Тест 1: Проверка успешной авторизации пользователя.
    """
    browser = playwright.chromium.launch(headless=False) # headless=True для запуска в фоне
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://opensource-demo.orangehrmlive.com/")
    
    page.get_by_placeholder("Username").fill("Admin")
    page.get_by_placeholder("Password").fill("admin123")
    
    page.get_by_role("button", name="Login").click()
    
    expect(page).to_have_url(re.compile(r".*/dashboard/index$"))
    expect(page.locator("h6").filter(has_text="Dashboard")).to_be_visible()

    context.close()
    browser.close()


def test_add_new_employee(playwright: Playwright) -> None:
    """
    Тест 2: Проверка добавления нового сотрудника в систему.
    Предполагается, что мы уже авторизованы.
    """
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://opensource-demo.orangehrmlive.com/")
    page.get_by_placeholder("Username").fill("Admin")
    page.get_by_placeholder("Password").fill("admin123")
    page.get_by_role("button", name="Login").click()

    page.locator("span:has-text('PIM')").click()
    expect(page).to_have_url(re.compile(r".*/pim/viewEmployeeList$"))

    page.locator("button:has-text('Add')").click()
    expect(page).to_have_url(re.compile(r".*/pim/addEmployee$"))

    first_name = "Иван"
    last_name = "Петров"
    page.get_by_placeholder("First Name").fill(first_name)
    page.get_by_placeholder("Last Name").fill(last_name)
    
    employee_id = page.locator(":nth-match(.oxd-input, 5)").input_value()

    page.locator("button[type='submit']").click()

    expect(page).to_have_url(re.compile(r".*/pim/personalDetails/.*"))
    expect(page.locator("h6").filter(has_text="Personal Details")).to_be_visible()

    page.locator("span:has-text('Employee List')").click()
    expect(page).to_have_url(re.compile(r".*/pim/viewEmployeeList$"))

    page.locator(":nth-match(.oxd-input, 2)").fill(employee_id)
    page.locator("button:has-text('Search')").click()

    expect(page.locator("div.oxd-table-row", has_text=employee_id)).to_be_visible()
    expect(page.locator("div.oxd-table-row", has_text=first_name)).to_be_visible()
    expect(page.locator("div.oxd-table-row", has_text=last_name)).to_be_visible()

    context.close()
    browser.close()
