import json
import uuid
from typing import List, Dict, Optional, Set
from app.cache.redis import redis_client
from app.core.logger import logger
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryTreeResponse, CategoryResponse


class RecommendationService:
    CACHE_KEY_TREE = "ecommerce:categories:tree"
    CACHE_KEY_DESCENDANTS = "ecommerce:categories:descendants:"
    CACHE_TTL = 86400  # 24 hours

    def __init__(self):
        self.category_repo = CategoryRepository()

    def get_category_tree(self) -> List[dict]:
        """
        Retrieves the full category tree, using Redis caching if available.
        """
        client = redis_client.client
        if client:
            try:
                cached = client.get(self.CACHE_KEY_TREE)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        # Compute tree from database
        all_categories = self.category_repo.get_all(active_only=True)
        tree = self._build_tree(all_categories)

        if client:
            try:
                client.set(self.CACHE_KEY_TREE, json.dumps(tree), ex=self.CACHE_TTL)
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")

        return tree

    def get_descendant_category_ids(self, root_category_id: uuid.UUID) -> List[uuid.UUID]:
        """
        Uses Depth-First Search (DFS) to traverse the category tree and gather
        all subcategory IDs belonging to the given root category.
        """
        client = redis_client.client
        cache_key = f"{self.CACHE_KEY_DESCENDANTS}{root_category_id}"

        if client:
            try:
                cached = client.get(cache_key)
                if cached:
                    return [uuid.UUID(cat_id) for cat_id in json.loads(cached)]
            except Exception as e:
                logger.warning(f"Redis get descendants failed: {e}")

        all_categories = self.category_repo.get_all(active_only=True)
        adjacency_list: Dict[uuid.UUID, List[uuid.UUID]] = {}
        for cat in all_categories:
            if cat.parent_id:
                adjacency_list.setdefault(cat.parent_id, []).append(cat.id)

        descendant_ids: List[uuid.UUID] = []
        visited: Set[uuid.UUID] = set()

        def dfs(current_id: uuid.UUID):
            if current_id in visited:
                return
            visited.add(current_id)
            descendant_ids.append(current_id)
            for child_id in adjacency_list.get(current_id, []):
                dfs(child_id)

        dfs(root_category_id)

        if client:
            try:
                serialized = json.dumps([str(cat_id) for cat_id in descendant_ids])
                client.set(cache_key, serialized, ex=self.CACHE_TTL)
            except Exception as e:
                logger.warning(f"Redis set descendants failed: {e}")

        return descendant_ids

    def invalidate_category_cache(self) -> None:
        """
        Invalidates category tree and descendant caches upon catalog mutations.
        """
        client = redis_client.client
        if not client:
            return

        try:
            client.delete(self.CACHE_KEY_TREE)
            # Find and delete all descendant keys
            cursor = 0
            while True:
                cursor, keys = client.scan(cursor=cursor, match=f"{self.CACHE_KEY_DESCENDANTS}*", count=100)
                if keys:
                    client.delete(*keys)
                if cursor == 0:
                    break
            logger.info("Category cache successfully invalidated.")
        except Exception as e:
            logger.warning(f"Failed to invalidate category cache: {e}")

    def _build_tree(self, categories: list) -> List[dict]:
        category_map = {}
        root_categories = []

        for cat in categories:
            node = {
                "id": str(cat.id),
                "name": cat.name,
                "slug": cat.slug,
                "description": cat.description,
                "parent_id": str(cat.parent_id) if cat.parent_id else None,
                "is_active": cat.is_active,
                "children": [],
            }
            category_map[cat.id] = node

        for cat in categories:
            node = category_map[cat.id]
            if cat.parent_id and cat.parent_id in category_map:
                category_map[cat.parent_id]["children"].append(node)
            elif not cat.parent_id:
                root_categories.append(node)

        return root_categories
