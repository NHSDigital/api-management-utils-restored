import collections
import re
from typing import List


def apigee_apps_to_product_map(apps_list: List[dict], product_filter: str = None):

    result = dict()

    not_matched = []

    for app in apps_list:

        credentials = app.get('credentials', [])

        for cred in credentials:

            api_products = cred.get('apiProducts', [])

            for product in api_products:
                api_product = product['apiproduct']
                if product_filter and not re.match(product_filter, api_product):
                    not_matched.append(api_product)
                    continue

                if api_product not in result:
                    result[api_product] = []

                result[api_product].append(
                    dict(
                        appId=app["appId"],
                        appName=app["name"],
                        developerId=app.get("developerId"),
                        companyName=app.get("companyName"),
                        consumerKey=cred["consumerKey"],
                        apiproduct=api_product
                     )
                )
    for product in sorted(set(not_matched)):
        print(f'did not match: {product}')
    return result


def apigee_products_to_api_map(products: List[dict], proxy_filter: str = None):

    result = dict()

    not_matched = []

    for product in products:

        proxies = product.get('proxies', [])

        for proxy in proxies:

            if proxy_filter and not re.match(proxy_filter, proxy):
                not_matched.append(proxy)
                continue

            if proxy not in result:
                result[proxy] = []

            result[proxy].append(product['name'])

    for proxy in sorted(set(not_matched)):
        print(f'did not match: {proxy}')
    return result


def apigee_remove_proxy_from_product(product: dict, proxy_to_remove):
    product["proxies"] = [
        p for p in product.get("proxies", [])
        if p != proxy_to_remove
    ]
    return product


def apigee_teams_map(teamMembers: List[dict], teams: List[dict]):
    joined = collections.defaultdict(dict)
    for item in teamMembers + teams:
        joined[item['name']].update(item)
    full_teams = list(joined.values())

    return {
        team['name']: {
            "contact": next((attr.get('value') for attr in team['attributes'] if attr['name'] == 'ADMIN_EMAIL'), {}),
            "members": team['members']
        }
        for team in full_teams
    }


def apigee_teams_to_point_of_contact(teams: List[dict]):

    return {
        next((attr.get('value') for attr in team['attributes'] if attr['name'] == 'ADMIN_EMAIL'), {})
        for team in teams
    }


def apigee_teams_to_members(teams: List[dict]):

    return {
        team.get('members', []) for team in teams
    }


def apigee_product_developers(
    product_app_map: dict, dev_id_to_email: dict, teams_map: dict, product_filter: str = None
):
    if not product_app_map:
        raise ValueError('product_app_map not set')

    if not dev_id_to_email:
        raise ValueError('dev_id_to_email not set')

    teams_map = teams_map or {}
    result = {}
    for product_name, apps in product_app_map.items():
        if product_filter and not re.match(product_filter, product_name):
            continue
        if product_name not in result:
            result[product_name] = []

        for app in apps:
            entry = {
                "app": app["appName"]
            }

            team = teams_map.get(app.get("companyName"), {})

            if team:
                entry['developer'] = team['contact']
                entry['team'] = team['members']
            else:
                entry['developer'] = dev_id_to_email[app["developerId"]]

            result[product_name].append(entry)

    result = {
        key: sorted(apps, key=lambda x: x['app']) for key, apps in result.items()
    }

    return result


class FilterModule:

    @staticmethod
    def filters():
        return {
            # jinja2 overrides
            'apigee_apps_to_product_map': apigee_apps_to_product_map,
            'apigee_products_to_api_map': apigee_products_to_api_map,
            'apigee_remove_proxy_from_product': apigee_remove_proxy_from_product,
            'apigee_teams_to_point_of_contact': apigee_teams_to_point_of_contact,
            'apigee_teams_to_members': apigee_teams_to_members,
            'apigee_teams_map': apigee_teams_map,
            'apigee_product_developers': apigee_product_developers
        }
