from app.services.discovery.base import BaseDiscoveryEngine


class CloudDiscoveryEngine(BaseDiscoveryEngine):
    """Discover assets across cloud providers (AWS, Azure, GCP)."""

    async def validate_target(self, target: str) -> bool:
        """Validate cloud provider name."""
        return target.lower() in ("aws", "azure", "gcp", "alibaba", "digital_ocean")

    async def discover(self, target: str, credentials: dict = None, **kwargs) -> dict:
        """Discover cloud assets for the given provider."""
        provider = target.lower()

        if provider == "aws":
            return await self._discover_aws(credentials)
        elif provider == "azure":
            return await self._discover_azure(credentials)
        elif provider == "gcp":
            return await self._discover_gcp(credentials)
        else:
            return {"error": f"Unsupported provider: {provider}"}

    async def _discover_aws(self, credentials: dict) -> dict:
        """Discover AWS resources."""
        import boto3

        results = {
            "provider": "aws",
            "resources": [],
            "regions": [],
        }

        try:
            session = boto3.Session(
                aws_access_key_id=credentials.get("access_key_id"),
                aws_secret_access_key=credentials.get("secret_access_key"),
                region_name=credentials.get("region", "us-east-1"),
            )

            # EC2 Instances
            ec2 = session.client("ec2")
            instances = ec2.describe_instances()
            for reservation in instances["Reservations"]:
                for instance in reservation["Instances"]:
                    self.add_asset(
                        {
                            "name": instance.get(
                                "PrivateDnsName", instance["InstanceId"]
                            ),
                            "asset_type": "cloud_resource",
                            "resource_type": "ec2_instance",
                            "resource_id": instance["InstanceId"],
                            "provider": "aws",
                            "region": instance.get("Placement", {}).get(
                                "AvailabilityZone", ""
                            ),
                            "public_ip": instance.get("PublicIpAddress"),
                            "private_ip": instance.get("PrivateIpAddress"),
                            "state": instance["State"]["Name"],
                            "tags": {
                                t["Key"]: t["Value"] for t in instance.get("Tags", [])
                            },
                            "discovery_method": "cloud_api",
                            "metadata": {
                                "instance_type": instance.get("InstanceType"),
                                "vpc_id": instance.get("VpcId"),
                                "subnet_id": instance.get("SubnetId"),
                                "security_groups": [
                                    sg["GroupId"]
                                    for sg in instance.get("SecurityGroups", [])
                                ],
                            },
                        }
                    )

            # S3 Buckets
            s3 = session.client("s3")
            buckets = s3.list_buckets()
            for bucket in buckets["Buckets"]:
                self.add_asset(
                    {
                        "name": bucket["Name"],
                        "asset_type": "cloud_resource",
                        "resource_type": "s3_bucket",
                        "provider": "aws",
                        "discovery_method": "cloud_api",
                        "metadata": {
                            "creation_date": bucket["CreationDate"].isoformat(),
                        },
                    }
                )

            # RDS Instances
            rds = session.client("rds")
            db_instances = rds.describe_db_instances()
            for db in db_instances["DBInstances"]:
                self.add_asset(
                    {
                        "name": db["DBInstanceIdentifier"],
                        "asset_type": "cloud_resource",
                        "resource_type": "rds_instance",
                        "provider": "aws",
                        "region": db.get("DBSubnetGroup", {}).get("VpcId", ""),
                        "discovery_method": "cloud_api",
                        "metadata": {
                            "engine": db.get("Engine"),
                            "engine_version": db.get("EngineVersion"),
                            "status": db.get("DBInstanceStatus"),
                            "publicly_accessible": db.get("PubliclyAccessible", False),
                        },
                    }
                )

            # Lambda Functions
            lambda_client = session.client("lambda")
            functions = lambda_client.list_functions()
            for func in functions["Functions"]:
                self.add_asset(
                    {
                        "name": func["FunctionName"],
                        "asset_type": "serverless",
                        "resource_type": "lambda_function",
                        "provider": "aws",
                        "discovery_method": "cloud_api",
                        "metadata": {
                            "runtime": func.get("Runtime"),
                            "handler": func.get("Handler"),
                            "role": func.get("Role"),
                            "vpc_config": func.get("VpcConfig"),
                        },
                    }
                )

        except Exception as e:
            self.logger.error("aws_discovery_failed", error=str(e))
            return {"error": str(e)}

        return results

    async def _discover_azure(self, credentials: dict) -> dict:
        """Discover Azure resources."""
        results = {
            "provider": "azure",
            "resources": [],
        }

        try:
            from azure.identity import ClientSecretCredential
            from azure.mgmt.resource import ResourceManagementClient

            credential = ClientSecretCredential(
                tenant_id=credentials["tenant_id"],
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
            )

            subscription_id = credentials.get("subscription_id")
            client = ResourceManagementClient(credential, subscription_id)

            for resource in client.resources.list():
                self.add_asset(
                    {
                        "name": resource.name,
                        "asset_type": "cloud_resource",
                        "resource_type": resource.type,
                        "resource_id": resource.id,
                        "provider": "azure",
                        "region": resource.location,
                        "discovery_method": "cloud_api",
                        "metadata": {
                            "resource_group": resource.id.split("/")[4]
                            if "/" in resource.id
                            else "",
                            "tags": resource.tags or {},
                        },
                    }
                )

        except Exception as e:
            self.logger.error("azure_discovery_failed", error=str(e))
            return {"error": str(e)}

        return results

    async def _discover_gcp(self, credentials: dict) -> dict:
        """Discover GCP resources."""
        results = {
            "provider": "gcp",
            "resources": [],
        }

        try:
            from google.cloud import resourcemanager_v3

            client = resourcemanager_v3.ProjectsClient()

            for project in client.list_projects():
                self.add_asset(
                    {
                        "name": project.display_name,
                        "asset_type": "cloud_resource",
                        "resource_type": "gcp_project",
                        "resource_id": project.project_id,
                        "provider": "gcp",
                        "discovery_method": "cloud_api",
                        "metadata": {
                            "project_number": project.number,
                            "state": str(project.state),
                            "lifecycle": str(project.lifecycle_state),
                        },
                    }
                )

        except Exception as e:
            self.logger.error("gcp_discovery_failed", error=str(e))
            return {"error": str(e)}

        return results
