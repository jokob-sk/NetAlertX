import graphene
from graphene import ObjectType, String, Int, Boolean, List, Field, InputObjectType, Argument
import json
import sys
import os

# Register NetAlertX directories
INSTALL_PATH = os.getenv("NETALERTX_APP", "/app")
sys.path.extend([f"{INSTALL_PATH}/server"])

from logger import mylog
from const import apiPath
from helper import (
    is_random_mac,
    get_number_of_children,
    format_ip_long,
    get_setting_value,
)

# Define a base URL with the user's home directory
folder = apiPath


# --- DEVICES ---
# Pagination and Sorting Input Types
class SortOptionsInput(InputObjectType):
    field = String()
    order = String()


class FilterOptionsInput(InputObjectType):
    filterColumn = String()
    filterValue = String()


class PageQueryOptionsInput(InputObjectType):
    page = Int()
    limit = Int()
    sort = List(SortOptionsInput)
    search = String()
    status = String()
    filters = List(FilterOptionsInput)


# Device ObjectType
class Device(ObjectType):
    rowid = Int()
    devMac = String()
    devName = String()
    devOwner = String()
    devType = String()
    devVendor = String()
    devFavorite = Int()
    devGroup = String()
    devComments = String()
    devFirstConnection = String()
    devLastConnection = String()
    devLastIP = String()
    devStaticIP = Int()
    devScan = Int()
    devLogEvents = Int()
    devAlertEvents = Int()
    devAlertDown = Int()
    devSkipRepeated = Int()
    devLastNotification = String()
    devPresentLastScan = Int()
    devIsNew = Int()
    devLocation = String()
    devIsArchived = Int()
    devParentMAC = String()
    devParentPort = String()
    devIcon = String()
    devGUID = String()
    devSite = String()
    devSSID = String()
    devSyncHubNode = String()
    devSourcePlugin = String()
    devCustomProps = String()
    devStatus = String()
    devIsRandomMac = Int()
    devParentChildrenCount = Int()
    devIpLong = Int()
    devFilterStatus = String()
    devFQDN = String()
    devParentRelType = String()
    devReqNicsOnline = Int()


class DeviceResult(ObjectType):
    devices = List(Device)
    count = Int()


# --- SETTINGS ---


# Setting ObjectType
class Setting(ObjectType):
    setKey = String()
    setName = String()
    setDescription = String()
    setType = String()
    setOptions = String()
    setGroup = String()
    setValue = String()
    setEvents = String()
    setOverriddenByEnv = Boolean()


class SettingResult(ObjectType):
    settings = List(Setting)
    count = Int()

# --- LANGSTRINGS --- 

# In-memory cache for lang strings
_langstrings_cache = {}        # caches lists per file (core JSON or plugin)
_langstrings_cache_mtime = {}  # tracks last modified times

# LangString ObjectType
class LangString(ObjectType):
    langCode = String()
    langStringKey = String()
    langStringText = String()


class LangStringResult(ObjectType):
    langStrings = List(LangString)
    count = Int()

