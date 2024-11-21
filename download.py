from http.client import HTTPSConnection, HTTPConnection
from threading import Thread
from urllib.parse import urlparse
import time
import os
import sys

# Глобальные переменные для хранения количества загруженных байтов
downloaded_bytes = 0
download_complete = False
MAX_REDIRECTS = 5  # Максимальное количество перенаправлений


def download_file(url):
    global downloaded_bytes, download_complete

    redirect_count = 0

    while redirect_count < MAX_REDIRECTS:
        # Разбор URL
        parsed_url = urlparse(url)

        # Выбираем тип соединения на основе схемы URL
        if parsed_url.scheme == "https":
            conn = HTTPSConnection(parsed_url.netloc)
        else:
            conn = HTTPConnection(parsed_url.netloc)

        try:
            # Выполняем GET-запрос
            conn.request("GET", parsed_url.path)
            response = conn.getresponse()

            # Обработка перенаправлений
            if response.status in {301, 302, 303}:
                # Извлекаем новый URL из заголовка Location
                new_url = response.getheader("Location")
                if new_url:
                    url = new_url
                    print(f"Перенаправление на {url}")
                    redirect_count += 1
                    continue
                else:
                    print("Ошибка: отсутствует заголовок Location для перенаправления.")
                    download_complete = True
                    return

            # Проверка успешности запроса
            if response.status != 200:
                print(f"Ошибка: {response.status} {response.reason}")
                download_complete = True
                return

            # Имя файла берем из URL
            filename = os.path.basename(parsed_url.path)
            if not filename:
                print("Ошибка: не удалось определить имя файла.")
                download_complete = True
                return

            # Открываем файл для записи
            with open(filename, "wb") as file:
                while chunk := response.read(1024):
                    file.write(chunk)
                    downloaded_bytes += len(chunk)

            print("Загрузка завершена.")
            break

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            break

        finally:
            conn.close()

    download_complete = True  # Устанавливаем после успешного завершения загрузки

    if redirect_count >= MAX_REDIRECTS:
        print("Ошибка: превышено максимальное количество перенаправлений.")
        download_complete = True


def progress_report():
    while not download_complete:
        print(f"Загружено байтов: {downloaded_bytes}")
        time.sleep(1)
    # Последний вывод для окончательного размера
    print(f"Загружено байтов: {downloaded_bytes}")


def main():
    if len(sys.argv) < 2:
        print("Использование: python download.py <URL>")
        return

    url = sys.argv[1]

    # Запускаем потоки для загрузки файла и вывода прогресса
    download_thread = Thread(target=download_file, args=(url,))
    progress_thread = Thread(target=progress_report)

    download_thread.start()
    progress_thread.start()

    # Дожидаемся завершения загрузки
    download_thread.join()
    progress_thread.join()


if __name__ == "__main__":
    main()
