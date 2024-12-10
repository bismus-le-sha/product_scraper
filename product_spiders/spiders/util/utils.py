def extract_links(response, link_selector, name_selector):
    item_map = {}
    elements = response.css(link_selector)

    for element in elements:
        name = element.css(name_selector + '::text').get()
        link = element.attrib.get('href')

        if name and link:
            full_link = response.urljoin(link)
            item_map[name.strip()] = full_link

    return item_map

def filter_items(item_map, excluded_items):
    return {
        name: url
        for name, url in item_map.items()
        if name not in excluded_items
    }
