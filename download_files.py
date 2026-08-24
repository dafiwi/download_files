#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from bs4 import BeautifulSoup
from getpass import getpass
from pathlib import Path
import requests
import time
from urllib.parse import urljoin, urlparse, unquote


def enter_the_url():
    url = input("Please enter the URL: ").strip()
    if not url.endswith("/"):
        url += "/"

    return url


def check_authentication(session, url):
    response = session.get(url)

    if response.status_code == 401:
        authenticate_header = response.headers.get("WWW-Authenticate", "")

        if authenticate_header.lower().startswith("basic"):
            return "basic", response

        return "other", response

    if response.status_code == 403:
        return "forbidden", response

    response.raise_for_status()

    return None, response


def authenticate(session):
    username = input("Please enter the username: ")
    password = getpass("Please enter the password: ")

    session.auth = (username, password)

    return session


def check_authenticated_access(session, url):
    response = session.get(url)

    if response.status_code == 401:
        return "failed", response

    if response.status_code == 403:
        return "forbidden", response

    response.raise_for_status()

    return "success", response


def is_within_root(url, root_url):
    url_parts = urlparse(url)
    root_parts = urlparse(root_url)

    if url_parts.netloc != root_parts.netloc:
        return False

    url_path = url_parts.path
    root_path = root_parts.path

    if not root_path.endswith("/"):
        root_path += "/"

    return url_path.startswith(root_path)


def get_file_links(
    session,
    url,
    root_url,
    relative_path="",
    response=None
):
    file_links = []

    if response is None:
        response = session.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for link in soup.find_all("a", href=True):
        href = link["href"]

        link_text = link.get_text(strip=True)

        if (
            not href
            or href.startswith("#")
            or href in ("../", "..")
            or link_text.lower() == "parent directory"
        ):
            continue

        absolute_url = urljoin(url, href)

        if not is_within_root(absolute_url, root_url):
            continue

        if href.endswith("/"):
            directory_name = unquote(href.rstrip("/"))

            if directory_name in (".", ".."):
                continue

            new_relative_path = str(
                Path(relative_path) / directory_name
            )

            file_links.extend(
                get_file_links(
                    session,
                    absolute_url,
                    root_url,
                    new_relative_path
                )
            )

        else:
            file_links.append(
                (absolute_url, relative_path)
            )

    return file_links


def create_target_directory():
    print("\nAll files will be placed inside a directory in ~/Downloads.")
    directory_name = input("Please enter the name of the directory: ").strip()

    target_directory = Path.home() / "Downloads" / directory_name

    target_directory.mkdir(parents=True, exist_ok=True)

    return target_directory


def download_file(session, file_link, relative_path, target_directory):
    parsed_url = urlparse(file_link)

    filename = unquote(Path(parsed_url.path).name)

    if not filename:
        return "Invalid filename"

    destination_directory = target_directory / relative_path
    destination_directory.mkdir(parents=True, exist_ok=True)

    destination_file = destination_directory / filename
    temporary_file = destination_directory / f"{filename}.part"

    if destination_file.exists():
        return "Skipped"

    try:
        with session.get(file_link, stream=True) as response:
            response.raise_for_status()

            content_length = response.headers.get("Content-Length")

            with open(temporary_file, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)

        if content_length is not None:
            actual_size = temporary_file.stat().st_size

            if actual_size != int(content_length):
                temporary_file.unlink(missing_ok=True)

                return (
                    "File size mismatch: "
                    f"expected {content_length} bytes, "
                    f"received {actual_size} bytes"
                )

        temporary_file.replace(destination_file)

        return True

    except requests.RequestException as error:
        temporary_file.unlink(missing_ok=True)
        return f"HTTP error: {error}"

    except (OSError, ValueError) as error:
        temporary_file.unlink(missing_ok=True)
        return f"File error: {error}"


def main():
    print("\nDOWNLOAD FILES\n")

    url = enter_the_url()

    session = requests.Session()

    authentication, response = check_authentication(session, url)

    if authentication == "basic":
        print("HTTP Basic Authentication required.")

        session = authenticate(session)

        authentication, response = check_authenticated_access(session, url)

        if authentication == "failed":
            print("Authentication failed.")
            return

        if authentication == "forbidden":
            print("Access forbidden (HTTP 403).")
            return

    elif authentication == "other":
        print("The server requires another authentication method than HTTP Basic Authentication.")
        return

    elif authentication == "forbidden":
        print("Access forbidden (HTTP 403).")
        print("The server refused access to this URL.")
        return

    target_directory = create_target_directory()

    print("\nSearching for files...\n")

    file_links = get_file_links(
        session,
        url,
        url,
        response=response
    )

    print(f"Found {len(file_links)} files.\n")

    downloaded = 0
    skipped = 0
    failed = 0

    skipped_files = []
    failed_files = []

    download_start = time.time()

    for file_link, relative_path in file_links:

        print(f"Downloading: {file_link}")

        result = download_file(
            session,
            file_link,
            relative_path,
            target_directory
        )

        if result is True:
            print("  Downloaded successfully.\n")
            downloaded += 1

        elif result == "Skipped":
            print("  This file exists already and was skipped.\n")
            skipped += 1
            skipped_files.append(file_link)

        else:
            print(f"  {result}\n")
            failed += 1
            failed_files.append((file_link, result))

    download_end = time.time()
    download_duration = download_end - download_start

    print("\nDOWNLOAD FINISHED")
    print(f"Downloaded:         {downloaded}")
    print(f"Skipped:            {skipped}")
    print(f"Failed:             {failed}")
    print(f"Total:              {len(file_links)}")
    print(f"Download duration:  {download_duration:.2f} seconds")

    if skipped_files or failed_files:
        print("\nSTATUS REPORT")

    if skipped_files:
        print("\nSkipped:")
        for file_link in skipped_files:
            filename = unquote(Path(urlparse(file_link).path).name)
            print(f"  {filename} - Skipped")

    if failed_files:
        print("\nFailed:")
        for file_link, error in failed_files:
            filename = unquote(Path(urlparse(file_link).path).name)
            print(f"  {filename} - {error}")  


if __name__ == "__main__":
    main()