# Define Query Type with Pagination Support
class Query(ObjectType):
    # --- DEVICES ---
    devices = Field(DeviceResult, options=PageQueryOptionsInput())

    def resolve_devices(self, info, options=None):
        # mylog('none', f'[graphql_schema] resolve_devices: {self}')
        try:
            with open(folder + "table_devices.json", "r") as f:
                devices_data = json.load(f)["data"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            mylog("none", f"[graphql_schema] Error loading devices data: {e}")
            return DeviceResult(devices=[], count=0)

        # Add dynamic fields to each device
        for device in devices_data:
            device["devIsRandomMac"] = 1 if is_random_mac(device["devMac"]) else 0
            device["devParentChildrenCount"] = get_number_of_children(
                device["devMac"], devices_data
            )
            device["devIpLong"] = format_ip_long(device.get("devLastIP", ""))

        mylog("trace", f"[graphql_schema] devices_data: {devices_data}")

        # initialize total_count
        total_count = len(devices_data)

        # Apply sorting if options are provided
        if options:
            # Define status-specific filtering
            if options.status:
                status = options.status
                mylog("trace", f"[graphql_schema] Applying status filter: {status}")

                # Include devices matching criteria in UI_MY_DEVICES
                allowed_statuses = get_setting_value("UI_MY_DEVICES")
                hidden_relationships = get_setting_value("UI_hide_rel_types")
                network_dev_types = get_setting_value("NETWORK_DEVICE_TYPES")

                mylog("trace", f"[graphql_schema] allowed_statuses: {allowed_statuses}")
                mylog(
                    "trace",
                    f"[graphql_schema] hidden_relationships: {hidden_relationships}",
                )
                mylog(
                    "trace", f"[graphql_schema] network_dev_types: {network_dev_types}"
                )

                # Filtering based on the "status"
                if status == "my_devices":
                    devices_data = [
                        device
                        for device in devices_data
                        if (device.get("devParentRelType") not in hidden_relationships)
                    ]

                    devices_data = [
                        device
                        for device in devices_data
                        if (
                            (
                                device["devPresentLastScan"] == 1
                                and "online" in allowed_statuses
                            )
                            or (device["devIsNew"] == 1 and "new" in allowed_statuses)
                            or (
                                device["devPresentLastScan"] == 0
                                and device["devAlertDown"]
                                and "down" in allowed_statuses
                            )
                            or (
                                device["devPresentLastScan"] == 0
                                and "offline" in allowed_statuses
                            )
                            and device["devIsArchived"] == 0
                            or (
                                device["devIsArchived"] == 1
                                and "archived" in allowed_statuses
                            )
                        )
                    ]
                elif status == "connected":
                    devices_data = [
                        device
                        for device in devices_data
                        if device["devPresentLastScan"] == 1
                    ]
                elif status == "favorites":
                    devices_data = [
                        device for device in devices_data if device["devFavorite"] == 1
                    ]
                elif status == "new":
                    devices_data = [
                        device for device in devices_data if device["devIsNew"] == 1
                    ]
                elif status == "down":
                    devices_data = [
                        device
                        for device in devices_data
                        if device["devPresentLastScan"] == 0 and device["devAlertDown"]
                    ]
                elif status == "archived":
                    devices_data = [
                        device
                        for device in devices_data
                        if device["devIsArchived"] == 1
                    ]
                elif status == "offline":
                    devices_data = [
                        device
                        for device in devices_data
                        if device["devPresentLastScan"] == 0
                    ]
                elif status == "network_devices":
                    devices_data = [
                        device
                        for device in devices_data
                        if device["devType"] in network_dev_types
                    ]
                elif status == "all_devices":
                    devices_data = devices_data  # keep all

            # additional filters
            if options.filters:
                for filter in options.filters:
                    if filter.filterColumn and filter.filterValue:
                        devices_data = [
                            device
                            for device in devices_data
                            if str(device.get(filter.filterColumn, "")).lower()
                            == str(filter.filterValue).lower()
                        ]

            # Search data if a search term is provided
            if options.search:
                # Define static list of searchable fields
                searchable_fields = [
                    "devName",
                    "devMac",
                    "devOwner",
                    "devType",
                    "devVendor",
                    "devLastIP",
                    "devGroup",
                    "devComments",
                    "devLocation",
                    "devStatus",
                    "devSSID",
                    "devSite",
                    "devSourcePlugin",
                    "devSyncHubNode",
                    "devFQDN",
                    "devParentRelType",
                    "devParentMAC",
                ]

                search_term = options.search.lower()

                devices_data = [
                    device
                    for device in devices_data
                    if any(
                        search_term in str(device.get(field, "")).lower()
                        for field in searchable_fields  # Search only predefined fields
                    )
                ]

            # sorting
            if options.sort:
                for sort_option in options.sort:
                    devices_data = sorted(
                        devices_data,
                        key=lambda x: mixed_type_sort_key(
                            x.get(sort_option.field).lower()
                            if isinstance(x.get(sort_option.field), str)
                            else x.get(sort_option.field)
                        ),
                        reverse=(sort_option.order.lower() == "desc"),
                    )

            # capture total count after all the filtering and searching, BEFORE pagination
            total_count = len(devices_data)

            # Then apply pagination
            if options.page and options.limit:
                start = (options.page - 1) * options.limit
                end = start + options.limit
                devices_data = devices_data[start:end]

        # Convert dict objects to Device instances to enable field resolution
        devices = [Device(**device) for device in devices_data]

        return DeviceResult(devices=devices, count=total_count)

    # --- SETTINGS ---
    settings = Field(SettingResult)

    def resolve_settings(root, info):
        try:
            with open(folder + "table_settings.json", "r") as f:
                settings_data = json.load(f)["data"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            mylog("none", f"[graphql_schema] Error loading settings data: {e}")
            return SettingResult(settings=[], count=0)

        mylog("trace", f"[graphql_schema] settings_data: {settings_data}")

        # Convert to Setting objects
        settings = [Setting(**setting) for setting in settings_data]

        return SettingResult(settings=settings, count=len(settings))

    # --- LANGSTRINGS --- 
    langStrings = Field(
        LangStringResult,
        langCode=Argument(String, required=False),
        langStringKey=Argument(String, required=False)
    )

    def resolve_langStrings(self, info, langCode=None, langStringKey=None, fallback_to_en=True):
        """
        Collect language strings, optionally filtered by language code and/or string key.
        Caches in memory for performance. Can fallback to 'en_us' if a string is missing.
        """
        global _langstrings_cache, _langstrings_cache_mtime

        langStrings = []

        # --- CORE JSON FILES ---
        language_folder = '/app/front/php/templates/language/'
        if os.path.exists(language_folder):
            for filename in os.listdir(language_folder):
                if filename.endswith('.json'):
                    file_lang_code = filename.replace('.json', '')

                    # Filter by langCode if provided
                    if langCode and file_lang_code != langCode:
                        continue

                    file_path = os.path.join(language_folder, filename)
                    file_mtime = os.path.getmtime(file_path)
                    cache_key = f'core_{file_lang_code}'

                    # Use cached data if available and not modified
                    if cache_key in _langstrings_cache_mtime and _langstrings_cache_mtime[cache_key] == file_mtime:
                        lang_list = _langstrings_cache[cache_key]
                    else:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                lang_list = [
                                    LangString(
                                        langCode=file_lang_code,
                                        langStringKey=key,
                                        langStringText=value
                                    ) for key, value in data.items()
                                ]
                                _langstrings_cache[cache_key] = lang_list
                                _langstrings_cache_mtime[cache_key] = file_mtime
                        except (FileNotFoundError, json.JSONDecodeError) as e:
                            mylog('none', f'[graphql_schema] Error loading core language strings from {filename}: {e}')
                            lang_list = []

                    langStrings.extend(lang_list)

        # --- PLUGIN STRINGS ---
        plugin_file = folder + 'table_plugins_language_strings.json'
        try:
            file_mtime = os.path.getmtime(plugin_file)
            cache_key = 'plugin'
            if cache_key in _langstrings_cache_mtime and _langstrings_cache_mtime[cache_key] == file_mtime:
                plugin_list = _langstrings_cache[cache_key]
            else:
                with open(plugin_file, 'r', encoding='utf-8') as f:
                    plugin_data = json.load(f).get("data", [])
                    plugin_list = [
                        LangString(
                            langCode=entry.get("Language_Code"),
                            langStringKey=entry.get("String_Key"),
                            langStringText=entry.get("String_Value")
                        ) for entry in plugin_data
                    ]
                    _langstrings_cache[cache_key] = plugin_list
                    _langstrings_cache_mtime[cache_key] = file_mtime
        except (FileNotFoundError, json.JSONDecodeError) as e:
            mylog('none', f'[graphql_schema] Error loading plugin language strings from {plugin_file}: {e}')
            plugin_list = []

        # Filter plugin strings by langCode if provided
        if langCode:
            plugin_list = [p for p in plugin_list if p.langCode == langCode]

        langStrings.extend(plugin_list)

        # --- Filter by string key if requested ---
        if langStringKey:
            langStrings = [ls for ls in langStrings if ls.langStringKey == langStringKey]

        # --- Fallback to en_us if enabled and requested lang is missing ---
        if fallback_to_en and langCode and langCode != "en_us":
            for i, ls in enumerate(langStrings):
                if not ls.langStringText:  # empty string triggers fallback
                    # try to get en_us version
                    en_list = _langstrings_cache.get("core_en_us", [])
                    en_list += [p for p in _langstrings_cache.get("plugin", []) if p.langCode == "en_us"]
                    en_fallback = [e for e in en_list if e.langStringKey == ls.langStringKey]
                    if en_fallback:
                        langStrings[i] = en_fallback[0]

        mylog('trace', f'[graphql_schema] Collected {len(langStrings)} language strings '
                    f'(langCode={langCode}, key={langStringKey}, fallback_to_en={fallback_to_en})')

        return LangStringResult(langStrings=langStrings, count=len(langStrings))

# helps sorting inconsistent dataset mixed integers and strings
def mixed_type_sort_key(value):
    if value is None or value == "":
        return (2, "")  # Place None or empty strings last
    try:
        return (0, int(value))  # Integers get priority
    except (ValueError, TypeError):
        return (1, str(value))  # Strings come next


# Schema Definition
devicesSchema = graphene.Schema(query=Query)
