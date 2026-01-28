function getApiBase()
{
    let apiBase = getSetting("BACKEND_API_URL");

    if(apiBase == "")
    {
        // Default to the same-origin proxy bridge
        apiBase = "/server";
    }

    // Remove trailing slash for consistency
    return apiBase.replace(/\/$/, '');
}