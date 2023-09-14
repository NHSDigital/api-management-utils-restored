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

                company_exists = "companyName" in app.keys()
                developer_exists = "developerId" in app.keys()
                if developer_exists and not company_exists:
                    owner = app["developerId"]
                elif company_exists and not developer_exists:
                    owner = app["companyName"]
                else:
                    raise RuntimeError(f"Invalid owner for app {app['appId']}")

                result[api_product].append(
                    dict(
                        appId=app["appId"],
                        appName=app["name"],
                        owner=owner,
                        ownerEndpoint="companies" if company_exists else "developers",
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


def apigee_teams_map(teams: List[dict]):

    return {
        f"{team['id']}@devteam.apigee.io": {
            "contact": team['pointOfContact'],
            "members": list(mem['userId'] for mem in team.get('memberships', []))
        }
        for team in teams
    }


def apigee_teams_to_point_of_contact(teams: List[dict]):

    return {
        f"{team['id']}@devteam.apigee.io": team['pointOfContact'] for team in teams
    }


def apigee_teams_to_members(teams: List[dict]):

    return {
        f"{team['id']}@devteam.apigee.io": list(mem['userId'] for mem in team.get('memberships', [])) for team in teams
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
            developer = dev_id_to_email[app["developerId"]]

            team = teams_map.get(developer, {})

            entry = {
                "app": app["appName"],
                "developer": developer
            }

            if team:
                entry['developer'] = team['contact']
                entry['team'] = team['members']

            result[product_name].append(entry)

    result = {
        key: sorted(apps, key=lambda x: x['app']) for key, apps in result.items()
    }

    return result

    # return {
    #     f"{team['id']}@devteam.apigee.io": list(mem['userId'] for mem in team.get('memberships', [])) for team in teams
    # }


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
