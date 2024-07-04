# readme

a proxy that given the URL injects transparently the authentication
saves the requests to a local cache - so you won't be spending for repeated api calls (POST; check the create_cache_key method if you need more)

check qa/sample.http to see how to use it

## use case

strip api keys from your tests leveraging vcr or similar

## sample secrets file

save this into secrets/secrets.yaml

```yaml
api.anthropic.com:
  header: x-api-key
  value: sk-ant-yeahhereyouputyourkey
```

add any number of domains
