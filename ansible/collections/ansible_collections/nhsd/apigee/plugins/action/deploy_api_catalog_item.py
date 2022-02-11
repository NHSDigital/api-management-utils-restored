import json
from ansible_collections.nhsd.apigee.plugins.module_utils.apigee_action import (
    ApigeeAction,
)
from ansible_collections.nhsd.apigee.plugins.module_utils.models.ansible.deploy_api_catalog_item import (
    DeployApidoc,
)
from ansible_collections.nhsd.apigee.plugins.module_utils import constants
from ansible_collections.nhsd.apigee.plugins.module_utils import utils


class ActionModule(ApigeeAction):
    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        diff_mode = self._play_context.diff
        check_mode = self._play_context.check_mode
        args, errors = self.validate_args(DeployApidoc)
        if errors:
            return errors

        result = {"changed": False, "ansible_facts": {}}
        apidoc = args.api_catalog_item

        # This will fail if apigee_apidoc is called before apigee_spec
        # as APIGEE_SPEC_RESOURCES will not exist!
        if apidoc.specId:
            # TODO: here we loosen the selection criteria to just
            # pick the first match rather than asserting that
            # there has to be exactly 1 spec that matches.
            specs = list(
                filter(
                    lambda spec: spec["name"] == apidoc.specId,
                    task_vars["APIGEE_SPEC_RESOURCES"],
                )
            )

            if check_mode:
                # Then we never PUT this on the remote, so our entry has no 'id'
                apidoc.specContent = ""
            else:
                apidoc.specContent = specs[0]["id"]

        task_vars = utils.get_all_apidocs(
            args.organization, args.access_token, task_vars=task_vars
        )
        if task_vars.get("failed"):
            return task_vars

        try:
            existing_apidocs = utils.select_unique(
                task_vars["APIGEE_APIDOCS"],
                "edgeAPIProductName",
                apidoc.edgeAPIProductName,
            )
        except ValueError as e:
            return {
                "failed": True,
                "msg": f"Unable to find unique apidoc with edgeAPIProductName = {apidoc.specId}",
                "matching_apidocs": json.loads(str(e))
            }

        if len(existing_apidocs) == 1:
            current_apidoc = existing_apidocs[0]
            apidoc_id = current_apidoc["id"]
            url = constants.portal_uri(args.organization) + f"/{apidoc_id}"
            method = "PUT"
        else:
            method = "POST"
            url = constants.portal_uri(args.organization)
            current_apidoc = {}

        if apidoc.specId:
            # Look up matching specContent
            try:
                spec = next(
                    filter(
                        lambda spec: spec["name"] == apidoc.specId,
                        task_vars["APIGEE_SPEC_RESOURCES"],
                    )
                )
            except StopIteration as e:
                return {
                    "failed": True,
                    "msg": f"Unable to find spec named {apidoc.specId}",
                }
            apidoc.specContent = spec.get("id")
            if apidoc.specContent is None and not check_mode:
                raise RuntimeError(f"Could not get spec id from apidoc: {json.dumps(apidoc.dict())}")

        keys_to_ignore = [
            "apiId",
            "id",
            "categoryIds",
            "enrollment",
            "imageUrl",
            "modified",
            "productExists",
            "siteId",
            "snapshotExists",
            "snapshotModified",
            "snapshotOutdated",
            "snapshotSourceMissing",
            "snapshotState",
            "specModified",
            "specTitle",
        ]

        delta = utils.delta(
            current_apidoc, apidoc.dict(), keys_to_ignore=keys_to_ignore,
        )
        result["changed"] = bool(delta)

        if diff_mode:
            result["diff"] = [
                {
                    "before_header": current_apidoc.get("specId", ""),
                    "before": utils.exclude_keys(current_apidoc, keys_to_ignore),
                    "after_header": apidoc.specId,
                    "after": utils.exclude_keys(apidoc.dict(), keys_to_ignore),
                }
            ]

        if not delta or check_mode:
            return result

        apidoc_request = utils.request(
            method,
            url,
            args.access_token,
            json=apidoc.dict(),
            status_code=[200, 500]  # Allow 500 due to broken Apigee API.
        )
        if apidoc_request.get("failed"):
            return apidoc_request

        # Since we can't trust the return code...  we re-interrogate
        # the apidocs
        if method == "POST":
            # we were creating a new apidoc so we have no idea of the
            # apidoc id.  Therefore we need to get them all.
            apidocs = utils.get_all_apidocs(
                args.organization, args.access_token, refresh=True
            )
            if apidocs.get("failed"):
                return apidocs
            try:
                apidocs = utils.select_unique(
                    apidocs["APIGEE_APIDOCS"],
                    "edgeAPIProductName",
                    apidoc.edgeAPIProductName,
                    valid_lengths=[1],
                )
            except ValueError as e:
                return {
                    "failed": True,
                    "msg": f"Unable to find unique apidoc with edgeAPIProductName {apidoc.edgeAPIProductName}",
                    "matching_apidocs": json.loads(str(e)),
                }
            result["apidoc"] = apidocs[0]

        else:  # method == "PUT"
            apidoc_request = utils.get(url, args.access_token)
            if apidoc_request.get("failed"):
                return apidoc_request
            result["apidoc"] = apidoc_request["response"]["body"]["data"]

        if diff_mode:
            result["diff"][0]["after"] = utils.exclude_keys(
                result["apidoc"], keys_to_ignore
            )

        # Once spec apidoc deployed, update the snapshot
        apidoc_id = result["apidoc"]["id"]
        url = constants.portal_uri(args.organization) + f"/{apidoc_id}/snapshot"
        apidoc_snapshot_request = utils.put(url, args.access_token)
        if apidoc_snapshot_request.get("failed"):
            return apidoc_snapshot_request

        return result
