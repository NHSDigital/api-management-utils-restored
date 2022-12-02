"""
Script to force unlock locks in terraform with a given prefix and of a certain age.

Warning this script should be used with care.

This script has to be used because sometimes the ecs pr pipeline cleanup won't always properly release the lock when
it fails.

CLI arguments:
    --min-age-hr
    --key-prefix
    --table-name
    --profile

Example usage:

python ./terraform_force_unlock.py --min-age-hr=8 --key-prefix=nhsd-apm-management-ptl-terraform/env:/api-deployment:ptl: --table-name=terraform-state-lock --profile=apm_ptl

"""

import boto3
import dateutil
import datetime
import click


@click.command()
@click.option("--min-age-hr", type=int, default=8)
@click.option("--key-prefix", type=str, default="nhsd-apm-management-ptl-terraform/env:/api-deployment:ptl:")
@click.option("--table-name", type=str, default="terraform-state-lock")
@click.option("--profile", type=str, default="apm_ptl")
def main(min_age_hr, key_prefix, table_name, profile):

    accepted_envs = ["apm_ptl", "apm_prod"]

    if profile not in accepted_envs:
        raise ValueError("Profile must be apm_ptl or apm_prod")

    terraform_lock_table = boto3.Session(profile_name=profile).resource("dynamodb").Table(table_name)

    filter_expr = "begins_with(#n0, :v0) AND attribute_exists(#n1)"

    ExpressionAttributeNames = {"#n0": "LockID", "#n1": "Info"}
    ExpressionAttributeValues = {
        ":v0": "nhsd-apm-management-ptl-terraform/env:/api-deployment:ptl:"
    }
    items = terraform_lock_table.scan(FilterExpression=filter_expr, ExpressionAttributeNames=ExpressionAttributeNames, ExpressionAttributeValues=ExpressionAttributeValues)
    print(f"Found {len(items['Items'])} locks which start with key prefix '{key_prefix}'")

    removed_count = 0
    for lock_item in items["Items"]:
        lock_item_info = lock_item["Info"]
        lock_id = lock_item["LockID"]
        created_at = dateutil.parser.parse(lock_item_info["Created"])

        if datetime.datetime.now(datetime.timezone.utc) - created_at > datetime.timedelta(hours=min_age_hr):
            print(f"{lock_id} {created_at=} is more than {min_age_hr} hours old, deleting lock...")
            terraform_lock_table.delete_item(Key={"LockID": lock_id})
            removed_count += 1

        else:
            print(f"{lock_id} {created_at=} is not more than {min_age_hr} hours old, leaving it alone!")

    print(f"Removed {removed_count} locks")


if __name__ == "__main__":
    main()
