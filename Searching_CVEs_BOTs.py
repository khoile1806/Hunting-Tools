import logging
import asyncio
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from collections import Counter
from telegram import Update, InputFile
from deep_translator import GoogleTranslator
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackContext

TELEGRAM_BOT_TOKEN = ""
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
MAX_MESSAGE_LENGTH = 4000
MAX_CVE_MESSAGES = 5

async def translate_text(text, target_language="vi"):
    try:
        return GoogleTranslator(source="auto", target=target_language).translate(text)
    except Exception:
        return text

async def search_cve(keyword, year=None, translate_lang="vi"):
    encoded_keyword = quote(keyword)
    search_url = f"https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword={encoded_keyword}"

    try:
        print("🔍 Searching for CVEs...")
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return [f"⚠️ Lỗi khi lấy dữ liệu: {e}"], None

    soup = BeautifulSoup(response.text, "html.parser")
    results_table = soup.find("div", {"id": "TableWithRules"})

    if not results_table:
        return ["❌ Không tìm thấy CVE nào."], None

    cve_list = []
    year_counts = Counter()
    rows = results_table.find_all("tr")[1:]
    total_cve_found = 0
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            cve_id = cols[0].get_text(strip=True)
            description = cols[1].get_text(strip=True)
            cve_year = cve_id.split("-")[1] if "-" in cve_id else "Unknown"

            if year and cve_year != str(year):
                continue

            translated_description = await translate_text(description, translate_lang)
            cve_url = f"https://www.cve.org/CVERecord?id={cve_id}"

            cve_list.append(f"🔹 *{cve_id}*\n🔗 [Chi tiết]({cve_url})\n📜 {translated_description}\n")
            year_counts[cve_year] += 1
            total_cve_found += 1

    if not cve_list:
        return [f"❌ Không tìm thấy CVE nào cho từ khóa \"{keyword}\" trong năm {year}."], None

    year_summary = "📊 Số lượng CVE theo từng năm:\n" + "\n".join(
        [f"- {y}: {c}" for y, c in sorted(year_counts.items(), reverse=True)])
    messages = [year_summary] + cve_list[:MAX_CVE_MESSAGES]
    remaining_cves = cve_list[MAX_CVE_MESSAGES:]
    if remaining_cves:
        file_path = "cve_results.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(remaining_cves))
        return messages, file_path

    return messages, None

async def handle_message(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    parts = text.split()
    keyword = " ".join(parts[:-1]) if parts[-1].isdigit() else text
    year = parts[-1] if parts[-1].isdigit() else None
    await update.message.reply_text("⏳ Đang tìm kiếm, vui lòng chờ...", parse_mode="Markdown")
    responses, file_path = await search_cve(keyword, year)

    for response in responses:
        await update.message.reply_text(response, parse_mode="Markdown", disable_web_page_preview=True)

    if file_path:
        with open(file_path, "rb") as file:
            await update.message.reply_document(InputFile(file, filename="CVE_Results.txt"))

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "🤖 Xin chào! Gửi từ khóa để tôi tìm CVE cho bạn. Ví dụ: \n\n`log4j 2021` để tìm CVE liên quan đến log4j trong năm 2021.",
        parse_mode="Markdown")

async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "🔍 *Hướng dẫn sử dụng Bot tìm kiếm CVE* 🔍\n\n"
        "1️⃣ Gửi một từ khóa để tìm CVE liên quan, ví dụ: `log4j`\n"
        "2️⃣ Bạn có thể chỉ định năm, ví dụ: `log4j 2021`\n"
        "3️⃣ Nếu danh sách CVE quá dài, tôi sẽ gửi 7 CVEs đầu tiên qua tin nhắn và phần còn lại dưới dạng file.\n"
        "4️⃣ Tôi sẽ hiển thị số lượng CVE theo từng năm để bạn dễ theo dõi.\n\n"
        "📌 Sử dụng lệnh `/start` để bắt đầu, `/help` để xem hướng dẫn."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()