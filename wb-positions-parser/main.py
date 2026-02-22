import asyncio
from playwright.async_api import async_playwright, ViewportSize, Page
import models
from sqlmodel import Session


async def parse_positions(page: Page, key: str, limit: int) -> list[dict]:
    """
    Метод для парса карточек товаров

    :param page: объект страницы Playwright
    :param key: запрос для поиска на ВБ
    :param limit: количество, которое необходимо парсить
    :return: список словарей, где каждый словарь — информация по карточке
    """

    # 1. Находим поиск, вбиваем ключ и жмем Enter
    search_input = page.locator("#searchInput")
    await search_input.click()  # Кликаем, чтобы фокус точно был там

    await search_input.press_sequentially(key, delay=150)
    await asyncio.sleep(1)  # Потупили секунду
    await page.keyboard.press("Enter")

    # Ждем, пока в URL появится поисковый запрос (или просто слово search)
    await page.wait_for_url(lambda url: "search" in url.lower(), timeout=10000)

    # Ждем появления товаров
    await page.wait_for_selector(".product-card", state="visible")
    await asyncio.sleep(2)

    # 2. Скролим вниз, чтобы товары подгрузились (имитация человека), собираем карточки товаров
    while True:
        items = await page.locator(".product-card").all()
        if len(items) >= limit:  # Если набрали нужное количество
            break
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)  # Даем время на подгрузку

    # 3. Собираем карточки товаров
    results = []
    for i, item in enumerate(items[:limit], start=1):

        # Вытаскиваем артикул
        sku = await item.get_attribute("data-nm-id")
        # Ссылка
        link = f"https://www.wildberries.ru/catalog/{sku}/detail.aspx"
        data = {
            "position": i,
            "sku": sku,
            "link": link,
            "key": key
        }

        results.append(data)

    return results


async def main() -> None:
    """
    Основной процесс для запуска браузера и
    сохранения в базу данных полученных данных парсинга

    :return: None
    """

    models.create_db_and_tables()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False,
                                          args=["--disable-blink-features=AutomationControlled"])  # Видим процесс, маскируемся от сайта
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport=ViewportSize(width=1920, height=1080))  # "Досье" и имитация экрана человека

        page = await context.new_page()

        await page.goto("https://www.wildberries.ru", wait_until="networkidle")
        await page.wait_for_selector("#searchInput", state="visible", timeout=15000)

        # Запускаем наш метод
        items = await parse_positions(page, "гель для стирки", limit=10)

        with Session(models.engine) as session:
            for item in items:
                # Создаем объект
                db_position = models.WBPosition(**item)
                session.add(db_position)

            session.flush()
            session.commit()  # Сохраняем в Postgres

        # await asyncio.sleep(60)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
