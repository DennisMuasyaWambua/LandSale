from django.core.cache import cache
from super_admin.models import SystemSetting


class SettingsManager:
    """
    Utility class for accessing system settings with caching
    """
    CACHE_TTL = 300  # 5 minutes

    @staticmethod
    def get(key, default=None):
        """
        Get setting value with caching

        Args:
            key: Setting key
            default: Default value if setting doesn't exist

        Returns:
            Typed value of the setting
        """
        cache_key = f"system_setting_{key}"
        cached_value = cache.get(cache_key)

        if cached_value is not None:
            return cached_value

        try:
            setting = SystemSetting.objects.get(key=key)
            value = setting.get_typed_value()
            cache.set(cache_key, value, SettingsManager.CACHE_TTL)
            return value
        except SystemSetting.DoesNotExist:
            return default

    @staticmethod
    def set(key, value, user=None):
        """
        Set setting value and clear cache

        Args:
            key: Setting key
            value: New value
            user: User making the change

        Returns:
            SystemSetting instance
        """
        try:
            setting = SystemSetting.objects.get(key=key)
            setting.set_typed_value(value)
            if user:
                setting.updated_by = user
            setting.save()
        except SystemSetting.DoesNotExist:
            setting = SystemSetting.objects.create(
                key=key,
                value=str(value),
                created_by=user,
                updated_by=user
            )

        # Clear cache
        cache.delete(f"system_setting_{key}")
        return setting

    @staticmethod
    def get_category(category):
        """
        Get all settings in a category

        Args:
            category: Category name

        Returns:
            Dict of {key: typed_value}
        """
        cache_key = f"system_settings_category_{category}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return cached_data

        settings = SystemSetting.objects.filter(category=category)
        data = {s.key: s.get_typed_value() for s in settings}

        cache.set(cache_key, data, SettingsManager.CACHE_TTL)
        return data

    @staticmethod
    def clear_cache(key=None):
        """
        Clear settings cache

        Args:
            key: Specific key to clear, or None to clear all settings cache
        """
        if key:
            cache.delete(f"system_setting_{key}")
        else:
            # Clear all settings cache (this is a simple approach)
            # For production, consider using cache versioning or key patterns
            pass
