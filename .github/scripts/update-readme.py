import requests
import os
import re

REPO_OWNER = 'MartinHlavna'
REPO_NAME = 'hector'
README_FILE = 'README.md'
BEGIN_TAG = '<!-- BEGIN DOWNLOAD LINKS -->'
END_TAG = '<!-- END DOWNLOAD LINKS -->'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Hlavičky pre autentifikáciu
headers = {}
if GITHUB_TOKEN:
    headers['Authorization'] = f'Bearer {GITHUB_TOKEN}'


# Funkcia na získanie releasov z GitHub API
def get_releases():
    releases = []
    page = 1
    while True:
        url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases?page={page}'
        response = requests.get(url, headers=headers)
        data = response.json()
        if not data or 'message' in data:
            break
        releases.extend(data)
        page += 1
    return releases


# Funkcia na generovanie obsahu pre README.md
def generate_content(releases):
    beta_releases = [r for r in releases if r['prerelease']]
    stable_releases = [r for r in releases if not r['prerelease']]

    content = ''

    # Sekcia pre Stable
    if stable_releases:
        latest_stable = stable_releases[0]
        content += '## Stable\n\n'
        content += f'**Najnovšia verzia:** [{latest_stable["name"]}]({latest_stable["html_url"]})\n\n'
        content += '### Súbory:\n\n'
        content += '| Súbor | Stiahnuť |\n'
        content += '|------|----------|\n'
        for asset in latest_stable['assets']:
            content += f'| {asset["name"]} | [Stiahnuť]({asset["browser_download_url"]}) |\n'
        content += '\n'

    # Sekcia pre Beta
    if beta_releases:
        latest_beta = beta_releases[0]
        content += '## Beta\n\n'
        content += f'**Najnovšia testovacia verzia:** [{latest_beta["name"]}]({latest_beta["html_url"]})\n\n'
        content += '### Súbory:\n\n'
        content += '| Súbor | Stiahnuť |\n'
        content += '|------|----------|\n'
        for asset in latest_beta['assets']:
            content += f'| {asset["name"]} | [Download]({asset["browser_download_url"]}) |\n'
        content += '\n'

    return content


# Funkcia na aktualizáciu README.md
def update_readme(new_content):
    with open(README_FILE, 'r', encoding='utf-8') as f:
        readme = f.read()

    pattern = re.compile(
        rf'{BEGIN_TAG}.*?{END_TAG}',
        re.DOTALL
    )
    replacement = f'{BEGIN_TAG}\n{new_content}\n{END_TAG}'
    updated_readme = pattern.sub(replacement, readme)

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(updated_readme)


def main():
    releases = get_releases()
    if not releases:
        print('Žiadne verzie na stiahnutie.')
        return
    new_content = generate_content(releases)
    update_readme(new_content)
    print('README.md bol úspešne aktualizovaný.')


if __name__ == '__main__':
    main()
