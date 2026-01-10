function getApiBase()
{
    let apiBase = getSetting("BACKEND_API_URL");

    if(apiBase == "")
    {
        const protocol = window.location.protocol.replace(':', '');
        const host = window.location.hostname;
        const port = getSetting("GRAPHQL_PORT");

        apiBase = `${protocol}://${host}:${port}`;
    }

    return apiBase;
}