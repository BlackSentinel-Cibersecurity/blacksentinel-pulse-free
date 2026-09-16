import re

import httpx

from app.services.discovery.base import BaseDiscoveryEngine


class GitHubDiscoveryEngine(BaseDiscoveryEngine):
    """Discover assets in GitHub organizations - repos, secrets, configs."""

    SECRET_PATTERNS = [
        (r"api[_-]?key\s*[:=]\s*['\"]([^'\"]+)['\"]", "API Key"),
        (r"secret[_-]?key\s*[:=]\s*['\"]([^'\"]+)['\"]", "Secret Key"),
        (r"password\s*[:=]\s*['\"]([^'\"]+)['\"]", "Password"),
        (r"token\s*[:=]\s*['\"]([^'\"]+)['\"]", "Token"),
        (
            r"aws[_-]?(?:access|secret)[_-]?(?:key|id)\s*[:=]\s*['\"]([^'\"]+)['\"]",
            "AWS Credential",
        ),
        (r"private[_-]?key\s*[:=]\s*['\"]([^'\"]+)['\"]", "Private Key"),
        (r"connection[_-]?string\s*[:=]\s*['\"]([^'\"]+)['\"]", "Connection String"),
        (r"mongodb(?:\+srv)?://[^'\"]+", "MongoDB URI"),
        (r"postgres(?:ql)?://[^'\"]+", "PostgreSQL URI"),
        (r"mysql://[^'\"]+", "MySQL URI"),
        (r"redis://[^'\"]+", "Redis URI"),
    ]

    async def validate_target(self, target: str) -> bool:
        """Validate GitHub organization name."""
        return bool(re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$", target))

    async def discover(self, target: str, token: str = None, **kwargs) -> dict:
        """Discover GitHub organization assets."""
        results = {
            "organization": target,
            "repositories": [],
            "secrets_found": [],
            "config_files": [],
            "members": [],
            "domains": [],
        }

        headers = {"Authorization": f"token {token}"} if token else {}
        base_url = "https://api.github.com"

        async with httpx.AsyncClient(headers=headers, timeout=30) as client:
            # Get organization info
            org_response = await client.get(f"{base_url}/orgs/{target}")
            if org_response.status_code == 200:
                org_data = org_response.json()
                results["organization_info"] = {
                    "name": org_data.get("name"),
                    "description": org_data.get("description"),
                    "blog": org_data.get("blog"),
                    "email": org_data.get("email"),
                    "public_repos": org_data.get("public_repos"),
                }

            # List repositories
            page = 1
            while True:
                repos_response = await client.get(
                    f"{base_url}/orgs/{target}/repos",
                    params={"page": page, "per_page": 100, "type": "all"},
                )
                if repos_response.status_code != 200:
                    break

                repos = repos_response.json()
                if not repos:
                    break

                for repo in repos:
                    repo_data = {
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "private": repo["private"],
                        "description": repo.get("description"),
                        "language": repo.get("language"),
                        "default_branch": repo.get("default_branch"),
                        "topics": repo.get("topics", []),
                        "has_wiki": repo.get("has_wiki"),
                        "has_pages": repo.get("has_pages"),
                        "open_issues": repo.get("open_issues_count"),
                    }
                    results["repositories"].append(repo_data)

                    # Create asset for each repo
                    self.add_asset(
                        {
                            "name": repo["full_name"],
                            "asset_type": "repository",
                            "discovery_method": "github_api",
                            "metadata": repo_data,
                        }
                    )

                    # Check for pages (exposed sites)
                    if repo.get("has_pages"):
                        pages_url = f"https://{target}.github.io/{repo['name']}"
                        self.add_asset(
                            {
                                "name": pages_url,
                                "asset_type": "web_application",
                                "url": pages_url,
                                "discovery_method": "github_pages",
                            }
                        )

                page += 1
                await self._rate_limit(0.5)

            # Search for exposed secrets in public repos
            secret_search = await client.get(
                f"{base_url}/search/code",
                params={
                    "q": f"org:{target} filename:.env OR filename:credentials OR filename:config",
                    "per_page": 50,
                },
            )
            if secret_search.status_code == 200:
                for item in secret_search.json().get("items", []):
                    results["config_files"].append(
                        {
                            "repository": item["repository"]["full_name"],
                            "path": item["path"],
                            "name": item["name"],
                        }
                    )

        return results
