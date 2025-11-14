from modrinth_api_wrapper import Client

client = Client()

def query(mod_name, client_side='any', server_side='any'):
    results = client.search_project(query="sodium")

    mods = {}

    if not results.hits:
        return []

    for i, project in enumerate(results.hits, 1):
        print(f"\n{i}. {project.title}")
        print(f"   ID: {project.project_id}")
        print(f"   Slug: {project.slug}")
        print(f"   描述: {project.description[:100]}...")  # 只显示前100个字符
        print(f"   下载量: {project.downloads}")
        print(f"   关注数: {project.follows}")
        if client_side != 'any' and project.client_side != client_side:
            continue
        if server_side != 'any' and project.client_side != client_side:
            continue
        mods[id] = {
            'title': project.title,
            'slug': project.slug,
            'description': project.description,
            'author': project.author,
            'date_modified': project.date_modified,
            'date_create': project.date_created,
            'downloads': project.downloads,
            'follows': project.follows,
            'icon_url': project.icon_url,
            'server_side': project.server_side,
            'client_side': project.client_side,
        }