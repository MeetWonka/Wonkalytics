// Your API request 
const exampleAuthInfo = {
    // Optional authinfo key
    auth_info:    {
        clientPrincipal:  {
            claims: [
            { typ: "iss", val: "https://login.microsoftonline.com/{SOME_TENANT_ID}/v2.0" },
            { typ: "name", val: "Test username" },
            { typ: "http://schemas.microsoft.com/identity/claims/objectidentifier", val: "{SOME_USER_ID}" },
            { typ: "preferred_username", val: "test@testmail.eu" },
            { typ: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier", val: "yp7A9ctNvtDWYXMLCNS9qaokNoorgC3VQQPmpbwsqoM" },
            { typ: "http://schemas.microsoft.com/identity/claims/tenantid", val: "{SOME_TENANT_ID}" },
            { typ: "ver", val: "2.0" }],
            identityProvider: "aad",
            userDetails: "test@testmail.eu",
            userId: "{SOME_USER_ID}",
            userRoles: [
                "authenticated",
                "anonymous"
            ],
        }
    }
}