import requests
from bs4 import BeautifulSoup
import re
import json
import sys

def get_size_from_volume(volume_ml):
    """Maps volume in ml to a beverage size name."""
    if volume_ml <= 237:
        return "SHORT", 237
    elif volume_ml <= 355:
        return "TALL", 355
    elif volume_ml <= 473:
        return "GRANDE", 473
    elif volume_ml <= 591:
        return "VENTI", 591
    else:
        return "MEGA", volume_ml

def get_megacoffee_data():
    """
    Crawls Mega Coffee's official website to get beverage data, handling pagination.
    Returns a list of beverage dictionaries.
    """
    base_url = "https://www.mega-mgccoffee.com"
    menu_api_url = f"{base_url}/menu/menu.php"
    beverages = []

    headers = {
        'Referer': f'{base_url}/menu/menu_list.html'
    }

    # Iterate through beverage sub-categories
    for sub_category_code in range(1, 10):
        for page in range(1, 20): # Loop through a max of 19 pages (1 to 19)
            params = {
                'menu_category1': '1',
                'menu_category2': sub_category_code,
                'category': '',
                'list_checkbox_all': 'all'
            }
            if page > 1:
                params['page'] = page

            try:
                response = requests.get(menu_api_url, params=params, headers=headers)
                response.raise_for_status()
                response.encoding = 'utf-8'
            except requests.RequestException as e:
                print(f"Failed to fetch category {sub_category_code} page {page}: {e}", file=sys.stderr)
                break # Stop trying this category if a page fails

            soup = BeautifulSoup(response.text, 'lxml')
            items = soup.find_all("li")

            # If no items are found, it means we've reached the last page for this category
            if not items:
                break # Exit the page loop for this category

            for item in items:
                name_tag = item.select_one(".cont_text_title b")
                if not name_tag:
                    continue
                name = name_tag.text.strip()

                img_tag = item.select_one(".cont_gallery_list_img img")
                if not img_tag:
                    continue
                img_src = img_tag.get('src', '')

                modal = item.select_one(".inner_modal")
                if not modal:
                    continue
                
                modal_text = modal.get_text(separator=' ')

                volume_match = re.search(r"([0-9.]+)ml", modal_text)
                kcal_match = re.search(r"1회 제공량 ([0-9.]+)\s*kcal", modal_text)
                sugar_match = re.search(r"당류 ([0-9.]+)\s*g", modal_text)
                protein_match = re.search(r"단백질 ([0-9.]+)\s*g", modal_text)
                fat_match = re.search(r"포화지방 ([0-9.]+)\s*g", modal_text)
                sodium_match = re.search(r"나트륨 ([0-9.]+)\s*mg", modal_text)
                caffeine_match = re.search(r"카페인 ([0-9.]+)\s*mg", modal_text)

                volume_ml = float(volume_match.group(1)) if volume_match else 0
                if volume_ml == 0:
                    continue

                size_name, size_volume = get_size_from_volume(volume_ml)
                temperature = "ICED" if "(ICE)" in name.upper() or item.select_one(".cont_gallery_list_label2") else "HOT"

                nutrition_info = {
                    "size": size_name,
                    "volume": size_volume,
                    "servingKcal": float(kcal_match.group(1)) if kcal_match else 0,
                    "sugarG": float(sugar_match.group(1)) if sugar_match else 0,
                    "proteinG": float(protein_match.group(1)) if protein_match else 0,
                    "saturatedFatG": float(fat_match.group(1)) if fat_match else 0,
                    "sodiumMg": float(sodium_match.group(1)) if sodium_match else 0,
                    "caffeineMg": float(caffeine_match.group(1)) if caffeine_match else 0,
                }
                
                cleaned_name = name.replace("(HOT)", "").replace("(ICE)", "").strip()

                existing_beverage = next((b for b in beverages if b["name"] == cleaned_name), None)
                if existing_beverage:
                    is_duplicate = any(nutri['size'] == nutrition_info['size'] for nutri in existing_beverage["beverageNutritions"])
                    if not is_duplicate:
                        existing_beverage["beverageNutritions"].append(nutrition_info)
                else:
                    beverages.append({
                        "brand": "MEGA_COFFEE",
                        "name": cleaned_name,
                        "image": img_src,
                        "beverageType": str(sub_category_code),
                        "beverageTemperature": temperature,
                        "beverageNutritions": [nutrition_info]
                    })

    return beverages

if __name__ == '__main__':
    data = get_megacoffee_data()
    print(json.dumps(data, indent=4, ensure_ascii=False))