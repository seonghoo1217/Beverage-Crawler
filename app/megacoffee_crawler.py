import requests
from bs4 import BeautifulSoup
import re
import json
import sys

def get_size_from_volume(volume_ml):
    """Maps volume in ml to a beverage size name."""
    return "MEGA", volume_ml

def infer_beverage_type_from_name(name: str, current_type: str) -> str:
    name_lower = name.lower()

    # Keywords for specific types
    if "커피" in name_lower or "아메리카노" in name_lower or ("라떼" in name_lower and "녹차" not in name_lower and "초코" not in name_lower):
        return "COFFEE"
    if "에이드" in name_lower or "주스" in name_lower:
        return "ADE_JUICE"
    if "스무디" in name_lower or "프라페" in name_lower or "쉐이크" in name_lower:
        return "SMOOTHIE_FRAPPE"
    if "티" in name_lower or "차" in name_lower or "녹차" in name_lower:
        return "TEA"
    if "초코" in name_lower or "핫초코" in name_lower:
        return "CHOCOLATE" # New type for chocolate beverages
    if "에스프레소" in name_lower:
        return "ESPRESSO"
    if "콜드 브루" in name_lower:
        return "COLD_BREW"
    if "블렌디드" in name_lower:
        return "BLENDED"
    if "피지오" in name_lower:
        return "FIZZIO"
    if "리프레셔" in name_lower:
        return "REFRESHER"

    # If no specific keyword, use the current_type from category_map or default to OTHERS
    if current_type == "BEVERAGE" or current_type == "OTHERS":
        return "OTHERS" # Keep it as OTHERS if it's a generic BEVERAGE
    return current_type # Otherwise, keep the type from category_map

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

    category_map = {
        1: "COFFEE",
        2: "BEVERAGE",
        3: "SMOOTHIE_FRAPPE",
        4: "ADE_JUICE",
        5: "TEA",
    }

    print("Starting Mega Coffee crawl.") # DEBUG
    # Iterate through beverage sub-categories
    for sub_category_code in range(1, 10):
        beverage_type = category_map.get(sub_category_code, "OTHERS")
        print(f"\nProcessing category code: {sub_category_code}, Type: {beverage_type}") # DEBUG

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
            
            print(f"  Page {page}: Found {len(items)} items.") # DEBUG

            # If no items are found, it means we've reached the last page for this category
            if not items:
                print(f"  No items found on page {page}. Breaking page loop for category {sub_category_code}.") # DEBUG
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

                volume_match = re.search(r"([0-9.]+)" + "ml", modal_text)
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
                inferred_beverage_type = infer_beverage_type_from_name(cleaned_name, beverage_type)

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
                        "beverageType": inferred_beverage_type,
                        "beverageTemperature": temperature,
                        "beverageNutritions": [nutrition_info]
                    })

    print(f"\nFinished Mega Coffee crawl. Total beverages found: {len(beverages)}") # DEBUG
    return beverages

if __name__ == '__main__':
    data = get_megacoffee_data()
    print(json.dumps(data, indent=4, ensure_ascii=False))