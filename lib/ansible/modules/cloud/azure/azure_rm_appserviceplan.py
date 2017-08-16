#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'curated'
}

DOCUMENTATION = '''
    hi
'''

EXAMPLES = '''
    wao
'''

RETURN = '''
    omg
'''

from ansible.module_utils.azure_rm_common import AzureRMModuleBase

try:
    from azure.common import AzureHttpError
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.web.models import AppServicePlan
    from azure.mgmt.web.models import SkuDescription
except ImportError:
    pass


def appserviceplan_to_dict(appserviceplan):
    return dict(
        id=appserviceplan.id,
        name=appserviceplan.name,
        tags=appserviceplan.tags,
    )


def _get_sku_name(tier):
    tier = tier.upper()
    if tier == 'F1':
        return 'FREE'
    elif tier == 'D1':
        return 'SHARED'
    elif tier in ['B1', 'B2', 'B3']:
        return 'BASIC'
    elif tier in ['S1', 'S2', 'S3']:
        return 'STANDARD'
    elif tier in ['P1', 'P2', 'P3']:
        return 'PREMIUM'


class AzureRMAppServicePlan(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            resource_group_name=dict(type='str', required=True),
            resource_group_location=dict(type='str', required=False),
            app_service_plan_name=dict(type='str', required=True),
            app_service_plan_worker_count=dict(type='str', required=False),
            app_service_plan_worker_size_id=dict(type='str', required=False),
            admin_site_name=dict(type='str', required=False),
            worker_tier_name=dict(type='str', required=False),
            reserved=dict(type='bool', required=False),
            per_site_scaling=dict(type='bool', required=False),
            hosting_environment_profile=dict(type='str', required=False),
            state=dict(
                type='str',
                required=False,
                default='present',
                choices=['present', 'absent']
            ),
            sku=dict(type='str', required=False, default='B1')
        )

        # Name is actually the resource group.
        self.resource_group_name = None
        self.resource_group_location = None
        self.app_service_plan_name = None
        self.app_service_plan_worker_count = None
        self.app_service_plan_worker_size_id = None
        self.admin_site_name = None
        self.worker_tier_name = None
        self.reserved = None
        self.state = None
        self.tags = None
        self.per_site_scaling = None
        self.hosting_environment_profile = None

        self.type = "Microsoft.Web/serverfarms"
        self.kind = "app"
        self.sku = None

        self.results = dict(changed=False, state=dict())

        super(AzureRMAppServicePlan, self).__init__(
            derived_arg_spec=self.module_arg_spec,
            supports_check_mode=True,
            supports_tags=True
        )

    def exec_module(self, **kwargs):
        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        resource_group_obj = None

        try:
            resource_group_obj = self.get_resource_group(
                self.resource_group_name
            )
        except CloudError:
            self.fail('resource group {0} not found'.format(
                self.resource_group_name
            ))

        if not self.resource_group_location:
            self.resource_group_location = resource_group_obj.location

        if (self.state == 'present'):
            # create
            response = self.get_appserviceplan()

            if not response:
                self.results['state'] = self.create_appserviceplan()
            else:
                self.log("App Service Plan exists, updating tags")
                update_tags, self.tags = self.update_tags(
                    self.tags
                )

                if update_tags:
                    self.create_appserviceplan()
                    self.results['changed'] = True
        else:
            # delete
            self.delete_appserviceplan()

        return self.results

    def get_appserviceplan(self):
        self.log("Checking if the App Service Plan {0} is present".format(
            self.app_service_plan_name
        ))

        found = False
        try:
            response = self.web_client.app_service_plans.get(
                self.resource_group_name,
                self.app_service_plan_name
            )

            found = True
        except CloudError as e:
            self.log("Did not find app service plan")

        if found:
            return appserviceplan_to_dict(response)

        return False

    def create_appserviceplan(self):
        self.log("Creating App Service Plan {0}".format(
            self.app_service_plan_name
        ))

        try:
            self.log('before app service plan create')

            sku_params = SkuDescription(
                tier=_get_sku_name(self.sku),
                name=self.sku,
                capacity=self.app_service_plan_worker_count
            )

            app_service_plan_params = AppServicePlan(
                location=self.resource_group_location,
                tags=self.tags,
                kind=self.kind,
                type=self.type,
                app_service_plan_name=self.app_service_plan_name,
                worker_tier_name=self.worker_tier_name,
                admin_site_name=self.admin_site_name,
                hosting_environment_profile=self.hosting_environment_profile,
                per_site_scaling=self.per_site_scaling,
                reserved=self.reserved,
                target_worker_count=self.app_service_plan_worker_count,
                target_worker_size_id=self.app_service_plan_worker_size_id,
                sku=sku_params
            )

            poller = self.web_client.app_service_plans.create_or_update(
                self.resource_group_name,
                self.app_service_plan_name,
                app_service_plan_params
            )

            self.get_poller_result(poller)

        except AzureHttpError as e:
            self.log('Error attempting to create App Service Plan')
            self.fail('Error create the App Service Plan: {0}'.format(
                str(e)
            ))

    def delete_appserviceplan(self):
        self.log('Deleting App Service Plan {0}'.format(
            self.app_service_plan_name
        ))

        try:
            poller = self.web_client.app_service_plans.delete(
                self.resource_group_name,
                self.app_service_plan_name
            )
            self.get_poller_result(poller)

        except AzureHttpError as e:
            self.log('Deleting App Service Plan {0} failed.')
            self.fail('Error deleting the App Service Plan: {0}'.format(
                str(e)
            ))


def main():
    AzureRMAppServicePlan()

if __name__ == '__main__':
    main()
