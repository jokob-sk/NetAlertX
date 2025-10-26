# Webhook Secrets

> [!NOTE]
> You need to enable the `WEBHOOK` plugin first in order to follow this guide. See the [Plugins guide](./PLUGINS.md) for details.  

## How does the signing work?

NetAlertX will use the configured secret to create a hash signature of the request body. This SHA256-HMAC signature will appear in the `X-Webhook-Signature` header of each request to the webhook target URL. You can use the value of this header to validate the request was sent by NetAlertX.

## Activating webhook signatures

All you need to do in order to add a signature to the request headers is to set the `WEBHOOK_SECRET` config value to a non-empty string.

## Validating webhook deliveries

There are a few things to keep in mind when validating the webhook delivery:

- NetAlertX uses an HMAC hex digest to compute the hash
- The signature in the `X-Webhook-Signature` header always starts with `sha256=`
- The hash signature is generated using the configured `WEBHOOK_SECRET` and the request body.
- Never use a plain `==` operator. Instead, consider using a method like [`secure_compare`](https://www.rubydoc.info/gems/rack/Rack%2FUtils:secure_compare) or [`crypto.timingSafeEqual`](https://nodejs.org/api/crypto.html#cryptotimingsafeequala-b), which performs a "constant time" string comparison to help mitigate certain timing attacks against regular equality operators, or regular loops in JIT-optimized languages.

## Testing the webhook payload validation

You can use the following secret and payload to verify that your implementation is working correctly.

`secret`: 'this is my secret'

`payload`: '{"test":"this is a test body"}'

If your implementation is correct, the signature you generated should match the following:

`signature`: bed21fcc34f98e94fd71c7edb75e51a544b4a3b38b069ebaaeb19bf4be8147e9

`X-Webhook-Signature`: sha256=bed21fcc34f98e94fd71c7edb75e51a544b4a3b38b069ebaaeb19bf4be8147e9

## More information

If you want to learn more about webhook security, take a look at [GitHub's webhook documentation](https://docs.github.com/en/webhooks/about-webhooks).

You can find examples for validating a webhook delivery [here](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries#examples).
