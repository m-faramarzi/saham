from datetime import datetime

from utility.sahamyab_crawler import NewsCrawler
from utility.state import StateManager
from utility.storage import NewsStorage

def crawl():

    logging.info("Crawler started")

    state = StateManager(state_file="data/state.json")

    storage = NewsStorage(storage_path="data/news.json")

    crawler = NewsCrawler()

    # آخرین وضعیت crawl
    last_seen = state.get_last_seen()

    print(f"Last seen item: {last_seen}")

    # دریافت اخبار جدید
    news_items = crawler.fetch(last_seen=last_seen)

    if not news_items:
        logging.info("No new news found")
        return

    saved_count = 0

    latest_seen = last_seen

    for item in news_items:

        try:

            # جلوگیری از ذخیره تکراری
            if state.is_processed(item.id):
                continue

            # ذخیره خبر
            storage.save(item)

            # ثبت در state
            state.mark_processed(item.id, first_seen=item.first_seen)

            saved_count += 1

            # برای آپدیت آخرین خبر
            latest_seen = item.id

        except Exception:
            logging.exception(f"Error processing item {item.id}")

    # بروزرسانی آخرین وضعیت
    if latest_seen:
        state.update_last_seen(latest_seen)

    logging.info(f"Crawler finished. Saved: {saved_count}")


if __name__ == "__main__":
    crawl()
